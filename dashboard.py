import json
import os
import subprocess
import sys
from pathlib import Path
import streamlit as st
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_PATH = OUTPUT_DIR / "run_log.json"
FINAL_REPORT_PATH = BASE_DIR / "final_report.txt"
MARKDOWN_REPORT_PATH = OUTPUT_DIR / "final_report.md"
st.set_page_config(
    page_title="Multi-Agent AI Dashboard",
    page_icon="🤖",
    layout="wide",
)
def read_text(path):
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return ""
def load_log():
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
st.title("🤖 Multi-Agent AI System")
st.caption("Researcher → Writer → Reviewer")
st.write(
    "Enter a research question, run the agents, "
    "and view your final research report here."
)
st.subheader("1. Enter your research question")
with st.form("research_form"):
    question = st.text_area(
        "Research question",
        placeholder=(
            "Example: Explain the impact of AI on healthcare, "
            "including applications, benefits, challenges, and future scope."
        ),
        height=150,
    )
    submitted = st.form_submit_button(
        "🚀 Run Multi-Agent Workflow",
        type="primary",
        use_container_width=True,
    )
if submitted:
    if not question.strip():
        st.warning("Please enter a research question.")
    elif not (BASE_DIR / "main.py").exists():
        st.error(f"main.py not found in {BASE_DIR}")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["MAS_TASK"] = question.strip()
        st.session_state["last_question"] = question.strip()
        st.session_state["last_stdout"] = ""
        st.session_state["last_stderr"] = ""
        st.session_state["last_returncode"] = None
        try:
            with st.spinner(
                "Running Researcher → Writer → Reviewer. Please wait..."
            ):
                result = subprocess.run(
                    [sys.executable, "-u", str(BASE_DIR / "main.py")],
                    cwd=str(BASE_DIR),
                    env=env,
                    input=question.strip() + "\n",
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=900,
                )
            st.session_state["last_stdout"] = result.stdout
            st.session_state["last_stderr"] = result.stderr
            st.session_state["last_returncode"] = result.returncode
            if result.returncode == 0:
                st.success("Workflow completed successfully!")
            else:
                st.error(
                    f"Workflow failed with exit code {result.returncode}."
                )
        except subprocess.TimeoutExpired:
            st.error(
                "The workflow exceeded 15 minutes. "
                "Check your API connection and model response time."
            )
        except Exception as exc:
            st.error(f"Could not start the workflow: {exc}")
if "last_question" in st.session_state:
    st.divider()
    st.subheader("2. Agent execution logs")
    st.write("**Research question:**", st.session_state["last_question"])
    with st.expander("View execution output", expanded=True):
        st.code(
            st.session_state.get("last_stdout", "")
            or "No standard output captured."
        )
        stderr = st.session_state.get("last_stderr", "")
        if stderr:
            st.markdown("**Diagnostic messages**")
            st.code(stderr)
st.divider()
st.subheader("3. Agent status")
log_data = load_log()
agent_status = log_data.get("agent_status", {})
if agent_status:
    cols = st.columns(3)
    for col, name in zip(cols, ["Researcher", "Writer", "Reviewer"]):
        with col:
            col.metric(
                label=name,
                value=str(agent_status.get(name, "Not recorded")),
            )
else:
    st.info("Agent statuses will appear after a workflow run.")
if log_data:
    with st.expander("Workflow metadata"):
        st.json(log_data)
st.divider()
st.subheader("4. Final research report")
report = read_text(MARKDOWN_REPORT_PATH)
if not report:
    report = read_text(FINAL_REPORT_PATH)
if report:
    st.markdown(report)
    st.download_button(
        "📥 Download final report",
        data=report,
        file_name="final_report.md",
        mime="text/markdown",
    )
else:
    st.info("Your final report will appear here after the agents finish.")
if st.button("🔄 Refresh dashboard"):
    st.rerun()
