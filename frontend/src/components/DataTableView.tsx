"use client";

import React from "react";

interface DataTableViewProps {
  documentTypeName: string | null;
}

export function DataTableView({ documentTypeName }: DataTableViewProps) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">
        Data Table for {documentTypeName || "Selected Document Type"}
      </h1>
      <p>Data table view and associated actions will go here.</p>
      {/* Add more placeholder content or structure as needed */}
    </div>
  );
}
