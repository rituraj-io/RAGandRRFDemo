import { proxy } from "@/lib/proxy";


// GET /api/chat/status -> GET /api/chat/status
export async function GET() {
  return proxy("/api/chat/status");
}
