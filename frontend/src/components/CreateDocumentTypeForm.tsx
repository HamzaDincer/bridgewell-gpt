"use client";

import { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  UploadCloud,
  ChevronLeft,
  Link as LinkIcon,
  ChevronDown,
  File as FileIcon,
  X,
  Loader2,
} from "lucide-react";
import { useDropzone, FileRejection } from "react-dropzone";
import { cn } from "@/lib/utils";
import { useUpload } from "@/contexts/UploadContext";

import type { CreateDocumentTypeFormProps, DocumentType } from "@/types";

export function CreateDocumentTypeForm({
  initialDocumentTypeName,
  documentTypes,
  setDocumentTypes,
  ...props
}: CreateDocumentTypeFormProps & {
  documentTypes: DocumentType[];
  setDocumentTypes: (types: DocumentType[]) => void;
}) {
  const [documentTypeName, setDocumentTypeName] = useState(
    initialDocumentTypeName || "",
  );
  const [acceptedFile, setAcceptedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addUpload, updateUpload } = useUpload();

  // Add a fallback for documentTypes
  const safeDocumentTypes = documentTypes ?? [];

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      setError(null);
      setAcceptedFile(null);
      if (acceptedFiles.length > 0) {
        console.log("Accepted file:", acceptedFiles[0]);
        setAcceptedFile(acceptedFiles[0]);
      }
      if (fileRejections.length > 0) {
        console.error("Rejected file:", fileRejections[0]);
        setError(`File rejected: ${fileRejections[0].errors[0].message}`);
      }
    },
    [],
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isFocused,
    isDragAccept,
    isDragReject,
  } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/jpeg": [".jpeg", ".jpg"],
      "image/png": [".png"],
      "image/tiff": [".tif", ".tiff"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
    },
    maxSize: 75 * 1024 * 1024,
    maxFiles: 1,
  });

  const handleRemoveFile = () => {
    setAcceptedFile(null);
    setError(null);
  };

  const handleCreateClick = async () => {
    if (!acceptedFile || !documentTypeName.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add upload to global state for progress bar
    const uploadId = addUpload({
      fileName: acceptedFile.name,
      status: "uploading",
      progress: 0,
      phase: "uploading",
    });

    // Check if document type already exists
    const existingType = safeDocumentTypes.find(
      (t) => t.title.toLowerCase() === documentTypeName.trim().toLowerCase(),
    );
    let typeId = existingType ? existingType.id : null;

    try {
      if (!typeId) {
        // Create document type if it doesn't exist
        const response = await fetch("/api/v1/document-types", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: documentTypeName.trim() }),
        });
        if (!response.ok) throw new Error("Failed to create document type");
        const result = await response.json();
        typeId = result.id;
      }

      // Step 1: Upload the document file
      const formData = new FormData();
      formData.append("file", acceptedFile);
      const uploadResponse = await fetch("/api/v1/ingest/file", {
        method: "POST",
        body: formData,
      });
      if (!uploadResponse.ok) throw new Error("Failed to upload document");
      updateUpload(uploadId, {
        status: "processing",
        phase: "processing",
        progress: 50,
      });
      const uploadResult = await uploadResponse.json();
      const docId = Array.isArray(uploadResult.doc_ids)
        ? uploadResult.doc_ids[0]
        : undefined;
      if (!docId) throw new Error("No document ID returned from upload");

      // Step 2: Associate the uploaded document with the document type
      const associateResponse = await fetch(
        `/api/v1/document-types/${typeId}/documents`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doc_id: docId, doc_name: acceptedFile.name }),
        },
      );
      if (!associateResponse.ok)
        throw new Error("Failed to associate document with type");

      updateUpload(uploadId, {
        status: "completed",
        phase: "completed",
        progress: 100,
      });

      // After upload, always re-fetch document types from backend
      const typesResponse = await fetch("/api/v1/document-types");
      if (typesResponse.ok) {
        const types = await typesResponse.json();
        setDocumentTypes(types);
      }

      // Notify parent of success so it can navigate to the document list
      if (props.onCreate) {
        props.onCreate(documentTypeName, acceptedFile, docId);
      }

      // Poll for backend phase and update progress bar
      const phaseProgress = {
        uploading: 10,
        parsing: 25,
        extraction: 50,
        embedding: 75,
        rag: 90,
        completed: 100,
        error: 0,
      };
      let polling = true;
      async function pollPhase() {
        while (polling) {
          try {
            const res = await fetch(`/api/v1/ingest/status/${docId}`);
            if (!res.ok) break;
            const data = await res.json();
            const phase = data.phase || "uploading";
            const progress =
              phaseProgress[phase as keyof typeof phaseProgress] ?? 0;
            updateUpload(uploadId, {
              phase,
              progress,
              status: phase === "completed" ? "completed" : "processing",
            });
            if (phase === "completed" || phase === "error") {
              polling = false;
              break;
            }
            await new Promise((resolve) => setTimeout(resolve, 1000));
          } catch {
            break;
          }
        }
      }
      pollPhase();

      // ... (rest of your success logic) ...
    } catch (err: unknown) {
      console.error("Upload error:", err);
      const message =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during upload.";
      setError(message);
      updateUpload(uploadId, { status: "error", error: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button variant="ghost" onClick={props.onNavigateBack} className="mb-4">
        <ChevronLeft className="h-4 w-4 mr-2" />
        Back to Document Types
      </Button>

      <h1 className="text-2xl font-semibold">Upload Document</h1>

      <div className="space-y-2">
        <Label htmlFor="docTypeName">
          Document type <span className="text-red-500">*</span>
        </Label>
        <Input
          id="docTypeName"
          value={documentTypeName}
          onChange={(e) => setDocumentTypeName(e.target.value)}
          placeholder="E.g., Invoices, Receipts"
          disabled={isLoading || !!initialDocumentTypeName}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="flex items-center gap-2 font-medium">
            <UploadCloud className="h-5 w-5" /> Upload Files
          </Label>
        </div>
        <div
          {...getRootProps()}
          className={cn(
            "relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg p-6 text-center transition-colors",
            isLoading
              ? "cursor-not-allowed bg-muted/50"
              : "cursor-pointer border-muted bg-muted/20",
            !isLoading &&
              isFocused &&
              "outline-none ring-2 ring-ring ring-offset-2",
            !isLoading && isDragAccept && "border-green-500 bg-green-500/10",
            !isLoading && isDragReject && "border-red-500 bg-red-500/10",
            !isLoading && isDragActive && "border-primary",
            error && "border-destructive bg-destructive/10",
          )}
        >
          <input {...getInputProps()} disabled={isLoading} />

          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80 rounded-lg z-10">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="ml-2">Uploading...</span>
            </div>
          )}

          {!isLoading && acceptedFile ? (
            <div className="flex flex-col items-center text-center">
              <FileIcon className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="font-semibold text-primary break-all">
                {acceptedFile.name}
              </p>
              <p className="text-xs text-muted-foreground mb-4">
                {(acceptedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => {
                  handleRemoveFile();
                }}
              >
                <X className="h-4 w-4 mr-1" /> Remove File
              </Button>
            </div>
          ) : !isLoading ? (
            <>
              <UploadCloud className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="mb-2 text-sm text-muted-foreground">
                <span className="font-semibold text-primary">
                  Drag and drop file here
                </span>{" "}
                or
              </p>
              <Button
                type="button"
                variant="default"
                className="bg-indigo-600 hover:bg-indigo-700 pointer-events-none"
              >
                Click here to upload
              </Button>
              <p className="mt-4 text-xs text-muted-foreground">
                Supported: JPG, JPEG, PNG, TIFF, PDF, TIF, XLSX, XLS
              </p>
              <p className="text-xs text-muted-foreground">
                File size should be maximum 75mb and shouldn't be password
                protected
              </p>
            </>
          ) : null}
        </div>
        {error && (
          <p className="text-sm text-destructive text-center mt-1">{error}</p>
        )}
      </div>

      <div className="rounded-md border border-border p-4 space-y-3 bg-background">
        <div className="flex items-center justify-between cursor-pointer">
          <Label className="flex items-center gap-2 font-medium">
            <LinkIcon className="h-5 w-5" /> Auto-import files via integrations
          </Label>
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="text-sm text-muted-foreground flex items-center gap-2">
          <span>Logos for Google Drive, Box, etc.</span> and more
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          onClick={handleCreateClick}
          className="bg-indigo-600 hover:bg-indigo-700 w-48"
          disabled={!documentTypeName.trim() || !acceptedFile || isLoading}
        >
          {isLoading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <ChevronLeft className="h-4 w-4 mr-2 -rotate-180" />
          )}
          {isLoading ? "Processing..." : "Upload Document"}
        </Button>
      </div>
    </div>
  );
}
