import { NextResponse } from "next/server";
import { resolveGraphNode } from "@/lib/queries";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { cpfCnpj?: unknown } | null;
  const cpfCnpj = typeof body?.cpfCnpj === "string" ? body.cpfCnpj : "";
  const node = resolveGraphNode(cpfCnpj);
  return NextResponse.json({ node });
}
