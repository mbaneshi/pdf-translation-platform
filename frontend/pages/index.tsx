import React, { useEffect, useState } from 'react';
import FileUpload from '../components/FileUpload';
import DocumentViewer from '../components/DocumentViewer';
import EnhancedDocumentViewer from '../components/EnhancedDocumentViewer';
import OnboardingModal from '../components/Onboarding/OnboardingModal';
import { useTheme } from '../contexts/ThemeContext';
import { PDFIcon, TranslationIcon } from '../components/Icons';
import { Toaster } from 'react-hot-toast';
import type { UploadResponse } from '../types/api';
import { useDocumentState } from '../contexts/DocumentContext';

const Home: React.FC = () => {
  const { documentId, setDocumentId, useEnhancedMode, setUseEnhancedMode, setUploadMeta } = useDocumentState();
  const [currentDocument, setCurrentDocument] = useState<UploadResponse | null>(null);
  const { theme } = useTheme();

  const handleUploadSuccess = (result: UploadResponse) => {
    setCurrentDocument(result);
    setDocumentId(result.document_id);
    // capture quick meta for UX (fields present on enhanced upload response)
    if ((result as any)?.total_pages !== undefined || (result as any)?.file_size_bytes !== undefined) {
      setUploadMeta({
        total_pages: (result as any).total_pages,
        file_size_bytes: (result as any).file_size_bytes,
      });
    }
  };

  useEffect(() => {
    if (documentId && !currentDocument) {
      // Minimal hydration to allow viewer when returning to Home
      setCurrentDocument({ message: 'Restored', document_id: documentId });
    }
  }, [documentId]);

  return (
    <div className={`min-h-screen`}>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
            borderRadius: '12px',
            padding: '16px',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow:
              '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          },
        }}
      />

      <OnboardingModal />

      <header className={`${theme.cardBg} backdrop-blur-md shadow-lg border-b border-white/20 rounded-xl p-4`}> 
        <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className={`w-12 h-12 bg-gradient-to-r ${theme.primary} rounded-xl flex items-center justify-center shadow-lg`}>
                <PDFIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className={`text-2xl font-bold bg-gradient-to-r ${theme.primary} bg-clip-text text-transparent`}>
                  PDF Translation Platform
                </h1>
                <p className={`${theme.textSecondary} hidden sm:block`}>
                  AI-powered English to Persian translation
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setUseEnhancedMode(!useEnhancedMode)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
                  useEnhancedMode
                    ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {useEnhancedMode ? 'Enhanced Mode' : 'Legacy Mode'}
              </button>
              {currentDocument && (
                <button
                  onClick={() => {
                    setCurrentDocument(null);
                    setDocumentId(null);
                    setUploadMeta({});
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium transition-all"
                >
                  New Document
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <section className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-6">
        {!currentDocument ? (
          <div className="space-y-8">
            <div className="text-center space-y-4">
              <div className={`inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r ${theme.primary} rounded-2xl shadow-xl`}>
                <TranslationIcon className="w-10 h-10 text-white" />
              </div>
              <div>
                <h2 className={`text-3xl font-bold ${theme.text} mb-3`}>Upload Your PDF Document</h2>
                <p className={`text-lg ${theme.textSecondary} max-w-2xl mx-auto`}>
                  Select a PDF to begin translation from English to Persian.
                </p>
              </div>
            </div>
            <FileUpload onUploadSuccess={handleUploadSuccess} useEnhancedMode={useEnhancedMode} />
          </div>
        ) : useEnhancedMode ? (
          <EnhancedDocumentViewer documentId={currentDocument.document_id} useEnhancedMode={useEnhancedMode} />
        ) : (
          <DocumentViewer documentId={currentDocument.document_id} />
        )}
      </section>
    </div>
  );
};

export default Home;
