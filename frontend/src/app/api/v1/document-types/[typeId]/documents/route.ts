import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL;

type RouteContext = {
  params: {
    typeId: string;
  };
};

export async function GET(request: NextRequest, { params }: RouteContext) {
  const { typeId } = params;
  if (!BACKEND_URL) {
    console.error("BACKEND_API_URL environment variable is not set.");
    return NextResponse.json(
      { detail: "Server configuration error." },
      { status: 500 },
    );
  }

  try {
    const targetUrl = `${BACKEND_URL}/v1/document-types/${typeId}/documents`;
    console.log(`(Proxy GET) Forwarding to: ${targetUrl}`);

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
    console.error("(Proxy GET) Error in API proxy route:", error);
    let message = "Internal server error during GET proxy";
    if (error instanceof Error) {
      message = error.message;
    }
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest, { params }: RouteContext) {
  if (!BACKEND_URL) {
    console.error("BACKEND_API_URL environment variable is not set.");
    return NextResponse.json(
      { detail: "Server configuration error." },
      { status: 500 },
    );
  }

  try {
    const targetUrl = `${BACKEND_URL}/v1/document-types/${params.typeId}/documents`;
    const requestBody = await request.json();
    console.log(
      `(Proxy POST) Forwarding to: ${targetUrl} with body:`,
      requestBody,
    );

    const backendResponse = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    const responseBodyText = await backendResponse.text();
    let responseBodyJson = {};
    try {
      responseBodyJson = JSON.parse(responseBodyText);
    } catch {
      console.warn(
        "(Proxy POST) Backend response was not valid JSON or empty:",
        responseBodyText,
      );
      if (!backendResponse.ok && !responseBodyText) {
        responseBodyJson = {
          detail: `Backend error: ${backendResponse.status}`,
        };
      } else if (!backendResponse.ok) {
        responseBodyJson = { detail: responseBodyText };
      }
    }

    console.log(
      `(Proxy POST) Backend response status: ${backendResponse.status}, body:`,
      responseBodyJson,
    );

    return NextResponse.json(responseBodyJson, {
      status: backendResponse.status,
    });
  } catch (error) {
    console.error("(Proxy POST) Error in API proxy route:", error);
    let message = "Internal server error during POST proxy";
    if (error instanceof Error) {
      message = error.message;
    }
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
