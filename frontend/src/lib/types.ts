export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDoc[];
  region?: string | null;
  language: string;
  latency_ms?: number;
  cache_hit?: boolean;
  timestamp: Date;
}

export interface SourceDoc {
  title: string;
  state: string;
  topic: string;
  score: number;
}

export interface Language {
  code: string;
  name: string;
  native: string;
}

export interface RegionInfo {
  pincode: string;
  district: string;
  state: string;
  agro_zone: string;
}

export interface ChatResponse {
  response: string;
  sources: SourceDoc[];
  region: string | null;
  language: string;
  latency_ms: number;
  cache_hit: boolean;
}
