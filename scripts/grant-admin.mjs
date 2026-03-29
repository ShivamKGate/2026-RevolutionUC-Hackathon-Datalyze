/**
 * Set role = 'admin' for given user emails (matches API admin check).
 * Usage: node scripts/grant-admin.mjs user1@x.edu user2@y.edu
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
  if (!match) {
    throw new Error("DATABASE_URL not set in apps/api/.env");
  }
  return match[1].trim();
}

const emails = process.argv
  .slice(2)
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);
if (emails.length === 0) {
  console.error("Usage: node scripts/grant-admin.mjs <email> [email ...]");
  process.exit(1);
}

const client = new Client({ connectionString: readDatabaseUrl() });
await client.connect();

try {
  const res = await client.query(
    `UPDATE users SET role = 'admin' WHERE lower(trim(email)) = ANY($1::text[])
     RETURNING id, email, role`,
    [emails],
  );
  const updated = new Set(res.rows.map((r) => r.email.toLowerCase()));
  for (const row of res.rows) {
    console.log(`[ok] ${row.email} → role=${row.role} (id=${row.id})`);
  }
  for (const e of emails) {
    if (!updated.has(e)) {
      console.warn(`[skip] No user found for: ${e}`);
    }
  }
} finally {
  await client.end();
}
