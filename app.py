"""
app.py
Streamlit User Interface — Employee Document PII Detection & Redaction System.
Supports two document types:
  - CSV: tabular employee data (existing pipeline)
  - PDF: hybrid documents with native text and/or scanned image pages (new pipeline)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
import sys

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PII Detection & Redaction System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# High-Contrast Enterprise Theme (CSS)
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0f172a;
    }

    .app-header {
        background-color: #0f172a;
        border-bottom: 3px solid #1d4ed8;
        border-radius: 8px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.75rem;
    }
    .app-header h1 {
        color: #ffffff !important;
        font-size: 1.45rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.01em;
    }
    .app-header p {
        color: #94a3b8 !important;
        font-size: 0.875rem;
        margin: 0;
        font-weight: 400;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin: 1.5rem 0 0.85rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #cbd5e1;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.85rem;
        margin: 1rem 0 1.5rem 0;
    }
    .metric-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 1rem 1.1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }
    .metric-box.highlight {
        border-left: 4px solid #1d4ed8;
        background-color: #f8fafc;
    }
    .metric-box .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .metric-box .metric-val {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }

    .badge-container {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-info  { background-color:#eff6ff; color:#1e40af; border:1px solid #bfdbfe; }
    .badge-warn  { background-color:#fffbeb; color:#92400e; border:1px solid #fde68a; }
    .badge-native{ background-color:#f0fdf4; color:#14532d; border:1px solid #bbf7d0; }
    .badge-ocr   { background-color:#fef3c7; color:#78350f; border:1px solid #fde68a; }

    .notice-box {
        background-color: #fffbeb;
        border-left: 4px solid #d97706;
        border: 1px solid #fde68a;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        font-size: 0.85rem;
        color: #92400e;
    }

    .page-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.85rem;
    }
    .page-num { font-weight: 700; color: #1e293b; min-width: 60px; }
    .page-pii { color: #334155; }

    .stButton > button[kind="primary"] {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: 1px solid #1e40af !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.5rem !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1e40af !important;
    }
    .stDownloadButton > button {
        background-color: #047857 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: 1px solid #065f46 !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.5rem !important;
    }
    .empty-state-box {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 8px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    .empty-state-title { font-size:1rem; font-weight:600; color:#1e293b; margin-bottom:0.35rem; }
    .empty-state-desc  { font-size:0.85rem; color:#64748b; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Redaction Settings")
    st.markdown("---")

    redaction_mode = st.radio(
        "Redaction Method",
        options=["mask", "full", "tokenize"],
        format_func=lambda x: {
            "mask": "Partial Masking (081****5678)",
            "full": "Full Redaction ([REDACTED])",
            "tokenize": "Pseudo-anonymization ([EMP_001])",
        }[x],
        index=0,
        help="Partial Masking: masks intermediate characters for internal use.\n\n"
             "Full Redaction: replaces values with placeholders for external distribution.\n\n"
             "Pseudo-anonymization: consistent tokenized identifiers across the document.",
    )

    st.markdown("---")

    use_ner = st.toggle(
        "Enable spaCy NER",
        value=True,
        help="Named Entity Recognition for detecting person names across all document content.",
    )

    st.markdown("---")
    st.markdown("### Role-Based Policy")

    from redaction_policy import (
        POLICY_PROFILES, POLICY_LABELS, ALL_PII_TYPES,
        PII_TYPE_LABELS, MODE_OPTIONS, MODE_LABELS, get_policy,
    )

    policy_options = list(POLICY_LABELS.keys())
    selected_policy = st.selectbox(
        "Access Role",
        options=policy_options,
        format_func=lambda x: POLICY_LABELS[x],
        index=0,
        help="Select an organizational role to apply preset field-level redaction policies.",
    )

    active_policy = None
    if selected_policy == "custom":
        st.caption("Configure per-field redaction mode:")
        custom_policy = {}
        for pii_type in ALL_PII_TYPES:
            custom_policy[pii_type] = st.selectbox(
                PII_TYPE_LABELS[pii_type],
                options=MODE_OPTIONS,
                format_func=lambda x: MODE_LABELS[x],
                index=1,  # default to mask
                key=f"policy_{pii_type}",
            )
        active_policy = custom_policy
    elif selected_policy != "hr_manager":
        # hr_manager is effectively the default (no override needed for mask mode)
        active_policy = get_policy(selected_policy)

    st.markdown("---")
    st.markdown("### Test Dataset Generator")
    st.caption("Generate synthetic records for evaluation without real data exposure.")
    num_rows = st.slider("Record Count", min_value=10, max_value=500, value=100, step=10)

    if st.button("Generate Test CSV", use_container_width=True):
        try:
            from generate_dummy_data import generate_dummy_data
            path = generate_dummy_data(num_rows=num_rows)
            st.success(f"Generated {num_rows} synthetic records.")
            dummy_df = pd.read_csv(path)
            st.download_button(
                label="Download dummy_input.csv",
                data=dummy_df.to_csv(index=False).encode("utf-8"),
                file_name="dummy_input.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")

    if st.button("Generate Test PDF", use_container_width=True):
        try:
            from generate_dummy_pdf import generate_dummy_pdf
            path = generate_dummy_pdf()
            with open(path, "rb") as f:
                pdf_bytes = f.read()
            st.success("Generated 3-page hybrid PDF (2 native + 1 scanned).")
            st.download_button(
                label="Download dummy_hybrid.pdf",
                data=pdf_bytes,
                file_name="dummy_hybrid.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown(
        "<div style='color:#64748b;font-size:0.75rem;line-height:1.4;'>"
        "<strong>PII Redaction System v1.2</strong><br>"
        "CSV + PDF Hybrid Pipeline<br>"
        "Role-Based Policies + Tokenization<br>"
        "Internal Testing Environment"
        "</div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

PII_LABELS = {
    "NIK": "National ID (NIK)",
    "NO_HP": "Phone Number",
    "EMAIL": "Email Address",
    "NPWP": "Tax ID (NPWP)",
    "NAMA": "Full Name",
    "NO_REKENING": "Bank Account",
}

CHART_PALETTE = {
    "NAMA": "#334155",
    "NIK": "#1d4ed8",
    "NO_HP": "#0284c7",
    "EMAIL": "#0d9488",
    "NPWP": "#475569",
    "NO_REKENING": "#7c3aed",
}


def _render_metric_grid(summary: dict) -> str:
    total = sum(summary.values())
    html = '<div class="metric-grid">'
    html += (
        f'<div class="metric-box highlight">'
        f'<div class="metric-label">Total PII Entities</div>'
        f'<div class="metric-val">{total}</div></div>'
    )
    for ptype in ["NAMA", "NIK", "NO_HP", "EMAIL", "NPWP", "NO_REKENING"]:
        count = summary.get(ptype, 0)
        html += (
            f'<div class="metric-box">'
            f'<div class="metric-label">{PII_LABELS.get(ptype, ptype)}</div>'
            f'<div class="metric-val">{count}</div></div>'
        )
    html += '</div>'
    return html


def _render_pii_chart(summary: dict):
    chart_df = pd.DataFrame([
        {"Category": PII_LABELS.get(k, k), "Count": v, "Code": k}
        for k, v in summary.items()
    ])
    fig = go.Figure()
    for _, row in chart_df.iterrows():
        fig.add_trace(go.Bar(
            x=[row["Category"]],
            y=[row["Count"]],
            name=row["Category"],
            marker_color=CHART_PALETTE.get(row["Code"], "#1d4ed8"),
            text=[row["Count"]],
            textposition="outside",
            textfont=dict(size=12, color="#0f172a", family="Inter"),
        ))
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter", color="#334155"),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#0f172a"), linecolor="#cbd5e1"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=11, color="#64748b"), linecolor="#cbd5e1"),
        margin=dict(l=20, r=20, t=25, b=30),
        height=260,
        bargap=0.45,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_pdf_page_as_image(pdf_bytes: bytes, page_index: int, dpi: int = 120):
    """Renders a PDF page to a PIL Image for Streamlit preview."""
    import fitz
    from PIL import Image
    import io
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_index]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    doc.close()
    return img


# ──────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>Personally Identifiable Information (PII) Redaction System</h1>
    <p>Automated Privacy Protection for Employee Records — CSV Tabular Data and Hybrid PDF Documents</p>
</div>
""", unsafe_allow_html=True)

