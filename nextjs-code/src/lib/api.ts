/**
 * API client for the Next.js proxy layer.
 * All calls go to /api/* which proxies to the Python backend.
 */


/* -- Types -- */

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  score: number;
  metadata: Record<string, string>;
}

export interface IngestResponse {
  doc_id: string;
  chunks: number;
}

export interface ChatCreateResponse {
  chat_id: string;
}

export interface ChatMessageResponse {
  response: string;
  sources: SearchResult[];
}


/* -- Documents -- */

export async function ingestDocument(title: string, content: string): Promise<IngestResponse> {
  const res = await fetch("/api/documents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content }),
  });

  if (!res.ok) throw new Error(`Ingestion failed: ${res.status}`);
  return res.json();
}


export async function deleteDocument(docId: string): Promise<void> {
  await fetch(`/api/documents/${docId}`, { method: "DELETE" });
}


/* -- Search -- */

export async function searchDocuments(
  query: string,
  mode: "vector" | "bm25" | "hybrid",
  limit: number,
  scope: { doc_id: string } | { source: string }
): Promise<SearchResult[]> {
  const params = new URLSearchParams({
    q: query,
    mode,
    limit: String(limit),
  });

  if ("doc_id" in scope) params.set("doc_id", scope.doc_id);
  else params.set("source", scope.source);

  const res = await fetch(`/api/search?${params}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);

  const data = await res.json();
  return data.results;
}


/* -- Chat -- */

export async function checkChatStatus(): Promise<boolean> {
  const res = await fetch("/api/chat/status");
  if (!res.ok) return false;

  const data = await res.json();
  return data.enabled;
}


export async function createChat(
  scope: { doc_id: string } | { source: string }
): Promise<string> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scope),
  });

  if (!res.ok) throw new Error(`Chat creation failed: ${res.status}`);
  const data: ChatCreateResponse = await res.json();
  return data.chat_id;
}


export async function sendChatMessage(
  chatId: string,
  message: string
): Promise<ChatMessageResponse> {
  const res = await fetch(`/api/chat/${chatId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) throw new Error(`Message failed: ${res.status}`);
  return res.json();
}


export async function deleteChat(chatId: string): Promise<void> {
  await fetch(`/api/chat/${chatId}`, { method: "DELETE" });
}
