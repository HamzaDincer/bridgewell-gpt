import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL;

export async function POST(request: NextRequest) {
  if (!BACKEND_URL) {
    return new Response("Server configuration error.", { status: 500 });
  }

  // Forward the JSON body to the backend and pipe the file response
  const backendRes = await fetch(`${BACKEND_URL}/v1/export_excel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: request.body,
    // @ts-expect-error: duplex is required for streaming body in Node.js fetch but not recognized by TypeScript
    duplex: "half",
  });

  // Pipe the file response directly
  const headers = new Headers(backendRes.headers);
  headers.set(
    "Content-Disposition",
    'attachment; filename="benefit_comparison.xlsx"',
  );

  return new Response(backendRes.body, {
    status: backendRes.status,
    headers,
  });
}
