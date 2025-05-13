"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import {
  Bell,
  HelpCircle,
  LayoutGrid,
  ChevronDown,
  // FileText, // Not used in this header part, was for a commented out section
} from "lucide-react";

// Define props if any are needed in the future, e.g., user details
interface DashboardHeaderProps {
  userName?: string;
  userPlan?: string;
  userInitials?: string;
  // Add any other dynamic data or handlers here
}

export function DashboardHeader({
  userName = "Hamza dincer", // Default mock data
  userPlan = "Free Plan",
  userInitials = "H",
}: DashboardHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b bg-white px-4 sm:px-6">
      {/* Removed pages left and upgrade button as requested previously in Dashboard.tsx */}
      <div className="ml-auto flex items-center gap-4">
        {/* Example: Pages left / Upgrade button (currently commented out) */}
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
            {userInitials}
          </div>
          <div className="hidden md:block">
            <div className="text-sm font-medium">{userName}</div>
            <div className="text-xs text-muted-foreground">{userPlan}</div>
          </div>
          <ChevronDown className="h-4 w-4" />
        </div>
      </div>
    </header>
  );
}
