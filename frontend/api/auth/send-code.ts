import type { VercelRequest, VercelResponse } from "@vercel/node";
import { getDb } from "../_lib/mongo";
import nodemailer from "nodemailer";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") return res.status(405).end();
  const { email } = req.body || {};
  const clean = String(email || "").trim().toLowerCase();
  if (!clean) return res.status(400).json({ error: "missing_email" });

  const code = (Math.floor(100000 + Math.random()*900000)).toString();
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 10*60*1000);

  const db = await getDb();
  await db.collection("users").updateOne(
    { email: clean },
    { $setOnInsert: { email: clean, active: true, role: "admin", createdAt: now } },
    { upsert: true }
  );
  await db.collection("loginCodes").insertOne({ email: clean, code, createdAt: now, expiresAt, usedAt: null });

  const t = nodemailer.createTransport({
    host: process.env.SMTP_HOST!, port: Number(process.env.SMTP_PORT || 587),
    auth: { user: process.env.SMTP_USER!, pass: process.env.SMTP_PASS! }
  });
  await t.sendMail({ from: process.env.SMTP_FROM!, to: clean, subject: "Your login code", text: `Code: ${code} (valid 10 min)` });

  res.json({ ok: true });
}
