"use strict";

const MAX_MESSAGE_LENGTH = 4000;
const form = document.querySelector("#composer");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const messageList = document.querySelector("#message-list");
const welcomeBlock = document.querySelector("#welcome-block");
const errorMessage = document.querySelector("#compose-error");
const characterCount = document.querySelector("#character-count");
const connectionState = document.querySelector("#connection-state");

const SAFE_API_ERRORS = {
  invalid_request: "Enter a message of up to 4,000 characters.",
  command_unavailable: "Exit commands are not available in browser chat.",
  backend_not_configured: "Gemini is not configured for this local ARIA service.",
  gemini_unavailable: "Gemini is temporarily unavailable right now. Please try again.",
};

function setConnectionState(connected) {
  connectionState.classList.toggle("is-connected", connected);
  connectionState.classList.toggle("is-offline", !connected);
  connectionState.querySelector(".connection-label").textContent = connected
    ? "Local API connected"
    : "Local API offline";
}

async function checkConnection() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    setConnectionState(response.ok);
  } catch {
    setConnectionState(false);
  }
}

function updateComposer() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
  characterCount.textContent = `${input.value.length} / ${MAX_MESSAGE_LENGTH}`;
  errorMessage.hidden = true;
  errorMessage.textContent = "";
}

function addMessage(role, text, options = {}) {
  const message = document.createElement("article");
  message.className = `message ${role}${options.error ? " error" : ""}`;

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "Y" : "A";

  const body = document.createElement("div");
  body.className = "message-body";

  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : options.error ? "ARIA · error" : "ARIA";

  const content = document.createElement("p");
  content.className = "message-text";
  content.textContent = text;

  body.append(label, content);
  message.append(avatar, body);
  messageList.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return message;
}

function addTypingIndicator() {
  const message = document.createElement("article");
  message.className = "message assistant typing-message";
  message.setAttribute("aria-label", "ARIA is preparing a response");

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "A";

  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = "ARIA · working";
  const indicator = document.createElement("span");
  indicator.className = "typing-indicator";
  indicator.setAttribute("aria-hidden", "true");
  indicator.append(document.createElement("span"), document.createElement("span"), document.createElement("span"));
  body.append(label, indicator);
  message.append(avatar, body);
  messageList.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return message;
}

async function sendMessage(value = input.value) {
  const message = value.trim();
  if (!message) {
    errorMessage.textContent = "Write a message before sending.";
    errorMessage.hidden = false;
    input.focus();
    return;
  }

  if (message.length > MAX_MESSAGE_LENGTH) {
    errorMessage.textContent = `Messages must be ${MAX_MESSAGE_LENGTH} characters or fewer.`;
    errorMessage.hidden = false;
    input.focus();
    return;
  }

  welcomeBlock?.remove();
  addMessage("user", message);
  input.value = "";
  updateComposer();
  input.style.height = "46px";
  sendButton.disabled = true;
  sendButton.querySelector("span:first-child").textContent = "Sending";
  const typing = addTypingIndicator();

  try {
    typing.remove();
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const result = await response.json().catch(() => null);

    if (!response.ok) {
      const errorCode = result?.error?.code;
      const safeMessage = SAFE_API_ERRORS[errorCode]
        || "ARIA could not complete this request. Please try again.";
      addMessage("assistant", safeMessage, { error: true });
      return;
    }

    if (typeof result?.reply !== "string") {
      addMessage("assistant", "ARIA returned an invalid response. Please try again.", { error: true });
      return;
    }

    addMessage("assistant", result.reply);
  } catch {
    typing.remove();
    setConnectionState(false);
    addMessage("assistant", "The local ARIA service is unavailable. Try again when it is running.", { error: true });
  } finally {
    sendButton.disabled = false;
    sendButton.querySelector("span:first-child").textContent = "Send";
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  void sendMessage();
});

input.addEventListener("input", updateComposer);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    updateComposer();
    form.requestSubmit();
  });
});

void checkConnection();