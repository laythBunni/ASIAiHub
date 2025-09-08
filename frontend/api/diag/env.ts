import type { VercelRequest, VercelResponse } from "@vercel/node";

export default function handler(_req: VercelRequest, res: VercelResponse) {
  // Do not log secret values. Just booleans.
  res.json({
    ok: true,
    keysVisible: Object.keys(process.env).filter(k =>
      ["MONGODB_URI","MONGODB_DB","JWT_SECRET"].includes(k)
    ),
    MONGODB_URI: !!process.env.MONGODB_URI,
    MONGODB_DB: !!process.env.MONGODB_DB,
    JWT_SECRET: !!process.env.JWT_SECRET,
    NODE_ENV: process.env.NODE_ENV,
  });
}
