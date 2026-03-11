"""
Run History page — browse completed pipeline runs.
"""

import streamlit as st
from ui.run_utils import list_runs, format_run_id


def render():
    st.header("Run History")
    st.caption("All completed pipeline runs, newest first.")

    runs = list_runs()

    if not runs:
        st.info("No runs found in `outputs/`. Launch a new run to get started.")
        return

    for run in runs:
        run_id = run.get("run_id", "unknown")
        run_dir = run.get("_run_dir", "")
        status = run.get("status", "unknown")
        course_title = run.get("course_title") or run.get("inputs", {}).get("course_title", "")
        client = run.get("client") or run.get("inputs", {}).get("client", "")

        label_parts = [format_run_id(run_id)]
        if course_title:
            label_parts.append(course_title)
        if client:
            label_parts.append(f"({client})")
        label = "  ·  ".join(label_parts)

        badge = "✅" if status == "complete" else "⏳" if status == "running" else "❓"

        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{badge} {label}**")
                st.caption(f"Run ID: `{run_id}`  ·  Dir: `{run_dir}`")
            with col2:
                if st.button("View", key=f"view_{run_id}"):
                    st.session_state["view_run"] = run_dir
                    st.rerun()
