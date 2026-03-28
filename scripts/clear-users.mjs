/**
 * Clears all users, companies, datasets, and analyses, then resets sequences.
 * Run from repo root: node scripts/clear-users.mjs
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";

const { Client } = pg;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

function readDatabaseUrl() {
  const envPath = path.join(ROOT, "apps", "api", ".env");
  const content = readFileSync(envPath, "utf8");
  const match = content.match(/^DATABASE_URL=(.+)$/m);
  if (!match) throw new Error("DATABASE_URL not set in apps/api/.env");
  return match[1].trim();
}

const client = new Client({ connectionString: readDatabaseUrl() });
await client.connect();

const { rows: before } = await client.query("SELECT COUNT(*) AS n FROM users");
console.log(`Users before: ${before[0].n}`);

// TRUNCATE resets sequences and cascades to datasets + analyses automatically
await client.query("TRUNCATE analyses, datasets, users, companies RESTART IDENTITY CASCADE");

const { rows: after } = await client.query("SELECT COUNT(*) AS n FROM users");
console.log(`Users after:  ${after[0].n}`);

await client.end();
