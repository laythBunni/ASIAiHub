import type { VercelRequest, VercelResponse } from "@vercel/node";
import { openai, MODEL } from "../_lib/openai";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") return res.status(405).end();
  const { messages } = req.body || {};
  if (!messages) return res.status(400).json({ error: "missing_messages" });
  const completion = await openai.chat.completions.create({ model: MODEL, messages });
  res.json(completion);
}
