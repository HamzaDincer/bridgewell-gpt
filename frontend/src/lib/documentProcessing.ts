interface ProcessingResponse {
  fileId: string;
  status: string;
  message: string;
  error?: {
    detail: string;
    [key: string]: unknown;
  };
  data?: Record<string, unknown>;
}

export class DocumentProcessingError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: ProcessingResponse,
  ) {
    super(message);
    this.name = "DocumentProcessingError";
  }
}

export async function uploadDocument(file: File): Promise<ProcessingResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/v1/ingest/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new DocumentProcessingError(
      "Failed to upload document",
      response.status,
      await response.json(),
    );
  }

  return response.json();
}

export async function parseDocument(
  fileId: string,
): Promise<ProcessingResponse> {
  const response = await fetch(`/api/v1/ingest/parse/${fileId}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new DocumentProcessingError(
      "Failed to parse document",
      response.status,
      await response.json(),
    );
  }

  return response.json();
}

export async function extractDocument(
  fileId: string,
  documentTypeId: string,
): Promise<ProcessingResponse> {
  const response = await fetch(`/api/v1/ingest/extract/${fileId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_type_id: documentTypeId }),
  });

  if (!response.ok) {
    throw new DocumentProcessingError(
      "Failed to extract document",
      response.status,
      await response.json(),
    );
  }

  return response.json();
}

export async function generateEmbeddings(
  fileId: string,
): Promise<ProcessingResponse> {
  const response = await fetch(`/api/v1/ingest/embed/${fileId}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new DocumentProcessingError(
      "Failed to generate embeddings",
      response.status,
      await response.json(),
    );
  }

  return response.json();
}

export async function deleteDocumentCompletely(
  docId: string,
): Promise<import("../types").DocumentDeletionResponse> {
  const response = await fetch(`/api/v1/documents/${docId}/delete`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new DocumentProcessingError(
      "Failed to delete document",
      response.status,
      await response.json(),
    );
  }

  return response.json();
}

export async function getProcessingStatus(
  fileId: string,
): Promise<ProcessingResponse> {
  const response = await fetch(`/api/v1/ingest/status/${fileId}`);

  if (!response.ok) {
    throw new DocumentProcessingError(
      "Failed to get processing status",
      response.status,
      await response.json(),
    );
  }

  return response.json();
}

export async function processDocument(
  file: File,
  documentTypeId: string,
  onProgress?: (status: string, message: string) => void,
): Promise<ProcessingResponse> {
  try {
    // Step 1: Upload
    onProgress?.("uploading", "Uploading document...");
    const uploadResponse = await uploadDocument(file);
    const { fileId } = uploadResponse;

    // Start processing pipeline
    onProgress?.("processing", "Starting document processing...");

    // Step 2: Parse
    await parseDocument(fileId);

    // Step 3: Extract
    await extractDocument(fileId, documentTypeId);

    // Step 4: Generate embeddings
    await generateEmbeddings(fileId);

    // Poll for completion
    let isComplete = false;
    while (!isComplete) {
      const status = await getProcessingStatus(fileId);
      onProgress?.(status.status, status.message);

      if (status.status === "completed") {
        isComplete = true;
      } else if (status.status === "error") {
        throw new DocumentProcessingError(status.message, 500, status);
      } else {
        // Wait before next poll
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }

    onProgress?.("completed", "Document processing completed successfully");
    return await getProcessingStatus(fileId);
  } catch (error) {
    if (error instanceof DocumentProcessingError) {
      onProgress?.("error", error.message);
      throw error;
    }
    onProgress?.("error", "An unexpected error occurred");
    throw new DocumentProcessingError(
      "An unexpected error occurred during document processing",
      500,
    );
  }
}
