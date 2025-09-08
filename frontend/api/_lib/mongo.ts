import { MongoClient, ServerApiVersion, Db } from "mongodb";

const uri = process.env.MONGODB_URI;
if (!uri) {
  throw new Error(
    "❌ MONGODB_URI is not set. Add it in Vercel → Settings → Environment Variables (Preview)."
  );
}

let client: MongoClient | null = null;
let db: Db | null = null;

/**
 * Get a cached MongoDB Db instance.
 * Uses the recommended Atlas connection settings (Stable API v1).
 */
export async function getDb(): Promise<Db> {
  if (db) return db;

  if (!client) {
    client = new MongoClient(uri, {
      serverApi: {
        version: ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
      },
    });
    await client.connect();
  }

  db = client.db(process.env.MONGODB_DB || "asi_aihub_production");
  return db;
}
