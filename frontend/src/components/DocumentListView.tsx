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
  Loader2, // Added Loader2
} from "lucide-react";
import { useRouter } from "next/navigation";

// Import Document and DocumentListViewProps from @/types
import type { DocumentListViewProps } from "@/types";

export function DocumentListView({
  documentTypeName,
  documents,
  onBack,
  isLoading,
  error,
}: DocumentListViewProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <Loader2 className="h-10 w-10 animate-spin mb-4 text-indigo-600" />
        <p className="text-lg">Loading documents...</p>
      </div>
    );
  }

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
          <Button variant="outline">
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow
                key={doc.id}
                className="cursor-pointer hover:bg-indigo-50 transition-colors"
                style={{ textDecoration: "none" }}
                onClick={() => router.push(`/documents/${doc.id}`)}
              >
                <TableCell>
                  <Checkbox />
                </TableCell>
                <TableCell className="font-medium">{doc.name}</TableCell>
                <TableCell>
                  {/* Example Status Button - make dynamic */}
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-blue-300 text-blue-600 bg-blue-50 hover:bg-blue-100"
                  >
                    {doc.status}
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {/* Add pagination later if needed */}
    </div>
  );
}
