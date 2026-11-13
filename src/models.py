import os
import logging
from pathlib import Path

from google import genai
from google.genai import types
from google.genai.errors import APIError


TEMPORARY_GEMINI_ERROR_RESPONSE = (
    "Gemini is temporarily unavailable right now. Please try again."
)
TEMPORARY_GEMINI_STATUS_CODES = {408, 429, 500, 502, 503, 504}
SEARCH_QUOTA_ERROR_RESPONSE = (
    "Live search could not run because the Gemini API project quota was exceeded. "
    "Check usage and quota at https://ai.dev/rate-limit, then review billing and "
    "limits at https://ai.google.dev/gemini-api/docs/rate-limits."
)
logger = logging.getLogger(__name__)


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


def _grounding_sources(response):
    """Return distinct source URLs attached to Gemini Google Search grounding."""
    sources = []
    for candidate in getattr(response, "candidates", None) or []:
        metadata = getattr(candidate, "grounding_metadata", None)
        for chunk in getattr(metadata, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            uri = getattr(web, "uri", None)
            title = getattr(web, "title", None)
            if uri and uri not in {item[1] for item in sources}:
                sources.append((title or uri, uri))
    if not sources:
        return ""
    return "\n\nSources:\n" + "\n".join(f"- [{title}]({url})" for title, url in sources)


def ask_gemini(prompt, use_search=False):
    try:
        request = {
            "model": "gemini-3.5-flash-lite",
            "contents": prompt,
        }
        if use_search:
            request["config"] = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        response = client.models.generate_content(**request)
    except APIError as error:
        if error.code in TEMPORARY_GEMINI_STATUS_CODES:
            if use_search:
                logger.warning(
                    "Gemini Google Search request failed (HTTP %s): %s",
                    error.code,
                    error,
                )
                if error.code == 429:
                    return SEARCH_QUOTA_ERROR_RESPONSE
            return TEMPORARY_GEMINI_ERROR_RESPONSE
        raise

    return (response.text or "") + (_grounding_sources(response) if use_search else "")


def transcribe_audio(audio_data, mime_type):
    """Convert a short browser microphone recording to plain prompt text."""
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                "Transcribe the speech in this audio verbatim. Return only the spoken words, without commentary.",
                types.Part.from_bytes(data=audio_data, mime_type=mime_type),
            ],
        )
    except APIError as error:
        if error.code in TEMPORARY_GEMINI_STATUS_CODES:
            return TEMPORARY_GEMINI_ERROR_RESPONSE
        raise
    return response.text or ""