# ── File Upload ──
st.markdown('<div class="section-title">Upload Document</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Select or drop a CSV or PDF employee document:",
    type=["csv", "pdf"],
    help="CSV: tabular employee records  |  PDF: employment contracts, ID scans, mixed documents",
)

if uploaded_file is not None:
    file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

    # ════════════════════════════════════════════
    # CSV PIPELINE (unchanged)
    # ════════════════════════════════════════════
    if file_ext == "csv":
        try:
            df_original = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            st.stop()

        st.markdown(f"""
        <div class="badge-container">
            <span class="badge badge-info">File: {uploaded_file.name}</span>
            <span class="badge badge-info">Dimensions: {len(df_original)} rows x {len(df_original.columns)} columns</span>
            <span class="badge badge-native">CSV — Tabular Pipeline</span>
        </div>
        """, unsafe_allow_html=True)

        if len(df_original) > 200:
            st.markdown(
                '<div class="notice-box"><strong>Notice:</strong> File contains over 200 rows. '
                'Ensure only synthetic or pre-approved test data is used during prototype evaluation.</div>',
                unsafe_allow_html=True,
            )

        from redactor import scan_dataframe_for_review, redact_dataframe_with_review, redact_dataframe
        from audit_logger import log_redaction_event
        from tokenizer import PIITokenizer

        # Initial scan for review records
        if "csv_review_records" not in st.session_state or st.session_state.get("csv_review_file") != uploaded_file.name:
            initial_records, _, _ = scan_dataframe_for_review(df_original, use_ner=use_ner)
            st.session_state["csv_review_records"] = initial_records
            st.session_state["csv_review_file"] = uploaded_file.name

        # ── Interactive Review Expander ──
        st.markdown('<div class="section-title">Human-in-the-Loop: Review & Spot-Check</div>', unsafe_allow_html=True)
        with st.expander("Interactive PII Verification Table (Select Entities to Redact)", expanded=True):
            st.caption("Review all automatically detected PII candidates. Uncheck any false positives before applying redactions.")

            current_review_records = st.session_state.get("csv_review_records", [])
            if current_review_records:
                review_df = pd.DataFrame(current_review_records)
                display_cols = ["approved", "row", "column", "pii_type", "matched_text", "cell_preview"]
                edited_df = st.data_editor(
                    review_df[display_cols],
                    column_config={
                        "approved": st.column_config.CheckboxColumn("Redact?", default=True),
                        "row": st.column_config.NumberColumn("Row", disabled=True),
                        "column": st.column_config.TextColumn("Column", disabled=True),
                        "pii_type": st.column_config.TextColumn("PII Type", disabled=True),
                        "matched_text": st.column_config.TextColumn("Detected Value", disabled=True),
                        "cell_preview": st.column_config.TextColumn("Context Preview", disabled=True),
                    },
                    disabled=["row", "column", "pii_type", "matched_text", "cell_preview"],
                    hide_index=True,
                    use_container_width=True,
                    height=280,
                    key="csv_hitl_editor",
                )
                # Keep session state updated with user checkbox edits
                for i, row in edited_df.iterrows():
                    if i < len(st.session_state["csv_review_records"]):
                        st.session_state["csv_review_records"][i]["approved"] = bool(row["approved"])
            else:
                st.info("No PII candidates detected in this dataset.")

        col1, col2 = st.columns(2)
        with col1:
            process_approved = st.button("Apply Approved Redactions", use_container_width=True, type="primary")
        with col2:
            process_all = st.button("Redact All Automatically", use_container_width=True)

        if process_approved or process_all:
            _tokenizer = PIITokenizer() if redaction_mode == "tokenize" else None
            with st.spinner("Applying privacy transformations..."):
                if process_approved and st.session_state.get("csv_review_records"):
                    df_redacted, detail, summary = redact_dataframe_with_review(
                        df_original,
                        st.session_state["csv_review_records"],
                        mode=redaction_mode,
                        policy=active_policy,
                        tokenizer=_tokenizer,
                    )
                else:
                    df_redacted, detail, summary = redact_dataframe(
                        df_original,
                        mode=redaction_mode,
                        use_ner=use_ner,
                        policy=active_policy,
                        tokenizer=_tokenizer,
                    )

                csv_raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else None
                log_redaction_event(
                    document_name=uploaded_file.name,
                    document_type="csv",
                    total_records_or_pages=len(df_original),
                    redaction_mode=redaction_mode,
                    summary=summary,
                    file_bytes=csv_raw,
                )

            st.session_state.update({
                "csv_df_redacted": df_redacted,
                "csv_detail": detail,
                "csv_summary": summary,
                "csv_processed": True,
                "csv_tokenizer": _tokenizer,
            })

        if st.session_state.get("csv_processed"):
            df_redacted = st.session_state["csv_df_redacted"]
            detail = st.session_state["csv_detail"]
            summary = st.session_state["csv_summary"]

            st.markdown('<div class="section-title">PII Detection Summary</div>', unsafe_allow_html=True)
            st.markdown(_render_metric_grid(summary), unsafe_allow_html=True)
            if summary:
                _render_pii_chart(summary)

            st.markdown('<div class="section-title">Data Preview: Original vs Redacted</div>', unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["Side-by-Side View", "Toggle View"])
            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div style='font-size:0.85rem;font-weight:600;color:#334155;margin-bottom:0.4rem;'>Original Data</div>", unsafe_allow_html=True)
                    st.dataframe(df_original, use_container_width=True, height=420)
                with c2:
                    st.markdown("<div style='font-size:0.85rem;font-weight:600;color:#1d4ed8;margin-bottom:0.4rem;'>Redacted Data</div>", unsafe_allow_html=True)
                    st.dataframe(df_redacted, use_container_width=True, height=420)
            with tab2:
                sel = st.radio("Select Dataset:", ["Original Data", "Redacted Data"], horizontal=True)
                st.dataframe(df_original if "Original" in sel else df_redacted, use_container_width=True, height=450)

            with st.expander("Per-Row PII Detection Details", expanded=False):
                rows_with_pii = {idx: cols for idx, cols in detail.items() if cols}
                if rows_with_pii:
                    for idx, cols in list(rows_with_pii.items())[:25]:
                        items = [
                            f"<strong>{col}</strong>: {PII_LABELS.get(pt, pt)} ({len(m)} entity/entities)"
                            for col, pd_ in cols.items()
                            for pt, m in pd_.items()
                        ]
                        st.markdown(f"<div style='font-size:0.85rem;padding:0.25rem 0;'>Row {idx+1}: {' &bull; '.join(items)}</div>", unsafe_allow_html=True)
                    if len(rows_with_pii) > 25:
                        st.caption(f"Showing 25 of {len(rows_with_pii)} rows with PII findings.")
                else:
                    st.info("No personal data detected.")

            st.markdown('<div class="section-title">Export Redacted Files & Audit Artifacts</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    label="Download Redacted CSV File",
                    data=df_redacted.to_csv(index=False).encode("utf-8"),
                    file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_redacted.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with c2:
                from redactor import generate_pdf_report
                pdf_cert_bytes = generate_pdf_report(
                    summary=summary,
                    total_records_or_pages=len(df_original),
                    document_name=uploaded_file.name,
                    document_type="CSV",
                    mode=redaction_mode,
                )
                st.download_button(
                    label="Download PDF Compliance Certificate",
                    data=pdf_cert_bytes,
                    file_name="compliance_audit_certificate.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            from redactor import generate_report
            with st.expander("Compliance Audit Report (Text Format)", expanded=False):
                st.code(generate_report(summary, len(df_original)), language="text")

            # Token mapping download (only for tokenize mode)
            csv_tokenizer = st.session_state.get("csv_tokenizer")
            if csv_tokenizer is not None and csv_tokenizer.total_tokens > 0:
                with st.expander("Pseudo-anonymization Token Mapping", expanded=False):
                    st.caption(
                        f"Total unique tokens assigned: {csv_tokenizer.total_tokens}. "
                        "This mapping can be used to re-identify entities when authorized."
                    )
                    mapping_json = csv_tokenizer.export_json()
                    st.json(csv_tokenizer.get_mapping())
                    st.download_button(
                        label="Download Token Mapping (JSON)",
                        data=mapping_json.encode("utf-8"),
                        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_token_mapping.json",
                        mime="application/json",
                        use_container_width=True,
                    )

    # ════════════════════════════════════════════
    # PDF PIPELINE (new)
    # ════════════════════════════════════════════
    elif file_ext == "pdf":
        pdf_bytes = uploaded_file.getvalue()

        # Quick classification preview
        try:
            from page_classifier import classify_pdf_bytes
            page_infos = classify_pdf_bytes(pdf_bytes)
        except Exception as e:
            st.error(f"Failed to read PDF: {e}")
            st.stop()

        n_native = sum(1 for p in page_infos if p.classification == "native-text")
        n_image  = sum(1 for p in page_infos if p.classification == "image-based")

        st.markdown(f"""
        <div class="badge-container">
            <span class="badge badge-info">File: {uploaded_file.name}</span>
            <span class="badge badge-info">{len(page_infos)} page(s)</span>
            <span class="badge badge-native">{n_native} Native Text Page(s)</span>
            <span class="badge badge-ocr">{n_image} Image-Based Page(s) (OCR)</span>
        </div>
        """, unsafe_allow_html=True)

        # Per-page classification indicator
        st.markdown('<div class="section-title">Page Classification</div>', unsafe_allow_html=True)
        page_rows_html = ""
        for pi in page_infos:
            badge_cls = "badge-native" if pi.classification == "native-text" else "badge-ocr"
            label = "Native Text" if pi.classification == "native-text" else "Processed via OCR"
            chars = f"({pi.char_count} chars extracted)" if pi.classification == "native-text" else "(no extractable text)"
            page_rows_html += (
                f'<div class="page-row">'
                f'<span class="page-num">Page {pi.page_number + 1}</span>'
                f'<span class="badge {badge_cls}">{label}</span>'
                f'<span class="page-pii">{chars}</span>'
                f'</div>'
            )
        st.markdown(page_rows_html, unsafe_allow_html=True)

        # Original page previews
        st.markdown('<div class="section-title">Document Preview (Before Redaction)</div>', unsafe_allow_html=True)
        preview_cols = st.columns(min(len(page_infos), 3))
        for i, pi in enumerate(page_infos):
            with preview_cols[i % 3]:
                try:
                    img = _render_pdf_page_as_image(pdf_bytes, pi.page_number)
                    label = "Native Text" if pi.classification == "native-text" else "Image-Based (OCR)"
                    st.image(img, caption=f"Page {pi.page_number + 1} — {label}", use_column_width=True)
                except Exception as e:
                    st.error(f"Preview unavailable for page {pi.page_number + 1}: {e}")

        if n_image > 0:
            st.markdown(
                '<div class="notice-box">'
                '<strong>Note:</strong> '
                f'{n_image} page(s) contain no extractable text and will be processed via Tesseract OCR. '
                'OCR accuracy depends on image quality and scan resolution.'
                '</div>',
                unsafe_allow_html=True,
            )

        from redactor import scan_pdf_for_review, redact_pdf_with_review, redact_pdf
        from audit_logger import log_redaction_event

        # Initial scan for PDF review
        if "pdf_review_records" not in st.session_state or st.session_state.get("pdf_review_file") != uploaded_file.name:
            with st.spinner("Pre-scanning PDF for PII candidates..."):
                pdf_records, _ = scan_pdf_for_review(pdf_bytes, use_ner=use_ner)
                st.session_state["pdf_review_records"] = pdf_records
                st.session_state["pdf_review_file"] = uploaded_file.name

        # ── Interactive PDF Review Expander ──
        st.markdown('<div class="section-title">Human-in-the-Loop: Review & Spot-Check</div>', unsafe_allow_html=True)
        with st.expander("Interactive PII Verification Table (Select Entities to Redact)", expanded=True):
            st.caption("Review all automatically detected PII candidates across PDF pages before drawing redactions.")

            current_pdf_records = st.session_state.get("pdf_review_records", [])
            if current_pdf_records:
                pdf_review_df = pd.DataFrame(current_pdf_records)
                display_cols = ["approved", "page", "source", "pii_type", "matched_text"]
                edited_pdf_df = st.data_editor(
                    pdf_review_df[display_cols],
                    column_config={
                        "approved": st.column_config.CheckboxColumn("Redact?", default=True),
                        "page": st.column_config.NumberColumn("Page", disabled=True),
                        "source": st.column_config.TextColumn("Source", disabled=True),
                        "pii_type": st.column_config.TextColumn("PII Type", disabled=True),
                        "matched_text": st.column_config.TextColumn("Detected Value", disabled=True),
                    },
                    disabled=["page", "source", "pii_type", "matched_text"],
                    hide_index=True,
                    use_container_width=True,
                    height=240,
                    key="pdf_hitl_editor",
                )
                for i, row in edited_pdf_df.iterrows():
                    if i < len(st.session_state["pdf_review_records"]):
                        st.session_state["pdf_review_records"][i]["approved"] = bool(row["approved"])
            else:
                st.info("No PII candidates detected in this PDF.")

        col1, col2 = st.columns(2)
        with col1:
            process_approved_pdf = st.button("Apply Approved Redactions to PDF", use_container_width=True, type="primary")
        with col2:
            process_all_pdf = st.button("Redact Full PDF Automatically", use_container_width=True)

        if process_approved_pdf or process_all_pdf:
            with st.spinner("Classifying pages, running OCR where needed, applying redaction..."):
                try:
                    if process_approved_pdf and st.session_state.get("pdf_review_records"):
                        redacted_bytes, page_metadata, summary = redact_pdf_with_review(
                            pdf_bytes,
                            st.session_state["pdf_review_records"],
                            mode=redaction_mode,
                        )
                    else:
                        redacted_bytes, page_metadata, summary = redact_pdf(
                            pdf_bytes,
                            mode=redaction_mode,
                            use_ner=use_ner,
                        )

                    # Log audit event
                    log_redaction_event(
                        document_name=uploaded_file.name,
                        document_type="pdf",
                        total_records_or_pages=len(page_metadata),
                        redaction_mode=redaction_mode,
                        summary=summary,
                        file_bytes=pdf_bytes,
                    )
                    st.session_state.update({
                        "pdf_redacted_bytes": redacted_bytes,
                        "pdf_page_metadata": page_metadata,
                        "pdf_summary": summary,
                        "pdf_original_bytes": pdf_bytes,
                        "pdf_processed": True,
                    })
                except Exception as e:
                    st.error(f"Redaction failed: {e}")

        if st.session_state.get("pdf_processed"):
            redacted_bytes  = st.session_state["pdf_redacted_bytes"]
            page_metadata   = st.session_state["pdf_page_metadata"]
            summary         = st.session_state["pdf_summary"]
            original_bytes  = st.session_state["pdf_original_bytes"]

            st.markdown('<div class="section-title">PII Detection Summary</div>', unsafe_allow_html=True)
            st.markdown(_render_metric_grid(summary), unsafe_allow_html=True)
            if summary:
                _render_pii_chart(summary)

            # Per-page findings
            st.markdown('<div class="section-title">Per-Page Detection Results</div>', unsafe_allow_html=True)
            for pm in page_metadata:
                badge_cls = "badge-native" if pm["classification"] == "native-text" else "badge-ocr"
                label = "Native Text" if pm["classification"] == "native-text" else "Image-Based (OCR)"
                pii_count = len(pm["pii_found"])
                pii_summary = ", ".join(
                    f"{PII_LABELS.get(e['type'], e['type'])}"
                    for e in pm["pii_found"][:5]
                )
                if pii_count > 5:
                    pii_summary += f" (+{pii_count - 5} more)"
                st.markdown(
                    f'<div class="page-row">'
                    f'<span class="page-num">Page {pm["page_number"]}</span>'
                    f'<span class="badge {badge_cls}">{label}</span>'
                    f'<span class="page-pii">{pii_count} PII entities found'
                    f'{": " + pii_summary if pii_summary else ""}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Before/after page previews
            st.markdown('<div class="section-title">Page Preview: Before vs After Redaction</div>', unsafe_allow_html=True)
            for pm in page_metadata:
                pg_idx = pm["page_number"] - 1
                st.markdown(f"**Page {pm['page_number']}**")
                c1, c2 = st.columns(2)
                with c1:
                    try:
                        img_before = _render_pdf_page_as_image(original_bytes, pg_idx)
                        st.image(img_before, caption="Before Redaction", use_column_width=True)
                    except Exception as e:
                        st.error(f"Preview unavailable: {e}")
                with c2:
                    try:
                        img_after = _render_pdf_page_as_image(redacted_bytes, pg_idx)
                        st.image(img_after, caption="After Redaction", use_column_width=True)
                    except Exception as e:
                        st.error(f"Preview unavailable: {e}")

            # Download
            st.markdown('<div class="section-title">Export Redacted Files & Audit Artifacts</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    label="Download Redacted PDF File",
                    data=redacted_bytes,
                    file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_redacted.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with c2:
                from redactor import generate_pdf_report
                pdf_cert_bytes = generate_pdf_report(
                    summary=summary,
                    total_records_or_pages=len(page_metadata),
                    document_name=uploaded_file.name,
                    document_type="PDF",
                    mode=redaction_mode,
                )
                st.download_button(
                    label="Download PDF Compliance Certificate",
                    data=pdf_cert_bytes,
                    file_name="compliance_audit_certificate.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    # ── Real-Time Audit Trail Viewer ──
    from audit_logger import read_audit_log
    audit_entries = read_audit_log(max_entries=10)
    if audit_entries:
        with st.expander("Compliance Audit Trail (Latest Operations)", expanded=False):
            st.caption("Immutable JSON Lines ledger stored at data/audit_trail.log for UU PDP compliance.")
            audit_table = [
                {
                    "Timestamp (UTC)": e["timestamp"][:19].replace("T", " "),
                    "Document": e["document_name"],
                    "Type": e["document_type"],
                    "Mode": e["redaction_mode"],
                    "Entities Protected": e["total_pii_entities_redacted"],
                    "SHA-256 Hash": e["file_sha256"][:12] + "...",
                }
                for e in audit_entries
            ]
            st.dataframe(pd.DataFrame(audit_table), use_container_width=True)

else:
    st.markdown("""
    <div class="empty-state-box">
        <div class="empty-state-title">No Document Uploaded</div>
        <div class="empty-state-desc">
            Upload an employee CSV dataset or a hybrid PDF document to begin PII analysis.<br>
            You can generate synthetic test files using the generators in the sidebar.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show audit history even on empty state if log exists
    from audit_logger import read_audit_log
    audit_entries = read_audit_log(max_entries=10)
    if audit_entries:
        with st.expander("Compliance Audit Trail (Historical Log)", expanded=False):
            st.caption("Immutable JSON Lines ledger stored at data/audit_trail.log for UU PDP compliance.")
            audit_table = [
                {
                    "Timestamp (UTC)": e["timestamp"][:19].replace("T", " "),
                    "Document": e["document_name"],
                    "Type": e["document_type"],
                    "Mode": e["redaction_mode"],
                    "Entities Protected": e["total_pii_entities_redacted"],
                    "SHA-256 Hash": e["file_sha256"][:12] + "...",
                }
                for e in audit_entries
            ]
            st.dataframe(pd.DataFrame(audit_table), use_container_width=True)

