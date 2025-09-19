import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useDocumentState } from '../contexts/DocumentContext';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useRouter } from 'next/router';
import ErrorBoundary from '../components/Errors/ErrorBoundary';

const TranslationsPage: React.FC = () => {
  const { theme } = useTheme();
  const { documentId } = useDocumentState();
  const router = useRouter();

  const progressQuery = useQuery({
    queryKey: ['progress', documentId],
    queryFn: () => api.getProgress(documentId!),
    enabled: !!documentId,
    refetchInterval: 3000,
  });

  const testPage = useMutation({
    mutationFn: async (pageNumber: number) => api.translateTestPage(documentId!, pageNumber),
    onSuccess: (data, pageNumber) => {
      // Navigate to quick review view with translated sample
      router.push({ pathname: '/review', query: { documentId, page: pageNumber, preview: '1' } });
      // Optionally store sample in session storage so review can show it
      try { sessionStorage.setItem('pdftr.preview.sample', JSON.stringify(data)); } catch {}
    },
  });

  const pagesQuery = useQuery({
    queryKey: ['pages', documentId],
    queryFn: () => api.getDocumentPages(documentId!),
    enabled: !!documentId,
    refetchInterval: 3000,
  });

  const [pageInput, setPageInput] = React.useState('1');

  // Derive safe progress numbers to avoid undefined property reads
  const rawProgress: any = (progressQuery.data as any)?.progress || {};
  const completedPages = Number(rawProgress?.completed_pages || 0);
  const totalPages = Number(rawProgress?.total_pages || 0);
  const percentage = Number.isFinite(rawProgress?.percentage)
    ? Math.round(rawProgress.percentage)
    : (totalPages > 0 ? Math.round((completedPages / totalPages) * 100) : 0);

  return (
    <ErrorBoundary>
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <h1 className={`text-2xl font-semibold mb-4 ${theme.text}`}>Translations</h1>
      {!documentId ? (
        <p className={`${theme.textSecondary}`}>No current document. Go to Home to upload.</p>
      ) : (
        <div className={`${theme.cardBg} p-4 rounded-xl border border-gray-200/60 space-y-4`}>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={1}
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              className="px-3 py-2 border rounded-lg w-24"
            />
            <button
              onClick={() => testPage.mutate(parseInt(pageInput || '1', 10))}
              className="px-3 py-2 bg-gray-900 text-white rounded-lg text-sm"
            >
              Test Translate Page
            </button>
          </div>
          {testPage.isPending && <div className="text-sm text-gray-600">Translating sample...</div>}
          {testPage.isSuccess && (
            <div className="text-sm text-green-700">Sample translated. Check page list for status.</div>
          )}
          <div>
            {progressQuery.isLoading ? (
              <p className="text-gray-500">Loading progress...</p>
            ) : (
              <div className="text-sm text-gray-700">
                {completedPages}/{totalPages} pages • {percentage}%
              </div>
            )}
          </div>

          <div>
            <div className="font-medium mb-2">Pages</div>
            {pagesQuery.isLoading ? (
              <p className="text-gray-500">Loading pages...</p>
            ) : Array.isArray(pagesQuery.data) && pagesQuery.data.length ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {pagesQuery.data.map((p) => (
                  <div key={p.id} className="p-3 rounded-lg border border-gray-200/70">
                    <div className="flex items-center justify-between">
                      <div className="text-sm">Page {p.page_number}</div>
                      <div className="text-xs text-gray-500">{p.translation_status}</div>
                    </div>
                    <div className="mt-2 flex gap-2">
                      <button className="px-2 py-1 text-xs rounded bg-gray-900 text-white" onClick={() => testPage.mutate(p.page_number)}>
                        Test Translate
                      </button>
                      <button className="px-2 py-1 text-xs rounded border" onClick={() => router.push({ pathname: '/review', query: { documentId, page: p.page_number } })}>
                        Review
                      </button>
                    </div>
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
    </ErrorBoundary>
  );
};

export default TranslationsPage;
