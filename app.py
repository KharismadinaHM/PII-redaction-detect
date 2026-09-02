"""
app.py
Streamlit User Interface — Employee Document PII Detection & Redaction System.
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

    /* ── Header Banner ── */
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

    /* ── Section Title ── */
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

    /* ── Metric Cards (High Contrast) ── */
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

    /* ── Status Pills ── */
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
    .badge-info {
        background-color: #eff6ff;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }
    .badge-warning {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    /* ── Notice / Warning Box ── */
    .notice-box {
        background-color: #fffbeb;
        border-left: 4px solid #d97706;
        border-top: 1px solid #fde68a;
        border-right: 1px solid #fde68a;
        border-bottom: 1px solid #fde68a;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        font-size: 0.85rem;
        color: #92400e;
    }

    /* ── Primary Action Button ── */
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
        border-color: #172554 !important;
    }

    /* ── Download Button ── */
    .stDownloadButton > button {
        background-color: #047857 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: 1px solid #065f46 !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.5rem !important;
    }
    .stDownloadButton > button:hover {
        background-color: #065f46 !important;
    }

    /* ── Empty State ── */
    .empty-state-box {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 8px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    .empty-state-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.35rem;
    }
    .empty-state-desc {
        font-size: 0.85rem;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Sidebar: Configurations
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Redaction Settings")
    st.markdown("---")

    redaction_mode = st.radio(
        "Redaction Method",
        options=["mask", "full"],
        format_func=lambda x: "Partial Masking (081****5678)" if x == "mask" else "Full Redaction ([REDACTED])",
        index=0,
        help="Partial Masking: Masks intermediate characters for internal operational use.\n\n"
             "Full Redaction: Replaces the full value with placeholders for external distribution.",
    )

    st.markdown("---")

    use_ner = st.toggle(
        "Enable spaCy NER",
        value=True,
        help="Enables Named Entity Recognition to detect person names across all document columns."
    )

    st.markdown("---")
    st.markdown("### Test Dataset Generator")
    st.caption("Generate synthetic employee records for evaluation without exposing real data.")

    num_rows = st.slider("Record Count", min_value=10, max_value=500, value=100, step=10)

    if st.button("Generate Test Dataset", use_container_width=True):
        try:
            from generate_dummy_data import generate_dummy_data
            path = generate_dummy_data(num_rows=num_rows)
            st.success(f"Generated {num_rows} synthetic records successfully.")
            
            dummy_df = pd.read_csv(path)
            csv_data = dummy_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download dummy_input.csv",
                data=csv_data,
                file_name="dummy_input.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Failed to generate dataset: {e}")

    st.markdown("---")
    st.markdown(
        "<div style='color: #64748b; font-size: 0.75rem; line-height: 1.4;'>"
        "<strong>PII Redaction System v1.0</strong><br>"
        "Enterprise Data Privacy Compliance<br>"
        "Internal Testing Environment"
        "</div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────

# Header
st.markdown("""
<div class="app-header">
    <h1>Personally Identifiable Information (PII) Redaction System</h1>
    <p>Automated Privacy Protection and Redaction for Internal Employee Records</p>
