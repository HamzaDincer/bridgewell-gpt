import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL;
// Set a longer timeout for large file processing (10 minutes)
const UPLOAD_TIMEOUT = 10 * 60 * 1000;

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

    // Create an AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT);

    try {
      // Forward the FormData to the backend with timeout handling
      const backendResponse = await fetch(targetUrl, {
        method: "POST",
        body: formData,
        signal: controller.signal,
        // Duplex must be set for streaming request bodies in Node >= 18
        // @ts-expect-error Property 'duplex' does not exist on type 'RequestInit<NextJsRequestInit>'.
        duplex: "half",
      });

      clearTimeout(timeoutId);

      // Check if the backend response is okay
      if (!backendResponse.ok) {
        // Forward the backend error response
        const errorData = await backendResponse.text(); // Read as text first
        let errorJson = { detail: `Backend error: ${backendResponse.status}` };
        try {
          errorJson = JSON.parse(errorData); // Try parsing as JSON
        } catch {
          console.warn("Backend error response was not valid JSON:", errorData);
        }
        return NextResponse.json(errorJson, { status: backendResponse.status });
      }

      // Forward the successful backend response
      const successData = await backendResponse.json();
      return NextResponse.json(successData, { status: backendResponse.status });
    } catch (fetchError) {
      clearTimeout(timeoutId);
      if (fetchError instanceof Error) {
        if (fetchError.name === "AbortError") {
          return NextResponse.json(
            {
              detail:
                "Request timed out. The file might be too large or the server is busy.",
            },
            { status: 504 },
          );
        }
        throw fetchError; // Re-throw other errors to be handled by outer catch
      }
      throw fetchError;
    }
  } catch (error) {
    console.error("Error in API proxy route:", error);
    let message = "Internal server error";
    if (error instanceof Error) {
      message = error.message;
    }
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
