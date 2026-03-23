#!/usr/bin/env node
/**
 * bin/install.js
 * ==============
 * CLI installer for ola-obs-contracts.
 *
 * Usage:
 *   npx ola-obs-contracts              # Install globally (default)
 *   npx ola-obs-contracts --local      # Install into current project
 *   npx ola-obs-contracts --uninstall  # Remove installation
 *   npx ola-obs-contracts --help       # Show usage
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

// ── Constants ────────────────────────────────────────────────────────────────

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const VERSION = require(path.join(PACKAGE_ROOT, "package.json")).version;
const HOOK_IDENTIFIER = "obs-post-edit";

const C = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  cyan: "\x1b[36m",
  red: "\x1b[31m",
};

// ── Arg Parsing ──────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const flags = {
  global: args.includes("--global") || args.includes("-g") || (!args.includes("--local") && !args.includes("-l")),
  local: args.includes("--local") || args.includes("-l"),
  uninstall: args.includes("--uninstall") || args.includes("-u"),
  help: args.includes("--help") || args.includes("-h"),
  configDir: null,
};

const configIdx = args.indexOf("--config-dir");
if (configIdx !== -1 && args[configIdx + 1]) {
  flags.configDir = args[configIdx + 1];
}

if (flags.local) flags.global = false;

// ── Help ─────────────────────────────────────────────────────────────────────

if (flags.help) {
  console.log(`
${C.bold}ola-obs-contracts v${VERSION}${C.reset}
Observable Language Applied — Observability contracts for AI-assisted development.

${C.cyan}Usage:${C.reset}
  npx ola-obs-contracts              Install globally to ~/.claude/ (default)
  npx ola-obs-contracts --local      Install into current project .claude/
  npx ola-obs-contracts --uninstall  Remove installation
  npx ola-obs-contracts --help       Show this help

${C.cyan}Options:${C.reset}
  -g, --global       Install to ~/.claude/ (default)
  -l, --local        Install to ./.claude/
  -u, --uninstall    Remove obs-contracts files and hooks
  --config-dir <dir> Override the target config directory

${C.cyan}After install:${C.reset}
  /obs:init          Scaffold a new project with observability contracts
  /obs:check         Run compliance check on current project
  /obs:trace         Show endpoint trace map
`);
  process.exit(0);
}

// ── Path Helpers ─────────────────────────────────────────────────────────────

function expandHome(p) {
  if (p.startsWith("~")) return path.join(os.homedir(), p.slice(1));
  return p;
}

function forwardSlash(p) {
  return p.replace(/\\/g, "/");
}

function getTargetDir() {
  if (flags.configDir) return expandHome(flags.configDir);
  if (flags.local) return path.resolve(process.cwd(), ".claude");
  return expandHome(process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude"));
}

// ── File Operations ──────────────────────────────────────────────────────────

function copyDirRecursive(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function removeDirSafe(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
    return true;
  }
  return false;
}

function removeFileSafe(file) {
  if (fs.existsSync(file)) {
    fs.unlinkSync(file);
    return true;
  }
  return false;
}

// ── Settings.json Merge ──────────────────────────────────────────────────────

function readSettings(settingsPath) {
  if (fs.existsSync(settingsPath)) {
    try {
      return JSON.parse(fs.readFileSync(settingsPath, "utf8"));
    } catch {
      return {};
    }
  }
  return {};
}

function writeSettings(settingsPath, settings) {
  fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n");
}

function buildHookCommand(configDir) {
  const hookPath = forwardSlash(path.join(configDir, "hooks", "obs-post-edit.js"));
  return `node "${hookPath}"`;
}

function addHookToSettings(settingsPath, configDir) {
  const settings = readSettings(settingsPath);

  if (!settings.hooks) settings.hooks = {};
  if (!Array.isArray(settings.hooks.PostToolUse)) settings.hooks.PostToolUse = [];

  // Check if our hook is already registered
  const alreadyInstalled = settings.hooks.PostToolUse.some((entry) => {
    if (entry.command && entry.command.includes(HOOK_IDENTIFIER)) return true;
    if (entry.hooks && Array.isArray(entry.hooks)) {
      return entry.hooks.some((h) => h.command && h.command.includes(HOOK_IDENTIFIER));
    }
    return false;
  });

  if (!alreadyInstalled) {
    settings.hooks.PostToolUse.push({
      matcher: "Edit|Write",
      hooks: [
        {
          type: "command",
          command: buildHookCommand(configDir),
        },
      ],
    });
  }

  writeSettings(settingsPath, settings);
}

function removeHookFromSettings(settingsPath) {
  const settings = readSettings(settingsPath);

  if (settings.hooks && Array.isArray(settings.hooks.PostToolUse)) {
    settings.hooks.PostToolUse = settings.hooks.PostToolUse.filter((entry) => {
      if (entry.command && entry.command.includes(HOOK_IDENTIFIER)) return false;
      if (entry.hooks && Array.isArray(entry.hooks)) {
        const hasObs = entry.hooks.some((h) => h.command && h.command.includes(HOOK_IDENTIFIER));
        if (hasObs) return false;
      }
      return true;
    });

    // Clean up empty arrays/objects
    if (settings.hooks.PostToolUse.length === 0) delete settings.hooks.PostToolUse;
    if (Object.keys(settings.hooks).length === 0) delete settings.hooks;
  }

  writeSettings(settingsPath, settings);
}

// ── Install ──────────────────────────────────────────────────────────────────

function install() {
  const targetDir = getTargetDir();
  const scope = flags.global ? "global" : "local";
  const settingsPath = path.join(targetDir, "settings.json");

  console.log(`\n${C.bold}ola-obs-contracts v${VERSION}${C.reset}`);
  console.log(`${C.dim}Installing ${scope}ly to: ${forwardSlash(targetDir)}${C.reset}\n`);

  fs.mkdirSync(targetDir, { recursive: true });

  // 1. Commands
  const commandsSrc = path.join(PACKAGE_ROOT, "commands", "obs");
  const commandsDest = path.join(targetDir, "commands", "obs");
  if (fs.existsSync(commandsDest)) fs.rmSync(commandsDest, { recursive: true, force: true });
  copyDirRecursive(commandsSrc, commandsDest);
  console.log(`  ${C.green}\u2713${C.reset} commands/obs/ installed (${C.cyan}/obs:init${C.reset}, ${C.cyan}/obs:check${C.reset}, ${C.cyan}/obs:trace${C.reset})`);

  // 2. Global hook
  const hookSrc = path.join(PACKAGE_ROOT, "hooks", "obs-post-edit.js");
  const hookDest = path.join(targetDir, "hooks", "obs-post-edit.js");
  fs.mkdirSync(path.dirname(hookDest), { recursive: true });
  fs.copyFileSync(hookSrc, hookDest);
  console.log(`  ${C.green}\u2713${C.reset} hooks/obs-post-edit.js installed (PostToolUse enforcement)`);

  // 3. Templates
  const templatesSrc = path.join(PACKAGE_ROOT, "templates");
  const templatesDest = path.join(targetDir, "obs-templates");
  if (fs.existsSync(templatesDest)) fs.rmSync(templatesDest, { recursive: true, force: true });
  copyDirRecursive(templatesSrc, templatesDest);
  console.log(`  ${C.green}\u2713${C.reset} obs-templates/ installed (reference files for /obs:init)`);

  // 4. Version marker
  fs.writeFileSync(path.join(templatesDest, "VERSION"), VERSION + "\n");

  // 5. Merge hook into settings.json
  addHookToSettings(settingsPath, targetDir);
  console.log(`  ${C.green}\u2713${C.reset} settings.json updated (PostToolUse hook registered)`);

  // Done
  console.log(`
${C.bold}${C.green}\u2713 Installation complete!${C.reset}

${C.bold}Available commands:${C.reset}
  ${C.cyan}/obs:init${C.reset}   Scaffold observability contracts into any project
  ${C.cyan}/obs:check${C.reset}  Run compliance check (docstrings + @observable)
  ${C.cyan}/obs:trace${C.reset}  Show endpoint call-tree visualization

${C.bold}What happens automatically:${C.reset}
  After every Edit/Write, the PostToolUse hook checks for violations
  in any project that has contracts/observable.py.

${C.bold}Quick start:${C.reset}
  1. Open Claude Code in any project
  2. Type ${C.cyan}/obs:init${C.reset}
  3. Start coding \u2014 the hooks enforce quality automatically
`);
}

// ── Uninstall ────────────────────────────────────────────────────────────────

function uninstall() {
  const targetDir = getTargetDir();
  const scope = flags.global ? "global" : "local";
  const settingsPath = path.join(targetDir, "settings.json");

  console.log(`\n${C.bold}ola-obs-contracts${C.reset} ${C.dim}\u2014 uninstalling from ${forwardSlash(targetDir)}${C.reset}\n`);

  let removed = 0;
  if (removeDirSafe(path.join(targetDir, "commands", "obs"))) {
    console.log(`  ${C.yellow}\u2713${C.reset} commands/obs/ removed`);
    removed++;
  }
  if (removeFileSafe(path.join(targetDir, "hooks", "obs-post-edit.js"))) {
    console.log(`  ${C.yellow}\u2713${C.reset} hooks/obs-post-edit.js removed`);
    removed++;
  }
  if (removeDirSafe(path.join(targetDir, "obs-templates"))) {
    console.log(`  ${C.yellow}\u2713${C.reset} obs-templates/ removed`);
    removed++;
  }

  if (fs.existsSync(settingsPath)) {
    removeHookFromSettings(settingsPath);
    console.log(`  ${C.yellow}\u2713${C.reset} settings.json cleaned (hook removed)`);
    removed++;
  }

  if (removed === 0) {
    console.log(`  ${C.dim}Nothing to remove \u2014 not installed at this location.${C.reset}`);
  } else {
    console.log(`\n${C.green}\u2713 Uninstall complete.${C.reset}\n`);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────

if (flags.uninstall) {
  uninstall();
} else {
  install();
}
