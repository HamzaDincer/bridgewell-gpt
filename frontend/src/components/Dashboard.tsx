"use client";

// Removed comment // Import icons later
// import { PencilIcon, UploadIcon, EyeIcon, DotsVerticalIcon } from '@heroicons/react/outline'

import { useState, useEffect } from "react";
import {
  Bell,
  ChevronDown,
  FileText,
  Grid3X3,
  HelpCircle,
  LayoutGrid,
  MoreVertical,
  PenLine,
  Search,
  Settings,
  Upload,
  Wrench,
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
import { CreateDocumentTypeForm } from "@/components/CreateDocumentTypeForm";
import { DocumentListView } from "@/components/DocumentListView";
// Import types from the new file
import type { Document, DocumentType } from "@/types";
import { toast } from "sonner";

// Renamed function to DashboardComponent to avoid conflict if needed, but keeping Dashboard for now
export default function Dashboard() {
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [isLoadingTypes, setIsLoadingTypes] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [viewMode, setViewMode] = useState<
    "dashboard" | "createForm" | "documentList"
  >("dashboard");
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

  const handleSelectDocumentType = (typeName: string) => {
    setSelectedDocumentType(typeName);
    setViewMode("createForm");
    setIsDialogOpen(false);
  };

  const navigateToDashboard = () => {
    setViewMode("dashboard");
    setSelectedDocumentType(null);
    setActiveDocuments([]);
  };

  const handleCreateType = async (
    typeName: string,
    file: File | null,
    docId?: string,
  ) => {
    console.log(
      `Dashboard: Attempting to create type '${typeName}' via API...`,
    );
    setIsLoadingTypes(true); // Indicate loading state
    setFetchError(null);

    try {
      // ---> Step 1: Call the backend API to create the type <---
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

      // Get the actual created type data from the backend
      const createdType: DocumentType = await createResponse.json();
      console.log("Backend successfully created type:", createdType);
      toast.success(
        `Document type "${createdType.title}" created successfully.`,
      );

      // Update the frontend state with the *actual* data from the backend
      setDocumentTypes((prev) => [...prev, createdType]);

      // ---> Step 2: Create document representation for list view (if file was uploaded) <---
      if (file && docId) {
        const documentForList: Document = {
          id: docId,
          name: file.name,
          status: "Review",
          uploadedBy: "Hamza Dincer", // Replace later
          uploadType: "Direct Upload",
          dateModified: new Date().toLocaleString("en-US", {
            dateStyle: "medium",
            timeStyle: "short",
          }),
          dateAdded: new Date().toLocaleString("en-US", {
            dateStyle: "medium",
            timeStyle: "short",
          }),
        };
        setActiveDocuments([documentForList]);

        // ---> Step 3: Set selected type and switch view <---
        setSelectedDocumentType(createdType.title); // Use title from createdType
        setViewMode("documentList");
      } else {
        // If no file was uploaded during creation, just go back to dashboard? Or stay on form?
        // For now, let's just update the list and stay on the dashboard view.
        // Refreshing the list might be needed if staying on dashboard.
        setViewMode("dashboard");
      }
    } catch (err) {
      console.error("Failed to create document type:", err);
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      setFetchError(`Failed to create document type: ${message}`);
      toast.error(`Failed to create document type: ${message}`);
      // Optionally revert any optimistic UI updates here if needed
    } finally {
      setIsLoadingTypes(false); // Stop loading indicator
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <div className="hidden md:flex w-[240px] flex-col border-r bg-white">
        <div className="flex h-16 items-center border-b px-4">
          <img
            src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAaQAAABUCAYAAADNqUOYAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyhpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuNi1jMTQ1IDc5LjE2MzQ5OSwgMjAxOC8wOC8xMy0xNjo0MDoyMiAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKE1hY2ludG9zaCkiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6QzU0QzQ3QjI2RDYxMTFFQkI1MjNEMzM3MzQwNTk4MjQiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6QzU0QzQ3QjM2RDYxMTFFQkI1MjNEMzM3MzQwNTk4MjQiPiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDpDNTRDNDdCMDZENjExMUVCQjUyM0QzMzczNDA1OTgyNCIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDpDNTRDNDdCMTZENjExMUVCQjUyM0QzMzczNDA1OTgyNCIvPiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0YT4gPD94cGFja2V0IGVuZD0iciI/PkFg1CYAABzJSURBVHja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"
            alt="Bridgwell Document AI Logo"
            className="h-8 w-auto"
          />
        </div>
        <div className="flex-1 overflow-auto py-2">
          <nav className="grid gap-1 px-2">
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium bg-indigo-50 text-indigo-500"
            >
              <FileText className="h-5 w-5" />
              <span>Document Types</span>
            </Button>
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <LayoutGrid className="h-5 w-5" />
              <span>All Documents</span>
            </Button>
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <Grid3X3 className="h-5 w-5" />
              <span>All Data</span>
            </Button>
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <Wrench className="h-5 w-5" />
              <span>All Models</span>
            </Button>
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <Settings className="h-5 w-5" />
              <span>Integrations</span>
            </Button>
          </nav>
        </div>
        <div className="mt-auto border-t p-4">
          <nav className="grid gap-1">
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <HelpCircle className="h-5 w-5" />
              <span>Get Started</span>
            </Button>
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <Grid3X3 className="h-5 w-5" />
              <span>AI Models Hub</span>
            </Button>
            <Button
              variant="ghost"
              className="justify-start gap-2 h-12 px-4 font-medium"
            >
              <Settings className="h-5 w-5" />
              <span>Settings</span>
            </Button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b bg-white px-4 sm:px-6">
          {/* Removed pages left and upgrade button as requested */}
          <div className="ml-auto flex items-center gap-4">
            {/* <div className="flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4" />
              <span>84 pages left</span>
            </div>
            <Button className="bg-indigo-500 hover:bg-indigo-600">Upgrade</Button> */}
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <HelpCircle className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <LayoutGrid className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-500">
                H
              </div>
              <div className="hidden md:block">
                <div className="text-sm font-medium">Hamza dincer</div>
                <div className="text-xs text-muted-foreground">Free Plan</div>
              </div>
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </header>

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
                    onClick={() => setIsDialogOpen(true)}
                  >
                    <span className="mr-1">+</span> Add Document Type
                  </Button>
                </div>
              </div>

              {isLoadingTypes ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="ml-2">Loading Document Types...</span>
                </div>
              ) : fetchError ? (
                <div className="text-center text-destructive py-4">
                  <p>Error loading document types:</p>
                  <p className="text-sm">{fetchError}</p>
                </div>
              ) : documentTypes.length === 0 ? (
                <div className="text-center text-muted-foreground py-10">
                  <p>No document types found.</p>
                  <p>Click "+ Add Document Type" to get started.</p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {documentTypes.map((docType) => (
                    <Card key={docType.id} className="overflow-hidden">
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
              )}
            </div>
          )}

          {viewMode === "createForm" && selectedDocumentType && (
            <CreateDocumentTypeForm
              initialDocumentTypeName={selectedDocumentType}
              onCreate={handleCreateType}
              onNavigateBack={navigateToDashboard}
            />
          )}

          {viewMode === "documentList" && selectedDocumentType && (
            <DocumentListView
              documentTypeName={selectedDocumentType}
              documents={activeDocuments}
              onBack={navigateToDashboard}
            />
          )}

          {/* Dialog is rendered outside the conditional part */}
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
