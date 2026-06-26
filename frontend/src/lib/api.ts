// 后端交互封装。业务路由在 /api 前缀下。
export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000") + "/api";

export const LANGFUSE_URL =
  process.env.NEXT_PUBLIC_LANGFUSE_URL || "http://localhost:3001";

export interface Citation {
  n: number;
  chunk_id: number;
  document_id: number;
  document_title: string;
  content: string;
  link?: string | null;
}

export interface Persona {
  id: number;
  name: string;
  description?: string;
  system_prompt: string;
  tools: string[];
}

export interface DocumentItem {
  id: number;
  title: string;
  source: string;
  link?: string;
  num_chunks: number;
  created_at: string;
}

export interface IndexAttempt {
  id: number;
  connector_id: number;
  status: string;
  num_docs: number;
  num_chunks: number;
  error?: string;
  created_at: string;
}

export interface ChatSession {
  id: number;
  persona_id?: number;
  title?: string;
}

export interface NodeStep {
  node: string;
  label: string;
}

export interface ToolStep {
  name: string;
  args: Record<string, unknown>;
  output: string;
}

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const listPersonas = () => getJSON<Persona[]>("/admin/personas");
export const listDocuments = () => getJSON<DocumentItem[]>("/knowledge/documents");
export const listAttempts = () => getJSON<IndexAttempt[]>("/knowledge/index-attempts");
export const listSessions = () => getJSON<ChatSession[]>("/chat-sessions");
export const getStatus = () => getJSON<any>("/admin/status");
export const listTraces = () => getJSON<any[]>("/admin/traces");

export async function createPersona(body: {
  name: string;
  description?: string;
  system_prompt: string;
  tools: string[];
}): Promise<Persona> {
  const r = await fetch(`${API_BASE}/admin/personas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json();
}

export async function uploadFiles(files: FileList): Promise<IndexAttempt> {
  const fd = new FormData();
  Array.from(files).forEach((f) => fd.append("files", f));
  const r = await fetch(`${API_BASE}/knowledge/upload`, { method: "POST", body: fd });
  return r.json();
}

export async function indexWeb(url: string): Promise<IndexAttempt> {
  const r = await fetch(`${API_BASE}/knowledge/web`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return r.json();
}

// 聊天 SSE: meta / node / tool / citations / token / clarification / done
export async function chatStream(
  body: { message: string; session_id?: number; persona_id?: number },
  handlers: {
    onMeta?: (sessionId: number) => void;
    onNode?: (step: NodeStep) => void;
    onTool?: (step: ToolStep) => void;
    onCitations?: (citations: Citation[]) => void;
    onToken?: (t: string) => void;
    onClarification?: (text: string) => void;
    onDone?: () => void;
  }
): Promise<void> {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.body) throw new Error("无响应流");
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const evt of events) {
      let type = "message";
      const dataLines: string[] = [];
      for (const line of evt.split("\n")) {
        if (line.startsWith("event:")) type = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
      }
      const data = dataLines.join("\n");
      if (type === "meta") handlers.onMeta?.(JSON.parse(data).session_id);
      else if (type === "node") handlers.onNode?.(JSON.parse(data));
      else if (type === "tool") handlers.onTool?.(JSON.parse(data));
      else if (type === "citations") handlers.onCitations?.(JSON.parse(data));
      else if (type === "token") handlers.onToken?.(data);
      else if (type === "clarification") handlers.onClarification?.(JSON.parse(data).text);
      else if (type === "done") handlers.onDone?.();
    }
  }
}
