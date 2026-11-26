#!/usr/bin/env node
// Local-first review gate. Default: deterministic git check; AI modes require opt-in.
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
const base = opt("--base");
if (base && (base.startsWith("-") || !/^[\w.\/-]+$/.test(base))) {
  console.error("Invalid --base ref"); process.exit(2);
}
const git = (gitArgs) => spawnSync("git", gitArgs, { cwd: root, encoding: "utf8", maxBuffer: 1024 * 1024 });
const range = base ? [base + "...HEAD"] : [];
const check = git(["diff", "--check", ...range]);
if (check.status !== 0) {
  console.error(check.stderr || check.stdout || "git diff --check failed");
  process.exit(check.status || 1);
}
console.log("PASS: git diff --check");
console.log(git(["diff", "--stat", ...range]).stdout.trim() || "No tracked diff");
if (args.includes("--codex")) {
  console.log("Starting Codex review. This uses the configured Codex account and can consume usage quota.");
  const result = spawnSync("codex", ["review", ...(base ? ["--base", base] : ["--uncommitted"])], { cwd: root, stdio: "inherit", shell: process.platform === "win32" });
  process.exit(result.status ?? 1);
}
if (args.includes("--local-ai")) {
  const paths = [".", ":(exclude)**/.env*", ":(exclude)**/*.pem", ":(exclude)**/*.key", ":(exclude)**/secrets/**", ":(exclude)**/outputs/**"];
  const diff = git(["diff", "--no-ext-diff", ...range, "--", ...paths]);
  if (diff.status !== 0) throw new Error(diff.stderr || "Cannot read diff");
  if (!diff.stdout.trim()) { console.log("No code changes to review"); process.exit(0); }
  if (diff.stdout.length > 60000) { console.error("Diff too large; split the review"); process.exit(2); }
  const model = process.env.LOCAL_REVIEW_MODEL || "qwen2.5-coder:7b";
  try {
    const response = await fetch("http://127.0.0.1:11434/api/generate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, stream: false,
        prompt: "Review this git diff as a skeptical senior engineer. Identify only reproducible P0/P1/P2 bugs with file and evidence. Report uncertainty. Do not claim tests passed. Diff:\n" + diff.stdout })
    });
    if (!response.ok) throw new Error("Local Ollama returned HTTP " + response.status);
    const json = await response.json();
    console.log(json.response || "No review returned");
  } catch (error) {
    console.error("Local AI unavailable. Install Ollama, pull " + model + " and run its local service. " + error.message);
    process.exitCode = 1;
  }
} else {
  console.log("Deterministic gate only. Use --local-ai for localhost Ollama or --codex for account-backed AI review.");
}
