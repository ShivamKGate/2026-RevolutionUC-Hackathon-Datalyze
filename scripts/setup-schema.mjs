/**
 * Connects to PostgreSQL, applies the schema (idempotent), and seeds data
 * only if the users table is empty. Called automatically by run-api.mjs.
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

async function setupSchema() {
  const databaseUrl = readDatabaseUrl();

  // Log host/db only — never log the password
  const parsed = new URL(databaseUrl);
  const hostInfo = `${parsed.hostname}:${parsed.port || 5432}${parsed.pathname}`;

  const client = new Client({ connectionString: databaseUrl });

  try {
    process.stdout.write("[db] Connecting to PostgreSQL... ");
    await client.connect();
    console.log(`OK  (${hostInfo})`);

    // Schema uses CREATE TABLE IF NOT EXISTS — always safe to re-run
    const schemaSQL = readFileSync(
      path.join(
        ROOT,
        "apps",
        "api",
        "src",
        "db",
        "migrations",
        "001_initial_schema.sql",
      ),
      "utf8",
    );
    await client.query(schemaSQL);
    console.log("[db] Schema applied");

    // Only seed if the users table is empty
    const { rows } = await client.query(
      "SELECT COUNT(*) AS n FROM users",
    );
    const userCount = parseInt(rows[0].n, 10);

    if (userCount > 0) {
      console.log(
        `[db] Seed data already present (${userCount} users) — skipping`,
      );
      return;
    }

    const seedSQL = readFileSync(
      path.join(
        ROOT,
        "apps",
        "api",
        "src",
        "db",
        "seeds",
        "001_seed.sql",
      ),
      "utf8",
    );
    await client.query(seedSQL);
    console.log("[db] Seed data inserted");
  } catch (err) {
    console.error("[db] Setup FAILED:", err.message);
    process.exit(1);
  } finally {
    await client.end();
  }
}

await setupSchema();
