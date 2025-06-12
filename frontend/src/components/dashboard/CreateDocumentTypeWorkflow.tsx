"use client";

import { useState } from "react";
import { CreateDocumentTypeForm } from "@/components/CreateDocumentTypeForm";
import type {
  CreateDocumentTypeWorkflowProps,
  DocumentType,
  Document,
  ApiDocument,
} from "@/types";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CreateDocumentTypeWorkflow({
  initialDocumentTypeName,
  onSuccess,
  onCancel,
  documentTypes = [],
  setDocumentTypes = () => {},
}: CreateDocumentTypeWorkflowProps & {
  documentTypes?: DocumentType[];
  setDocumentTypes?: (types: DocumentType[]) => void;
}) {
  const [isLoadingWorkflow, setIsLoadingWorkflow] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  // This is the function that will be passed to CreateDocumentTypeForm\'s `onCreate` prop
  // It mirrors the first part of the original handleCreateType logic
  const handleFormSubmit = async (
    typeName: string,
    file: File | null,
    docId?: string,
  ) => {
    if (!file || !docId) {
      // This case should ideally be handled within CreateDocumentTypeForm
      // or an earlier validation. If docId is missing, ingestion failed.
      // If file is missing, form shouldn\'t submit.
      setWorkflowError(
        "File and document ID are required to proceed. Ingestion might have failed.",
      );
      toast.error(
        "File and document ID are required. Ingestion might have failed.",
      );
      return;
    }

    console.log(
      `Workflow: Received from form: typeName '${typeName}', file '${file.name}', docId '${docId}'`,
    );
    setIsLoadingWorkflow(true);
    setWorkflowError(null);

    // Continue with API calls in the background
    try {
      // Step 1: Create document type
      const createResponse = await fetch("/api/v1/document-types", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title: typeName }),
      });

      if (!createResponse.ok) {
        let errorMsg = `Error creating type: ${createResponse.status}`;
        try {
          const errorData = await createResponse.json();
          errorMsg = errorData.detail || errorMsg;
        } catch {
          /* Ignore JSON parsing error */
        }
        throw new Error(errorMsg);
      }

      const createdType: DocumentType = await createResponse.json();
      toast.success(
        `Document type "${createdType.title}" created successfully.`,
      );

      // Step 2: Associate document with the type
      const addDocResponse = await fetch(
        `/api/v1/document-types/${createdType.id}/documents`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            doc_id: docId,
            doc_name: file.name,
          }),
        },
      );

      if (!addDocResponse.ok) {
        throw new Error(
          `Failed to associate document with type: ${addDocResponse.statusText} (status: ${addDocResponse.status})`,
        );
      }

      const updatedTypeWithDocInfo: DocumentType = await addDocResponse.json();
      console.log(
        "Document associated, backend returned:",
        updatedTypeWithDocInfo,
      );

      // Update the document list with the latest data
      let finalDocuments: Document[] = [];
      if (
        updatedTypeWithDocInfo.documents &&
        Array.isArray(updatedTypeWithDocInfo.documents)
      ) {
        finalDocuments = updatedTypeWithDocInfo.documents.map(
          (doc: ApiDocument) => ({
            id: doc.id,
            name: doc.name,
            uploadedBy: "System",
            uploadType: "Direct Upload",
            dateModified: new Date(doc.date_added).toLocaleString("en-US", {
              dateStyle: "medium",
              timeStyle: "short",
            }),
            dateAdded: new Date(doc.date_added).toLocaleString("en-US", {
              dateStyle: "medium",
              timeStyle: "short",
            }),
          }),
        );
      }

      // Update the UI with the final data
      onSuccess(updatedTypeWithDocInfo, finalDocuments);
    } catch (err) {
      console.error(
        "Workflow: Failed during document type creation/association:",
        err,
      );
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      toast.error(`Operation failed: ${message}`);
    } finally {
      setIsLoadingWorkflow(false);
    }
  };

  if (isLoadingWorkflow) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-10">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-lg font-semibold">Processing Document Type...</p>
        <p className="text-muted-foreground">
          Please wait while we set up your new document type.
        </p>
      </div>
    );
  }

  // Render the actual form
  return (
    <div>
      <CreateDocumentTypeForm
        initialDocumentTypeName={initialDocumentTypeName}
        onCreate={handleFormSubmit} // The form now calls our workflow orchestrator
        onNavigateBack={onCancel} // if user cancels from the form itself
        documentTypes={documentTypes}
        setDocumentTypes={setDocumentTypes}
      />
      {workflowError && (
        <div className="mt-4 p-4 bg-destructive/10 border border-destructive text-destructive rounded-md text-center">
          <p className="font-semibold">Workflow Error:</p>
          <p>{workflowError}</p>
          <Button
            onClick={() => setWorkflowError(null)}
            variant="outline"
            className="mt-2"
          >
            Dismiss
          </Button>
        </div>
      )}
    </div>
  );
}
