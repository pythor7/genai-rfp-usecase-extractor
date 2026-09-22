"""RFP Use Case Extractor - enterprise MIS dashboard UI."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from config import load_settings, safe_filename
from src.excel_report import ExcelReportError, build_excel_report
from src.extractor import ExtractionError, extract_requirements
from src.hierarchy import build_hierarchy, compute_stats
from src.logging_config import get_logger, setup_logging
from src.pdf_reader import PdfValidationError, read_pdf
from src.records import UNCLASSIFIED, clean_pages, format_pages
from src.theme import (
    inject_theme, render_bar_chart, render_config_line, render_document_card,
    render_dossier_card, render_header, render_kpis, render_section_title,
    render_status_cards, render_status_pill,
)
from src.validator import revalidate_after_review, validate_records
from src.word_report import WordReportError, build_word_report

SETTINGS = load_settings()
setup_logging(SETTINGS.log_level)
logger = get_logger(__name__)
st.set_page_config(page_title="RFP Requirements Intelligence Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_theme()

EDITABLE_COLUMNS = ["Section", "Sub-Section", "Feature", "Requirement", "Source Page", "Business Context"]
DISPLAY_COLUMNS = ["ID"] + EDITABLE_COLUMNS + ["Confidence", "Review", "Review Reasons"]


def init_state() -> None:
    defaults: Dict[str, Any] = {"document": None, "records": [], "summary": None, "extraction": None, "reports": {}, "ran": False}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_results() -> None:
    for key, value in {"records": [], "summary": None, "extraction": None, "reports": {}, "ran": False, "document": None}.items():
        st.session_state[key] = value


def records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in records:
        rows.append({
            "ID": r.get("requirement_id", ""), "Section": r.get("section", ""), "Sub-Section": r.get("sub_section", ""),
            "Feature": r.get("feature", ""), "Requirement": r.get("requirement", ""), "Source Page": format_pages(r.get("source_pages")),
            "Business Context": r.get("business_context", ""), "Confidence": str(r.get("confidence", "")).upper(),
            "Review": "REVIEW" if r.get("review_required") else "OK", "Review Reasons": "; ".join(r.get("review_reasons") or []),
        })
    return pd.DataFrame(rows, columns=DISPLAY_COLUMNS)


def _parse_pages(value: Any) -> List[int]:
    text = str(value or "").strip()
    if not text or text.upper() == "NOT FOUND":
        return []
    return clean_pages(text.replace(";", ",").split(","))


def dataframe_to_records(edited: pd.DataFrame, originals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {r.get("requirement_id"): r for r in originals}
    merged = []
    for _, row in edited.iterrows():
        original = by_id.get(row["ID"])
        if original is None:
            continue
        updated = dict(original)
        values = {
            "section": str(row["Section"]).strip(), "sub_section": str(row["Sub-Section"]).strip(),
            "feature": str(row["Feature"]).strip(), "requirement": str(row["Requirement"]).strip(),
            "source_pages": _parse_pages(row["Source Page"]), "business_context": str(row["Business Context"]).strip(),
        }
        if any(updated.get(k) != v for k, v in values.items()):
            updated["modified_by_reviewer"] = True
        updated.update(values)
        merged.append(updated)
    return merged


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("<div style='font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;font-weight:700;opacity:.65'>RFP Intelligence</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:1.2rem;font-weight:800;margin:4px 0 20px'>Use Case Extractor</div>", unsafe_allow_html=True)
        if SETTINGS.use_mock_data:
            render_status_pill("warn", "Mock mode enabled")
        elif SETTINGS.google_api_key:
            render_status_pill("ok", "Gemini API configured")
        else:
            render_status_pill("error", "Gemini API key not found")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:#91A8C1;font-weight:700'>Processing Configuration</div>", unsafe_allow_html=True)
        render_config_line("Model", SETTINGS.model_name)
        render_config_line("Batch", f"{SETTINGS.batch_char_budget:,} chars")
        render_config_line("Max PDF", f"{SETTINGS.max_upload_mb} MB")
        st.divider()
        st.markdown("<div style='font-size:.72rem;line-height:1.5;color:#AFC0D7'>AI extraction is followed by validation and human review. Source pages are retained for traceability.</div>", unsafe_allow_html=True)
        if st.session_state.get("ran") and st.button("Start New RFP", use_container_width=True):
            reset_results()
            st.rerun()


def run_pipeline(file_bytes: bytes, file_name: str) -> None:
    status = st.status("Processing RFP…", expanded=True)
    try:
        status.write("1/6  Upload received")
        document = read_pdf(file_bytes, file_name, max_mb=SETTINGS.max_upload_mb, min_chars_per_page=SETTINGS.min_chars_per_page_for_text_pdf)
        st.session_state.document = document
        status.write(f"2/6  PDF read: {document.page_count:,} pages / {document.total_chars:,} characters")
        if document.likely_scanned:
            status.write("     Warning: document appears partly scanned")
        status.write("3/6  Sending page batches for requirement extraction…")
        extraction = extract_requirements(document, SETTINGS, progress=lambda msg: status.write(f"     {msg}"))
        st.session_state.extraction = extraction
        status.write(f"4/6  Extracted {len(extraction.records):,} requirement(s)")
        status.write("5/6  Validating traceability, hierarchy and duplicates…")
        records, summary = validate_records(extraction.records, document.page_numbers())
        st.session_state.records, st.session_state.summary = records, summary
        status.write("6/6  Building requirements intelligence dashboard…")
        st.session_state.ran = True
        status.update(label="RFP analysis completed", state="complete", expanded=False)
    except PdfValidationError as exc:
        status.update(label="PDF could not be processed", state="error")
        st.error(str(exc)); logger.warning("PDF rejected: %s", exc)
    except ExtractionError as exc:
        status.update(label="AI extraction failed", state="error")
        st.error(str(exc)); logger.error("Extraction failed: %s", exc)
    except Exception as exc:
        status.update(label="Unexpected processing error", state="error")
        st.error("Something went wrong while processing the document. Please try again or use another PDF.")
        logger.error("Unexpected failure: %s", exc, exc_info=True)


def render_overview() -> None:
    doc = st.session_state.document
    records = st.session_state.records
    stats = compute_stats(records)
    clean = stats.requirement_count - stats.review_required_count
    render_kpis([
        {"value": f"{stats.requirement_count:,}", "label": "Requirements", "sub": "Explicit requirements extracted", "tone": ""},
        {"value": f"{stats.section_count:,}", "label": "Sections", "sub": "Business areas identified", "tone": "teal"},
        {"value": f"{stats.feature_count:,}", "label": "Features", "sub": "Capabilities represented", "tone": "purple"},
        {"value": f"{len(stats.pages_referenced):,}", "label": "Pages referenced", "sub": "Traceable source pages", "tone": "amber"},
        {"value": f"{stats.review_required_count:,}", "label": "Review queue", "sub": "Records needing attention", "tone": "red"},
    ])
    if doc:
        render_document_card(doc.file_name, doc.page_count, doc.total_chars)

    extraction = st.session_state.extraction
    if extraction:
        for warning in extraction.warnings:
            st.warning(warning)
        if extraction.has_failures:
            with st.expander("View page batches that could not be analysed"):
                st.dataframe(pd.DataFrame(extraction.failed_batches), use_container_width=True, hide_index=True)

    render_section_title("Management Overview", "Current RFP analysis snapshot")
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Requirements by section**")
        counts = Counter((r.get("section") or UNCLASSIFIED) for r in records)
        render_bar_chart(counts.most_common(10), tone="blue")
        if len(counts) > 10:
            st.caption(f"Showing top 10 of {len(counts)} sections.")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Validation status**")
        render_status_cards(stats.requirement_count, stats.review_required_count, clean)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        conf = Counter(str(r.get("confidence", "medium")).upper() for r in records)
        render_bar_chart([(k, conf.get(k, 0)) for k in ["HIGH", "MEDIUM", "LOW"]], tone="teal")
        st.markdown('</div>', unsafe_allow_html=True)

    render_section_title("Quality Indicators", "Why records entered the review queue")
    s = st.session_state.summary
    if s:
        quality = [("Missing source pages", s.missing_pages), ("Invalid page references", s.invalid_pages), ("Missing hierarchy", s.missing_hierarchy), ("Empty requirements", s.empty_requirements), ("Exact duplicates", s.exact_duplicates), ("Near duplicates", s.near_duplicates)]
        render_bar_chart([(a, b) for a, b in quality if b], tone="amber")
        if not any(v for _, v in quality):
            st.success("No validation issues are currently flagged.")


def render_review() -> None:
    records = st.session_state.records
    render_section_title("Requirement Review", "Editable audit table • corrections are re-validated")
    if not records:
        st.info("No requirements available for review.")
        return
    review_count = sum(bool(r.get("review_required")) for r in records)
    modified = sum(bool(r.get("modified_by_reviewer")) for r in records)
    a, b, c = st.columns(3)
    a.metric("Total records", len(records))
    b.metric("Review flagged", review_count)
    c.metric("Human modified", modified)
    st.caption("Edit Section, Sub-Section, Feature, Requirement, Source Page or Business Context. Then save and re-validate.")
    edited = st.data_editor(
        records_to_dataframe(records), width="stretch", hide_index=True, num_rows="fixed", key="review_editor",
        column_config={
            "ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
            "Requirement": st.column_config.TextColumn("Requirement", width="large"),
            "Source Page": st.column_config.TextColumn("Source Page", width="small"),
            "Confidence": st.column_config.TextColumn("Confidence", disabled=True, width="small"),
            "Review": st.column_config.TextColumn("Status", disabled=True, width="small"),
            "Review Reasons": st.column_config.TextColumn("Validation Reason", disabled=True, width="large"),
        },
    )
    if st.button("Save changes & re-validate", type="primary"):
        merged = dataframe_to_records(edited, records)
        validated, summary = revalidate_after_review(merged, st.session_state.document.page_numbers())
        st.session_state.records, st.session_state.summary, st.session_state.reports = validated, summary, {}
        st.success(f"Saved successfully. {summary.review_required:,} record(s) remain in the review queue.")
        st.rerun()


def render_hierarchy() -> None:
    records = st.session_state.records
    render_section_title("Requirement Hierarchy", "Section → Sub-Section → Feature → Requirement")
    tree = build_hierarchy(records)
    for section, sub_sections in tree.items():
        total = sum(len(items) for features in sub_sections.values() for items in features.values())
        st.markdown(f'<div class="h-section"><div class="h-section-head">{escape(str(section))}<span style="float:right;color:#65758B;font-size:.68rem">{total:,} requirement(s)</span></div>', unsafe_allow_html=True)
        for sub_section, features in sub_sections.items():
            if sub_section != UNCLASSIFIED:
                st.markdown(f'<div class="h-sub">{escape(str(sub_section))}</div>', unsafe_allow_html=True)
            for feature, items in features.items():
                if feature != UNCLASSIFIED:
                    st.markdown(f'<div style="padding:7px 15px 1px;font-size:.72rem;font-weight:700;color:#1E2B3C">{escape(str(feature))}</div>', unsafe_allow_html=True)
                for record in items:
                    render_dossier_card(record, format_pages)
        st.markdown('</div>', unsafe_allow_html=True)


def render_reports() -> None:
    render_section_title("Management Reports", "Generate distribution-ready Excel and Word deliverables")
    doc = st.session_state.document
    records = st.session_state.records
    if not doc or not records:
        st.info("Run an RFP extraction before generating reports.")
        return
    s = st.session_state.summary
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="panel"><div class="report-card-title">Excel MIS Report</div>'
            '<div class="report-card-desc">Detailed requirement ledger, validation status, hierarchy and traceability fields.</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="panel"><div class="report-card-title">Word Management Report</div>'
            '<div class="report-card-desc">Presentation-ready hierarchical report for business review and circulation.</div></div>',
            unsafe_allow_html=True,
        )
    if s:
        render_kpis([
            {"value": len(records), "label": "Rows", "sub": "Requirements in final dataset", "tone": ""},
            {"value": s.review_required, "label": "Review flags", "sub": "Included in report", "tone": "red"},
            {"value": len(compute_stats(records).pages_referenced), "label": "Source pages", "sub": "Referenced by requirements", "tone": "teal"},
        ])
    base = safe_filename(doc.file_name)
    if st.button("Generate Excel + Word reports", type="primary"):
        extra = {"Extraction mode": st.session_state.extraction.mode if st.session_state.extraction else "unknown", "Model": SETTINGS.model_name}
        try:
            st.session_state.reports = {
                "excel": build_excel_report(records, doc.file_name, doc.page_count, extra),
                "word": build_word_report(records, doc.file_name, doc.page_count, extra),
            }
            st.success("Both management reports are ready.")
        except (ExcelReportError, WordReportError) as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error("The reports could not be created."); logger.error("Report generation failed: %s", exc, exc_info=True)
    reports = st.session_state.reports
    if reports:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        left, right = st.columns(2)
        left.download_button("Download Excel MIS report", reports["excel"], f"{base}_MIS_requirements_{stamp}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        right.download_button("Download Word management report", reports["word"], f"{base}_MIS_requirements_{stamp}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)


def render_empty_home() -> None:
    render_header("RFP Use Case Extractor", "Transform complex RFP documents into a traceable, reviewable requirements MIS.")
    st.markdown('''<div class="upload-hero"><div class="title">Start a new RFP analysis</div><div class="desc">Upload a text-based PDF. The engine extracts explicit requirements, validates source-page traceability and prepares an executive MIS view.</div><div class="file-meta"><span class="file-chip">AI extraction</span><span class="file-chip">Page traceability</span><span class="file-chip">Human review</span><span class="file-chip">Excel + Word</span></div></div>''', unsafe_allow_html=True)


def main() -> None:
    init_state()
    render_sidebar()
    if not st.session_state.ran:
        render_empty_home()
        uploaded = st.file_uploader("Upload RFP PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            st.markdown(f'<div style="font-size:.76rem;color:#65758B;margin:8px 0 12px">Selected: <b>{escape(uploaded.name)}</b></div>', unsafe_allow_html=True)
        go = st.button("Run RFP Analysis", type="primary", disabled=uploaded is None, use_container_width=False)
        if go and uploaded is not None:
            reset_results()
            run_pipeline(uploaded.getvalue(), uploaded.name)
    else:
        doc = st.session_state.document
        render_header("RFP Requirements Intelligence Dashboard", f"Management information view for {doc.file_name if doc else 'processed RFP'}")
        tab1, tab2, tab3, tab4 = st.tabs(["Executive Overview", "Review Queue", "Requirement Hierarchy", "Management Reports"])
        with tab1: render_overview()
        with tab2: render_review()
        with tab3: render_hierarchy()
        with tab4: render_reports()


if __name__ == "__main__":
    main()
