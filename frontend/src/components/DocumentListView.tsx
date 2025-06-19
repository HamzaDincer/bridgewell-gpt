"use client";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  ChevronLeft,
  Upload,
  Download,
  Search,
  ArrowUpDown,
  Filter,
  Eye, // For Start Reviewing icon
  FileText,
  SkipForward,
  CheckCheck,
  Trash2,
} from "lucide-react";
import { useRouter } from "next/navigation";

// Import Document and DocumentListViewProps from @/types
import type { DocumentListViewProps } from "@/types";
import { deleteDocumentCompletely } from "@/lib/documentProcessing";
import { useState } from "react";

export function DocumentListView({
  documentTypeName,
  documents,
  onBack,

  error,
  onUpload,
}: DocumentListViewProps) {
  const router = useRouter();
  const [deletingDocs, setDeletingDocs] = useState<Set<string>>(new Set());

  const handleDelete = async (docId: string, docName: string) => {
    if (
      !confirm(
        `Are you sure you want to delete "${docName}"? This action cannot be undone.`,
      )
    ) {
      return;
    }

    setDeletingDocs((prev) => new Set(prev).add(docId));

    try {
      const result = await deleteDocumentCompletely(docId);

      if (result.status === "success") {
        // Refresh the page to update the document list
        window.location.reload();
      } else {
        alert(
          `Failed to delete document: ${
            result.errors?.join(", ") || "Unknown error"
          }`,
        );
      }
    } catch (error) {
      alert(`Error deleting document: ${error}`);
    } finally {
      setDeletingDocs((prev) => {
        const newSet = new Set(prev);
        newSet.delete(docId);
        return newSet;
      });
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-destructive">
        <FileText className="h-10 w-10 mb-4" /> {/* Or some other error icon */}
        <p className="text-lg font-semibold">Error loading documents</p>
        <p className="text-sm">{error}</p>
        <Button onClick={onBack} variant="outline" className="mt-4">
          Go Back
        </Button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <FileText className="h-10 w-10 mb-4" />
        <p className="text-lg">No documents found.</p>
        <p className="text-sm mb-4">Upload a document to get started.</p>
        {/* Consider adding an Upload button here or direct to one if appropriate */}
        <Button onClick={onBack} variant="outline">
          Back to Document Type
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header section */}
      <div className="flex items-center justify-between mb-4">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-lg font-medium"
        >
          <ChevronLeft className="h-5 w-5 mr-2" />
          {documentTypeName}
        </Button>
        <div className="flex items-center gap-2">
          {/* Placeholder for future More Options button */}
          {/* <Button variant="outline" size="icon"><MoreVertical className="h-4 w-4" /></Button> */}
          <Button variant="outline" onClick={onUpload}>
            <Upload className="h-4 w-4 mr-2" /> Upload
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" /> Download data
          </Button>
          <Button className="bg-indigo-600 hover:bg-indigo-700">
            <Eye className="h-4 w-4 mr-2" /> Start Reviewing
          </Button>
        </div>
      </div>

      {/* Title and Search/Filter Bar */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Documents</h1>
        <div className="relative w-[300px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search documents"
            className="pl-8 bg-background"
          />
        </div>
      </div>

      {/* Tabs - Simplified for now */}
      <div className="border-b">
        <nav className="flex space-x-4" aria-label="Tabs">
          {/* Example tabs - make dynamic later */}
          <Button
            variant="ghost"
            className="px-3 py-2 font-medium text-sm rounded-md text-indigo-600 bg-indigo-100"
          >
            <FileText className="h-4 w-4 mr-2" /> All Files{" "}
            <span className="ml-2 bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full text-xs">
              {documents.length}
            </span>
          </Button>
          <Button
            variant="ghost"
            className="px-3 py-2 font-medium text-sm rounded-md text-muted-foreground hover:text-primary"
          >
            <Eye className="h-4 w-4 mr-2" /> Review{" "}
            <span className="ml-2 bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full text-xs">
              1
            </span>{" "}
            {/* Example count */}
          </Button>
          <Button
            variant="ghost"
            className="px-3 py-2 font-medium text-sm rounded-md text-muted-foreground hover:text-primary"
          >
            <SkipForward className="h-4 w-4 mr-2" /> Skipped{" "}
            <span className="ml-2 bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full text-xs">
              0
            </span>{" "}
            {/* Example count */}
          </Button>
          <Button
            variant="ghost"
            className="px-3 py-2 font-medium text-sm rounded-md text-muted-foreground hover:text-primary"
          >
            <CheckCheck className="h-4 w-4 mr-2" /> Processed{" "}
            <span className="ml-2 bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full text-xs">
              0
            </span>{" "}
            {/* Example count */}
          </Button>
        </nav>
      </div>

      {/* Document Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">
                <Checkbox />
              </TableHead>
              <TableHead>
                <Button variant="ghost" size="sm">
                  Name <ArrowUpDown className="ml-2 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>
                <Button variant="ghost" size="sm">
                  Status <Filter className="ml-2 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>
                <Button variant="ghost" size="sm">
                  Uploaded by <Filter className="ml-2 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>
                <Button variant="ghost" size="sm">
                  Date modified <Filter className="ml-2 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>
                <Button variant="ghost" size="sm">
                  Date added <Filter className="ml-2 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => {
              const phase = doc.phase;
              const isBlocked = !["embedding", "rag", "completed"].includes(
                phase || "",
              );
              return (
                <TableRow
                  key={doc.id}
                  className={`transition-colors ${
                    isBlocked
                      ? "opacity-60 cursor-not-allowed"
                      : "cursor-pointer hover:bg-indigo-50"
                  }`}
                  style={{ textDecoration: "none" }}
                  onClick={() => {
                    if (!isBlocked) router.push(`/documents/${doc.id}`);
                  }}
                  title={
                    isBlocked
                      ? `Processing: ${
                          phase || doc.phase
                        }. You can view the document when extraction is complete.`
                      : undefined
                  }
                >
                  <TableCell>
                    <Checkbox disabled={isBlocked} />
                  </TableCell>
                  <TableCell className="font-medium">{doc.name}</TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      className={`border-blue-300 text-blue-600 bg-blue-50 hover:bg-blue-100 ${
                        isBlocked ? "pointer-events-none" : ""
                      }`}
                    >
                      {phase
                        ? phase.charAt(0).toUpperCase() + phase.slice(1)
                        : "Unknown"}
                    </Button>
                  </TableCell>
                  <TableCell>
                    <div>{doc.uploadedBy}</div>
                    <div className="text-xs text-muted-foreground">
                      {doc.uploadType}
                    </div>
                  </TableCell>
                  <TableCell>{doc.dateModified}</TableCell>
                  <TableCell>{doc.dateAdded}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent row click
                        handleDelete(doc.id, doc.name);
                      }}
                      disabled={deletingDocs.has(doc.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      {deletingDocs.has(doc.id) ? (
                        "Deleting..."
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      {/* Add pagination later if needed */}
    </div>
  );
}
