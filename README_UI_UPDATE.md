# RFP Requirements Intelligence Dashboard — UI Update

The application presents processed RFPs as an enterprise-style **RFP Requirements Intelligence Dashboard**. The interface includes executive KPIs, requirement distribution, validation quality indicators, review workflow, hierarchy exploration, and management report generation.

## UI changes in this version
- Renamed the processed-RFP screen to **RFP Requirements Intelligence Dashboard**.
- Removed the decorative **MIS DASHBOARD** badge from the header.
- Corrected the Management Reports cards so raw HTML is not displayed as text.
- Preserved the extraction, validation, review, hierarchy, Excel and Word pipeline.
- Keeps report filename generation safe across Streamlit reruns.

## Run
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
