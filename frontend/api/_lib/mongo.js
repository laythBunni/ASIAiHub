// /api/_lib/mongo.js
import { MongoClient } from "mongodb";

const uri = process.env.MONGODB_URI;
if (!uri) throw new Error("❌ Missing MONGODB_URI environment variable");

let client;
let clientPromise;

if (process.env.NODE_ENV === "development") {
  // Reuse client across hot reloads in dev
  if (!global._mongoClientPromise) {
    client = new MongoClient(uri, { maxPoolSize: 10 });
    global._mongoClientPromise = client.connect();
  }
  clientPromise = global._mongoClientPromise;
} else {
  // On Vercel: new client per Lambda, but pooled internally
  client = new MongoClient(uri, { maxPoolSize: 10 });
  clientPromise = client.connect();
}

export async function getDb() {
  const conn = await clientPromise;
  const dbName = process.env.MONGODB_DB || "asi_ai_hub";
  return conn.db(dbName);
}
