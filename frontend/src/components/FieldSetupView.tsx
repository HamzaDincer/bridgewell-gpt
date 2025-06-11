"use client";

import React, { useState } from "react";
import type { FieldSetupViewProps, Field, FieldType } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PlusCircle, Trash2 } from "lucide-react";
import { BENEFIT_FIELDS } from "@/constants/benefitFields";

// Mock initial fields - in a real app, these would come from a backend
const getMockFields = (docTypeName: string | null): Field[] => {
  if (docTypeName === "Invoices") {
    return [
      {
        id: "inv-1",
        name: "Invoice ID",
        type: "text",
        isRequired: true,
      },
      {
        id: "inv-2",
        name: "Issue Date",
        type: "date",
        isRequired: true,
      },
      {
        id: "inv-3",
        name: "Amount Due",
        type: "number",
        isRequired: true,
      },
      {
        id: "inv-4",
        name: "Vendor Name",
        type: "text",
        isRequired: false,
      },
    ];
  }
  return [
    { id: "gen-1", name: "Document Name", type: "text", isRequired: true },
    { id: "gen-2", name: "Received Date", type: "date", isRequired: false },
  ];
};

const fieldTypeOptions: { value: FieldType; label: string }[] = [
  { value: "text", label: "Text" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
  { value: "checkbox", label: "Checkbox (Yes/No)" },
  { value: "select", label: "Select (Dropdown)" },
];

export function FieldSetupView({ documentTypeName }: FieldSetupViewProps) {
  const [fields, setFields] = useState<Field[]>(() =>
    getMockFields(documentTypeName),
  );
  const [newFieldName, setNewFieldName] = useState("");
  const [newFieldType, setNewFieldType] = useState<FieldType>("text");
  const [newFieldIsRequired, setNewFieldIsRequired] = useState(false);
  const [newFieldOptions, setNewFieldOptions] = useState(""); // For select type, comma-separated
  const [formState, setFormState] = useState<
    Record<string, Record<string, string>>
  >({});

  const handleAddField = () => {
    if (!newFieldName.trim()) {
      // Basic validation: ensure name is not empty
      alert("Field name cannot be empty.");
      return;
    }
    const newField: Field = {
      id: `field-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`, // Simple unique ID
      name: newFieldName.trim(),
      type: newFieldType,
      isRequired: newFieldIsRequired,
      options:
        newFieldType === "select"
          ? newFieldOptions
              .split(",")
              .map((opt) => opt.trim())
              .filter((opt) => opt)
          : undefined,
    };
    setFields([...fields, newField]);
    // Reset form
    setNewFieldName("");
    setNewFieldType("text");
    setNewFieldIsRequired(false);
    setNewFieldOptions("");
  };

  const handleDeleteField = (fieldId: string) => {
    setFields(fields.filter((field) => field.id !== fieldId));
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-semibold mb-1">
          Field Setup: {documentTypeName || "Selected Document Type"}
        </h1>
        <p className="text-muted-foreground">
          Define and manage the fields for this document type.
        </p>
      </div>

      {/* Form to add new field */}
      <div className="bg-card border rounded-lg p-4 md:p-6 space-y-4 shadow">
        <h2 className="text-xl font-semibold mb-3 border-b pb-2">
          Add New Field
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div className="space-y-1.5">
            <Label htmlFor="newFieldName">Field Name</Label>
            <Input
              id="newFieldName"
              value={newFieldName}
              onChange={(e) => setNewFieldName(e.target.value)}
              placeholder="E.g., Invoice Number"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="newFieldType">Field Type</Label>
            <select
              id="newFieldType"
              value={newFieldType}
              onChange={(e) => setNewFieldType(e.target.value as FieldType)}
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {fieldTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {newFieldType === "select" && (
            <div className="space-y-1.5 md:col-span-2 lg:col-span-1">
              <Label htmlFor="newFieldOptions">Options (comma-separated)</Label>
              <Input
                id="newFieldOptions"
                value={newFieldOptions}
                onChange={(e) => setNewFieldOptions(e.target.value)}
                placeholder="E.g., Option A, Option B"
              />
            </div>
          )}

          <div className="flex items-center space-x-2 pt-4 md:pt-7">
            <Checkbox
              id="newFieldIsRequired"
              checked={newFieldIsRequired}
              onCheckedChange={(checked) =>
                setNewFieldIsRequired(checked as boolean)
              }
            />
            <Label htmlFor="newFieldIsRequired" className="cursor-pointer">
              Required
            </Label>
          </div>

          <div className="md:col-start-2 lg:col-start-4 flex justify-end">
            <Button
              onClick={handleAddField}
              className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-700"
            >
              <PlusCircle className="mr-2 h-4 w-4" /> Add Field
            </Button>
          </div>
        </div>
      </div>

      {/* List of existing fields */}
      <div className="bg-card border rounded-lg shadow">
        <h2 className="text-xl font-semibold p-4 md:p-6 border-b">
          Current Fields
        </h2>
        {fields.length === 0 ? (
          <p className="p-4 md:p-6 text-muted-foreground">
            No fields defined yet. Add one above to get started.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Required</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fields.map((field) => (
                <TableRow key={field.id}>
                  <TableCell className="font-medium">{field.name}</TableCell>
                  <TableCell className="capitalize">
                    {fieldTypeOptions.find((opt) => opt.value === field.type)
                      ?.label || field.type}
                  </TableCell>
                  <TableCell>
                    {field.isRequired ? (
                      <span className="text-green-600 font-medium">Yes</span>
                    ) : (
                      <span className="text-muted-foreground">No</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteField(field.id)}
                      className="text-destructive hover:text-destructive-foreground hover:bg-destructive/90"
                    >
                      <Trash2 className="mr-1 h-4 w-4" /> Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <div>
        {Object.entries(BENEFIT_FIELDS).map(([section, fields]) => (
          <div key={section} className="mb-6">
            <h3 className="font-bold mb-2">
              {section.replace(/_/g, " ").toUpperCase()}
            </h3>
            {fields.map((field) => (
              <div key={field} className="mb-2 flex items-center">
                <label className="w-48">{field.replace(/_/g, " ")}</label>
                <input
                  className="border rounded px-2 py-1 flex-1"
                  value={formState[section]?.[field] || ""}
                  onChange={(e) =>
                    setFormState((prev) => ({
                      ...prev,
                      [section]: { ...prev[section], [field]: e.target.value },
                    }))
                  }
                />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
