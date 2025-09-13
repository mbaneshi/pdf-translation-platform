// API Types
export interface UploadResponse {
  message: string;
  document_id: number;
  uuid: string;
  total_pages?: number;
}

export interface Document {
  id: number;
  uuid: string;
  filename: string;
  status: string;
  total_pages: number;
  total_characters?: number;
  created_at: string;
}

export interface Page {
  id: number;
  page_number: number;
  char_count: number;
  translation_status: string;
  is_test_page: boolean;
  created_at: string;
}

export interface TranslationResult {
  translated_text: string;
  confidence: number;
  cost: number;
  processing_time?: number;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

// API Client Interface
export interface ApiClient {
  uploadDocument(file: File): Promise<UploadResponse>;
  getDocument(documentId: number): Promise<Document>;
  getDocumentPages(documentId: number): Promise<Page[]>;
  startTranslation(documentId: number): Promise<{ message: string; task_id: string }>;
  translateTestPage(documentId: number, pageNumber: number): Promise<TranslationResult>;
}

// Component Props
export interface FileUploadProps {
  onUploadSuccess: (result: UploadResponse) => void;
  onUploadError?: (error: { message: string; code?: string }) => void;
  maxSize?: number;
  acceptedTypes?: string[];
  disabled?: boolean;
}

export interface DocumentViewerProps {
  documentId: number | null;
}

// Utility Types
export type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';
export type TranslationStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type DocumentStatus = 'uploaded' | 'processing' | 'completed' | 'failed';
