// Enhanced Document Viewer with ReviewPanel and SmartProgressHeader
import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { StyledThemeProviderWrapper } from '../contexts/StyledThemeProvider';
import { ReviewPanel } from '../src/components/ReviewPanel';
import { SmartProgressHeader } from '../src/components/SmartProgressHeader';
import { api } from '../lib/api';
import { PDFIcon, ProcessIcon, CheckIcon, LoadingIcon } from './Icons';
import toast from 'react-hot-toast';

interface PageData {
  id: number;
  page_number: number;
  original_text: string;
  translated_text: string | null;
  translation_status: 'pending' | 'processing' | 'completed' | 'error';
  quality_score?: number;
  tokens_used?: number;
  cost?: number;
  char_count?: number;
  tokens_in?: number;
  tokens_out?: number;
  cost_estimate?: number;
  is_test_page?: boolean;
}

interface DocumentData {
  id: number;
  filename: string;
  total_pages: number;
  status: string;
  created_at: string;
  total_characters?: number;
  file_size_bytes?: number;
}

interface EnhancedDocumentViewerProps {
  documentId: string | number;
  useEnhancedMode?: boolean;
}

const EnhancedDocumentViewer: React.FC<EnhancedDocumentViewerProps> = ({
  documentId,
  useEnhancedMode = true
}) => {
  const [documentData, setDocumentData] = useState<DocumentData | null>(null);
  const [pages, setPages] = useState<PageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [translating, setTranslating] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [showReviewPanel, setShowReviewPanel] = useState(false);
  const [progressPaused, setProgressPaused] = useState(false);
  const { theme } = useTheme();

  // Load document and pages data
  const loadDocument = useCallback(async () => {
    try {
      const [docData, pagesData] = await Promise.all([
        api.getDocument(documentId as any),
        api.getDocumentPages(documentId as any)
      ]);
      setDocumentData(docData);
      setPages(pagesData as unknown as PageData[]);

      // Show review panel if any page has translation
      const hasTranslations = (pagesData as unknown as PageData[]).some((page: PageData) => page.translated_text);
      setShowReviewPanel(hasTranslations);

    } catch (error: any) {
      toast.error('Failed to load document: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    if (documentId) {
      loadDocument();
    }
  }, [documentId, loadDocument]);

  // Handle translation workflow
  const handleStartTranslation = useCallback(async () => {
    setTranslating(true);
    try {
      if (useEnhancedMode) {
        await (api as any).startGradualTranslation(documentId as any);
        toast.success('Enhanced translation started! Progress will be tracked in real-time.');
      } else {
        await api.startTranslation(documentId as any);
        toast.success('Translation started! Check back later for progress.');
      }

      // Refresh data and show progress header
      setTimeout(loadDocument, 2000);
    } catch (error: any) {
      toast.error('Failed to start translation: ' + error.message);
    } finally {
      setTranslating(false);
    }
  }, [documentId, useEnhancedMode, loadDocument]);

  // Handle sample translation
  const handleSampleTranslation = useCallback(async (pageNumber: number) => {
    try {
      await (api as any).translateSample(documentId as any, pageNumber);
      toast.success(`Sample translation completed for page ${pageNumber}`);
      loadDocument(); // Refresh to show updated status
    } catch (error: any) {
      toast.error('Sample translation failed: ' + error.message);
    }
  }, [documentId, loadDocument]);

  // Review panel handlers
  const handlePageApprove = useCallback(async (pageId: number) => {
    try {
      await (api as any).approvePage(pageId);
      toast.success('Translation approved');
      loadDocument();
    } catch (error: any) {
      toast.error('Failed to approve: ' + error.message);
    }
  }, [loadDocument]);

  const handlePageReject = useCallback(async (pageId: number) => {
    try {
      await (api as any).rejectPage(pageId);
      toast.success('Translation rejected');
      loadDocument();
    } catch (error: any) {
      toast.error('Failed to reject: ' + error.message);
    }
  }, [loadDocument]);

  const handleEditTranslation = useCallback(async (pageId: number, newText: string) => {
    try {
      await (api as any).updatePageTranslation(pageId, newText);
      toast.success('Translation updated');
      loadDocument();
    } catch (error: any) {
      toast.error('Failed to update translation: ' + error.message);
    }
  }, [loadDocument]);

  // Progress handling
  const handleProgressUpdate = useCallback((progress: any) => {
    // Update pages based on progress if needed
    if (progress.status === 'completed') {
      loadDocument();
    }
  }, [loadDocument]);

  const handleTranslationComplete = useCallback(() => {
    toast.success('Translation completed successfully!');
    setShowReviewPanel(true);
    loadDocument();
  }, [loadDocument]);

  const handleProgressError = useCallback((error: string) => {
    toast.error('Translation progress error: ' + error);
  }, []);

  const handleTogglePause = useCallback(() => {
    setProgressPaused(!progressPaused);
    toast(progressPaused ? 'Translation resumed' : 'Translation paused');
  }, [progressPaused]);

  // Export functionality
  const handleExportMarkdown = useCallback(async () => {
    try {
      const res = await (api as any).exportMarkdown(documentId as any);
      const content = res?.content || '';
      const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      const safeName = (documentData?.filename || `document-${documentId}`).replace(/\s+/g, '_').replace(/[^\w\.-]/g, '');
      a.href = url;
      a.download = `${safeName}.md`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Markdown exported');
    } catch (error: any) {
      toast.error('Failed to export Markdown: ' + (error.message || 'Unknown error'));
    }
  }, [documentId, document]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="text-center space-y-4">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <PDFIcon className="w-8 h-8 text-blue-600" />
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
          <PDFIcon className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Document not found</h3>
        <p className="text-gray-500">The requested document could not be loaded.</p>
      </div>
    );
  }

  return (
    <StyledThemeProviderWrapper>
      <div className="space-y-8">
        {/* Progress Header - Show during translation */}
        {(documentData?.status === 'processing' || translating) && useEnhancedMode && (
          <SmartProgressHeader
            documentId={documentId as string}
            onProgressUpdate={handleProgressUpdate}
            onComplete={handleTranslationComplete}
            onError={handleProgressError}
            isPaused={progressPaused}
            onTogglePause={handleTogglePause}
            showAdvancedMetrics={true}
          />
        )}

        {/* Document Info Card */}
        <div className={`${theme.cardBg} backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8`}>
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className={`w-12 h-12 bg-gradient-to-r ${theme.primary} rounded-xl flex items-center justify-center shadow-lg`}>
                <PDFIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h2 className={`text-2xl font-bold ${theme.text} mb-1 truncate max-w-2xl`} title={documentData?.filename}>
                  {documentData?.filename}
                </h2>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    documentData?.status === 'completed' ? 'bg-green-100 text-green-800' :
                    documentData?.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    documentData?.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    <div className={`w-2 h-2 rounded-full mr-2 ${
                      documentData?.status === 'completed' ? 'bg-green-400' :
                      documentData?.status === 'processing' ? 'bg-yellow-400 animate-pulse' :
                      documentData?.status === 'failed' ? 'bg-red-400' :
                      'bg-gray-400'
                    }`}></div>
                    {documentData?.status}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Document Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 bg-gradient-to-r ${theme.primary} rounded-lg flex items-center justify-center`}>
                  <PDFIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-sm text-blue-600 font-medium">Total Pages</p>
                  <p className="text-xl font-bold text-blue-900">{documentData?.total_pages}</p>
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
                  <p className="text-xl font-bold text-cyan-900">
                    {documentData?.total_characters ? documentData.total_characters.toLocaleString() : 'Processing...'}
                  </p>
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
                  <p className="text-lg font-bold text-teal-900">{new Date(documentData?.created_at || '').toLocaleDateString()}</p>
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
                  <p className="text-lg font-bold text-green-900">
                    {documentData?.file_size_bytes
                      ? `${(documentData.file_size_bytes / 1024 / 1024).toFixed(1)} MB`
                      : 'Processing...'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap space-x-4 gap-y-2">
            <button
              onClick={handleStartTranslation}
              disabled={translating || documentData?.status === 'processing'}
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
                    <span>{useEnhancedMode ? 'Start Enhanced Translation' : 'Start Translation'}</span>
                  </>
                )}
              </div>
            </button>

            <button
              onClick={handleExportMarkdown}
              className="group relative bg-white text-gray-800 px-6 py-3 rounded-xl font-semibold shadow hover:shadow-md ring-1 ring-gray-200 hover:ring-gray-300 transition-all"
            >
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1M7 10l5 5m0 0l5-5m-5 5V4" />
                </svg>
                <span>Download Markdown</span>
              </div>
            </button>

            {pages.length > 0 && (
              <button
                onClick={() => setShowReviewPanel(!showReviewPanel)}
                className={`group relative px-6 py-3 rounded-xl font-semibold transition-all ${
                  showReviewPanel
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <span>{showReviewPanel ? 'Hide Review Panel' : 'Show Review Panel'}</span>
                </div>
              </button>
            )}
          </div>
        </div>

        {/* Review Panel */}
        {showReviewPanel && pages.length > 0 && (
          <ReviewPanel
            pages={pages}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
            onApprove={handlePageApprove}
            onReject={handlePageReject}
            onEditTranslation={handleEditTranslation}
            isLoading={translating}
          />
        )}

        {/* Legacy Pages List - Show when review panel is hidden */}
        {!showReviewPanel && (
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
              {pages.map((page) => (
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
                            <span>
                              {page.char_count ? page.char_count.toLocaleString() : 'Processing'} characters
                            </span>
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
                        page.translation_status === 'error' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          page.translation_status === 'completed' ? 'bg-green-400' :
                          page.translation_status === 'processing' ? 'bg-yellow-400 animate-pulse' :
                          page.translation_status === 'error' ? 'bg-red-400' :
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
                        onClick={() => handleSampleTranslation(page.page_number)}
                        disabled={page.translation_status === 'processing'}
                        className="group/btn inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-medium rounded-lg shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                      >
                        <svg className="w-4 h-4 mr-2 group-hover/btn:animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        {useEnhancedMode ? 'Sample Translate' : 'Test Translate'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </StyledThemeProviderWrapper>
  );
};

export default EnhancedDocumentViewer;