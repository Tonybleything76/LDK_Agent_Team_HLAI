"""
View Run page — display all deliverables for a completed pipeline run.
"""

from pathlib import Path
import streamlit as st
from ui.run_utils import AGENT_LABELS, get_run_outputs, format_run_id


def render(run_dir: str):
    run_path = Path(run_dir)
    run_id = run_path.name

    # ── Header ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← Back"):
            del st.session_state["view_run"]
            st.rerun()
    with col2:
        st.header(f"Run: {format_run_id(run_id)}")
        st.caption(f"`{run_dir}`")

    st.divider()

    # ── Load outputs ───────────────────────────────────────────────────────────
    outputs = get_run_outputs(run_dir)

    if not outputs:
        st.warning("No step checkpoints found in this run directory.")
        return

    # ── Tab per agent ──────────────────────────────────────────────────────────
    available = [
        (step_num, agent_name, label)
        for step_num, agent_name, label in AGENT_LABELS
        if agent_name in outputs
    ]

    if not available:
        st.warning("No deliverable checkpoints found.")
        return

    tab_labels = [f"{num}. {label}" for num, _, label in available]
    tabs = st.tabs(tab_labels)

    for tab, (step_num, agent_name, label) in zip(tabs, available):
        with tab:
            deliverable = outputs[agent_name]
            if deliverable.strip():
                st.markdown(deliverable)
            else:
                st.info("No deliverable content recorded for this step.")

    # ── Download all as single markdown ───────────────────────────────────────
    st.divider()
    all_md = "\n\n---\n\n".join(
        f"# Step {num}: {label}\n\n{outputs.get(agent_name, '')}"
        for num, agent_name, label in AGENT_LABELS
        if agent_name in outputs
    )
    st.download_button(
        label="Download all deliverables (.md)",
        data=all_md,
        file_name=f"course_factory_{run_id}.md",
        mime="text/markdown",
    )
