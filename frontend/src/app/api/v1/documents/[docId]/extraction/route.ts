import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL;

export async function GET(
  request: NextRequest,
  context: { params: { docId: string } },
) {
  const { docId } = await context.params;
  if (!BACKEND_URL) {
    console.error("BACKEND_API_URL environment variable is not set.");
    return NextResponse.json(
      { detail: "Server configuration error." },
      { status: 500 },
    );
  }

  try {
    const targetUrl = `${BACKEND_URL}/v1/documents/${docId}/extraction`;
    const backendResponse = await fetch(targetUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text();
      let errorJson = { detail: `Backend error: ${backendResponse.status}` };
      try {
        errorJson = JSON.parse(errorData);
      } catch {
        console.warn(
          "(Proxy GET) Backend error response was not valid JSON:",
          errorData,
        );
      }
      return NextResponse.json(errorJson, { status: backendResponse.status });
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("(Proxy GET) Error in extraction API route:", error);
    let message = "Internal server error during GET proxy";
    if (error instanceof Error) {
      message = error.message;
    }
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  context: { params: { docId: string } },
) {
  const { docId } = await context.params;
  if (!BACKEND_URL) {
    console.error("BACKEND_API_URL environment variable is not set.");
    return NextResponse.json(
      { detail: "Server configuration error." },
      { status: 500 },
    );
  }

  try {
    const body = await request.json();
    const targetUrl = `${BACKEND_URL}/v1/documents/${docId}/extraction`;
    const backendResponse = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text();
      let errorJson = { detail: `Backend error: ${backendResponse.status}` };
      try {
        errorJson = JSON.parse(errorData);
      } catch {
        console.warn(
          "(Proxy POST) Backend error response was not valid JSON:",
          errorData,
        );
      }
      return NextResponse.json(errorJson, { status: backendResponse.status });
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("(Proxy POST) Error in extraction API route:", error);
    let message = "Internal server error during POST proxy";
    if (error instanceof Error) {
      message = error.message;
    }
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
