"""Local web boundary for ARIA's existing application core."""

import importlib
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


MAX_MESSAGE_LENGTH = 4000
MAX_AUDIO_BYTES = 15 * 1024 * 1024
SUPPORTED_AUDIO_TYPES = {"audio/webm", "audio/ogg", "audio/mp4", "audio/wav", "audio/mpeg"}
_MISSING_GEMINI_KEY_PREFIX = "GEMINI_API_KEY was not found"
_conversation_lock = threading.RLock()
_chat_histories = {}
_WEB_DIRECTORY = Path(__file__).resolve().parent.parent / "web"


class InvalidTurnError(Exception):
    pass

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    chat_id: str = Field(default="default", min_length=1, max_length=100)


class EditChatRequest(ChatRequest):
    message_index: int = Field(ge=0)


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


def _process_chat_turn(core, chat_id: str, message: str) -> str:
    """Keep independent browser chats on the shared core conversation safely."""
    if chat_id == "default":
        return _process_turn(core, message)
    with _conversation_lock:
        core.conversation = _chat_histories.setdefault(chat_id, [])
        response = _process_turn(core, message)
        _chat_histories[chat_id] = core.conversation
        return response


def _process_edit(core, message_index: int, message: str) -> str:
    """Replace a user turn and discard its old response and all later turns."""
    with _conversation_lock:
        history = core.conversation
        if message_index >= len(history) or history[message_index].get("role") != "user":
            raise InvalidTurnError("The conversation turn could not be edited.")
        previous_history = history[message_index:]
        del history[message_index:]
        try:
            response = _process_turn(core, message)
            if _is_temporary_gemini_failure(response):
                history[message_index:] = previous_history
            return response
        except Exception:
            history.extend(previous_history)
            raise


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


@app.post("/api/transcribe")
async def transcribe(request: Request):
    mime_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if mime_type not in SUPPORTED_AUDIO_TYPES:
        return _error_response(415, "unsupported_audio", "This microphone recording format is not supported.")
    audio_data = await request.body()
    if not audio_data:
        return _error_response(400, "empty_audio", "No audio was recorded. Please try again.")
    if len(audio_data) > MAX_AUDIO_BYTES:
        return _error_response(413, "audio_too_large", "That recording is too long. Please record a shorter prompt.")

    core = _load_core()
    if core is None:
        return _error_response(503, "backend_not_configured", "Gemini is not configured for this local ARIA service.")
    model_module = sys.modules.get("models")
    transcribe_audio = getattr(model_module, "transcribe_audio", None)
    if transcribe_audio is None:
        return _error_response(503, "transcription_unavailable", "Voice transcription is unavailable right now.")
    transcript = transcribe_audio(audio_data, mime_type)
    if _is_temporary_gemini_failure(transcript):
        return _error_response(503, "gemini_unavailable", "Voice transcription is temporarily unavailable. Please try again.")
    return {"transcript": transcript[:MAX_MESSAGE_LENGTH]}


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

    response = _process_chat_turn(core, request.chat_id, message)
    if _is_temporary_gemini_failure(response):
        return _error_response(
            503,
            "gemini_unavailable",
            "Gemini is temporarily unavailable right now. Please try again.",
        )
    return {"reply": response}


@app.post("/api/chat/edit")
def edit_chat(request: EditChatRequest):
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
    try:
        with _conversation_lock:
            if request.chat_id == "default":
                response = _process_edit(core, request.message_index, message)
            else:
                core.conversation = _chat_histories.setdefault(request.chat_id, [])
                response = _process_edit(core, request.message_index, message)
                _chat_histories[request.chat_id] = core.conversation
    except InvalidTurnError:
        return _error_response(404, "turn_unavailable", "That message can no longer be edited.")
    if _is_temporary_gemini_failure(response):
        return _error_response(
            503,
            "gemini_unavailable",
            "Gemini is temporarily unavailable right now. Please try again.",
        )
    return {"reply": response}


app.mount("/", StaticFiles(directory=str(_WEB_DIRECTORY), html=True), name="web")
