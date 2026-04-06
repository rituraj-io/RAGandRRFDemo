import { NextRequest } from "next/server";
import { proxy } from "@/lib/proxy";


// POST /api/chat/:chatId/message -> POST /api/chat/:chatId/message
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ chatId: string }> }
) {
  const { chatId } = await params;
  return proxy(`/api/chat/${chatId}/message`, request);
}
