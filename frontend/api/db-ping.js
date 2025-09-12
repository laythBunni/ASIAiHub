import { getDb } from "./_lib/mongo.js";

export default async function handler(req, res) {
  try {
    const db = await getDb();
    const result = await db.command({ ping: 1 });
    res.status(200).json({ ok: true, db: db.databaseName, result });
  } catch (err) {
    console.error("DB PING ERROR:", err);
    res.status(500).json({ ok: false, error: err.message });
  }
}
