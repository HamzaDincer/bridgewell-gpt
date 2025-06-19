// Define Document interface
export interface Document {
  id: string;
  name: string;
  uploadedBy: string;
  uploadType: string;
  dateModified: string;
  dateAdded: string;
  phase?: string; // Add phase for granular status
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
  date_added: string;
  phase?: string;
}

// From DocumentListView.tsx
export interface DocumentListViewProps {
  documentTypeName: string;
  documents: Document[]; // Uses Document from this file
  onBack: () => void;
  isLoading?: boolean;
  error?: string | null;
  onUpload?: () => void;
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
  type: string;
  color: string;
  pageNumber: number;
  width: number;
  height: number;
}

export interface AnnotationsByPage {
  [pageNumber: string]: Annotation[];
}

export interface ExtractionField {
  value: string;
  page: number | null;
  coordinates?: {
    x: number | null;
    y: number | null;
    width: number | null;
    height: number | null;
  } | null;
  source_snippet: string;
  bbox?: { l: number; t: number; r: number; b: number }[]; // Optional bbox for backend compatibility
}

export interface ExtractionResult {
  extraction_id: string;
  document_type: string;
  file_name: string;
  status: string;
  result: {
    [key: string]: ExtractionField;
  };
  timestamp: string;
}

export type ExtractionData = Record<string, ExtractionField>;

// Document deletion types
export interface DocumentDeletionResponse {
  doc_id: string;
  status: "success" | "partial_success" | "error";
  deleted_components: string[];
  errors?: string[];
  warnings?: string[];
}

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
