import React, { useState } from 'react';
import FileUpload from '../components/FileUpload';
import DocumentViewer from '../components/DocumentViewer';
import { Toaster } from 'react-hot-toast';

export default function Home() {
  const [currentDocument, setCurrentDocument] = useState(null);

  const handleUploadSuccess = (result) => {
    setCurrentDocument(result);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                PDF Translation Platform
              </h1>
              <p className="text-gray-600">
                Upload PDFs and translate them from English to Persian
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!currentDocument ? (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Upload Your PDF Document
              </h2>
              <p className="text-gray-600">
                Select a PDF file to begin the translation process
              </p>
            </div>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        ) : (
          <DocumentViewer documentId={currentDocument.document_id} />
        )}
      </main>
    </div>
  );
}
