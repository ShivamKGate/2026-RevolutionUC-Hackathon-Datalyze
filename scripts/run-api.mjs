/**
 * Ensures apps/api/.venv exists with Python 3.12, installs requirements, runs Uvicorn.
 * No manual `activate` needed — uses the venv interpreter directly (works on Windows + Unix).
 */
import { execFileSync, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const VENV_DIR = path.join(ROOT, "apps", "api", ".venv");
const REQUIREMENTS = path.join(ROOT, "apps", "api", "requirements.txt");
const APP_DIR = path.join(ROOT, "apps", "api", "src");

const isWin = process.platform === "win32";

const venvPython = isWin
  ? path.join(VENV_DIR, "Scripts", "python.exe")
  : path.join(VENV_DIR, "bin", "python");

const REQUIREMENTS_STAMP = path.join(VENV_DIR, ".datalyze-requirements.sha256");

function run(cmd, args, opts = {}) {
  execFileSync(cmd, args, { stdio: "inherit", cwd: ROOT, ...opts });
}

function requirementsFingerprint() {
  const buf = readFileSync(REQUIREMENTS);
  return createHash("sha256").update(buf).digest("hex");
}

function needsPipInstall() {
  if (!existsSync(REQUIREMENTS_STAMP)) {
    return true;
  }
  try {
    return (
      readFileSync(REQUIREMENTS_STAMP, "utf8").trim() !==
      requirementsFingerprint()
    );
  } catch {
    return true;
  }
}

function writeRequirementsStamp() {
  writeFileSync(REQUIREMENTS_STAMP, `${requirementsFingerprint()}\n`, "utf8");
}

/**
 * @returns {{ cmd: string; prefix: string[] } | null}
 */
function findPython312Launcher() {
  const versionProbe = [
    "-c",
    "import sys; assert sys.version_info[:2] == (3, 12), f'need 3.12, got {sys.version}'; print(sys.executable)",
  ];

  if (isWin) {
    try {
      execFileSync("py", ["-3.12", ...versionProbe], {
        stdio: "pipe",
      });
      return { cmd: "py", prefix: ["-3.12"] };
    } catch {
      /* continue */
    }
    const la = process.env.LOCALAPPDATA;
    if (la) {
      const exe = path.join(la, "Programs", "Python", "Python312", "python.exe");
      if (existsSync(exe)) {
        try {
          execFileSync(exe, versionProbe, { stdio: "pipe" });
          return { cmd: exe, prefix: [] };
        } catch {
          /* not 3.12 */
        }
      }
    }
  }

  // Windows: try `python` before `python3` — `python3` often resolves to the Store stub.
  const shims = isWin
    ? ["python3.12", "python", "python3"]
    : ["python3.12", "python3", "python"];
  for (const cmd of shims) {
    try {
      execFileSync(cmd, versionProbe, { stdio: "pipe" });
      return { cmd, prefix: [] };
    } catch {
      /* try next */
    }
  }

  return null;
}

function ensureVenv(launcher) {
  if (existsSync(venvPython)) {
    return;
  }

  console.log(
    "[api] Creating virtualenv at apps/api/.venv with Python 3.12...",
  );
  run(launcher.cmd, [...launcher.prefix, "-m", "venv", VENV_DIR]);
}

function pipInstall() {
  if (!needsPipInstall()) {
    return;
  }
  console.log("[api] pip install -r apps/api/requirements.txt");
  run(venvPython, ["-m", "pip", "install", "--upgrade", "pip"]);
  run(venvPython, ["-m", "pip", "install", "-r", REQUIREMENTS]);
  writeRequirementsStamp();
}

function printPython312Help() {
  console.error(`
[api] Could not find Python 3.12 on PATH.

Install Python 3.12, then re-run npm run dev.

  Windows (winget):
    winget install -e --id Python.Python.3.12

  Or download: https://www.python.org/downloads/release/python-3120/

  After install, fully quit and reopen Cursor (or open a new terminal) so PATH updates.

  If 3.12 is installed but not found, ensure your User PATH lists
  ...\\Python\\Python312\\ before older Python versions.
`);
}

const launcher = findPython312Launcher();
if (!launcher) {
  printPython312Help();
  process.exit(1);
}

ensureVenv(launcher);

if (!existsSync(venvPython)) {
  console.error("[api] venv python missing after create:", venvPython);
  process.exit(1);
}

pipInstall();

const uvicorn = spawn(
  venvPython,
  [
    "-m",
    "uvicorn",
    "main:app",
    "--reload",
    "--app-dir",
    APP_DIR,
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
  ],
  { stdio: "inherit", cwd: ROOT, shell: false },
);

uvicorn.on("error", (err) => {
  console.error("[api] failed to start uvicorn:", err);
  process.exit(1);
});

uvicorn.on("exit", (code, signal) => {
  if (signal) {
    process.exit(1);
  }
  process.exit(code ?? 0);
});
