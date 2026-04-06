import { proxy } from "@/lib/proxy";


// GET /api/health -> GET /health
export async function GET() {
  return proxy("/health");
}
