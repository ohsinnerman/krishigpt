import type { ChatResponse, RegionInfo } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChat(params: {
  message: string;
  language: string;
  pincode?: string;
  sessionId?: string;
}): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: params.message,
      language: params.language,
      pincode: params.pincode,
      session_id: params.sessionId,
    }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function resolvePin(pincode: string): Promise<RegionInfo | null> {
  try {
    const res = await fetch(`${API_URL}/pincode/${pincode}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
