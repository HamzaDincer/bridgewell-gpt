/* eslint-disable @typescript-eslint/no-explicit-any */
import { NextRequest, NextResponse } from "next/server";

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ docId: string }> },
) {
  const body = await req.json();
  const { docId } = await context.params;

  // Ensure context_filter includes the docId
  const newBody = {
    ...body,
    context_filter: {
      ...(body.context_filter || {}),
      docs_ids: [docId],
    },
  };

  const backendRes = await fetch(
    `${
      process.env.BACKEND_API_URL || "http://localhost:8001"
    }/v1/chat/completions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(newBody),
    },
  );
  const contentType = backendRes.headers.get("content-type");
  let data;
  if (contentType && contentType.includes("application/json")) {
    data = await backendRes.json();
  } else {
    data = { error: await backendRes.text() };
  }
  return NextResponse.json(data, { status: backendRes.status });
}
