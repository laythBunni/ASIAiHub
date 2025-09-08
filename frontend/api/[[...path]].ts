// api/[[...path]].ts
import type { VercelRequest, VercelResponse } from "@vercel/node";

// Point to Emergent for everything except /auth/**
const TARGET = process.env.TARGET_API || "https://ai-workspace-17.emergent.host/api";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const path = req.query.path ? (Array.isArray(req.query.path) ? req.query.path.join("/") : req.query.path) : "";

  // Let our own auth routes handle themselves
  if (path.startsWith("auth/")) {
    return res.status(404).json({ error: "Not found" });
  }

  const url = `${TARGET}/${path}${req.url?.includes("?") ? req.url?.split("?")[1] && "?" + req.url.split("?")[1] : ""}`;

  const headers = new Headers();
  // forward headers except host & content-length
  for (const [k, v] of Object.entries(req.headers)) {
    if (!v) continue;
    const key = k.toLowerCase();
    if (["host", "content-length"].includes(key)) continue;
    headers.set(key, Array.isArray(v) ? v.join(",") : (v as string));
  }

  const init: RequestInit = {
    method: req.method,
    headers,
    body: req.method && req.method !== "GET" && req.method !== "HEAD" ? (req as any).rawBody || JSON.stringify(req.body) : undefined,
    redirect: "manual",
  };

  try {
    const upstream = await fetch(url, init);
    const body = Buffer.from(await upstream.arrayBuffer());
    res.status(upstream.status);

    upstream.headers.forEach((val, key) => {
      if (!["content-encoding", "transfer-encoding", "connection"].includes(key.toLowerCase())) {
        res.setHeader(key, val);
      }
    });

    res.send(body);
  } catch (e: any) {
    res.status(502).json({ error: "proxy_failed", detail: e?.message || String(e) });
  }
}
