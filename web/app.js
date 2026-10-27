"use strict";

const MAX_MESSAGE_LENGTH = 4000;
const form = document.querySelector("#composer");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const voiceButton = document.querySelector("#voice-button");
const messageList = document.querySelector("#message-list");
const welcomeBlock = document.querySelector("#welcome-block");
const errorMessage = document.querySelector("#compose-error");
const characterCount = document.querySelector("#character-count");
const connectionState = document.querySelector("#connection-state");
const themeToggle = document.querySelector("#theme-toggle");
const themeColorMeta = document.querySelector("#theme-color-meta");
const THEME_STORAGE_KEY = "aria.theme.v1";

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";
  themeToggle?.setAttribute("aria-pressed", String(isDark));
  themeToggle?.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} mode`);
  const icon = themeToggle?.querySelector(".theme-toggle-icon");
  const label = themeToggle?.querySelector(".theme-toggle-label");
  if (icon) icon.textContent = isDark ? "☀" : "☾";
  if (label) label.textContent = isDark ? "Light mode" : "Dark mode";
  if (themeColorMeta) themeColorMeta.content = isDark ? "#111a16" : "#eef2ed";
}

let savedTheme = "light";
try { savedTheme = localStorage.getItem(THEME_STORAGE_KEY) === "dark" ? "dark" : "light"; } catch { /* Storage may be unavailable. */ }
applyTheme(savedTheme);
themeToggle?.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  try { localStorage.setItem(THEME_STORAGE_KEY, nextTheme); } catch { /* Storage may be unavailable. */ }
});
let isSending = false;
let editTarget = null;
let turnCount = 0;
let activeReadAloud = null;
let voiceStream = null;
let voiceRecorder = null;
let voiceChunks = [];
const chatGroups = document.querySelector("#chat-groups");
const newChatButton = document.querySelector("#new-chat-button");
const CHAT_STORAGE_KEY = "aria.chats.v1";
const CATEGORIES = ["Work", "Coding", "Learning", "Writing", "Planning", "Personal", "General"];
let chats = loadChats();
let activeChatId = null;

function loadChats() {
  try {
    const saved = globalThis.localStorage?.getItem(CHAT_STORAGE_KEY);
    return saved ? JSON.parse(saved).filter((chat) => chat && chat.id && Array.isArray(chat.messages)) : [];
  } catch { return []; }
}

function saveChats() {
  try { globalThis.localStorage?.setItem(CHAT_STORAGE_KEY, JSON.stringify(chats)); } catch { /* Storage may be unavailable. */ }
}

function categorizeChat(text) {
  const value = text.toLowerCase();
  const rules = [
    ["Coding", /\b(code|coding|program|python|javascript|typescript|debug|function|api|html|css|sql|git|bug)\b/],
    ["Work", /\b(work|career|job|meeting|business|client|office|resume|interview|team)\b/],
    ["Learning", /\b(explain|learn|teach|study|meaning|why|how does|what is|derive|proof|concept)\b/],
    ["Writing", /\b(write|rewrite|draft|essay|story|email|blog|poem|edit|grammar|caption)\b/],
    ["Planning", /\b(plan|schedule|organize|itinerary|trip|budget|goals|checklist|steps|project)\b/],
    ["Personal", /\b(personal|health|fitness|recipe|cook|relationship|feel|habit|home)\b/],
  ];
  for (const [category, pattern] of rules) if (pattern.test(value)) return category;
  return "General";
}

function renderChatGroups() {
  if (!chatGroups) return;
  chatGroups.replaceChildren();
  for (const category of CATEGORIES) {
    const items = chats.filter((chat) => chat.category === category);
    if (!items.length) continue;
    const group = document.createElement("section"); group.className = "chat-group";
    const title = document.createElement("h2"); title.className = "chat-group-title"; title.textContent = category;
    group.append(title);
    for (const chat of items) {
      const button = document.createElement("button"); button.type = "button";
      button.className = `chat-item${chat.id === activeChatId ? " is-active" : ""}`;
      button.textContent = chat.title; button.title = chat.title;
      button.addEventListener("click", () => openChat(chat.id)); group.append(button);
    }
    chatGroups.append(group);
  }
}

function persistActiveChat() {
  if (!activeChatId) return;
  const chat = chats.find((item) => item.id === activeChatId);
  if (!chat) return;
  chat.messages = [...messageList.children].filter((item) => item.className.includes("message") && !item.className.includes("typing-message"))
    .map((item) => ({ role: item.className.includes("user") ? "user" : "assistant", text: item.children[1].children[1].textContent }));
  saveChats();
}

function openChat(id) {
  stopReadAloud();
  persistActiveChat(); activeChatId = id; const chat = chats.find((item) => item.id === id);
  messageList.replaceChildren(); welcomeBlock?.remove();
  if (chat?.messages.length) for (const item of chat.messages) addMessage(item.role, item.text, { turnIndex: turnCount++ });
  else showWelcome();
  renderChatGroups();
}

function showWelcome() {
  const block = document.createElement("div"); block.className = "welcome-block";
  block.innerHTML = '<p class="eyebrow"><span class="eyebrow-line" aria-hidden="true"></span> A thoughtful assistant</p><h1>Where should we<br><em>begin?</em></h1><p class="welcome-copy">Good questions, half-formed ideas, and tricky problems all belong here.</p>';
  messageList.append(block);
}

function startNewChat() {
  stopReadAloud();
  persistActiveChat(); activeChatId = null; turnCount = 0; editTarget = null;
  messageList.replaceChildren(); showWelcome(); renderChatGroups(); input.focus();
}

if (newChatButton) newChatButton.addEventListener("click", startNewChat);
renderChatGroups();
if (chats.length) openChat(chats[0].id);

const SAFE_API_ERRORS = {
  invalid_request: "Enter a message of up to 4,000 characters.",
  command_unavailable: "Exit commands are not available in browser chat.",
  backend_not_configured: "Gemini is not configured for this local ARIA service.",
  gemini_unavailable: "Gemini is temporarily unavailable right now. Please try again.",
  turn_unavailable: "That message can no longer be edited. Please refresh the conversation and try again.",
};

let markdownRenderer;
const SANITIZER_OPTIONS = {
  FORBID_TAGS: ["script", "style", "iframe", "object", "embed", "form", "input", "button", "img", "audio", "video"],
  ALLOW_DATA_ATTR: false,
};

function renderAssistantContent(content, text) {
  if (
    typeof globalThis.markdownit !== "function"
    || typeof globalThis.texmath !== "function"
    || typeof globalThis.katex?.renderToString !== "function"
    || typeof globalThis.DOMPurify?.sanitize !== "function"
  ) {
    content.textContent = text;
    return;
  }

  try {
    if (!markdownRenderer) {
      markdownRenderer = globalThis.markdownit({
        html: false,
        breaks: true,
        linkify: false,
        typographer: false,
      });
      markdownRenderer.renderer.rules.image = (tokens, index) =>
        markdownRenderer.utils.escapeHtml(tokens[index].content || "");
      markdownRenderer.use(globalThis.texmath, {
        engine: globalThis.katex,
        delimiters: ["dollars", "brackets"],
        katexOptions: {
          throwOnError: false,
          trust: false,
          strict: "warn",
        },
      });
    }

    const rendered = markdownRenderer.render(text);
    const sanitized = globalThis.DOMPurify.sanitize(rendered, SANITIZER_OPTIONS);
    content.innerHTML = sanitized;
  } catch {
    content.textContent = text;
  }
}

function stopReadAloud() {
  if (!activeReadAloud) return;
  const previous = activeReadAloud;
  activeReadAloud = null;
  previous.button.textContent = "Read aloud";
  previous.button.setAttribute("aria-label", "Read this response aloud");
  globalThis.speechSynthesis?.cancel();
}

function addReadAloudControl(body, content) {
  const button = document.createElement("button");
  button.className = "read-aloud-button";
  button.type = "button";
  button.textContent = "Read aloud";
  button.setAttribute("aria-label", "Read this response aloud");
  const speechAvailable = typeof globalThis.SpeechSynthesisUtterance === "function"
    && typeof globalThis.speechSynthesis?.speak === "function";
  button.disabled = !speechAvailable;
  if (!speechAvailable) button.title = "Read aloud is not available in this browser.";

  button.addEventListener("click", () => {
    if (!speechAvailable) return;
    if (activeReadAloud?.button === button) {
      stopReadAloud();
      return;
    }

    stopReadAloud();
    const utterance = new globalThis.SpeechSynthesisUtterance(content.innerText || content.textContent);
    const current = { button, utterance };
    activeReadAloud = current;
    button.textContent = "Stop";
    button.setAttribute("aria-label", "Stop reading this response");
    const reset = () => {
      if (activeReadAloud !== current) return;
      activeReadAloud = null;
      button.textContent = "Read aloud";
      button.setAttribute("aria-label", "Read this response aloud");
    };
    utterance.onend = reset;
    utterance.onerror = reset;
    try {
      globalThis.speechSynthesis.speak(utterance);
    } catch {
      reset();
    }
  });
  body.append(button);
}

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

  const richAssistantMessage = role === "assistant" && !options.error;
  const content = document.createElement(richAssistantMessage ? "div" : "p");
  content.className = "message-text";
  if (richAssistantMessage) {
    renderAssistantContent(content, text);
  } else {
    content.textContent = text;
  }

  body.append(label, content);
  if (richAssistantMessage) addReadAloudControl(body, content);
  if (role === "user") {
    const editButton = document.createElement("button");
    editButton.className = "edit-message-button";
    editButton.type = "button";
    editButton.textContent = "Edit";
    editButton.setAttribute("aria-label", "Edit this message");
    editButton.addEventListener("click", () => {
      editTarget = { element: message, index: options.turnIndex, content };
      input.value = content.textContent;
      updateComposer();
      sendButton.querySelector("span:first-child").textContent = "Update";
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    });
    body.append(editButton);
  }
  message.append(avatar, body);
  messageList.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return message;
}

function addTypingIndicator() {
  const message = document.createElement("article");
  message.className = "message assistant typing-message";
  message.setAttribute("aria-label", "ARIA is thinking");

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "A";

  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = "ARIA is thinking…";
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
  if (isSending) {
    return;
  }

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

  isSending = true;
  let typing;
  const editing = editTarget;

  try {
    if (!activeChatId && !editing) {
      activeChatId = `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const category = categorizeChat(message);
      chats.unshift({ id: activeChatId, title: message.slice(0, 48), category, messages: [] });
      renderChatGroups();
    }
    welcomeBlock?.remove();
    if (!editing) {
      addMessage("user", message, { turnIndex: turnCount });
      turnCount += 1;
    }
    input.value = "";
    updateComposer();
    input.style.height = "46px";
    sendButton.disabled = true;
    sendButton.querySelector("span:first-child").textContent = "Sending";
    typing = addTypingIndicator();

    const response = await fetch(editing ? "/api/chat/edit" : "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editing
        ? { message, message_index: editing.index * 2, chat_id: activeChatId }
        : { message, chat_id: activeChatId }),
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

    if (editing) {
      stopReadAloud();
      editing.content.textContent = message;
      let removeFollowing = false;
      for (const child of [...messageList.children]) {
        if (child === editing.element) {
          removeFollowing = true;
          continue;
        }
        if (removeFollowing) child.remove();
      }
      turnCount = editing.index + 1;
      editTarget = null;
    }
    addMessage("assistant", result.reply);
    persistActiveChat();
    renderChatGroups();
  } catch {
    setConnectionState(false);
    addMessage("assistant", "The local ARIA service is unavailable. Try again when it is running.", { error: true });
  } finally {
    typing?.remove();
    isSending = false;
    sendButton.disabled = false;
    sendButton.querySelector("span:first-child").textContent = editTarget ? "Update" : "Send";
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  void sendMessage();
});

