import { NextRequest } from "next/server";
import { proxy } from "@/lib/proxy";


// GET /api/documents -> GET /api/documents
export async function GET() {
  return proxy("/api/documents");
}


// POST /api/documents -> POST /api/documents
export async function POST(request: NextRequest) {
  return proxy("/api/documents", request);
}
