import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useDocumentState } from '../contexts/DocumentContext';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

const HistoryPage: React.FC = () => {
  const { theme } = useTheme();
  const { documentId } = useDocumentState();
  const docQuery = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => api.getDocument(documentId!),
    enabled: !!documentId,
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <h1 className={`text-2xl font-semibold mb-4 ${theme.text}`}>History</h1>
      {!documentId ? (
        <p className={`${theme.textSecondary}`}>No recent activity. Upload a document first.</p>
      ) : docQuery.data ? (
        <div className={`${theme.cardBg} p-4 rounded-xl border border-gray-200/60`}>
          <div className="font-medium">Last document</div>
          <div className="text-sm text-gray-700">{docQuery.data.filename}</div>
          <div className="text-xs text-gray-500">Created: {new Date(docQuery.data.created_at).toLocaleString()}</div>
          <div className="text-xs text-gray-500">Status: {docQuery.data.status}</div>
        </div>
      ) : (
        <p className="text-gray-500">Loading...</p>
      )}
    </motion.div>
  );
};

export default HistoryPage;
