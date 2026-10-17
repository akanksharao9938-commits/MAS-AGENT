from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
import os
load_dotenv(Path(__file__).resolve().parent / ".env")
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("ERROR: GROQ_API_KEY was not loaded from .env")
    raise SystemExit(1)
client = Groq(api_key=api_key)
try:
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "user", "content": "Reply with exactly: GROQ TEST PASSED"}
        ],
        max_completion_tokens=200,
        reasoning_effort="none",
    )
    print("Finish reason:", response.choices[0].finish_reason)
    print("Response:", repr(response.choices[0].message.content))
except Exception as error:
    print("ERROR TYPE:", type(error).__name__)
    print("ERROR DETAILS:", str(error))
