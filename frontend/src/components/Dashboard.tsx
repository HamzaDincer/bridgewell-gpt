"use client";

import { useState, useEffect } from "react";
import {
  ChevronDown,
  MoreVertical,
  PenLine,
  Search,
  Upload,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DocumentTypeDialog } from "@/components/ui/DocumentTypeDialog";
import { DocumentListView } from "@/components/DocumentListView";
// Import types from the new file
import type { Document, DocumentType, ApiDocument } from "@/types";
import { toast } from "sonner";

// Import new view components
import { FieldSetupView } from "@/components/FieldSetupView";
import { DataTableView } from "@/components/DataTableView";

// Import newly created dashboard layout components
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
// Import the new workflow component
import { CreateDocumentTypeWorkflow } from "@/components/dashboard/CreateDocumentTypeWorkflow";

// Add viewMode type
type ViewMode =
  | "dashboard"
  | "documentList"
  | "fieldSetup"
  | "dataTable"
  | "createForm"
  | "upload";

// Renamed function to DashboardComponent to avoid conflict if needed, but keeping Dashboard for now
export default function Dashboard() {
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [isLoadingTypes, setIsLoadingTypes] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("dashboard");
  const [selectedDocumentType, setSelectedDocumentType] = useState<
    string | null
  >(null);
  const [activeDocuments, setActiveDocuments] = useState<Document[]>([]);

  useEffect(() => {
    const fetchTypes = async () => {
      setIsLoadingTypes(true);
      setFetchError(null);
      try {
        const response = await fetch("/api/v1/document-types");
        if (!response.ok) {
          let errorMsg = `Error fetching types: ${response.status}`;
          try {
            const errorData = await response.json();
            errorMsg = errorData.detail || errorMsg;
          } catch {
            /* Ignore JSON parsing error */
          }
          throw new Error(errorMsg);
        }
        const data: DocumentType[] = await response.json();
        setDocumentTypes(data);
      } catch (err) {
        console.error("Failed to fetch document types:", err);
        const message =
          err instanceof Error ? err.message : "An unknown error occurred.";
        setFetchError(message);
        setDocumentTypes([]);
      } finally {
        setIsLoadingTypes(false);
      }
    };

    fetchTypes();
  }, []);

  const handleSelectDocumentType = async (typeName: string) => {
    setSelectedDocumentType(typeName);
    setViewMode("createForm");
    setIsDialogOpen(false);
  };

  const navigateToDashboard = async () => {
    setViewMode("dashboard");
    setSelectedDocumentType(null);
    setActiveDocuments([]);
  };

  const handleWorkflowSuccess = (
    newlyCreatedType: DocumentType,
    documents?: Document[], // documents are passed from workflow
  ) => {
    console.log(
      "Workflow Success! New Type:",
      newlyCreatedType,
      "Docs:",
      documents,
    );

    setDocumentTypes((prevTypes) => {
      const existingTypeIndex = prevTypes.findIndex(
        (t) => t.id === newlyCreatedType.id,
      );
      if (existingTypeIndex > -1) {
        const updatedTypes = [...prevTypes];
        updatedTypes[existingTypeIndex] = newlyCreatedType;
        return updatedTypes;
      } else {
        return [...prevTypes, newlyCreatedType];
      }
    });

    if (documents) {
      setActiveDocuments(documents);
    } else {
      // If documents array is not provided by workflow, or is empty, ensure state is clean.
      setActiveDocuments([]);
    }

    setSelectedDocumentType(newlyCreatedType.title);
    setViewMode("documentList");
    setIsLoadingTypes(false);
    setFetchError(null);
  };

  const handleWorkflowCancel = () => {
    navigateToDashboard();
  };

  // Handler for when a document type card is clicked
  const handleCardClick = async (typeId: string, typeTitle: string) => {
    setSelectedDocumentType(typeTitle); // Store title for display
    // Fetch documents for this type and set to activeDocuments
    // For now, just switch view. Actual data fetching can be added from handleCreateType or made separate
    setIsLoadingTypes(true);
    try {
      const docsResponse = await fetch(
        `/api/v1/document-types/${typeId}/documents`,
      );
      if (!docsResponse.ok) {
        throw new Error(`Failed to fetch documents: ${docsResponse.status}`);
      }
      const documents = await docsResponse.json();
      const formattedDocuments: Document[] = documents.map(
        (doc: ApiDocument) => ({
          id: doc.id,
          name: doc.name,
          status: doc.status,
          uploadedBy: "User", // Placeholder
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
      setActiveDocuments(formattedDocuments);
      setViewMode("documentList"); // Default to document list view
    } catch (err) {
      console.error("Failed to fetch documents on card click:", err);
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      toast.error(`Failed to load documents: ${message}`);
      setActiveDocuments([]);
      setViewMode("documentList"); // Still go to the view, it will show empty/error
    } finally {
      setIsLoadingTypes(false);
    }
  };

  // Add handler for upload button
  const handleUploadClick = () => {
    setViewMode("upload");
  };

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar onNavigateToDashboard={navigateToDashboard} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <DashboardHeader />

        {/* Content: Render based on viewMode */}
        <main className="flex-1 overflow-auto p-4 sm:p-6">
          {viewMode === "dashboard" && (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold">Document types</h1>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="search"
                      placeholder="Search document type"
                      className="w-[300px] pl-8 bg-white"
                    />
                  </div>
                  <Button
                    className="bg-indigo-500 hover:bg-indigo-600"
                    onClick={() => {
                      // Option 1: Directly go to form with no pre-selected name
                      // setSelectedDocumentType(null);
                      // setViewMode("createForm");
                      // Option 2: Open dialog to pick a template name (current behavior)
                      setIsDialogOpen(true);
                    }}
                  >
                    <span className="mr-1">+</span> Add Document Type
                  </Button>
                </div>
              </div>

              {isLoadingTypes && viewMode === "dashboard" ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="ml-2">Loading Document Types...</span>
                </div>
              ) : fetchError && viewMode === "dashboard" ? (
                <div className="text-center text-destructive py-4">
                  <p>Error loading document types:</p>
                  <p className="text-sm">{fetchError}</p>
                </div>
              ) : documentTypes.length === 0 && viewMode === "dashboard" ? (
                <div className="text-center text-muted-foreground py-10">
                  <p>No document types found.</p>
                  <p>Click "+ Add Document Type" to get started.</p>
                </div>
              ) : viewMode === "dashboard" ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {documentTypes.map((docType) => (
                    <Card
                      key={docType.id}
                      className="overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() =>
                        handleCardClick(String(docType.id), docType.title)
                      }
                    >
                      <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-xl">
                          {docType.title}
                        </CardTitle>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-5 w-5" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>Edit</DropdownMenuItem>
                            <DropdownMenuItem>Duplicate</DropdownMenuItem>
                            <DropdownMenuItem>Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </CardHeader>
                      <CardContent className="pb-2">
                        <div className="grid gap-2">
                          <div className="flex justify-between text-sm">
                            <span>Uploaded:</span>
                            <span className="font-medium">
                              {docType.uploaded}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Review Pending:</span>
                            <span className="font-medium">
                              {docType.reviewPending}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Approved:</span>
                            <span className="font-medium">
                              {docType.approved}
                            </span>
                          </div>
                          {docType.setupRequired && (
                            <div className="mt-2 flex items-center gap-1 text-amber-500 text-sm">
                              <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                              <span>Setup required</span>
                              <ChevronDown className="h-4 w-4 -rotate-90" />
                            </div>
                          )}
                        </div>
                      </CardContent>
                      <Separator />
                      <CardFooter className="flex justify-between p-0">
                        <Button
                          variant="ghost"
                          className="flex-1 rounded-none h-12 gap-2 text-indigo-500"
                        >
                          <PenLine className="h-4 w-4" />
                          Edit Fields
                        </Button>
                        <Separator orientation="vertical" />
                        <Button
                          variant="ghost"
                          className="flex-1 rounded-none h-12 gap-2 text-indigo-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedDocumentType(docType.title);
                            setViewMode("upload");
                          }}
                        >
                          <Upload className="h-4 w-4" />
                          Upload
                        </Button>
                        <Separator orientation="vertical" />
                        <Button
                          variant="ghost"
                          className="flex-1 rounded-none h-12 gap-2 text-indigo-500"
                        >
                          <Search className="h-4 w-4" />
                          Review
                        </Button>
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              ) : null}
            </div>
          )}

          {viewMode === "createForm" && (
            <CreateDocumentTypeWorkflow
              initialDocumentTypeName={selectedDocumentType}
              onSuccess={handleWorkflowSuccess}
              onCancel={handleWorkflowCancel}
            />
          )}

          {(viewMode === "documentList" ||
            viewMode === "fieldSetup" ||
            viewMode === "dataTable") &&
          selectedDocumentType ? (
            <div className="flex-1 flex flex-col">
              {/* Header for selected document type and tabs */}
              <div className="border-b p-4">
                <Button
                  variant="ghost"
                  onClick={navigateToDashboard}
                  className="mb-2"
                >
                  &larr; Back to Document Types
                </Button>
                <h1 className="text-2xl font-semibold mb-4">
                  {selectedDocumentType || "Selected Type"}
                </h1>
                <div className="flex space-x-2 border-b mb-4">
                  <Button
                    variant={
                      viewMode === "documentList" ? "secondary" : "ghost"
                    }
                    onClick={() => setViewMode("documentList")}
                  >
                    Documents
                  </Button>
                  <Button
                    variant={viewMode === "fieldSetup" ? "secondary" : "ghost"}
                    onClick={() => setViewMode("fieldSetup")}
                  >
                    Field Setup
                  </Button>
                  <Button
                    variant={viewMode === "dataTable" ? "secondary" : "ghost"}
                    onClick={() => setViewMode("dataTable")}
                  >
                    Data Table
                  </Button>
                </div>
              </div>

              {/* Content area for the selected tab */}
              <div className="flex-1 p-6 overflow-auto">
                {viewMode === "documentList" && (
                  <DocumentListView
                    documentTypeName={selectedDocumentType}
                    documents={activeDocuments}
                    onBack={navigateToDashboard}
                    isLoading={isLoadingTypes}
                    error={fetchError}
                    onUpload={handleUploadClick}
                  />
                )}
                {viewMode === "fieldSetup" && (
                  <FieldSetupView
                    documentTypeName={selectedDocumentType || ""}
                  />
                )}
                {viewMode === "dataTable" && (
                  <DataTableView
                    documentTypeName={selectedDocumentType || ""}
                  />
                )}
              </div>
            </div>
          ) : null}

          {viewMode === "upload" && selectedDocumentType && (
            <CreateDocumentTypeWorkflow
              initialDocumentTypeName={selectedDocumentType}
              onSuccess={handleWorkflowSuccess}
              onCancel={handleWorkflowCancel}
            />
          )}

          {viewMode !== "documentList" &&
            viewMode !== "fieldSetup" &&
            viewMode !== "dataTable" &&
            viewMode !== "createForm" &&
            viewMode !== "dashboard" &&
            viewMode !== "upload" && (
              <div className="text-center text-muted-foreground py-10">
                <p>
                  No content to display for the current view mode or an
                  unexpected state has occurred.
                </p>
              </div>
            )}

          <DocumentTypeDialog
            open={isDialogOpen}
            onOpenChange={setIsDialogOpen}
            onSelectType={handleSelectDocumentType}
          />
        </main>
      </div>
    </div>
  );
}
