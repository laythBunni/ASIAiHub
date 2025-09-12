module.exports = (req, res) => {
  // DO NOT print actual secrets; just show if they're present
  const keys = ["MONGODB_URI", "MONGODB_DB", "JWT_SECRET", "OPENAI_API_KEY", "OPENAI_MODEL"];
  const status = {};
  for (const k of keys) status[k] = process.env[k] ? "set" : "missing";
  res.status(200).json({ ok: true, env: status });
};
