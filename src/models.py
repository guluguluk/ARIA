import os
from pathlib import Path

from google import genai
from google.genai.errors import APIError


TEMPORARY_GEMINI_ERROR_RESPONSE = (
    "Gemini is temporarily unavailable right now. Please try again."
)
TEMPORARY_GEMINI_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def load_env_file():
    env_path = Path(__file__).with_name(".env")

    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found. Add it to src/.env.")

client = genai.Client(api_key=api_key)


def ask_gemini(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
    except APIError as error:
        if error.code in TEMPORARY_GEMINI_STATUS_CODES:
            return TEMPORARY_GEMINI_ERROR_RESPONSE
        raise

    return response.text
