import { proxy } from "@/lib/proxy";


// GET /api/chat/:chatId -> GET /api/chat/:chatId
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ chatId: string }> }
) {
  const { chatId } = await params;
  return proxy(`/api/chat/${chatId}`);
}


// DELETE /api/chat/:chatId -> DELETE /api/chat/:chatId
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ chatId: string }> }
) {
  const { chatId } = await params;
  return proxy(`/api/chat/${chatId}`, undefined, { method: "DELETE" });
}