if (voiceButton) {
  if (!navigator.mediaDevices?.getUserMedia || typeof globalThis.MediaRecorder !== "function") {
    voiceButton.disabled = true;
    voiceButton.title = "Voice recording is not supported in this browser";
    voiceButton.setAttribute("aria-label", "Voice recording is not supported in this browser");
  } else {
    const resetVoiceButton = () => {
      voiceButton.classList.remove("is-listening", "is-processing");
      voiceButton.setAttribute("aria-pressed", "false");
      voiceButton.disabled = false;
      voiceButton.title = "Dictate prompt";
      voiceButton.setAttribute("aria-label", "Dictate prompt");
    };

    const transcribeVoice = async (blob) => {
      voiceButton.classList.remove("is-listening");
      voiceButton.classList.add("is-processing");
      voiceButton.disabled = true;
      voiceButton.title = "Transcribing voice input";
      voiceButton.setAttribute("aria-label", "Transcribing voice input");
      try {
        const response = await fetch("/api/transcribe", {
          method: "POST",
          headers: { "Content-Type": blob.type || "audio/webm" },
          body: blob,
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error?.message || "Voice transcription failed. Please try again.");
        const transcript = String(data.transcript || "").trim();
        if (!transcript) throw new Error("No speech was detected. Please try again.");
        const separator = input.value && !/\s$/.test(input.value) ? " " : "";
        input.value = `${input.value}${separator}${transcript}`.slice(0, MAX_MESSAGE_LENGTH);
        updateComposer();
        input.focus();
      } catch (error) {
        errorMessage.textContent = error.message || "Voice transcription failed. Please try again.";
        errorMessage.hidden = false;
      } finally {
        voiceStream?.getTracks().forEach((track) => track.stop());
        voiceStream = null;
        voiceRecorder = null;
        resetVoiceButton();
      }
    };

    voiceButton.addEventListener("click", async () => {
      if (voiceRecorder?.state === "recording") {
        voiceRecorder.stop();
        voiceButton.classList.remove("is-listening");
        voiceButton.classList.add("is-processing");
        voiceButton.title = "Transcribing voice input";
        voiceButton.setAttribute("aria-label", "Transcribing voice input");
        return;
      }
      try {
        errorMessage.hidden = true;
        voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        voiceChunks = [];
        const preferredType = "audio/webm;codecs=opus";
        const options = MediaRecorder.isTypeSupported?.(preferredType) ? { mimeType: preferredType } : undefined;
        voiceRecorder = new MediaRecorder(voiceStream, options);
        voiceRecorder.addEventListener("dataavailable", (event) => {
          if (event.data.size) voiceChunks.push(event.data);
        });
        voiceRecorder.addEventListener("stop", () => {
          const blob = new Blob(voiceChunks, { type: voiceRecorder?.mimeType || "audio/webm" });
          if (blob.size) void transcribeVoice(blob);
          else {
            voiceStream?.getTracks().forEach((track) => track.stop());
            voiceStream = null;
            voiceRecorder = null;
            resetVoiceButton();
            errorMessage.textContent = "No audio was recorded. Check your microphone and try again.";
            errorMessage.hidden = false;
          }
        }, { once: true });
        voiceRecorder.start();
        voiceButton.classList.add("is-listening");
        voiceButton.setAttribute("aria-pressed", "true");
        voiceButton.title = "Stop recording and transcribe";
        voiceButton.setAttribute("aria-label", "Stop recording and transcribe");
      } catch (error) {
        voiceStream?.getTracks().forEach((track) => track.stop());
        voiceStream = null;
        resetVoiceButton();
        errorMessage.textContent = error.name === "NotAllowedError"
          ? "Allow microphone access in your browser to use voice input."
          : "Could not access the microphone. Check that it is connected and try again.";
        errorMessage.hidden = false;
      }
    });
  }
}

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
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });
});

void checkConnection();
