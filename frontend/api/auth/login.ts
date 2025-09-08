// api/auth/login.ts
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { getDb } from "../_lib/mongo";
import jwt from "jsonwebtoken";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") return res.status(405).end();

  const { email, personalCode, verificationCode, code, personal_code } = req.body || {};
  const clean = String(email || "").trim().toLowerCase();
  const provided = String(personalCode ?? verificationCode ?? code ?? personal_code ?? "");

  if (!clean || !provided) return res.status(400).json({ error: "missing_params" });

  const db = await getDb();
  const lc = await db.collection("loginCodes").findOne({
    email: clean,
    code: provided,
    usedAt: null,
    expiresAt: { $gt: new Date() }
  });
  if (!lc) return res.status(401).json({ error: "invalid_code" });

  await db.collection("loginCodes").updateOne({ _id: lc._id }, { $set: { usedAt: new Date() } });

  const user = await db.collection("users").findOne({ email: clean, active: { $ne: false } });
  if (!user) return res.status(403).json({ error: "no_user" });

  const token = jwt.sign(
    { sub: String(user._id), email: user.email, role: user.role || "user" },
    process.env.JWT_SECRET!,
    { expiresIn: "7d" }
  );

  // Set cookie so server can read it if needed
  res.setHeader(
    "Set-Cookie",
    `asi_session=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${60 * 60 * 24 * 7}`
  );

  // Return the shape your frontend expects
  res.json({
    access_token: token,
    user: {
      _id: String(user._id),
      email: user.email,
      role: user.role || "user",
      name: user.name || (user.email?.split("@")[0]?.split(".")?.map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(" ") || "")
    }
  });
}
