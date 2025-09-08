import type { VercelRequest, VercelResponse } from "@vercel/node";
import jwt from "jsonwebtoken";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const cookie = req.headers.cookie || "";
  const match = cookie.match(/(?:^|;\s*)asi_session=([^;]+)/);
  if (!match) return res.json({ authenticated: false });
  try {
    const payload = jwt.verify(decodeURIComponent(match[1]), process.env.JWT_SECRET!);
    res.json({ authenticated: true, user: payload });
  } catch {
    res.json({ authenticated: false });
  }
}
