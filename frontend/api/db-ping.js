const { getDb } = require("./_lib/mongo.js");

module.exports = async (req, res) => {
  // CORS (ok for local testing)
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") return res.status(405).json({ ok: false, error: "Method not allowed" });

  try {
    const db = await getDb();

    // Use db.command for a lightweight ping
    const result = await db.command({ ping: 1 });

    // Try to show which host you’re connecting to (for sanity)
    let host = "unknown";
    try { host = new URL(process.env.MONGODB_URI).hostname || "unknown"; } catch {}

    res.status(200).json({ ok: true, db: db.databaseName, host, result });
  } catch (err) {
    console.error("DB PING ERROR:", err);
    res.status(500).json({
      ok: false,
      error: err.name || "Error",
      message: err.message || String(err)
    });
  }
};
