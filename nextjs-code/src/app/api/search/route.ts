import { NextRequest } from "next/server";
import { proxy } from "@/lib/proxy";


// GET /api/search?q=...&mode=...&limit=... -> GET /api/search?q=...&mode=...&limit=...
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString();
  return proxy(`/api/search?${searchParams}`);
}
