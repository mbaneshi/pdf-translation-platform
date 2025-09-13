import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

const FileUpload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [lastError, setLastError] = useState(null);

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
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="space-y-4">
          <div className="mx-auto w-12 h-12 text-gray-400">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          {uploading ? (
            <div className="text-gray-600">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              Uploading...
            </div>
          ) : (
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop the PDF here' : 'Drag & drop a PDF file here'}
              </p>
              <p className="text-sm text-gray-500">or click to select a file</p>
            </div>
          )}
        </div>
      </div>

      {/* Error Details Display */}
      {lastError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                Upload Error Details
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p className="font-medium">{lastError.message}</p>
                {lastError.details && (
                  <div className="mt-2">
                    <details className="cursor-pointer">
                      <summary className="font-medium hover:text-red-800">
                        Technical Details (Click to expand)
                      </summary>
                      <div className="mt-2 p-3 bg-red-100 rounded border text-xs font-mono">
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
                            <ul className="list-disc list-inside mt-1">
                              {lastError.details.possibleCauses.map((cause, index) => (
                                <li key={index}>{cause}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {lastError.details.stack && (
                          <div className="mt-2">
                            <strong>Stack Trace:</strong>
                            <pre className="mt-1 whitespace-pre-wrap">{lastError.details.stack}</pre>
                          </div>
                        )}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            </div>
            <div className="ml-3 flex-shrink-0">
              <button
                onClick={() => setLastError(null)}
                className="text-red-400 hover:text-red-600"
              >
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
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
