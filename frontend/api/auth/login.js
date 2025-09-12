const { getDb } = require("../_lib/mongo.js");
const jwt = require("jsonwebtoken");

module.exports = async (req, res) => {
  // --- CORS ---
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  try {
    // Parse JSON body in Vercel Node: req.body may be a string
    const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {});
    const { email, code } = body;

    if (!email || !code) {
      return res.status(400).json({ ok: false, error: "Missing email or code" });
    }

    const db = await getDb();
    const users = db.collection("beta_users");
    const user = await users.findOne({ email, code });

    if (!user) {
      return res.status(401).json({ ok: false, error: "Invalid credentials" });
    }

    const token = jwt.sign(
      { userId: String(user._id), email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: "1d" }
    );

    res.status(200).json({ ok: true, token });
  } catch (err) {
    console.error("LOGIN ERROR:", err);
    res.status(500).json({ ok: false, error: "Internal server error" });
  }
};
