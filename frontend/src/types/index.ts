// Define Document interface
export interface Document {
  id: string;
  name: string;
  status: string;
  uploadedBy: string;
  uploadType: string;
  dateModified: string;
  dateAdded: string;
}

// Define DocumentType interface based on usage in the Card
export interface DocumentType {
  id: string;
  title: string;
  uploaded: number;
  reviewPending: number;
  approved: number;
  setupRequired?: boolean; // Optional based on usage
  documents?: ApiDocument[]; // Added to support documents being returned with the type
}

// From Dashboard.tsx
export interface ApiDocument {
  id: string;
  name: string;
  status: string;
  date_added: string;
}

// From DocumentListView.tsx
export interface DocumentListViewProps {
  documentTypeName: string;
  documents: Document[]; // Uses Document from this file
  onBack: () => void;
  isLoading?: boolean;
  error?: string | null;
}

// From CreateDocumentTypeForm.tsx
export interface CreateDocumentTypeFormProps {
  initialDocumentTypeName: string | null;
  onCreate: (typeName: string, file: File | null, docId?: string) => void;
  onNavigateBack: () => void;
}

// From FieldSetupView.tsx
export interface FieldSetupViewProps {
  documentTypeName: string | null;
}

// From DataTableView.tsx
export interface DataTableViewProps {
  documentTypeName: string | null;
}

// From frontend/src/app/documents/[docId]/page.tsx
export interface Annotation {
  id: string;
  content: string;
  position: { x: number; y: number };
  type: "bounding_box";
  color: string;
  pageNumber: number;
  width: number;
  height: number;
}

export type AnnotationsByPage = {
  [key: string]: Annotation[];
};

export type ExtractionSection = Record<string, string>;

export type ExtractionData = Record<string, ExtractionSection>;

// For FieldSetupView
export type FieldType = "text" | "number" | "date" | "checkbox" | "select"; // Added select type

export interface Field {
  id: string;
  name: string;
  type: FieldType;
  isRequired?: boolean;
  options?: string[]; // For select type
}

export interface CreateDocumentTypeWorkflowProps {
  initialDocumentTypeName: string | null;
  onSuccess: (newlyCreatedType: DocumentType, documents?: Document[]) => void;
  onCancel: () => void;
}
