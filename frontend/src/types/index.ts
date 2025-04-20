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
  id: number; // Or string, depending on how you generate it
  title: string;
  uploaded: number;
  reviewPending: number;
  approved: number;
  setupRequired?: boolean; // Optional based on usage
}
