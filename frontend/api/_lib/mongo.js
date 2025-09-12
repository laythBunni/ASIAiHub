const { MongoClient } = require("mongodb");

let client, connecting;

/**
 * Lazily reads envs each call and returns a pooled DB.
 * Throws with a clear message if envs are missing.
 */
async function getDb() {
  const uri = process.env.MONGODB_URI;
  const dbName = process.env.MONGODB_DB || "asi_ai_hub";

  if (!uri) throw new Error("MONGODB_URI is not set");
  if (!dbName) throw new Error("MONGODB_DB is not set");

  if (!client) {
    if (!connecting) {
      connecting = new MongoClient(uri, { maxPoolSize: 10 }).connect();
    }
    client = await connecting;
  }
  return client.db(dbName);
}

module.exports = { getDb };
