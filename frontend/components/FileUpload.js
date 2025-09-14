import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { api } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';
import { UploadIcon, LoadingIcon } from './Icons';
import toast from 'react-hot-toast';

const FileUpload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [lastError, setLastError] = useState(null);
  const { theme } = useTheme();

  const logError = (error, context = '') => {
    console.error(`[FileUpload] ${context}:`, {
      error: error.message,
      stack: error.stack,
      name: error.name,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Clear previous error
    setLastError(null);

    // Enhanced file validation
    if (!file.name.endsWith('.pdf')) {
      const errorMsg = 'Only PDF files are allowed';
      toast.error(errorMsg);
      setLastError({ type: 'validation', message: errorMsg, details: { filename: file.name } });
      return;
    }

    // Check file size (100MB limit)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      const errorMsg = `File too large. Maximum size is ${Math.round(maxSize / 1024 / 1024)}MB`;
      toast.error(errorMsg);
      setLastError({ 
        type: 'validation', 
        message: errorMsg, 
        details: { 
          filename: file.name, 
          fileSize: file.size, 
          maxSize: maxSize 
        } 
      });
      return;
    }

    // Check if file is empty
    if (file.size === 0) {
      const errorMsg = 'File is empty';
      toast.error(errorMsg);
      setLastError({ 
        type: 'validation', 
        message: errorMsg, 
        details: { filename: file.name } 
      });
      return;
    }

    console.log('[FileUpload] Starting upload:', {
      filename: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified
    });

    setUploading(true);
    try {
      const result = await api.uploadDocument(file);
      console.log('[FileUpload] Upload successful:', result);
      toast.success('File uploaded successfully!');
      onUploadSuccess(result);
    } catch (error) {
      logError(error, 'Upload failed');
      
      // Enhanced error handling with detailed information
      let errorMessage = 'Upload failed';
      let errorDetails = {};

      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        // Network/CORS error
        errorMessage = 'Network error: Unable to connect to server';
        errorDetails = {
          type: 'network',
          originalError: error.message,
          possibleCauses: [
            'Server is down',
            'CORS configuration issue',
            'Network connectivity problem',
            'API endpoint not accessible'
          ]
        };
      } else if (error.message.includes('413')) {
        // File too large
        errorMessage = 'File too large for upload';
        errorDetails = {
          type: 'file_size',
          originalError: error.message
        };
      } else if (error.message.includes('415')) {
        // Unsupported media type
        errorMessage = 'Unsupported file type';
        errorDetails = {
          type: 'file_type',
          originalError: error.message
        };
      } else if (error.message.includes('500')) {
        // Server error
        errorMessage = 'Server error occurred during upload';
        errorDetails = {
          type: 'server_error',
          originalError: error.message
        };
      } else {
        // Generic error
        errorMessage = error.message || 'Unknown error occurred';
        errorDetails = {
          type: 'unknown',
          originalError: error.message,
          stack: error.stack
        };
      }

      setLastError({
        type: errorDetails.type,
        message: errorMessage,
        details: errorDetails,
        timestamp: new Date().toISOString()
      });

      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  return (
    <div className="space-y-6">
      <div
        {...getRootProps()}
        className={`group relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ease-in-out transform hover:scale-[1.02] ${
          isDragActive
            ? `border-blue-500 bg-gradient-to-br ${theme.background} shadow-xl scale-[1.02]`
            : 'border-gray-300 hover:border-blue-400 hover:bg-gradient-to-br hover:from-blue-50 hover:to-indigo-50'
        } ${uploading ? 'opacity-50 pointer-events-none' : 'hover:shadow-lg'}`}
      >
        <input {...getInputProps()} />
        <div className="space-y-6">
          <div className="mx-auto w-16 h-16 text-gray-400 group-hover:text-blue-500 transition-colors duration-300">
            {uploading ? (
              <LoadingIcon className="w-16 h-16 text-blue-600" />
            ) : (
              <UploadIcon className="w-16 h-16" />
            )}
          </div>
          {uploading ? (
            <div className="space-y-3">
              <div className="text-gray-700 font-medium text-lg">
                Uploading your document...
              </div>
              <div className="text-sm text-gray-500">
                Please wait while we process your PDF
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-2xl font-semibold text-gray-900 group-hover:text-blue-700 transition-colors duration-300">
                {isDragActive ? 'Drop your PDF here' : 'Drag & drop your PDF file'}
              </p>
              <p className="text-lg text-gray-500 group-hover:text-blue-600 transition-colors duration-300">
                or click to browse files
              </p>
              <div className="flex items-center justify-center space-x-6 text-sm text-gray-400 mt-4">
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>PDF format only</span>
                </div>
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Max 100MB</span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Decorative elements */}
        <div className="absolute top-4 right-4 w-8 h-8 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full opacity-20 group-hover:opacity-40 transition-opacity duration-300"></div>
        <div className="absolute bottom-4 left-4 w-6 h-6 bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full opacity-20 group-hover:opacity-40 transition-opacity duration-300"></div>
      </div>

      {/* Error Details Display */}
      {lastError && (
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-2xl p-6 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="h-6 w-6 text-red-600" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-semibold text-red-800 mb-2">
                Upload Error
              </h3>
              <div className="text-red-700">
                <p className="font-medium mb-3">{lastError.message}</p>
                {lastError.details && (
                  <div>
                    <details className="cursor-pointer group">
                      <summary className="font-medium hover:text-red-800 transition-colors duration-200 flex items-center space-x-2">
                        <span>Technical Details</span>
                        <svg className="w-4 h-4 group-open:rotate-180 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </summary>
                      <div className="mt-3 p-4 bg-red-100 rounded-xl border text-sm font-mono space-y-2">
                        <div><strong>Error Type:</strong> {lastError.type}</div>
                        <div><strong>Timestamp:</strong> {lastError.timestamp}</div>
                        {lastError.details.originalError && (
                          <div><strong>Original Error:</strong> {lastError.details.originalError}</div>
                        )}
                        {lastError.details.filename && (
                          <div><strong>Filename:</strong> {lastError.details.filename}</div>
                        )}
                        {lastError.details.fileSize && (
                          <div><strong>File Size:</strong> {Math.round(lastError.details.fileSize / 1024)} KB</div>
                        )}
                        {lastError.details.possibleCauses && (
                          <div>
                            <strong>Possible Causes:</strong>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {lastError.details.possibleCauses.map((cause, index) => (
                                <li key={index}>{cause}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {lastError.details.stack && (
                          <div className="mt-2">
                            <strong>Stack Trace:</strong>
                            <pre className="mt-1 whitespace-pre-wrap text-xs bg-red-200 p-2 rounded">{lastError.details.stack}</pre>
                          </div>
                        )}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            </div>
            <div className="ml-4 flex-shrink-0">
              <button
                onClick={() => setLastError(null)}
                className="text-red-400 hover:text-red-600 transition-colors duration-200 p-1 rounded-full hover:bg-red-100"
              >
                <svg className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
