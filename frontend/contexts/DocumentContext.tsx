import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

interface UploadMeta {
  total_pages?: number;
  file_size_bytes?: number;
}

interface DocumentState {
  documentId: number | null;
  useEnhancedMode: boolean;
  uploadMeta?: UploadMeta | null;
}

interface DocumentContextType extends DocumentState {
  setDocumentId: (id: number | null) => void;
  setUseEnhancedMode: (v: boolean) => void;
  setUploadMeta: (m: UploadMeta | null) => void;
  reset: () => void;
}

const STORAGE_KEY = 'pdftr.current';

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export const useDocumentState = (): DocumentContextType => {
  const ctx = useContext(DocumentContext);
  if (!ctx) throw new Error('useDocumentState must be used within DocumentProvider');
  return ctx;
};

export const DocumentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [useEnhancedMode, setUseEnhancedMode] = useState<boolean>(true);
  const [uploadMeta, setUploadMeta] = useState<UploadMeta | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed: DocumentState = JSON.parse(raw);
        setDocumentId(parsed.documentId ?? null);
        setUseEnhancedMode(parsed.useEnhancedMode ?? true);
        setUploadMeta(parsed.uploadMeta ?? null);
      }
    } catch {}
  }, []);

  useEffect(() => {
    const state: DocumentState = { documentId, useEnhancedMode, uploadMeta };
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
  }, [documentId, useEnhancedMode, uploadMeta]);

  const value = useMemo<DocumentContextType>(() => ({
    documentId,
    useEnhancedMode,
    setDocumentId,
    setUseEnhancedMode,
    setUploadMeta,
    reset: () => { setDocumentId(null); setUseEnhancedMode(true); setUploadMeta(null); },
  }), [documentId, useEnhancedMode, uploadMeta]);

  return (
    <DocumentContext.Provider value={value}>{children}</DocumentContext.Provider>
  );
};
