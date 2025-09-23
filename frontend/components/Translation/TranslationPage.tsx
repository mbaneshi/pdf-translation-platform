import React, { useState, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useTranslation } from '../../contexts/TranslationContext';
import { useGlossary } from '../../contexts/GlossaryContext';
import { 
  DocumentArrowUpIcon, 
  PlayIcon, 
  StopIcon,
  DocumentArrowDownIcon,
  Cog6ToothIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

const TranslationPage: React.FC = () => {
  const { theme } = useTheme();
  const { 
    currentJob, 
    translationResult, 
    isLoading, 
    settings, 
    setSettings, 
    startTranslation,
    cancelTranslation 
  } = useTranslation();
  const { entries } = useGlossary();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      // In a real implementation, you would upload the file and get a document ID
      // For now, we'll simulate this
      setDocumentId(Math.floor(Math.random() * 1000));
    } else {
      alert('Please select a valid PDF file');
    }
  };

  const handleStartTranslation = async () => {
    if (!documentId) {
      toast.error('Please upload a PDF file first');
      return;
    }

    await startTranslation(documentId, settings);
  };

  const handleCancelTranslation = async () => {
    if (currentJob) {
      await cancelTranslation(currentJob.id);
    }
  };

  const handleExportTranslation = () => {
    if (translationResult) {
      const blob = new Blob([translationResult.translated_text], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'translation.txt';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  const getStatusIcon = () => {
    if (!currentJob) return null;
    
    switch (currentJob.status) {
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'processing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    if (!currentJob) return '';
    
    switch (currentJob.status) {
      case 'pending':
        return 'Translation queued...';
      case 'processing':
        return `Translating... ${currentJob.progress}%`;
      case 'completed':
        return 'Translation completed';
      case 'failed':
        return 'Translation failed';
      default:
        return '';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className={`text-3xl font-bold ${theme.text} mb-2`}>Translate PDF</h1>
        <p className={`${theme.textSecondary}`}>
          Upload a PDF document and translate it from English to Persian with AI-powered accuracy.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Translation Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Upload */}
          <div className={`${theme.cardBg} rounded-lg p-6 shadow-sm`}>
            <h2 className={`text-xl font-semibold ${theme.text} mb-4`}>Upload Document</h2>
            
            {!selectedFile ? (
              <div 
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className={`text-lg ${theme.text} mb-2`}>Drag and drop your PDF here</p>
                <p className={`${theme.textSecondary} mb-4`}>or click to browse files</p>
                <button className={`px-4 py-2 bg-gradient-to-r ${theme.primary} text-white rounded-lg hover:opacity-90 transition-all`}>
                  Choose File
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <DocumentArrowUpIcon className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className={`font-medium ${theme.text}`}>{selectedFile.name}</p>
                    <p className={`text-sm ${theme.textSecondary}`}>
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setDocumentId(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Translation Settings */}
          <div className={`${theme.cardBg} rounded-lg p-6 shadow-sm`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`text-xl font-semibold ${theme.text}`}>Translation Settings</h2>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <Cog6ToothIcon className="h-5 w-5" />
              </button>
            </div>

            {showSettings && (
              <div className="space-y-4 mb-6">
                <div>
                  <label className={`block text-sm font-medium ${theme.text} mb-2`}>
                    Target Language
                  </label>
                  <select
                    value={settings.target_language}
                    onChange={(e) => setSettings({ ...settings, target_language: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="persian">Persian (فارسی)</option>
                    <option value="arabic">Arabic (العربية)</option>
                    <option value="french">French (Français)</option>
                    <option value="spanish">Spanish (Español)</option>
                  </select>
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text} mb-2`}>
                    Translation Style
                  </label>
                  <select
                    value={settings.translation_style}
                    onChange={(e) => setSettings({ ...settings, translation_style: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="academic">Academic</option>
                    <option value="technical">Technical</option>
                    <option value="general">General</option>
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="use_glossary"
                    checked={settings.use_glossary}
                    onChange={(e) => setSettings({ ...settings, use_glossary: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="use_glossary" className={`ml-2 text-sm ${theme.text}`}>
                    Use glossary for consistency ({entries.length} terms available)
                  </label>
                </div>
              </div>
            )}

            {/* Translation Controls */}
            <div className="flex items-center space-x-4">
              {!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed' ? (
                <button
                  onClick={handleStartTranslation}
                  disabled={!selectedFile || isLoading}
                  className={`inline-flex items-center px-6 py-3 bg-gradient-to-r ${theme.primary} text-white rounded-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <PlayIcon className="h-5 w-5 mr-2" />
                  Start Translation
                </button>
              ) : (
                <button
                  onClick={handleCancelTranslation}
                  className="inline-flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all"
                >
                  <StopIcon className="h-5 w-5 mr-2" />
                  Cancel Translation
                </button>
              )}
            </div>
          </div>

          {/* Translation Status */}
          {currentJob && (
            <div className={`${theme.cardBg} rounded-lg p-6 shadow-sm`}>
              <h2 className={`text-xl font-semibold ${theme.text} mb-4`}>Translation Status</h2>
              
              <div className="flex items-center space-x-3 mb-4">
                {getStatusIcon()}
                <span className={`${theme.text}`}>{getStatusText()}</span>
              </div>

              {currentJob.status === 'processing' && (
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${currentJob.progress}%` }}
                  />
                </div>
              )}

              {currentJob.error_message && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800 text-sm">{currentJob.error_message}</p>
                </div>
              )}
            </div>
          )}

          {/* Translation Result */}
          {translationResult && (
            <div className={`${theme.cardBg} rounded-lg p-6 shadow-sm`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className={`text-xl font-semibold ${theme.text}`}>Translation Result</h2>
                <button
                  onClick={handleExportTranslation}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                  Export
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className={`${theme.textSecondary}`}>Quality Score: </span>
                    <span className={`font-medium ${theme.text}`}>
                      {translationResult.quality_score.toFixed(1)}/10
                    </span>
                  </div>
                  <div>
                    <span className={`${theme.textSecondary}`}>Consistency Score: </span>
                    <span className={`font-medium ${theme.text}`}>
                      {translationResult.consistency_score.toFixed(1)}/10
                    </span>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className={`whitespace-pre-wrap text-sm ${theme.text}`}>
                    {translationResult.translated_text}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Glossary Summary */}
          <div className={`${theme.cardBg} rounded-lg p-6 shadow-sm`}>
            <h3 className={`text-lg font-semibold ${theme.text} mb-4`}>Glossary</h3>
            <p className={`${theme.textSecondary} text-sm mb-4`}>
              {entries.length} terms available for consistent translation
            </p>
            <button
              onClick={() => window.location.href = '/glossary'}
              className={`w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors`}
            >
              Manage Glossary
            </button>
          </div>

          {/* Translation Tips */}
          <div className={`${theme.cardBg} rounded-lg p-6 shadow-sm`}>
            <h3 className={`text-lg font-semibold ${theme.text} mb-4`}>Translation Tips</h3>
            <ul className={`space-y-2 text-sm ${theme.textSecondary}`}>
              <li>• Use the glossary to maintain consistency</li>
              <li>• Academic style is best for research papers</li>
              <li>• Technical style for manuals and documentation</li>
              <li>• General style for everyday content</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranslationPage;
