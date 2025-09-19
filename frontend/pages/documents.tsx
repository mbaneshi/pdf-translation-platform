import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useDocumentState } from '../contexts/DocumentContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

const DocumentsPage: React.FC = () => {
  const { theme } = useTheme();
  const { documentId } = useDocumentState();
  const qc = useQueryClient();

  const docQuery = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => api.getDocument(documentId!),
    enabled: !!documentId,
    refetchOnWindowFocus: false,
  });

  const pagesQuery = useQuery({
    queryKey: ['pages', documentId],
    queryFn: () => api.getDocumentPages(documentId!),
    enabled: !!documentId,
    refetchInterval: 3000,
  });

  const startTranslation = useMutation({
    mutationFn: () => api.startTranslation(documentId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['progress', documentId] }),
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <h1 className={`text-2xl font-semibold mb-4 ${theme.text}`}>Documents</h1>
      {!documentId ? (
        <p className={`${theme.textSecondary}`}>No current document. Go to Home to upload.</p>
      ) : (
        <div className="space-y-6">
          {docQuery.isLoading ? (
            <p className={theme.textSecondary}>Loading document...</p>
          ) : docQuery.data ? (
            <div className={`${theme.cardBg} p-4 rounded-xl border border-gray-200/60`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{docQuery.data.filename}</div>
                  <div className="text-sm text-gray-500">
                    Status: {docQuery.data.status} • Pages: {docQuery.data.total_pages ?? '—'} • Characters: {docQuery.data.total_characters ?? '—'}
                  </div>
                </div>
                <button
                  onClick={() => startTranslation.mutate()}
                  className="px-3 py-2 bg-gray-900 text-white rounded-lg text-sm"
                >
                  Start Translation
                </button>
              </div>
            </div>
          ) : null}

          <div className={`${theme.cardBg} p-4 rounded-xl border border-gray-200/60`}>
            <div className="font-medium mb-2">Pages</div>
            {pagesQuery.isLoading ? (
              <p className="text-gray-500">Loading pages...</p>
            ) : pagesQuery.data && pagesQuery.data.length ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {pagesQuery.data.map((p) => (
                  <div key={p.id} className="p-3 rounded-lg border border-gray-200/70">
                    <div className="flex items-center justify-between">
                      <div className="text-sm">Page {p.page_number}</div>
                      <div className="text-xs text-gray-500">{p.translation_status}</div>
                    </div>
                    {p.is_test_page ? (<div className="text-xs text-green-600 mt-1">Tested</div>) : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No pages yet.</p>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default DocumentsPage;
