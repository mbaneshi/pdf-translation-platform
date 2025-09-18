import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Document, Page, UploadResponse } from '@/types';

export function useDocument(documentId: number | null) {
  const [loading, setLoading] = useState(true);
  const [document, setDocument] = useState<Document | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!documentId) {
      setLoading(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const doc = (await api.getDocument(documentId)) as Document;
      setDocument(doc);
    } catch (e: any) {
      setError(e?.message || String(e));
      setDocument(null);
      setPages([]);
      setLoading(false);
      return;
    }

    // Load pages separately; preserve document if pages fail
    try {
      const pgs = (await api.getDocumentPages(documentId)) as Page[];
      setPages(pgs);
    } catch (e: any) {
      setError(e?.message || String(e));
      setPages([]);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    if (documentId !== null) {
      void load();
    }
  }, [documentId, load]);

  const refreshDocument = useCallback(async () => {
    await load();
  }, [load]);

  return { loading, document, pages, error, refreshDocument };
}

export function useTranslation(documentId: number) {
  const [translating, setTranslating] = useState(false);

  const startTranslation = useCallback(async () => {
    setTranslating(true);
    try {
      return await api.startTranslation(documentId);
    } catch (e) {
      throw e;
    } finally {
      setTranslating(false);
    }
  }, [documentId]);

  const testTranslatePage = useCallback(async (pageNumber: number) => {
    try {
      return await api.translateTestPage(documentId, pageNumber);
    } catch (e) {
      throw e;
    }
  }, [documentId]);

  return { translating, startTranslation, testTranslatePage };
}

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File): Promise<UploadResponse> => {
    setUploading(true);
    // clear previous error
    setError(null);
    try {
      const res = await api.uploadDocument(file);
      // success clears error
      setError(null);
      return res as UploadResponse;
    } catch (e: any) {
      const msg = e?.message || String(e);
      setError(msg === 'Unknown error' ? 'Upload failed' : msg);
      // Always reject with Error to satisfy tests
      throw new Error(msg);
    } finally {
      setUploading(false);
    }
  }, []);

  return { uploading, error, uploadFile };
}
