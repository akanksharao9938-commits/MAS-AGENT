


import os
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found. Check your .env file."
    )

client = Groq(api_key=API_KEY)

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FINAL_REPORT_PATH = BASE_DIR / "final_report.txt"
LOG_PATH = OUTPUT_DIR / "run_log.json"

AGENT_STATUS = {
    "Researcher": "Not started",
    "Writer": "Not started",
    "Reviewer": "Not started",
}

RUN_LOG = {
    "started_at": "",
    "model": MODEL,
    "topic": "",
    "agent_status": AGENT_STATUS.copy(),
    "errors": [],
}


# ============================================================
# FILE HANDLING
# ============================================================

def save_text(filename, content):
    """Save text inside the outputs folder."""
    file_path = OUTPUT_DIR / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


def reset_run_state(topic):
    """Reset agent statuses and logs for a new run."""
    for agent_name in AGENT_STATUS:
        AGENT_STATUS[agent_name] = "Not started"

    RUN_LOG.clear()
    RUN_LOG.update({
        "started_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "model": MODEL,
        "topic": topic,
        "agent_status": AGENT_STATUS.copy(),
        "errors": [],
    })


def save_run_log():
    """Save the current workflow status as JSON."""
    RUN_LOG["finished_at"] = datetime.now().isoformat(
        timespec="seconds"
    )
    RUN_LOG["agent_status"] = AGENT_STATUS.copy()

    LOG_PATH.write_text(
        json.dumps(RUN_LOG, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


# ============================================================
# GROQ API CALL
# ============================================================

def call_agent(agent_name, system_prompt, user_prompt, max_tokens=2500):
    """Send a prompt to Groq and return the model's response."""
    print(f"\n[{agent_name}] Sending request to Groq...")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )

        if not response.choices:
            raise RuntimeError("Groq returned no response choices.")

        choice = response.choices[0]
        result = choice.message.content

        print(f"[{agent_name}] Finish reason: {choice.finish_reason}")

        if not result or not result.strip():
            raise RuntimeError("Groq returned an empty response.")

        if choice.finish_reason == "length":
            print(
                f"[{agent_name}] Warning: the response may have "
                "been cut short because of the token limit."
            )

        print(f"[{agent_name}] Response received.")
        return result.strip()

    except Exception as error:
        error_message = f"{agent_name} error: {error}"
        print(f"\n{error_message}")
        RUN_LOG["errors"].append(error_message)
        return None


# ============================================================
# AGENT 1: RESEARCHER
# ============================================================

def researcher_agent(topic):
    print("\n" + "=" * 65)
    print("AGENT 1: RESEARCHER")
    print("=" * 65)

    system_prompt = """
You are the Researcher agent in a multi-agent AI system.

Your responsibility is to prepare accurate, useful research notes
for a report writer.

Instructions:
1. Identify the important concepts related to the topic.
2. Explain the main ideas, applications, benefits, and challenges.
3. Organize the information using clear headings and bullet points.
4. Distinguish established facts from opinions or predictions.
5. Do not invent statistics, research papers, URLs, or citations.
6. If a claim needs verification, clearly indicate that.
7. Provide enough useful detail for another agent to write a report.
"""

    user_prompt = f"""
Research the following topic:

{topic}

Return organized research notes with:
- Introduction and background
- Key concepts
- Important developments
- Applications and examples
- Benefits
- Challenges and limitations
- Future possibilities
- A short list of important conclusions

Do not write the final report yet. Prepare research notes for the Writer.
"""

    result = call_agent(
        agent_name="Researcher",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=2500,
    )

    if result:
        AGENT_STATUS["Researcher"] = "Success"
        save_text("researcher_output.md", result)
        print("\n--- RESEARCHER OUTPUT ---\n")
        print(result)
        return result

    AGENT_STATUS["Researcher"] = "Failed"
    return None


# ============================================================
# AGENT 2: WRITER
# ============================================================

def writer_agent(
    topic,
    research_notes,
    previous_draft=None,
    reviewer_feedback=None,
):
    print("\n" + "=" * 65)
    print("AGENT 2: WRITER")
    print("=" * 65)

    system_prompt = """
You are the Writer agent in a multi-agent AI system.

Your job is to turn research notes into a complete, well-organized report.

Requirements:
1. Write a clear title and introduction.
2. Use meaningful section headings.
3. Explain the subject in logical order.
4. Include relevant applications, benefits, and challenges.
5. Write in professional but understandable English.
6. Include a conclusion.
7. Do not invent statistics, citations, references, or factual claims.
8. If information is uncertain, state the limitation.
9. Return the complete report in Markdown.
10. Do not describe your internal reasoning or agent workflow.
"""

    if previous_draft and reviewer_feedback:
        task_instructions = f"""
Revise the existing report using the review feedback below.

Keep the useful information from the existing report. Correct the
identified problems and return the COMPLETE improved report.

EXISTING REPORT:
{previous_draft}

REVIEW FEEDBACK:
{reviewer_feedback}
"""
    else:
        task_instructions = """
Create a complete report using the research notes provided below.
"""

    user_prompt = f"""
TOPIC:
{topic}

RESEARCH NOTES:
{research_notes}

{task_instructions}
"""

    result = call_agent(
        agent_name="Writer",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=3000,
    )

    if result:
        AGENT_STATUS["Writer"] = "Success"
        save_text("writer_draft.md", result)
        print("\n--- WRITER OUTPUT ---\n")
        print(result)
        return result

    AGENT_STATUS["Writer"] = "Failed"
    return None


# ============================================================
# AGENT 3: REVIEWER
# ============================================================

def reviewer_agent(topic, draft):
    print("\n" + "=" * 65)
    print("AGENT 3: REVIEWER")
    print("=" * 65)

    system_prompt = """
You are the Reviewer agent in a multi-agent AI system.

Your task is to review and improve a complete report.

Check:
1. Grammar, spelling, and readability.
2. Clarity and logical organization.
3. Repetition and irrelevant content.
4. Whether the report addresses the requested topic.
5. Unsupported or exaggerated claims.
6. Consistency between sections.
7. Whether the introduction and conclusion are appropriate.

Important instructions:
- Return the COMPLETE revised report, not just comments.
- Preserve useful information and the original topic.
- Improve weak explanations and remove unnecessary repetition.
- Do not invent facts, statistics, citations, or references.
- Do not return a score, verdict, or feedback-only response.
- Do not mention that you are an AI reviewer.
- Use Markdown formatting.
"""

    user_prompt = f"""
Review and improve the following report about:

{topic}

Return the complete corrected report.

REPORT TO REVIEW:
{draft}
"""

    result = call_agent(
        agent_name="Reviewer",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=3000,
    )

    if result:
        if len(result) < min(500, int(len(draft) * 0.20)):
            print(
                "[Reviewer] Response appears too short. "
                "The Writer's draft will be preserved."
            )
            AGENT_STATUS["Reviewer"] = "Failed - incomplete response"
            return None

        AGENT_STATUS["Reviewer"] = "Success"
        save_text("reviewer_output.md", result)
        print("\n--- REVIEWER OUTPUT ---\n")
        print(result)
        return result

    AGENT_STATUS["Reviewer"] = "Failed"
    return None


# ============================================================
# TOPIC INPUT: DASHBOARD OR TERMINAL
# ============================================================

def get_topic():
    """
    If the dashboard supplies MAS_TASK, use that question.
    Otherwise, request a topic through terminal input.
    """
    dashboard_topic = os.getenv("MAS_TASK", "").strip()

    if dashboard_topic:
        print("\nQuestion received from the dashboard.")
        print(f"Topic: {dashboard_topic}")
        return dashboard_topic

    return input("\nEnter your research topic: ").strip()


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():
    print("\n" + "=" * 65)
    print("MULTI-AGENT AI SYSTEM")
    print("Researcher -> Writer -> Reviewer")
    print(f"Model: {MODEL}")
    print("=" * 65)

    topic = get_topic()

    if not topic:
        print("Error: Please enter a research topic.")
        return

    reset_run_state(topic)

    try:
        # Step 1: Research
        research_notes = researcher_agent(topic)

        if not research_notes:
            print("\nWorkflow stopped because the Researcher failed.")
            return

        # Step 2: Writing
        draft = writer_agent(topic, research_notes)

        if not draft:
            print("\nWorkflow stopped because the Writer failed.")
            return

        # Step 3: Review
        reviewed_report = reviewer_agent(topic, draft)

        if reviewed_report:
            final_report = reviewed_report
            print("\nReviewer completed the report successfully.")
        else:
            final_report = draft
            print(
                "\nReviewer failed or returned an incomplete response. "
                "Using the Writer's draft as the final report."
            )

        # Save the final report in the project root.
        FINAL_REPORT_PATH.write_text(
            final_report,
            encoding="utf-8",
        )

        # Save a copy inside outputs.
        save_text("final_report.md", final_report)

        print("\n" + "=" * 65)
        print("WORKFLOW SUMMARY")
        print("=" * 65)

        for agent_name, status in AGENT_STATUS.items():
            print(f"{agent_name}: {status}")

        print(f"\nFinal report saved to: {FINAL_REPORT_PATH}")
        print(f"Individual agent outputs saved in: {OUTPUT_DIR}")
        print(f"Workflow log saved to: {LOG_PATH}")

    except Exception as error:
        error_message = f"Unexpected workflow error: {error}"
        print(f"\n{error_message}")
        RUN_LOG["errors"].append(error_message)

    finally:
        save_run_log()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user.")
        save_run_log()
