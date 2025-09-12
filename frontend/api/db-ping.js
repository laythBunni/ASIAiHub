const { getDb } = require("./_lib/mongo.js");

module.exports = async (req, res) => {
  // --- CORS ---
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }
  if (req.method !== "GET") {
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  try {
    const db = await getDb();
    const result = await db.command({ ping: 1 });
    res.status(200).json({ ok: true, db: db.databaseName, result });
  } catch (err) {
    console.error("DB PING ERROR:", err);
    res.status(500).json({ ok: false, error: err.message });
  }
};
