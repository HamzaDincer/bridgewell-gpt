import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL;

export async function POST(request: NextRequest) {
  if (!BACKEND_URL) {
    console.error("BACKEND_API_URL environment variable is not set.");
    return NextResponse.json(
      { detail: "Server configuration error." },
      { status: 500 },
    );
  }

  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!file) {
      return NextResponse.json(
        { detail: "No file found in request" },
        { status: 400 },
      );
    }

    // Construct the target backend URL
    const targetUrl = `${BACKEND_URL}/v1/ingest/file`;

    console.log(`Proxying file upload to: ${targetUrl}`);

    // Forward the FormData to the backend
    // Note: We don't manually set Content-Type header when sending FormData,
    // the browser/fetch API handles the multipart boundary correctly.
    const backendResponse = await fetch(targetUrl, {
      method: "POST",
      body: formData,
      // Optionally forward specific headers if needed, e.g., Authorization
      // headers: {
      //   'Authorization': request.headers.get('Authorization') || '',
      // },
      // Duplex must be set for streaming request bodies in Node >= 18
      // Use @ts-expect-error as recommended by linter
      // @ts-expect-error Property 'duplex' does not exist on type 'RequestInit<NextJsRequestInit>'.
      duplex: "half",
    });

    // Check if the backend response is okay
    if (!backendResponse.ok) {
      // Forward the backend error response
      const errorData = await backendResponse.text(); // Read as text first
      let errorJson = { detail: `Backend error: ${backendResponse.status}` };
      try {
        errorJson = JSON.parse(errorData); // Try parsing as JSON
      } catch {
        // Remove unused 'e' variable
        console.warn("Backend error response was not valid JSON:", errorData);
      }
      return NextResponse.json(errorJson, { status: backendResponse.status });
    }

    // Forward the successful backend response
    const successData = await backendResponse.json();
    return NextResponse.json(successData, { status: backendResponse.status });
  } catch (error) {
    console.error("Error in API proxy route:", error);
    let message = "Internal server error";
    if (error instanceof Error) {
      message = error.message;
    }
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
