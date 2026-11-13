"""One-shot check for Gemini 2.5 Flash-Lite Google Search grounding.

Run from the repository root with:
    python onlinetest.py

The script reads GEMINI_API_KEY from the environment or src/.env. It does not
change ARIA's model selection or routing.
"""

import os
from pathlib import Path

from google import genai
from google.genai import types
from google.genai.errors import APIError


MODEL = "gemini-2.5-flash-lite"
PROMPT = (
    "What are the latest major technology news stories today? "
    "Give a concise summary and cite the sources you find."
)


def load_api_key():
    """Read the existing ARIA key without printing or changing it."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parent / "src" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "GEMINI_API_KEY":
                return value.strip().strip('"').strip("'")
    return None


def main():
    api_key = load_api_key()
    if not api_key:
        raise SystemExit(
            "GEMINI_API_KEY is missing. Set it in the environment or src/.env."
        )

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=PROMPT,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            ),
        )
    except APIError as error:
        print(f"Model: {MODEL}")
        print(f"Google Search grounding request failed (HTTP {error.code}).")
        print(error)
        return 1

    print(f"Model: {MODEL}")
    print(f"Prompt: {PROMPT}\n")
    print(response.text or "(No text response)")

    grounded_sources = []
    search_queries = []
    for candidate in getattr(response, "candidates", None) or []:
        metadata = getattr(candidate, "grounding_metadata", None)
        if metadata is None:
            continue
        search_queries.extend(getattr(metadata, "web_search_queries", None) or [])
        for chunk in getattr(metadata, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            uri = getattr(web, "uri", None)
            title = getattr(web, "title", None)
            if uri and uri not in {url for _, url in grounded_sources}:
                grounded_sources.append((title or uri, uri))

    if search_queries:
        print("\nSearch queries:")
        for query in search_queries:
            print(f"- {query}")

    if grounded_sources:
        print("\nGrounded sources:")
        for title, uri in grounded_sources:
            print(f"- {title}: {uri}")
        print("\nRESULT: Search grounding returned sources.")
        return 0

    print("\nRESULT: The request succeeded, but no grounding sources were returned.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
