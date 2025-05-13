"use client";

import React from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  FileText,
  LayoutGrid,
  Grid3X3,
  Wrench,
  Settings,
  HelpCircle,
} from "lucide-react";

interface DashboardSidebarProps {
  // Add any other props needed, e.g., activePath for styling
  onNavigateToDashboard: () => void;
}

export function DashboardSidebar({
  onNavigateToDashboard,
}: DashboardSidebarProps) {
  // In a real app, you might have a more dynamic way to determine the active button
  // For now, we assume 'Document Types' is the primary focus of this sidebar section
  const isActive = (path: string) => path === "document-types"; // Example

  return (
    <div className="hidden md:flex w-[240px] flex-col border-r bg-white">
      <div className="flex h-14 items-center self-center border-b px-4">
        <Image
          src="/logo.png"
          alt="Bridgewell Logo"
          width={150}
          height={36}
          priority
        />
      </div>
      <div className="flex-1 overflow-auto py-2">
        <nav className="grid gap-1 px-2">
          {/* The onClick for this main "Document Types" button could also be onNavigateToDashboard 
              if it's meant to reset to the main card view from any deeper state within document types. 
              For now, assuming it's the active section and might not need an explicit onClick if Dashboard.tsx 
              handles the main view state primarily. Or, it could be a more specific navigation action.
              Let's make it call onNavigateToDashboard for consistency with the 'All Document Types' idea.
          */}
          <Button
            variant={isActive("document-types") ? "secondary" : "ghost"} // Example active styling
            className="justify-start gap-2 h-12 px-4 font-medium"
            onClick={onNavigateToDashboard} // Allow resetting to main dashboard view
          >
            <FileText className="h-5 w-5" />
            <span>Document Types</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start gap-2 h-12 px-4 font-medium"
            // onClick={() => console.log("Navigate to All Documents")}
          >
            <LayoutGrid className="h-5 w-5" />
            <span>All Documents</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start gap-2 h-12 px-4 font-medium"
            // onClick={() => console.log("Navigate to All Data")}
          >
            <Grid3X3 className="h-5 w-5" />
            <span>All Data</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start gap-2 h-12 px-4 font-medium"
            // onClick={() => console.log("Navigate to All Models")}
          >
            <Wrench className="h-5 w-5" />
            <span>All Models</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start gap-2 h-12 px-4 font-medium"
            // onClick={() => console.log("Navigate to Integrations")}
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
            // onClick={() => console.log("Navigate to Get Started")}
          >
            <HelpCircle className="h-5 w-5" />
            <span>Get Started</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start gap-2 h-12 px-4 font-medium"
            // onClick={() => console.log("Navigate to AI Models Hub")}
          >
            <Grid3X3 className="h-5 w-5" />
            <span>AI Models Hub</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start gap-2 h-12 px-4 font-medium"
            // onClick={() => console.log("Navigate to Settings")}
          >
            <Settings className="h-5 w-5" />
            <span>Settings</span>
          </Button>
        </nav>
      </div>
    </div>
  );
}
