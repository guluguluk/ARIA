"""Verified runtime capability facts and deterministic answers for direct questions."""

import re
from datetime import datetime


_REALTIME_QUESTIONS = {
    "are you up to date",
    "are you up-to-date",
    "are you aware of real-time information",
    "are you aware of real time information",
    "do you have real-time information",
    "do you have real time information",
    "do you have access to real-time information",
    "can you access real-time information",
}

_DATE_QUESTIONS = {
    "what's today's date",
    "what is today's date",
    "what is the date today",
    "what date is it today",
    "how do you know today's date",
    "what's the current date",
    "what is the current date",
    "what time is it",
    "what's the time now",
}

_CURRENT_EVENT_QUESTIONS = {
    "what happened yesterday",
    "what happened yesterday in india",
    "what happened yesterday internationally",
    "what happened yesterday in international news",
    "what happened yesterday in india and internationally",
    "give me today's news",
    "give me todays news",
    "what's today's news",
    "what is today's news",
    "today's news",
    "yesterday's international news",
    "yesterdays international news",
    "yesterday's india news",
    "yesterdays india news",
    "give me yesterday's international and india news",
    "give me yesterday's news",
    "give me yesterdays news",
}

_LIVE_INFO_TERMS = re.compile(
    r"\b(?:what(?:'s| is) new|latest|recent|recently|current|currently|today|today's|tonight|"
    r"yesterday|this week|this month|breaking|live|real[- ]time|news|"
    r"weather|forecast|stock price|exchange rate|score|standings|schedule)\b",
    re.IGNORECASE,
)


def needs_live_search(question: str) -> bool:
    """Return whether a request is likely to need fresh information."""
    return bool(_LIVE_INFO_TERMS.search(question))


def _normalize_question(question: str) -> str:
    normalized = question.casefold().replace("’", "'")
    return re.sub(r"\s+", " ", normalized).strip().rstrip(" ?!.")


def _host_clock_text(now: datetime | None = None) -> str:
    if now is None:
        current_time = datetime.now().astimezone()
    elif now.tzinfo is None:
        current_time = now.astimezone()
    else:
        current_time = now
    zone_name = current_time.tzname() or "local timezone"
    offset = current_time.strftime("%z")
    utc_offset = f"UTC{offset[:3]}:{offset[3:]}" if len(offset) == 5 else "UTC offset unavailable"
    return f"{current_time.isoformat(timespec='seconds')} ({zone_name}, {utc_offset})"


def build_runtime_capability_context() -> str:
    """Describe capabilities ARIA's application actually exposes to Gemini."""
    return (
        "ARIA RUNTIME CAPABILITY FACTS (authoritative for this application):\n"
        "- Gemini API: configured for model responses; an individual request may fail.\n"
        "- General model knowledge: available; its knowledge cutoff is not verified by ARIA.\n"
        "- Live web search: Exa is the primary provider when configured; searches may fail or return no sources.\n"
        "- Gemini Google Search grounding is an optional fallback and may be disabled.\n"
        "- Current date/time: ARIA Core reads the host system clock for direct date/time "
        "questions; that timestamp is not supplied to Gemini. Host clock accuracy is not "
        "independently verified.\n"
        "- Local calculator: available through the explicit calculate command.\n"
        "- Persistent memory: local SQLite, available through explicit memory commands "
        "and bounded matching retrieval when the database is accessible.\n\n"
        "Capability and provenance rules:\n"
        "- When web search results are supplied, use them for fresh claims and distinguish sourced facts from background knowledge.\n"
        "- Do not claim search was successful unless search results are present in this response.\n"
        "- If no web search results are available for a current-events request, say that current details could not be verified.\n"
        "- For date/time questions that reach Gemini, do not guess a timestamp; say that "
        "no timestamp was provided and ARIA Core can answer direct date/time questions "
        "from the host system clock.\n"
    )


def answer_capability_question(
    question: str, now: datetime | None = None
) -> str | None:
    """Answer a narrow set of direct capability, clock, and explicit news questions locally."""
    normalized = _normalize_question(question)

    if normalized in _REALTIME_QUESTIONS:
        return (
            "Yes. ARIA can use Exa for live web search when it is configured. Gemini Google Search grounding is an optional fallback."
        )

    if normalized in _DATE_QUESTIONS:
        current_time = _host_clock_text(now)
        return (
            f"According to ARIA's host system clock, the current date and time is "
            f"{current_time}. This timestamp was not supplied by Gemini."
        )

    if normalized in _CURRENT_EVENT_QUESTIONS:
        return None

    return None
