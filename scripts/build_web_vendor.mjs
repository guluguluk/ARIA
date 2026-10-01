import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = fileURLToPath(new URL("../", import.meta.url));
const modulesDirectory = path.join(repositoryRoot, "node_modules");
const vendorDirectory = path.join(repositoryRoot, "web", "vendor");
const katexDirectory = path.join(modulesDirectory, "katex", "dist");

await rm(vendorDirectory, { recursive: true, force: true });

const assets = [
  ["markdown-it/dist/browser/markdown-it.umd.min.js", "markdown-it.min.js"],
  ["dompurify/dist/purify.min.js", "purify.min.js"],
  ["markdown-it-texmath/texmath.js", "markdown-it-texmath/texmath.js"],
  ["markdown-it-texmath/css/texmath.css", "markdown-it-texmath/texmath.css"],
  ["katex/dist/katex.min.js", "katex/katex.min.js"],
  ["katex/dist/contrib/auto-render.min.js", "katex/auto-render.min.js"],
  ["katex/dist/katex.min.css", "katex/katex.min.css"],
];

for (const [source, destination] of assets) {
  const destinationPath = path.join(vendorDirectory, destination);
  await mkdir(path.dirname(destinationPath), { recursive: true });
  await cp(
    path.join(modulesDirectory, source),
    destinationPath,
  );
}

await mkdir(path.join(vendorDirectory, "katex", "fonts"), { recursive: true });
await cp(path.join(katexDirectory, "fonts"), path.join(vendorDirectory, "katex", "fonts"), {
  recursive: true,
  filter: (source) =>
    source.endsWith(`${path.sep}fonts`) || source.endsWith(".woff2"),
});

const notices = [];
for (const [packageName, licenseFile] of [
  ["markdown-it", "LICENSE"],
  ["markdown-it-texmath", "license.txt"],
  ["dompurify", "LICENSE"],
  ["katex", "LICENSE"],
]) {
  const licensePath = path.join(modulesDirectory, packageName, licenseFile);
  const licenseText = await readFile(licensePath, "utf8");
  notices.push(`===== ${packageName} =====\n${licenseText.trim()}`);
}
await writeFile(
  path.join(vendorDirectory, "THIRD_PARTY_NOTICES.txt"),
  `${notices.join("\n\n")}\n`,
);