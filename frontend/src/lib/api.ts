// 与后端交互的薄封装。NEXT_PUBLIC_API_BASE 指向 FastAPI。
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface Citation {
  n: number;
  chunk_id: number;
  document_id: number;
  document_title: string;
  content: string;
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

export async function listPersonas(): Promise<Persona[]> {
  const r = await fetch(`${API_BASE}/personas`, { cache: "no-store" });
  return r.json();
}

export async function createPersona(body: {
  name: string;
  description?: string;
  system_prompt: string;
  tools: string[];
}): Promise<Persona> {
  const r = await fetch(`${API_BASE}/personas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json();
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const r = await fetch(`${API_BASE}/documents`, { cache: "no-store" });
  return r.json();
}

export async function listAttempts(): Promise<IndexAttempt[]> {
  const r = await fetch(`${API_BASE}/connectors/attempts`, { cache: "no-store" });
  return r.json();
}

export async function uploadFiles(files: FileList): Promise<IndexAttempt> {
  const fd = new FormData();
  Array.from(files).forEach((f) => fd.append("files", f));
  const r = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: fd,
  });
  return r.json();
}

export async function indexWeb(url: string): Promise<IndexAttempt> {
  const r = await fetch(`${API_BASE}/connectors/web`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return r.json();
}

// Agent 模式 (非流式)
export async function chatAgent(body: {
  message: string;
  session_id?: number;
  persona_id?: number;
}): Promise<{
  session_id: number;
  content: string;
  citations: Citation[];
  steps: string[];
}> {
  const r = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, use_agent: true }),
  });
  return r.json();
}

// 普通 RAG 模式 (SSE 流式)。通过 fetch + ReadableStream 手动解析 SSE。
export async function chatStream(
  body: { message: string; session_id?: number; persona_id?: number },
  handlers: {
    onMeta: (sessionId: number, citations: Citation[]) => void;
    onToken: (t: string) => void;
    onDone: () => void;
  }
): Promise<void> {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, use_agent: false }),
  });
  if (!resp.body) throw new Error("无响应流");

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 事件以空行分隔
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const evt of events) {
      let eventType = "message";
      const dataLines: string[] = [];
      for (const line of evt.split("\n")) {
        if (line.startsWith("event:")) eventType = line.slice(6).trim();
        // 按 SSE 规范只去掉 "data:" 后的一个前导空格，保留 token 内的空格
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
      }
      const data = dataLines.join("\n");
      if (eventType === "meta") {
        const parsed = JSON.parse(data);
        handlers.onMeta(parsed.session_id, parsed.citations || []);
      } else if (eventType === "token") {
        handlers.onToken(data);
      } else if (eventType === "done") {
        handlers.onDone();
      }
    }
  }
}
