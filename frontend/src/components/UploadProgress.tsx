import React from "react";
import { Loader2, X, CheckCircle2, AlertCircle } from "lucide-react";

export type UploadStatus = "uploading" | "processing" | "completed" | "error";

export interface UploadInfo {
  id: string;
  fileName: string;
  status: UploadStatus;
  progress?: number;
  error?: string;
  phase?: string;
}

interface UploadProgressProps {
  uploads: UploadInfo[];
  onDismiss: (id: string) => void;
}

export function UploadProgress({ uploads, onDismiss }: UploadProgressProps) {
  if (uploads.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full">
      {uploads.map((upload) => (
        <div
          key={upload.id}
          className="bg-white rounded-lg shadow-lg p-4 border border-gray-200 flex items-start gap-3"
        >
          {/* Status Icon */}
          <div className="flex-shrink-0">
            {upload.status === "uploading" && (
              <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
            )}
            {upload.status === "processing" && (
              <Loader2 className="h-5 w-5 text-indigo-500 animate-spin" />
            )}
            {upload.status === "completed" && (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            )}
            {upload.status === "error" && (
              <AlertCircle className="h-5 w-5 text-red-500" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start">
              <p className="text-sm font-medium text-gray-900 truncate">
                {upload.fileName}
              </p>
              <button
                onClick={() => onDismiss(upload.id)}
                className="ml-2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="mt-1 text-sm text-gray-500">
              {upload.status === "uploading" &&
                (upload.phase === "uploading" || !upload.phase) &&
                "Uploading..."}
              {upload.phase === "parsing" && "Parsing document..."}
              {upload.phase === "extraction" && "Extracting fields..."}
              {upload.phase === "embedding" && "Generating embeddings..."}
              {upload.phase === "rag" && "Post-processing (RAG)..."}
              {upload.status === "processing" &&
                (!upload.phase || upload.phase === "processing") &&
                "Processing document..."}
              {upload.status === "completed" &&
                "Upload complete. You can now view the document."}
              {upload.status === "error" && (upload.error || "Upload failed")}
            </p>

            {(upload.status === "uploading" ||
              upload.status === "processing") && (
              <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                  style={{
                    width: `${upload.progress || 0}%`,
                  }}
                />
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
