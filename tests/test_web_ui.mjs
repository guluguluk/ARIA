import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const appSource = await readFile(new URL("../web/app.js", import.meta.url), "utf8");

class FakeElement {
  constructor() {
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.style = {};
    this.className = "";
    this.textContent = "";
    this.value = "";
    this.disabled = false;
    this.hidden = false;
    this.scrollHeight = 46;
    this.removed = false;
    this.dataset = {};
    this.parentElement = null;
    this.classList = {
      toggle: (name, enabled) => {
        const names = new Set(this.className.split(/\s+/).filter(Boolean));
        if (enabled) names.add(name);
        else names.delete(name);
        this.className = [...names].join(" ");
      },
    };
  }

  append(...elements) {
    for (const element of elements) {
      element.parentElement = this;
      this.children.push(element);
    }
  }

  addEventListener(name, listener) {
    this.listeners.set(name, listener);
  }

  dispatch(name, event = {}) {
    return this.listeners.get(name)?.({
      preventDefault() {},
      ...event,
    });
  }

  requestSubmit() {
    return this.dispatch("submit");
  }

  querySelector(selector) {
    if (selector === "span:first-child") return this.children[0];
    if (selector === ".connection-label") {
      return this.children.find((child) => child.className === "connection-label");
    }
    return undefined;
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  remove() {
    this.removed = true;
    if (this.parentElement) {
      this.parentElement.children = this.parentElement.children.filter(
        (child) => child !== this,
      );
    }
  }

  scrollIntoView() {}
  focus() {}
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function createUi(chatFetch) {
  const selectors = [
    "#composer",
    "#message-input",
    "#send-button",
    "#message-list",
    "#welcome-block",
    "#compose-error",
    "#character-count",
    "#connection-state",
  ];
  const elements = new Map(selectors.map((selector) => [selector, new FakeElement()]));
  const sendLabel = new FakeElement();
  sendLabel.textContent = "Send";
  elements.get("#send-button").append(sendLabel, new FakeElement());
  const connectionLabel = new FakeElement();
  connectionLabel.className = "connection-label";
  elements.get("#connection-state").append(connectionLabel);

  let chatRequestCount = 0;
  const document = {
    querySelector: (selector) => elements.get(selector),
    querySelectorAll: () => [],
    createElement: () => new FakeElement(),
  };
  const fetch = (url, options) => {
    if (url === "/api/health") return Promise.resolve({ ok: true });
    chatRequestCount += 1;
    return chatFetch(url, options);
  };
  const context = vm.createContext({ document, fetch });
  vm.runInContext(appSource, context, { filename: "web/app.js" });

  return {
    context,
    elements,
    get chatRequestCount() {
      return chatRequestCount;
    },
    typingMessages() {
      return elements.get("#message-list").children.filter((child) =>
        child.className.includes("typing-message"),
      );
    },
    assistantTexts() {
      return elements.get("#message-list").children
        .filter((message) => message.className.includes("assistant")
          && !message.className.includes("typing-message"))
        .map((message) => message.children[1].children[1].textContent);
    },
  };
}

test("thinking indicator stays until a delayed response arrives", async () => {
  const request = deferred();
  const ui = createUi(() => request.promise);

  const sendPromise = ui.context.sendMessage("Please wait");
  assert.equal(ui.chatRequestCount, 1);
  assert.equal(ui.typingMessages().length, 1);
  assert.equal(
    ui.typingMessages()[0].children[1].children[0].textContent,
    "ARIA is thinking…",
  );

  request.resolve({ ok: true, json: async () => ({ reply: "The response arrived." }) });
  await sendPromise;

  assert.equal(ui.typingMessages().length, 0);
  assert.deepEqual(ui.assistantTexts(), ["The response arrived."]);
  assert.equal(ui.elements.get("#send-button").disabled, false);
});

test("failed request displays the existing error and always removes indicator", async () => {
  const request = deferred();
  const ui = createUi(() => request.promise);

  const sendPromise = ui.context.sendMessage("Fail safely");
  assert.equal(ui.typingMessages().length, 1);
  request.reject(new Error("private transport detail"));
  await sendPromise;

  assert.equal(ui.typingMessages().length, 0);
  assert.deepEqual(ui.assistantTexts(), [
    "The local ARIA service is unavailable. Try again when it is running.",
  ]);
  assert.equal(ui.elements.get("#send-button").disabled, false);
});

test("form submissions during an active request do not start duplicates", async () => {
  const request = deferred();
  const ui = createUi(() => request.promise);
  const form = ui.elements.get("#composer");
  ui.elements.get("#message-input").value = "First message";

  form.dispatch("submit");
  form.dispatch("submit");
  await ui.context.sendMessage("Third message");

  assert.equal(ui.chatRequestCount, 1);
  assert.equal(ui.typingMessages().length, 1);
  request.resolve({ ok: true, json: async () => ({ reply: "Done." }) });
  await new Promise(setImmediate);

  assert.equal(ui.typingMessages().length, 0);
  assert.equal(ui.chatRequestCount, 1);
});