#!/usr/bin/env node
/**
 * hooks/obs-post-edit.js
 * ======================
 * Global PostToolUse hook for Claude Code.
 *
 * Runs after every Edit/Write. Detects if the current project uses
 * obs-contracts (has contracts/observable.py), then spawns the Python
 * compliance checker. Silent exit for non-obs projects.
 *
 * Installed by: npx ola-obs-contracts
 * Registered in: ~/.claude/settings.json (PostToolUse, matcher: Edit|Write)
 */

const fs = require("fs");
const path = require("path");
const { execSync, spawnSync } = require("child_process");

// 10-second timeout guard for stdin issues
const timeout = setTimeout(() => process.exit(0), 10000);

// ── Read stdin (Claude Code pipes JSON with tool_input, cwd, etc.) ──────────

let inputData = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { inputData += chunk; });
process.stdin.on("end", () => {
  clearTimeout(timeout);
  run(inputData);
});
// If stdin is already closed (piped empty), run immediately
if (process.stdin.isTTY) {
  clearTimeout(timeout);
  run("{}");
}

function run(raw) {
  let input = {};
  try {
    input = JSON.parse(raw || "{}");
  } catch {
    // Malformed input — exit silently
    process.exit(0);
  }

  const cwd = input.cwd || process.cwd();
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || "";

  // ── Gate 1: Is this an obs-contracts project? ───────────────────────────
  const contractPath = path.join(cwd, "contracts", "observable.py");
  if (!fs.existsSync(contractPath)) {
    process.exit(0);
  }

  // ── Gate 2: Was a Python file edited? ───────────────────────────────────
  if (filePath && !filePath.endsWith(".py")) {
    process.exit(0);
  }

  // ── Gate 3: Is the edited file in src/ or tests/? ──────────────────────
  const rel = filePath ? path.relative(cwd, filePath).replace(/\\/g, "/") : "";
  if (rel && !rel.startsWith("src/") && !rel.startsWith("tests/")) {
    process.exit(0);
  }

  // ── Find Python interpreter ─────────────────────────────────────────────
  const pythonCmd = findPython();
  if (!pythonCmd) {
    process.stdout.write("[obs] Python not found \u2014 skipping compliance check.\n");
    process.exit(0);
  }

  // ── Run the compliance checker ──────────────────────────────────────────
  const hookScript = path.join(cwd, "hooks", "post_edit_check.py");
  if (!fs.existsSync(hookScript)) {
    // No local hook script — try the eval directly
    const evalResult = spawnSync(pythonCmd, ["-m", "evals.check_observability", "./src", "./tests"], {
      cwd: cwd,
      stdio: ["ignore", "pipe", "pipe"],
      timeout: 15000,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    if (evalResult.stdout) process.stdout.write(evalResult.stdout);
    if (evalResult.stderr) process.stderr.write(evalResult.stderr);
    process.exit(evalResult.status || 0);
  }

  const result = spawnSync(pythonCmd, [hookScript, "./src", "./tests"], {
    cwd: cwd,
    stdio: ["ignore", "pipe", "pipe"],
    timeout: 15000,
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });

  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  process.exit(result.status || 0);
}

// ── Python Detection ──────────────────────────────────────────────────────────

let _cachedPython = undefined;

function findPython() {
  if (_cachedPython !== undefined) return _cachedPython;

  const candidates = process.platform === "win32"
    ? ["python", "python3", "py"]
    : ["python3", "python"];

  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: "ignore", timeout: 5000 });
      _cachedPython = cmd;
      return cmd;
    } catch {
      // Try next candidate
    }
  }

  _cachedPython = null;
  return null;
}
