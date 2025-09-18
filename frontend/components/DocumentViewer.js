import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';
import { PDFIcon, ProcessIcon, CheckIcon, LoadingIcon } from './Icons';
import toast from 'react-hot-toast';

const DocumentViewer = ({ documentId }) => {
  const [document, setDocument] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [translating, setTranslating] = useState(false);
  const [progress, setProgress] = useState(null);
  const [polling, setPolling] = useState(false);
  const { theme } = useTheme();

  useEffect(() => {
    if (documentId) {
      loadDocument();
      startPolling();
    }
    return stopPolling;
  }, [documentId]);

  const startPolling = () => {
    if (polling) return;
    setPolling(true);
    const id = setInterval(async () => {
      try {
        const p = await api.getProgress(documentId);
        setProgress(p);
        const pagesData = await api.getDocumentPages(documentId);
        setPages(pagesData);
      } catch (e) {}
    }, 3000);
    if (typeof window !== 'undefined') window.__docPoll = id;
  };

  const stopPolling = () => {
    if (typeof window !== 'undefined' && window.__docPoll) {
      clearInterval(window.__docPoll);
      delete window.__docPoll;
    }
    setPolling(false);
  };

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
      <div className="flex justify-center items-center h-96">
        <div className="text-center space-y-4">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="text-gray-600 font-medium">Loading document...</div>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Document not found</h3>
        <p className="text-gray-500">The requested document could not be loaded.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Document Info Card */}
      <div className={`${theme.cardBg} backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8`}>
        <div className="flex items-start justify-between mb-6">
        <div className="flex items-center space-x-4">
            <div className={`w-12 h-12 bg-gradient-to-r ${theme.primary} rounded-xl flex items-center justify-center shadow-lg`}>
              <PDFIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 className={`text-2xl font-bold ${theme.text} mb-1 truncate max-w-2xl`} title={document.filename}>
                {document.filename}
              </h2>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  document.status === 'completed' ? 'bg-green-100 text-green-800' :
                  document.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                  document.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    document.status === 'completed' ? 'bg-green-400' :
                    document.status === 'processing' ? 'bg-yellow-400 animate-pulse' :
                    document.status === 'failed' ? 'bg-red-400' :
                    'bg-gray-400'
                  }`}></div>
                  {document.status}
                </span>
              </div>
            </div>
          </div>
        </div>
        {progress && (
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-sm text-gray-500">Progress</div>
              <div className="text-xl font-semibold text-gray-900">{Math.round(progress.progress_percentage || 0)}%</div>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-sm text-gray-500">Tokens (in/out)</div>
              <div className="text-xl font-semibold text-gray-900">{(progress.tokens_in_total||0).toLocaleString()} / {(progress.tokens_out_total||0).toLocaleString()}</div>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-sm text-gray-500">Pages Cost (USD)</div>
              <div className="text-xl font-semibold text-gray-900">${(progress.pages_cost_total||0).toFixed(4)}</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 bg-gradient-to-r ${theme.primary} rounded-lg flex items-center justify-center`}>
                <PDFIcon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm text-blue-600 font-medium">Total Pages</p>
                <p className="text-xl font-bold text-blue-900">{document.total_pages}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-cyan-50 to-teal-100 rounded-xl p-4 border border-cyan-200">
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 bg-gradient-to-r ${theme.secondary} rounded-lg flex items-center justify-center`}>
                <ProcessIcon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm text-cyan-600 font-medium">Characters</p>
                <p className="text-xl font-bold text-cyan-900">{document.total_characters?.toLocaleString()}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-teal-50 to-emerald-100 rounded-xl p-4 border border-teal-200">
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 bg-gradient-to-r ${theme.accent} rounded-lg flex items-center justify-center`}>
                <CheckIcon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm text-teal-600 font-medium">Uploaded</p>
                <p className="text-lg font-bold text-teal-900">{new Date(document.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-green-600 font-medium">File Size</p>
                <p className="text-lg font-bold text-green-900">{Math.round(document.file_size_bytes / 1024 / 1024)} MB</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button
            onClick={handleStartTranslation}
            disabled={translating || document.status === 'processing'}
            className={`group relative bg-gradient-to-r ${theme.primary} text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
          >
            <div className="flex items-center space-x-2">
              {translating ? (
                <>
                  <LoadingIcon className="w-4 h-4 text-white" />
                  <span>Starting Translation...</span>
                </>
              ) : (
                <>
                  <ProcessIcon className="w-5 h-5 text-white" />
                  <span>Start Full Translation</span>
                </>
              )}
            </div>
          </button>
        </div>
      </div>

      {/* Pages List */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-gray-600 to-gray-700 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900">Document Pages</h3>
            <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
              {pages.length} pages
            </span>
          </div>
        </div>
        
        <div className="divide-y divide-gray-100">
          {pages.map((page, index) => (
            <div key={page.id} className="px-6 py-5 hover:bg-gray-50 transition-colors duration-200 group">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow duration-200">
                      <span className="text-white font-bold text-sm">{page.page_number}</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                      Page {page.page_number}
                    </p>
                    <div className="flex items-center space-x-6 text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                        </svg>
                        <span>{page.char_count.toLocaleString()} characters</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c1.657 0 3-1.343 3-3S13.657 5 12 5 9 6.343 9 8s1.343 3 3 3z M19.4 15a1 1 0 00-.894-.553H5.494a1 1 0 00-.9.555l-1.5 3A1 1 0 004 19h16a1 1 0 00.9-1.445L19.4 15z" />
                        </svg>
                        <span>{(page.tokens_in||0).toLocaleString()} / {(page.tokens_out||0).toLocaleString()} tokens</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-2.21 0-4 1.79-4 4v6h8v-6c0-2.21-1.79-4-4-4z" />
                        </svg>
                        <span>${(page.cost_estimate||0).toFixed(4)}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    page.translation_status === 'completed' ? 'bg-green-100 text-green-800' :
                    page.translation_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    page.translation_status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    <div className={`w-2 h-2 rounded-full mr-2 ${
                      page.translation_status === 'completed' ? 'bg-green-400' :
                      page.translation_status === 'processing' ? 'bg-yellow-400 animate-pulse' :
                      page.translation_status === 'failed' ? 'bg-red-400' :
                      'bg-gray-400'
                    }`}></div>
                    {page.translation_status}
                  </span>
                  
                  {page.is_test_page && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Test Page
                    </span>
                  )}
                  
                  <button
                    onClick={() => handleTestTranslation(page.page_number)}
                    disabled={page.translation_status === 'processing'}
                    className="group/btn inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-medium rounded-lg shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <svg className="w-4 h-4 mr-2 group-hover/btn:animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Test Translate
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
