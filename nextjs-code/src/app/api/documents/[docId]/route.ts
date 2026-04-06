import { proxy } from "@/lib/proxy";


// DELETE /api/documents/:docId -> DELETE /api/documents/:docId
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ docId: string }> }
) {
  const { docId } = await params;
  return proxy(`/api/documents/${docId}`, undefined, { method: "DELETE" });
}
