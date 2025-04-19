"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DocumentTypeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const documentTypes = [
  "Income",
  "Procurement",
  "Energy",
  "Identification",
  "Insurance",
  "Tax Forms",
  "Other",
  "USA Lending",
  // Add more types as needed
];

export function DocumentTypeDialog({
  open,
  onOpenChange,
}: DocumentTypeDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Select a Document Type</DialogTitle>
          <DialogDescription>
            Choose from a list of ready-to-use document types or create your
            own.
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4 py-4">
          {documentTypes.map((docType) => (
            <Button
              key={docType}
              variant="outline"
              className="justify-start h-auto py-3"
              onClick={() => {
                console.log(`Selected: ${docType}`); // Placeholder action
                onOpenChange(false); // Close dialog on selection
              }}
            >
              {docType}
            </Button>
          ))}
        </div>
        {/* Optional: Add Create custom document type button later */}
        {/* <DialogFooter>
          <Button type="button" variant="secondary">Create custom document type</Button>
        </DialogFooter> */}
      </DialogContent>
    </Dialog>
  );
}
