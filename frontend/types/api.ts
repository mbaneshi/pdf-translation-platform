// Shared API contracts to enforce type-safety across the app

export interface UploadResponse {
  message: string;
  document_id: number;
}

export interface DocumentSummary {
  id: number;
  filename: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export interface PageInfo {
  id: number;
  document_id: number;
  page_number: number;
  text_content?: string;
  translation?: string;
}

export interface DocumentDetail {
  id: number;
  filename: string;
  status: string;
  total_pages?: number;
}

