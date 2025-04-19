"use client";

// Removed comment // Import icons later
// import { PencilIcon, UploadIcon, EyeIcon, DotsVerticalIcon } from '@heroicons/react/outline'

import { useState } from "react";
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

// Renamed function to DashboardComponent to avoid conflict if needed, but keeping Dashboard for now
export default function Dashboard() {
  const [documentTypes, setDocumentTypes] = useState([
    {
      id: 1,
      title: "Insurance",
      uploaded: 2,
      reviewPending: 1,
      approved: 1,
      setupRequired: true,
    },
  ]);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <div className="hidden md:flex w-[240px] flex-col border-r bg-white">
        <div className="flex h-14 items-center border-b px-4">
          <div className="flex items-center gap-2">
            <div className="rounded-full bg-indigo-500 p-1">
              <FileText className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-indigo-500">DOCSUMO</h2>
              <p className="text-xs text-muted-foreground">Document AI</p>
            </div>
          </div>
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

        {/* Content */}
        <main className="flex-1 overflow-auto p-4 sm:p-6">
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
                <Button className="bg-indigo-500 hover:bg-indigo-600">
                  <span className="mr-1">+</span> Add Document Type
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {documentTypes.map((docType) => (
                <Card key={docType.id} className="overflow-hidden">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-xl">{docType.title}</CardTitle>
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
                        <span className="font-medium">{docType.uploaded}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Review Pending:</span>
                        <span className="font-medium">
                          {docType.reviewPending}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Approved:</span>
                        <span className="font-medium">{docType.approved}</span>
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
          </div>
        </main>
      </div>
    </div>
  );
}
