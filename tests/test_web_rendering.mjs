import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const markdownit = require("markdown-it");
const texmath = require("markdown-it-texmath");
const katex = require("katex");

function createRenderer() {
  const markdown = markdownit({ html: false, breaks: true });
  markdown.renderer.rules.image = (tokens, index) =>
    markdown.utils.escapeHtml(tokens[index].content || "");
  markdown.use(texmath, {
    engine: katex,
    delimiters: ["dollars", "brackets"],
    katexOptions: { throwOnError: false, trust: false },
  });
  return markdown;
}

test("renders headings, paragraphs, line breaks, emphasis, lists, quotes, and rules", () => {
  const source = [
    "# Heading",
    "",
    "Paragraph **bold** and *italic*.",
    "second line",
    "",
    "1. First",
    "2. Second",
    "",
    "- One",
    "- Two",
    "",
    "> Quote",
    "",
    "---",
  ].join("\n");
  const html = createRenderer().render(source);

  assert.match(html, /<h1>Heading<\/h1>/);
  assert.match(html, /<strong>bold<\/strong>/);
  assert.match(html, /<em>italic<\/em>/);
  assert.match(html, /<br>/);
  assert.match(html, /<ol>/);
  assert.match(html, /<ul>/);
  assert.match(html, /<blockquote>/);
  assert.match(html, /<hr/);
});

test("renders inline code and fenced code without interpreting their contents", () => {
  const html = createRenderer().render(
    "Use `**literal**` here.\n\n```html\n<script>doNotRun()</script>\n```",
  );

  assert.match(html, /<code>\*\*literal\*\*<\/code>/);
  assert.match(html, /<pre><code class=\"language-html\">/);
  assert.match(html, /&lt;script&gt;doNotRun\(\)&lt;\/script&gt;/);
  assert.doesNotMatch(html, /<script>/);
});

test("renders bracket inline math and dollar display math with KaTeX", () => {
  const source = String.raw`Inline \(E = mc^2\).` + "\n\n"
    + String.raw`$$\frac{a_1}{\sqrt{b^2}}$$`;
  const html = createRenderer().render(source);

  assert.match(html, /class=\"katex\"/);
  assert.match(html, /class=\"katex-display\"/);
  assert.match(html, /class=\"mfrac\"/);
  assert.match(html, /<msup>/);
  assert.match(html, /<msqrt>/);
  assert.match(html, /<svg\b/);
});

test("malformed Markdown and TeX fail gracefully", () => {
  const markdown = createRenderer();

  assert.doesNotThrow(() => markdown.render("### unfinished **emphasis\n\n- item"));
  assert.doesNotThrow(() => markdown.render(String.raw`$$\notARealCommand{$$`));
  assert.match(markdown.render("### unfinished **emphasis"), /<h3>/);
  assert.equal(markdown.render(""), "");
});

test("raw HTML, Markdown images, and unsafe link protocols do not create active markup", () => {
  const html = createRenderer().render(
    '<img src=x onerror="alert(1)"> [unsafe](javascript:alert(1)) ![remote](https://example.com/x.png)',
  );

  assert.doesNotMatch(html, /<img\b/i);
  assert.doesNotMatch(html, /<[^>]+\bonerror=/i);
  assert.doesNotMatch(html, /href=\"javascript:/i);
  assert.match(html, /&lt;img/);
  assert.match(html, /remote/);
  assert.doesNotMatch(html, /https:\/\/example\.com\/x\.png/);
});

test("long fenced code stays a single code block suitable for local horizontal scrolling", () => {
  const longLine = "x".repeat(12000);
  const html = createRenderer().render(`\`\`\`text\n${longLine}\n\`\`\``);

  assert.match(html, /<pre><code class=\"language-text\">/);
  assert.ok(html.length > 12000);
});