</div>
""", unsafe_allow_html=True)

# File Ingestion Section
st.markdown('<div class="section-title">Upload Document</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Select or drop a CSV employee dataset:",
    type=["csv"],
    help="Supported format: CSV with standard headers (nama/name, nik, no_hp/phone, email, alamat/address, gaji/salary, npwp)",
)

if uploaded_file is not None:
    try:
        df_original = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"An error occurred while reading the CSV file: {e}")
        st.stop()

    # File metadata badges
    st.markdown(f"""
    <div class="badge-container">
        <span class="badge badge-info">File: {uploaded_file.name}</span>
        <span class="badge badge-info">Dimensions: {len(df_original)} rows x {len(df_original.columns)} columns</span>
        <span class="badge badge-info">Status: Ready for Processing</span>
    </div>
    """, unsafe_allow_html=True)

    if len(df_original) > 200:
        st.markdown(
            '<div class="notice-box">'
            '<strong>Notice:</strong> The uploaded file contains over 200 rows. '
            'Ensure only synthetic or pre-approved test data is utilized during prototype evaluation.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Process Trigger
    col_proc1, col_proc2, col_proc3 = st.columns([1, 2, 1])
    with col_proc2:
        process_clicked = st.button(
            "Execute Redaction Process",
            use_container_width=True,
            type="primary",
        )

    if process_clicked:
        from redactor import redact_dataframe

        with st.spinner("Analyzing and redacting personal data..."):
            df_redacted, detail, summary = redact_dataframe(
                df_original, mode=redaction_mode, use_ner=use_ner
            )

        st.session_state["df_redacted"] = df_redacted
        st.session_state["detail"] = detail
        st.session_state["summary"] = summary
        st.session_state["processed"] = True

    # Result Presentation
    if st.session_state.get("processed"):
        df_redacted = st.session_state["df_redacted"]
        detail = st.session_state["detail"]
        summary = st.session_state["summary"]

        st.markdown('<div class="section-title">PII Detection Summary</div>', unsafe_allow_html=True)

        pii_labels = {
            "NIK": "National ID (NIK)",
            "NO_HP": "Phone Number",
            "EMAIL": "Email Address",
            "NPWP": "Tax ID (NPWP)",
            "NAMA": "Full Name",
        }

        total_pii = sum(summary.values()) if summary else 0

        # Metric grid
        metrics_html = '<div class="metric-grid">'
        metrics_html += (
            f'<div class="metric-box highlight">'
            f'<div class="metric-label">Total PII Entities</div>'
            f'<div class="metric-val">{total_pii}</div>'
            f'</div>'
        )

        for ptype in ["NAMA", "NIK", "NO_HP", "EMAIL", "NPWP"]:
            count = summary.get(ptype, 0)
            label = pii_labels.get(ptype, ptype)
            metrics_html += (
                f'<div class="metric-box">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-val">{count}</div>'
                f'</div>'
            )
        metrics_html += '</div>'
        st.markdown(metrics_html, unsafe_allow_html=True)

        # Plotly chart with high contrast corporate colors
        if summary:
            chart_df = pd.DataFrame([
                {
                    "PII Category": pii_labels.get(k, k),
                    "Count": v,
                    "Code": k,
                }
                for k, v in summary.items()
            ])

            # Corporate high contrast color mapping
            palette = {
                "NAMA": "#334155",
                "NIK": "#1d4ed8",
                "NO_HP": "#0284c7",
                "EMAIL": "#0d9488",
                "NPWP": "#475569",
            }

            fig = go.Figure()
            for _, row in chart_df.iterrows():
                fig.add_trace(go.Bar(
                    x=[row["PII Category"]],
                    y=[row["Count"]],
                    name=row["PII Category"],
                    marker_color=palette.get(row["Code"], "#1d4ed8"),
                    text=[row["Count"]],
                    textposition="outside",
                    textfont=dict(size=12, color="#0f172a", family="Inter"),
                ))

            fig.update_layout(
                showlegend=False,
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(family="Inter", color="#334155"),
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(size=12, color="#0f172a"),
                    linecolor="#cbd5e1",
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#f1f5f9",
                    tickfont=dict(size=11, color="#64748b"),
                    linecolor="#cbd5e1",
                ),
                margin=dict(l=20, r=20, t=25, b=30),
                height=260,
                bargap=0.45,
            )

            st.plotly_chart(fig, use_container_width=True)

        # Comparison Preview
        st.markdown('<div class="section-title">Data Preview: Original vs Redacted</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Side-by-Side View", "Toggle View"])

        with tab1:
            col_orig, col_red = st.columns(2)
            with col_orig:
                st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#334155; margin-bottom:0.4rem;'>Original Data (Before Redaction)</div>", unsafe_allow_html=True)
                st.dataframe(df_original, use_container_width=True, height=420)
            with col_red:
                st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#1d4ed8; margin-bottom:0.4rem;'>Redacted Data (After Redaction)</div>", unsafe_allow_html=True)
                st.dataframe(df_redacted, use_container_width=True, height=420)

        with tab2:
            view_selection = st.radio(
                "Select Dataset to Display:",
                ["Original Data (Before Redaction)", "Redacted Data (After Redaction)"],
                horizontal=True,
            )
            if "Original" in view_selection:
                st.dataframe(df_original, use_container_width=True, height=450)
            else:
                st.dataframe(df_redacted, use_container_width=True, height=450)

        # Row Detail Breakdown
        with st.expander("Per-Row PII Detection Details", expanded=False):
            rows_with_pii = {idx: cols for idx, cols in detail.items() if cols}
            if rows_with_pii:
                for idx, cols in list(rows_with_pii.items())[:25]:
                    items = []
                    for col, pii_dict in cols.items():
                        for ptype, matches in pii_dict.items():
                            label = pii_labels.get(ptype, ptype)
                            items.append(f"<strong>{col}</strong>: {label} ({len(matches)} entity/entities)")
                    st.markdown(f"<div style='font-size:0.85rem; padding:0.25rem 0;'>Row {idx + 1}: {' &bull; '.join(items)}</div>", unsafe_allow_html=True)

                if len(rows_with_pii) > 25:
                    st.caption(f"Showing 25 of {len(rows_with_pii)} total rows containing personal data findings.")
            else:
                st.info("No personal data detected in this dataset.")

        # Export Section
        st.markdown('<div class="section-title">Export Redacted File</div>', unsafe_allow_html=True)

        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
        with col_dl2:
            csv_output = df_redacted.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Redacted CSV File",
                data=csv_output,
                file_name="output_redacted.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Audit Report Text
        from redactor import generate_report
        report_text = generate_report(summary, len(df_original))

        with st.expander("Compliance Audit Report (Text Format)", expanded=False):
            st.code(report_text, language="text")

else:
    # Empty State
    st.markdown("""
    <div class="empty-state-box">
        <div class="empty-state-title">No Document Uploaded</div>
        <div class="empty-state-desc">
            Upload an employee CSV dataset using the box above to begin PII analysis.<br>
            You can also generate synthetic test records using the generator in the sidebar.
        </div>
    </div>
    """, unsafe_allow_html=True)
