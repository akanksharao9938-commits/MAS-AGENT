# Researcher–Writer–Reviewer Multi-Agent System

A small Agentic AI project with three role-based agents:
1. **Researcher** creates a structured research brief.
2. **Writer** creates a report from the brief.
3. **Reviewer** checks quality and requests revisions when needed.

The agents share information through their inputs and the workflow can loop back to the Writer based on reviewer feedback. The latest report is saved to `outputs/final_report.md`.

## Requirements
- Python 3.10+
- A Groq API key
- Internet connection for the model API

## Setup on Windows (VS Code / PowerShell)

1. Extract the ZIP and open the `mas_agentic_ai` folder in VS Code.
2. Open the terminal in that folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run this in the current terminal:
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to a new file named `.env` and replace the placeholder with your Groq API key. Get a key from https://console.groq.com/ . Keep `.env` private and do not upload it to GitHub.

6. Run:

   ```powershell
   python main.py
   ```

7. Enter a topic such as `Benefits and risks of AI in education`. The system will run the agents and save the output to `outputs/final_report.md`. Type `exit` to stop.

## How the agentic workflow works

```text
User topic
   |
   v
Researcher agent -> Research brief
   |
   v
Writer agent -> Draft report
   |
   v
Reviewer agent -> Score + feedback
   |                    |
   | APPROVE            | REVISE
   v                    v
Save report          Writer revises
                         |
                         +----> Reviewer (up to 2 revisions)
```

## Important limitation
This starter project uses an LLM to prepare a research brief, but **does not perform live web browsing or independently verify sources**. The Researcher is instructed not to invent citations and to flag claims needing verification. To make it a source-grounded research agent, add a search API/tool and require the Reviewer to check every cited source.

## Project structure

```text
mas_agentic_ai/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
└── outputs/                 # created when the program runs
    └── final_report.md
```

## Ideas to extend
- Add a web-search tool for the Researcher.
- Store agent messages and reports in SQLite or MongoDB.
- Add a Streamlit interface.
- Track reviewer scores across runs.
- Add a maximum revision count and structured JSON outputs.
