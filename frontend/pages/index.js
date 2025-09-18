import React, { useState } from 'react';
import FileUpload from '../components/FileUpload';
import DocumentViewer from '../components/DocumentViewer';
import ThemeSelector from '../components/ThemeSelector';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';
import { PDFIcon, TranslationIcon } from '../components/Icons';
import { Toaster } from 'react-hot-toast';

const AppContent = () => {
  const [currentDocument, setCurrentDocument] = useState(null);
  const { theme } = useTheme();

  const handleUploadSuccess = (result) => {
    setCurrentDocument(result);
  };

  return (
    <div className={`min-h-screen ${theme.background}`}>
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
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
      
      {/* Header */}
      <header className={`${theme.cardBg} backdrop-blur-md shadow-lg border-b border-white/20`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-8">
            <div className="flex items-center space-x-4">
              <div className={`w-12 h-12 bg-gradient-to-r ${theme.primary} rounded-xl flex items-center justify-center shadow-lg`}>
                <PDFIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className={`text-3xl font-bold bg-gradient-to-r ${theme.primary} bg-clip-text text-transparent`}>
                  PDF Translation Platform
                </h1>
                <p className={`${theme.textSecondary} mt-1`}>
                  Transform your documents with AI-powered English to Persian translation
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>Service Online</span>
              </div>
              <ThemeSelector />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!currentDocument ? (
          <div className="space-y-8">
            <div className="text-center space-y-4">
              <div className={`inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r ${theme.primary} rounded-2xl shadow-xl`}>
                <TranslationIcon className="w-10 h-10 text-white" />
              </div>
              <div>
                <h2 className={`text-4xl font-bold ${theme.text} mb-3`}>
                  Upload Your PDF Document
                </h2>
                <p className={`text-xl ${theme.textSecondary} max-w-2xl mx-auto`}>
                  Select a PDF file to begin the intelligent translation process. 
                  Our AI will analyze and translate your document from English to Persian.
                </p>
              </div>
            </div>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        ) : (
          <DocumentViewer documentId={currentDocument.document_id} />
        )}
      </main>
    </div>
  );
};

export default function Home() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
