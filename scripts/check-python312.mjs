/**
 * Runs after npm install. Always exits 0 so `npm i` succeeds without Python (web-only).
 * Prints whether Python 3.12 is available for `npm run dev` / the API.
 */
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const isWin = process.platform === "win32";
const probe = [
  "-c",
  "import sys; assert sys.version_info[:2] == (3, 12); print(sys.version.split()[0])",
];

function tryCmd(cmd, args = []) {
  try {
    const out = execFileSync(cmd, [...args, ...probe], {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    }).trim();
    return out;
  } catch {
    return null;
  }
}

let ver = null;
if (isWin) {
  ver = tryCmd("py", ["-3.12"]);
  if (!ver) {
    const la = process.env.LOCALAPPDATA;
    if (la) {
      const exe = path.join(la, "Programs", "Python", "Python312", "python.exe");
      if (existsSync(exe)) ver = tryCmd(exe);
    }
  }
}
if (!ver) {
  for (const cmd of isWin
    ? ["python3.12", "python", "python3"]
    : ["python3.12", "python3", "python"]) {
    ver = tryCmd(cmd);
    if (ver) break;
  }
}

if (ver) {
  console.log(`[datalyze] Python 3.12 OK (${ver}) — API can run with npm run dev.`);
} else {
  console.warn(
    "[datalyze] Python 3.12 not detected. Install with: winget install -e --id Python.Python.3.12",
  );
  console.warn(
    "[datalyze] Then restart your terminal (or Cursor) so PATH includes Python 3.12.",
  );
}
