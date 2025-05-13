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
}: CreateDocumentTypeWorkflowProps) {
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

    try {
      // Step 1: Create document type (moved from Dashboard)
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

      // Step 2: Associate document with the type (moved from Dashboard)
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
        // Potentially roll back or offer retry for document association
        throw new Error(
          `Failed to associate document with type: ${addDocResponse.statusText} (status: ${addDocResponse.status})`,
        );
      }

      const updatedTypeWithDocInfo: DocumentType = await addDocResponse.json(); // Backend returns the updated type with document list
      console.log(
        "Document associated, backend returned:",
        updatedTypeWithDocInfo,
      );

      // Step 3: Fetch all documents for this type to pass to onSuccess (moved from Dashboard)
      // The updatedTypeWithDocInfo from the POST might already contain the documents.
      // If not, or to be sure, we can fetch them.
      // Let\'s assume the POST response for associating document now returns the type *and* its documents
      // to align with what `onSuccess` expects.
      // If `updatedTypeWithDocInfo.documents` is populated, use that. Otherwise, fetch.

      let finalDocuments: Document[] = [];
      if (
        updatedTypeWithDocInfo.documents &&
        Array.isArray(updatedTypeWithDocInfo.documents)
      ) {
        finalDocuments = updatedTypeWithDocInfo.documents.map(
          (doc: ApiDocument) => ({
            id: doc.id,
            name: doc.name,
            status: doc.status,
            uploadedBy: "System", // Placeholder
            uploadType: "Direct Upload", // Placeholder
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
      } else {
        // Fallback: Fetch documents separately if not included
        const docsResponse = await fetch(
          `/api/v1/document-types/${createdType.id}/documents`,
        );
        if (!docsResponse.ok) {
          throw new Error(
            `Failed to fetch documents for type ${createdType.title}: ${docsResponse.status}`,
          );
        }
        const docsData: ApiDocument[] = await docsResponse.json();
        finalDocuments = docsData.map((doc: ApiDocument) => ({
          id: doc.id,
          name: doc.name,
          status: doc.status,
          uploadedBy: "System", // Placeholder
          uploadType: "Direct Upload", // Placeholder
          dateModified: new Date(doc.date_added).toLocaleString("en-US", {
            dateStyle: "medium",
            timeStyle: "short",
          }),
          dateAdded: new Date(doc.date_added).toLocaleString("en-US", {
            dateStyle: "medium",
            timeStyle: "short",
          }),
        }));
      }

      // The `createdType` from step 1 might not have the `documents` array.
      // `updatedTypeWithDocInfo` is more complete if the backend returns it fully.
      // Let's use `updatedTypeWithDocInfo` as the first arg if it includes all necessary fields of DocumentType.
      // Assuming updatedTypeWithDocInfo is a full DocumentType object.
      onSuccess(updatedTypeWithDocInfo, finalDocuments);
    } catch (err) {
      console.error(
        "Workflow: Failed during document type creation/association:",
        err,
      );
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      setWorkflowError(`Failed to complete process: ${message}`);
      toast.error(`Operation failed: ${message}`);
      // Decide if onCancel should be called or if the user can retry from the form.
      // For now, keep them on the form to see the error.
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
