import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

const DocumentViewer = ({ documentId }) => {
  const [document, setDocument] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [translating, setTranslating] = useState(false);

  useEffect(() => {
    if (documentId) {
      loadDocument();
    }
  }, [documentId]);

  const loadDocument = async () => {
    try {
      const [docData, pagesData] = await Promise.all([
        api.getDocument(documentId),
        api.getDocumentPages(documentId)
      ]);
      setDocument(docData);
      setPages(pagesData);
    } catch (error) {
      toast.error('Failed to load document: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTranslation = async () => {
    setTranslating(true);
    try {
      await api.startTranslation(documentId);
      toast.success('Translation started! Check back later for progress.');
      // Refresh data after a delay
      setTimeout(loadDocument, 2000);
    } catch (error) {
      toast.error('Failed to start translation: ' + error.message);
    } finally {
      setTranslating(false);
    }
  };

  const handleTestTranslation = async (pageNumber) => {
    try {
      const result = await api.translateTestPage(documentId, pageNumber);
      toast.success(`Test translation completed for page ${pageNumber}`);
      loadDocument(); // Refresh to show updated status
    } catch (error) {
      // Handle specific error types with user-friendly messages
      let errorMessage = 'Test translation failed: ' + error.message;
      
      if (error.message.includes('quota exceeded')) {
        errorMessage = 'Translation service quota exceeded. Please check your OpenAI billing settings.';
      } else if (error.message.includes('authentication failed')) {
        errorMessage = 'Translation service authentication failed. Please check your OpenAI API key.';
      } else if (error.message.includes('temporarily unavailable')) {
        errorMessage = 'Translation service is temporarily unavailable. Please try again later.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Unable to connect to translation service. Please check your connection and try again.';
      }
      
      toast.error(errorMessage);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!document) {
    return <div className="text-center text-gray-500">Document not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Document Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">{document.filename}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium capitalize">{document.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Pages</p>
            <p className="font-medium">{document.total_pages}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Characters</p>
            <p className="font-medium">{document.total_characters?.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Uploaded</p>
            <p className="font-medium">{new Date(document.created_at).toLocaleDateString()}</p>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="mt-6 flex space-x-4">
          <button
            onClick={handleStartTranslation}
            disabled={translating || document.status === 'processing'}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {translating ? 'Starting...' : 'Start Full Translation'}
          </button>
        </div>
      </div>

      {/* Pages List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Pages</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {pages.map((page) => (
            <div key={page.id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                    {page.page_number}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Page {page.page_number}
                  </p>
                  <p className="text-sm text-gray-500">
                    {page.char_count} characters
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  page.translation_status === 'completed' ? 'bg-green-100 text-green-800' :
                  page.translation_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                  page.translation_status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {page.translation_status}
                </span>
                {page.is_test_page && (
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    Test Page
                  </span>
                )}
                <button
                  onClick={() => handleTestTranslation(page.page_number)}
                  disabled={page.translation_status === 'processing'}
                  className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50"
                >
                  Test Translate
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
