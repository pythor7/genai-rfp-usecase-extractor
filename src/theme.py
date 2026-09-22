"""Visual system for the RFP Requirements Intelligence Dashboard."""
from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List
import streamlit as st

NAVY = "#10233F"
NAVY_2 = "#17345E"
BLUE = "#2E6FAD"
BLUE_SOFT = "#EAF3FB"
TEAL = "#198A87"
TEAL_SOFT = "#E8F6F5"
AMBER = "#C98318"
AMBER_SOFT = "#FFF5E4"
RED = "#C74A45"
RED_SOFT = "#FDEDEC"
GREEN = "#25805A"
GREEN_SOFT = "#EAF7F0"
PURPLE = "#6F5AA8"
PURPLE_SOFT = "#F1EEFA"
BG = "#F4F7FB"
CARD = "#FFFFFF"
BORDER = "#DCE4EE"
TEXT = "#1E2B3C"
MUTED = "#65758B"
WHITE = "#FFFFFF"
FONT = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {{ --navy:{NAVY}; --blue:{BLUE}; --bg:{BG}; --border:{BORDER}; --text:{TEXT}; --muted:{MUTED}; }}
html, body, [class*="css"] {{ font-family:{FONT}; color:{TEXT}; }}
.stApp {{ background:{BG}; }}
.block-container {{ max-width:1500px; padding-top:1.35rem; padding-bottom:3rem; }}
h1,h2,h3,h4 {{ color:{NAVY}; font-weight:700; letter-spacing:-.02em; }}
h1 {{ font-size:2rem !important; }}
h2 {{ font-size:1.35rem !important; }}
h3 {{ font-size:1.05rem !important; }}
[data-testid="stSidebar"] {{ background:{NAVY}; border-right:0; }}
[data-testid="stSidebar"] * {{ color:#EAF1FA; }}
[data-testid="stSidebar"] .stCaption {{ color:#AFC0D7 !important; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{ background:#17345E; border:1px dashed #5F7898 !important; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {{ color:#DDE8F5 !important; }}
[data-testid="stSidebar"] .stButton button {{ background:#FFFFFF !important; color:{NAVY} !important; border:0 !important; }}
.stButton > button {{ border-radius:9px !important; font-weight:600 !important; min-height:2.5rem; }}
button[kind="primary"], .stButton > button[kind="primary"] {{ background:{BLUE} !important; border-color:{BLUE} !important; color:white !important; box-shadow:0 4px 12px rgba(46,111,173,.18); }}
button[kind="primary"]:hover {{ background:{NAVY_2} !important; border-color:{NAVY_2} !important; }}
[data-testid="stFileUploaderDropzone"] {{ background:white; border:1px dashed #AFC0D4 !important; border-radius:12px; }}
.stTabs [data-baseweb="tab-list"] {{ gap:2rem; border-bottom:1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{ font-weight:600; color:{MUTED}; padding-left:.15rem; padding-right:.15rem; }}
.stTabs [aria-selected="true"] {{ color:{BLUE} !important; border-bottom-color:{BLUE} !important; }}
[data-testid="stExpander"] {{ background:white; border:1px solid {BORDER} !important; border-radius:10px !important; }}
[data-testid="stDataEditor"] {{ border:1px solid {BORDER}; border-radius:10px; overflow:hidden; }}
.stAlert {{ border-radius:9px; }}
hr {{ border-color:{BORDER}; }}

/* Header */
.mis-header {{ display:flex; justify-content:space-between; align-items:center; gap:20px; background:linear-gradient(135deg,{NAVY},{NAVY_2}); color:white; border-radius:14px; padding:24px 28px; margin-bottom:18px; box-shadow:0 10px 30px rgba(16,35,63,.12); }}
.mis-header .eyebrow {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.14em; opacity:.72; font-weight:700; }}
.mis-header h1 {{ color:white !important; margin:.25rem 0 .35rem; font-size:1.85rem !important; }}
.mis-header p {{ margin:0; color:#D8E5F4; font-size:.88rem; max-width:850px; line-height:1.45; }}
.report-card-title {{ color:{NAVY}; font-size:.92rem; font-weight:800; margin-bottom:5px; }}
.report-card-desc {{ color:{MUTED}; font-size:.75rem; line-height:1.45; }}

/* Cards */
.card {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; box-shadow:0 2px 9px rgba(25,45,70,.04); }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:14px 0 18px; }}
.kpi {{ background:white; border:1px solid {BORDER}; border-radius:11px; padding:15px 17px; position:relative; overflow:hidden; min-height:91px; }}
.kpi:before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:{BLUE}; }}
.kpi.teal:before {{ background:{TEAL}; }} .kpi.amber:before {{ background:{AMBER}; }} .kpi.red:before {{ background:{RED}; }} .kpi.purple:before {{ background:{PURPLE}; }}
.kpi .label {{ color:{MUTED}; font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }}
.kpi .value {{ color:{NAVY}; font-size:1.65rem; font-weight:800; margin-top:5px; line-height:1; }}
.kpi .sub {{ color:{MUTED}; font-size:.69rem; margin-top:6px; }}

.section-title {{ display:flex; justify-content:space-between; align-items:end; margin:18px 0 9px; }}
.section-title .title {{ font-size:1.02rem; font-weight:750; color:{NAVY}; }}
.section-title .hint {{ font-size:.72rem; color:{MUTED}; }}
.panel {{ background:white; border:1px solid {BORDER}; border-radius:12px; padding:17px 18px; }}

/* Charts */
.bar-row {{ display:grid; grid-template-columns:150px 1fr 45px; gap:10px; align-items:center; margin:11px 0; }}
.bar-label {{ font-size:.76rem; color:{TEXT}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bar-track {{ height:9px; background:#EEF2F7; border-radius:99px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:99px; background:{BLUE}; }}
.bar-value {{ font-size:.75rem; color:{MUTED}; text-align:right; font-weight:700; }}
.status-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
.status-card {{ border:1px solid {BORDER}; border-radius:9px; padding:12px; }}
.status-card .num {{ font-size:1.3rem; font-weight:800; }}
.status-card .lbl {{ font-size:.7rem; color:{MUTED}; margin-top:2px; }}
.status-card.ok {{ background:{GREEN_SOFT}; }} .status-card.review {{ background:{RED_SOFT}; }} .status-card.info {{ background:{BLUE_SOFT}; }}

/* Upload hero */
.upload-hero {{ background:white; border:1px solid {BORDER}; border-radius:14px; padding:21px 23px; margin-bottom:15px; }}
.upload-hero .title {{ font-size:1.05rem; font-weight:750; color:{NAVY}; }}
.upload-hero .desc {{ color:{MUTED}; font-size:.8rem; margin:4px 0 13px; }}
.file-meta {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:9px; }}
.file-chip {{ background:{BLUE_SOFT}; color:{BLUE}; border-radius:7px; padding:5px 9px; font-size:.7rem; font-weight:600; }}

/* Document summary */
.doc-card {{ display:flex; align-items:center; gap:14px; padding:13px 16px; background:white; border:1px solid {BORDER}; border-radius:10px; }}
.doc-icon {{ width:42px; height:42px; border-radius:10px; display:grid; place-items:center; background:{RED_SOFT}; color:{RED}; font-size:1.2rem; }}
.doc-name {{ font-weight:700; color:{NAVY}; font-size:.86rem; }} .doc-detail {{ color:{MUTED}; font-size:.7rem; margin-top:3px; }}

/* Hierarchy */
.h-section {{ margin:10px 0; border:1px solid {BORDER}; border-radius:11px; background:white; overflow:hidden; }}
.h-section-head {{ padding:12px 15px; background:#F8FAFD; font-weight:750; color:{NAVY}; border-bottom:1px solid {BORDER}; }}
.h-sub {{ padding:8px 15px 2px; color:{BLUE}; font-size:.76rem; font-weight:700; }}
.req-card {{ margin:7px 15px 11px; border:1px solid {BORDER}; border-left:3px solid {BLUE}; border-radius:8px; padding:11px 13px; background:white; }}
.req-card.flagged {{ border-left-color:{RED}; background:#FFFCFC; }}
.req-id {{ display:inline-block; background:{BLUE_SOFT}; color:{BLUE}; padding:3px 7px; border-radius:5px; font-size:.65rem; font-weight:700; margin-bottom:5px; }}
.req-card.flagged .req-id {{ background:{RED_SOFT}; color:{RED}; }}
.req-text {{ color:{TEXT}; font-size:.79rem; line-height:1.45; }}
.req-meta {{ color:{MUTED}; font-size:.65rem; margin-top:7px; }}
.req-flag {{ color:{RED}; font-size:.67rem; margin-top:6px; font-weight:600; }}

@media(max-width:1000px) {{ .kpi-grid {{ grid-template-columns:repeat(2,1fr); }} .mis-header {{ align-items:flex-start; }} }}
</style>
"""


def render_header(title: str, subtitle: str) -> None:
    """Render the application header without a decorative MIS badge."""
    st.markdown(
        f'''<div class="mis-header"><div><div class="eyebrow">RFP Intelligence</div>
        <h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div></div>''',
        unsafe_allow_html=True,
    )


def render_status_pill(state: str, text: str) -> None:
    palette = {"ok": GREEN, "warn": AMBER, "error": RED}
    color = palette.get(state, MUTED)
    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;font-size:.78rem;margin:7px 0"><span style="width:8px;height:8px;border-radius:50%;background:{color};display:inline-block"></span>{escape(text)}</div>', unsafe_allow_html=True)


def render_config_line(label: str, value: str) -> None:
    st.markdown(f'<div style="font-size:.7rem;color:#AFC0D7;padding:3px 0"><b style="color:white">{escape(label)}</b> &nbsp; {escape(value)}</div>', unsafe_allow_html=True)


def render_kpis(items: List[Dict[str, Any]]) -> None:
    html = '<div class="kpi-grid">'
    for item in items:
        tone = escape(str(item.get("tone", "")))
        html += f'<div class="kpi {tone}"><div class="label">{escape(str(item["label"]))}</div><div class="value">{escape(str(item["value"]))}</div><div class="sub">{escape(str(item.get("sub", "")))}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_section_title(title: str, hint: str = "") -> None:
    st.markdown(f'<div class="section-title"><div class="title">{escape(title)}</div><div class="hint">{escape(hint)}</div></div>', unsafe_allow_html=True)


def render_document_card(file_name: str, page_count: int, total_chars: int) -> None:
    st.markdown(f'''<div class="doc-card"><div class="doc-icon">PDF</div><div><div class="doc-name">{escape(file_name)}</div><div class="doc-detail">{page_count:,} pages &nbsp;•&nbsp; {total_chars:,} extracted characters &nbsp;•&nbsp; page-level traceability enabled</div></div></div>''', unsafe_allow_html=True)


def render_bar_chart(items: Iterable[tuple[str, int]], max_value: int | None = None, tone: str = "blue") -> None:
    rows = list(items)
    if not rows:
        st.caption("No data available.")
        return
    max_v = max_value or max(v for _, v in rows) or 1
    fill = {"blue": BLUE, "teal": TEAL, "amber": AMBER, "purple": PURPLE}.get(tone, BLUE)
    html = ""
    for label, value in rows:
        width = max(3, min(100, (value / max_v) * 100))
        html += f'<div class="bar-row"><div class="bar-label" title="{escape(str(label))}">{escape(str(label))}</div><div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%;background:{fill}"></div></div><div class="bar-value">{int(value):,}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def render_status_cards(total: int, review: int, clean: int) -> None:
    st.markdown(f'''<div class="status-grid"><div class="status-card ok"><div class="num">{clean:,}</div><div class="lbl">Validated / no review flag</div></div><div class="status-card review"><div class="num">{review:,}</div><div class="lbl">Records requiring review</div></div><div class="status-card info"><div class="num">{total:,}</div><div class="lbl">Total extracted requirements</div></div></div>''', unsafe_allow_html=True)


def render_dossier_card(record: Dict[str, Any], format_pages_fn) -> None:
    flagged = bool(record.get("review_required"))
    reasons = "; ".join(record.get("review_reasons") or [])
    css = "req-card flagged" if flagged else "req-card"
    flag = f'<div class="req-flag">Review required: {escape(reasons or "Validation flag")}</div>' if flagged else ""
    st.markdown(f'''<div class="{css}"><span class="req-id">{escape(str(record.get("requirement_id", "")))}</span><div class="req-text">{escape(str(record.get("requirement", "")))}</div><div class="req-meta">Source page(s): {escape(format_pages_fn(record.get("source_pages")))} &nbsp;•&nbsp; Confidence: {escape(str(record.get("confidence", "")).upper())}</div>{flag}</div>''', unsafe_allow_html=True)
