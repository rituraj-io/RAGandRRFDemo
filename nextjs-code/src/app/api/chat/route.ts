import { NextRequest } from "next/server";
import { proxy } from "@/lib/proxy";


// GET /api/chat -> GET /api/chat
export async function GET() {
  return proxy("/api/chat");
}


// POST /api/chat -> POST /api/chat
export async function POST(request: NextRequest) {
  return proxy("/api/chat", request);
}
