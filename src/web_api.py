"""Local web boundary for ARIA's existing application core."""

import importlib
import sys
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


MAX_MESSAGE_LENGTH = 4000
_MISSING_GEMINI_KEY_PREFIX = "GEMINI_API_KEY was not found"
_conversation_lock = threading.Lock()
_WEB_DIRECTORY = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def _load_core():
    try:
        return importlib.import_module("aria")
    except ValueError as error:
        if str(error).startswith(_MISSING_GEMINI_KEY_PREFIX):
            return None
        raise


def _is_temporary_gemini_failure(response: str) -> bool:
    model_module = sys.modules.get("models")
    expected_response = getattr(
        model_module, "TEMPORARY_GEMINI_ERROR_RESPONSE", None
    )
    return expected_response is not None and response == expected_response


def _process_turn(core, message: str) -> str:
    """Serialize user/history/core/assistant updates as one conversation turn."""
    with _conversation_lock:
        user_message = {"role": "user", "message": message}
        core.conversation.append(user_message)
        try:
            response = core.process_command(message)
        except Exception:
            if core.conversation and core.conversation[-1] is user_message:
                core.conversation.pop()
            raise

        if response is None:
            if core.conversation and core.conversation[-1] is user_message:
                core.conversation.pop()
            raise RuntimeError("A web chat turn unexpectedly returned no response.")

        core.conversation.append({"role": "aria", "message": response})
        return response


@app.exception_handler(RequestValidationError)
async def handle_invalid_request(_request, _error):
    return _error_response(
        422,
        "invalid_request",
        f"Provide a non-empty message of up to {MAX_MESSAGE_LENGTH} characters.",
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_request, _error):
    return _error_response(
        500,
        "internal_error",
        "ARIA could not complete this request. Please try again.",
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        return _error_response(
            422,
            "invalid_request",
            f"Provide a non-empty message of up to {MAX_MESSAGE_LENGTH} characters.",
        )

    if message.casefold() in {"exit", "quit"}:
        return _error_response(
            400,
            "command_unavailable",
            "Exit commands are not available in browser chat.",
        )

    core = _load_core()
    if core is None:
        return _error_response(
            503,
            "backend_not_configured",
            "Gemini is not configured for this local ARIA service.",
        )

    response = _process_turn(core, message)
    if _is_temporary_gemini_failure(response):
        return _error_response(
            503,
            "gemini_unavailable",
            "Gemini is temporarily unavailable right now. Please try again.",
        )
    return {"reply": response}


app.mount("/", StaticFiles(directory=str(_WEB_DIRECTORY), html=True), name="web")