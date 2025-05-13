"use client";

import { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label"; // Assuming Shadcn Label exists or will be added
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

// Import CreateDocumentTypeFormProps from @/types
import type { CreateDocumentTypeFormProps } from "@/types";

export function CreateDocumentTypeForm({
  initialDocumentTypeName,
  onCreate,
  onNavigateBack,
}: CreateDocumentTypeFormProps) {
  const [documentTypeName, setDocumentTypeName] = useState(
    initialDocumentTypeName || "",
  );
  const [acceptedFile, setAcceptedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

    const formData = new FormData();
    formData.append("file", acceptedFile);

    try {
      const response = await fetch("/api/v1/ingest/file", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = `Upload failed with status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch {
          /* Ignore JSON parsing error */
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();
      console.log("Ingest successful:", result);

      const docId = result?.data?.[0]?.doc_id;

      onCreate(documentTypeName, acceptedFile, docId);
    } catch (err: unknown) {
      console.error("Upload error:", err);
      const message =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during upload.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button variant="ghost" onClick={onNavigateBack} className="mb-4">
        <ChevronLeft className="h-4 w-4 mr-2" />
        Back to Document Types
      </Button>

      <h1 className="text-2xl font-semibold">Create document type</h1>

      <div className="space-y-2">
        <Label htmlFor="docTypeName">
          Name your document type <span className="text-red-500">*</span>
        </Label>
        <Input
          id="docTypeName"
          value={documentTypeName}
          onChange={(e) => setDocumentTypeName(e.target.value)}
          placeholder="E.g., Invoices, Receipts"
          disabled={isLoading}
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
          {isLoading ? "Processing..." : "Create document type"}
        </Button>
      </div>
    </div>
  );
}
