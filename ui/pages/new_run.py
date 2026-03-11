"""
New Run page — input form + live pipeline execution.
"""

import time
import streamlit as st
from ui.run_utils import (
    AGENT_LABELS,
    PHASE_GATES,
    start_pipeline,
    format_run_id,
    list_runs,
)


def render():
    st.header("New Course Run")
    st.caption(
        "Paste a Business Brief and SME Notes below, then launch the 10-agent pipeline."
    )

    # ── Input form ─────────────────────────────────────────────────────────────
    with st.form("run_form"):
        col1, col2 = st.columns(2)
        with col1:
            business_brief = st.text_area(
                "Business Brief",
                height=340,
                placeholder="# Business Brief\n\nOrganization name, goals, learner audience, scope...",
                help="Paste the full business brief markdown here.",
            )
        with col2:
            sme_notes = st.text_area(
                "SME Notes",
                height=340,
                placeholder="# SME Notes\n\nContent topics, key concepts, source material...",
                help="Paste SME notes or source content here.",
            )

        launch = st.form_submit_button("Launch Pipeline", type="primary", use_container_width=True)

    if not launch:
        return

    if not business_brief.strip():
        st.error("Business Brief is required.")
        return
    if not sme_notes.strip():
        st.error("SME Notes are required.")
        return

    # ── Pipeline execution ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Pipeline Progress")

    progress_bar = st.progress(0, text="Starting pipeline…")
    status_placeholder = st.empty()
    log_expander = st.expander("Live log", expanded=False)
    log_area = log_expander.empty()

    log_lines = []
    current_step = 0

    def update_progress(step: int, label: str):
        pct = int((step / 10) * 100)
        gate_badge = f"  ·  Gate {step // 3}" if step in PHASE_GATES else ""
        progress_bar.progress(pct, text=f"Step {step}/10 — {label}{gate_badge}")

    try:
        proc = start_pipeline(business_brief, sme_notes)
    except Exception as e:
        st.error(f"Failed to start pipeline: {e}")
        return

    status_placeholder.info("Pipeline running… this typically takes 5–15 minutes.")

    for line in proc.stdout:
        line = line.rstrip()
        log_lines.append(line)
        log_area.code("\n".join(log_lines[-120:]), language="text")

        # Detect step transitions from stdout markers
        for step_num, agent_name, label in AGENT_LABELS:
            marker = f"[Step {step_num}]"
            if marker in line and step_num > current_step:
                current_step = step_num
                update_progress(step_num, label)
                break

    proc.wait()

    progress_bar.progress(100, text="Pipeline complete")

    if proc.returncode == 0:
        status_placeholder.success("Pipeline completed successfully.")
        # Offer to view the latest run
        runs = list_runs()
        if runs:
            latest = runs[0]
            run_id = latest.get("run_id", "")
            if st.button(
                f"View outputs — {format_run_id(run_id)}",
                type="primary",
            ):
                st.session_state["view_run"] = latest["_run_dir"]
                st.rerun()
    else:
        status_placeholder.error(
            f"Pipeline exited with code {proc.returncode}. Check the live log for details."
        )
