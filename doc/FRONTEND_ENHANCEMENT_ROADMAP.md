# Frontend Enhancement Roadmap

**Document Version:** 1.0
**Date:** September 18, 2025
**Status:** Ready for Implementation
**Priority:** High

---

## 📋 Executive Summary

This document outlines a comprehensive enhancement plan for the PDF Translation Platform frontend, addressing critical test coverage gaps, UX improvements, and advanced features to match the robust backend capabilities discovered during system analysis.

### Current State
- **Test Coverage**: 4/7 suites passing (57% success rate)
- **Backend Integration**: Limited - missing advanced features
- **UX Maturity**: Basic upload/download, no real-time feedback
- **Persian Support**: Minimal RTL optimization

### Target State
- **Test Coverage**: 100% with comprehensive integration tests
- **Backend Integration**: Full utilization of enhanced API capabilities
- **UX Maturity**: Production-grade with real-time monitoring
- **Persian Support**: Culturally optimized RTL experience

---

## 🎯 Critical Gaps Analysis

### Test Coverage Gaps

Based on our system analysis revealing powerful backend capabilities, the frontend tests are missing:

#### 1. Enhanced Upload Workflow
**Backend Capability**: Advanced layout preservation with PyMuPDF + pdfplumber
```json
{
  "layout_preservation": true,
  "enhanced_features": [
    "layout_analysis",
    "table_detection",
    "format_preservation"
  ]
}
```

**Missing Frontend Tests**:
- Enhanced vs basic upload mode selection
- Layout preservation feature validation
- Semantic analysis response handling

#### 2. Real-time Translation Monitoring
**Backend Capability**: Comprehensive progress tracking
```json
{
  "progress_percentage": 100.0,
  "pages_processed": 1,
  "total_pages": 1,
  "actual_cost": 0.000176,
  "tokens_in_total": 108,
  "tokens_out_total": 7
}
```

**Missing Frontend Tests**:
- Progress polling mechanisms
- Cost display and updates
- Token usage visualization
- WebSocket/Server-Sent Events integration

#### 3. Export & Download System
**Backend Capability**: Markdown export with Persian content
```json
{
  "document_id": 23,
  "format": "markdown",
  "content": "# Page 1\n\nتست پی‌دی‌اف"
}
```

**Missing Frontend Tests**:
- Export format handling
- Download trigger mechanisms
- Persian content rendering validation

---

## 🚀 Enhancement Plan

### Phase 1: Foundation & Test Stability (Week 1)

#### 1.1 Fix Current Test Failures

**File**: `frontend/lib/api.js`
```typescript
export async function apiFetch(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...(!options.body || typeof options.body === 'string'
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status}: ${errorText}`);
  }

  // Robust response parsing for tests
  const text = await response.text();
  if (!text) return {};

  try {
    return JSON.parse(text);
  } catch (parseError) {
    console.warn('Non-JSON response:', text);
    return { data: text };
  }
}

// Enhanced API methods
export async function uploadEnhancedDocument(file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);

  return apiFetch('/api/enhanced/upload-enhanced', {
    method: 'POST',
    body: formData
  });
}

export async function translateSample(documentId, pageNumber) {
  return apiFetch(`/api/enhanced/translate-sample/${documentId}/page/${pageNumber}`, {
    method: 'POST'
  });
}

export async function fetchTranslationProgress(documentId) {
  return apiFetch(`/api/enhanced/translation-progress/${documentId}`);
}

export async function startGradualTranslation(documentId, strategy = 'semantic') {
  return apiFetch(`/api/enhanced/gradual-translate/${documentId}`, {
    method: 'POST',
    body: JSON.stringify({ strategy }),
    headers: { 'Content-Type': 'application/json' }
  });
}

export async function exportDocument(documentId) {
  return apiFetch(`/api/enhanced/export/${documentId}`);
}

export async function analyzeSemanticStructure(documentId) {
  return apiFetch(`/api/enhanced/analyze-semantic/${documentId}`, {
    method: 'POST'
  });
}

export async function getSystemHealth() {
  return apiFetch('/api/monitoring/system-health');
}
```

**Test File**: `tests/lib/api.test.ts`
```typescript
import { uploadEnhancedDocument, translateSample, fetchTranslationProgress } from '../lib/api';

describe('Enhanced API Integration', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  test('uploadEnhancedDocument should handle enhanced response', async () => {
    const mockResponse = {
      document_id: 123,
      layout_preservation: true,
      enhanced_features: ['layout_analysis', 'table_detection']
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(mockResponse))
    });

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const result = await uploadEnhancedDocument(file);

    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/enhanced/upload-enhanced'),
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData)
      })
    );
  });

  test('translateSample should return Persian translation', async () => {
    const mockSample = {
      original_text: 'Test PDF',
      translated_text: 'تست پی‌دی‌اف',
      cost_estimate: 0.000176,
      quality_score: 0.9
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(mockSample))
    });

    const result = await translateSample(123, 1);
    expect(result.translated_text).toBe('تست پی‌دی‌اف');
    expect(result.cost_estimate).toBe(0.000176);
  });
});
```

#### 1.2 Enhanced Hooks Implementation

**File**: `frontend/hooks/index.ts`
```typescript
import { useState, useEffect, useCallback } from 'react';
import * as api from '../lib/api';

export function useDocument(documentId: number) {
  const [document, setDocument] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocument = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const docData = await api.getDocument(documentId);
      setDocument(docData);

      // Clear pages before fetching new ones
      setPages([]);
      const pagesData = await api.getDocumentPages(documentId);
      setPages(pagesData);
    } catch (err) {
      setError(err.message);
      // Preserve document on pages error, only clear pages
      setPages([]);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    if (documentId) {
      fetchDocument();
    }
  }, [documentId, fetchDocument]);

  return { document, pages, loading, error, refetch: fetchDocument };
}

export function useTranslationProgress(documentId: number, pollInterval = 2000) {
  const [progress, setProgress] = useState(null);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!documentId || isComplete) return;

    const interval = setInterval(async () => {
      try {
        const progressData = await api.fetchTranslationProgress(documentId);
        setProgress(progressData);

        if (progressData.progress_percentage >= 100) {
          setIsComplete(true);
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Progress fetch failed:', error);
      }
    }, pollInterval);

    return () => clearInterval(interval);
  }, [documentId, pollInterval, isComplete]);

  return { progress, isComplete };
}

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const uploadFile = useCallback(async (file, enhanced = false) => {
    setUploading(true);
    setError(null);

    try {
      const result = enhanced
        ? await api.uploadEnhancedDocument(file)
        : await api.uploadDocument(file);

      return result;
    } catch (err) {
      const errorMessage = err.message || 'Upload failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setUploading(false);
    }
  }, []);

  return { uploadFile, uploading, error };
}

export function useSampleTranslation() {
  const [sample, setSample] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateSample = useCallback(async (documentId, pageNumber) => {
    setLoading(true);
    setError(null);

    try {
      const sampleData = await api.translateSample(documentId, pageNumber);
      setSample(sampleData);
      return sampleData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { sample, generateSample, loading, error };
}
```

### Phase 2: Real-time Translation Experience (Week 2)

#### 2.1 Progress Monitoring Component

**File**: `frontend/components/TranslationProgress.tsx`
```typescript
import React from 'react';
import { useTranslationProgress } from '../hooks';

interface ProgressData {
  progress_percentage: number;
  pages_processed: number;
  total_pages: number;
  actual_cost: number;
  tokens_in_total: number;
  tokens_out_total: number;
  status: string;
}

interface Props {
  documentId: number;
  onComplete?: () => void;
}

export function TranslationProgress({ documentId, onComplete }: Props) {
  const { progress, isComplete } = useTranslationProgress(documentId);

  React.useEffect(() => {
    if (isComplete && onComplete) {
      onComplete();
    }
  }, [isComplete, onComplete]);

  if (!progress) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-8 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 bg-white rounded-lg shadow-sm border">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Translation Progress</h3>
        <StatusBadge status={progress.status} />
      </div>

      <ProgressBar
        percentage={progress.progress_percentage}
        pages={`${progress.pages_processed}/${progress.total_pages}`}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CostTracker cost={progress.actual_cost} />
        <TokenUsage
          input={progress.tokens_in_total}
          output={progress.tokens_out_total}
        />
        <ProcessingSpeed
          pagesProcessed={progress.pages_processed}
          startTime={progress.started_at}
        />
      </div>

      {isComplete && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-green-800 font-medium">
              Translation completed successfully!
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function ProgressBar({ percentage, pages }: { percentage: number; pages: string }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-600">
        <span>Progress</span>
        <span>{pages} pages</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="text-right text-sm font-medium text-gray-900">
        {percentage.toFixed(1)}%
      </div>
    </div>
  );
}

function CostTracker({ cost }: { cost: number }) {
  return (
    <div className="text-center p-4 bg-blue-50 rounded-lg">
      <div className="text-2xl font-bold text-blue-600">
        ${cost.toFixed(6)}
      </div>
      <div className="text-sm text-blue-800">Current Cost</div>
    </div>
  );
}

function TokenUsage({ input, output }: { input: number; output: number }) {
  return (
    <div className="text-center p-4 bg-green-50 rounded-lg">
      <div className="text-lg font-bold text-green-600">
        {input.toLocaleString()} / {output.toLocaleString()}
      </div>
      <div className="text-sm text-green-800">Input / Output Tokens</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    started: 'bg-blue-100 text-blue-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || colors.pending}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
```

**Test File**: `tests/components/TranslationProgress.test.tsx`
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { TranslationProgress } from '../components/TranslationProgress';
import * as api from '../lib/api';

jest.mock('../lib/api');

describe('TranslationProgress', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should display progress data and update in real-time', async () => {
    const mockProgress = {
      progress_percentage: 50,
      pages_processed: 1,
      total_pages: 2,
      actual_cost: 0.000352,
      tokens_in_total: 216,
      tokens_out_total: 14,
      status: 'processing'
    };

    (api.fetchTranslationProgress as jest.Mock)
      .mockResolvedValue(mockProgress);

    render(<TranslationProgress documentId={123} />);

    await waitFor(() => {
      expect(screen.getByText('50.0%')).toBeInTheDocument();
      expect(screen.getByText('$0.000352')).toBeInTheDocument();
      expect(screen.getByText('216 / 14')).toBeInTheDocument();
      expect(screen.getByText('1/2 pages')).toBeInTheDocument();
    });
  });

  test('should call onComplete when translation finishes', async () => {
    const onComplete = jest.fn();
    const mockProgress = {
      progress_percentage: 100,
      pages_processed: 2,
      total_pages: 2,
      status: 'completed'
    };

    (api.fetchTranslationProgress as jest.Mock)
      .mockResolvedValue(mockProgress);

    render(<TranslationProgress documentId={123} onComplete={onComplete} />);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });

  test('should handle error states gracefully', async () => {
    (api.fetchTranslationProgress as jest.Mock)
      .mockRejectedValue(new Error('Network error'));

    render(<TranslationProgress documentId={123} />);

    // Should show loading state when API fails
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
```

### Phase 3: Enhanced UX Features (Week 3)

#### 3.1 Sample Translation Preview

**File**: `frontend/components/SamplePreview.tsx`
```typescript
import React, { useState } from 'react';
import { useSampleTranslation } from '../hooks';
import { PersianTextRenderer } from './PersianTextRenderer';

interface Props {
  documentId: number;
  pageNumber: number;
  onApprove?: () => void;
}

export function SamplePreview({ documentId, pageNumber, onApprove }: Props) {
  const { sample, generateSample, loading, error } = useSampleTranslation();
  const [approved, setApproved] = useState(false);

  const handleGenerate = async () => {
    try {
      await generateSample(documentId, pageNumber);
    } catch (err) {
      // Error is handled by the hook
      console.error('Sample generation failed:', err);
    }
  };

  const handleApprove = () => {
    setApproved(true);
    onApprove?.();
  };

  return (
    <div className="border rounded-lg p-6 space-y-6 bg-white shadow-sm">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Translation Preview</h3>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="btn-secondary"
        >
          {loading ? (
            <>
              <Spinner className="mr-2 h-4 w-4" />
              Generating...
            </>
          ) : (
            'Generate Sample'
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      )}

      {sample && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Original Text (English)</h4>
              <div className="bg-gray-50 p-4 rounded-lg border">
                <p className="text-left text-gray-800 leading-relaxed">
                  {sample.original_text}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Translation (Persian)</h4>
              <div className="bg-blue-50 p-4 rounded-lg border">
                <PersianTextRenderer
                  text={sample.translated_text}
                  className="text-blue-900 leading-relaxed"
                />
              </div>
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Quality Score:</span>
                <div className="font-medium">
                  <QualityScore score={sample.quality_score} />
                </div>
              </div>
              <div>
                <span className="text-gray-600">Est. Cost:</span>
                <div className="font-medium">${sample.cost_estimate}</div>
              </div>
              <div>
                <span className="text-gray-600">Processing Time:</span>
                <div className="font-medium">{sample.processing_time || 'N/A'}</div>
              </div>
              <div>
                <span className="text-gray-600">Status:</span>
                <div className="font-medium text-green-600">Ready</div>
              </div>
            </div>
          </div>

          {!approved && (
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleGenerate}
                className="btn-secondary"
              >
                Regenerate
              </button>
              <button
                onClick={handleApprove}
                className="btn-primary"
              >
                Approve & Continue
              </button>
            </div>
          )}

          {approved && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                <span className="text-green-800 font-medium">
                  Sample approved! Ready to start full translation.
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function QualityScore({ score }: { score: number }) {
  const percentage = Math.round(score * 100);
  const color = percentage >= 90 ? 'text-green-600' :
                percentage >= 70 ? 'text-yellow-600' : 'text-red-600';

  return <span className={color}>{percentage}%</span>;
}
```

#### 3.2 Export & Download Component

**File**: `frontend/components/ExportDownload.tsx`
```typescript
import React, { useState } from 'react';
import { exportDocument } from '../lib/api';

interface Props {
  documentId: number;
  documentName?: string;
  disabled?: boolean;
}

export function ExportDownload({ documentId, documentName = 'document', disabled = false }: Props) {
  const [exporting, setExporting] = useState(false);
  const [exported, setExported] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const { content, format } = await exportDocument(documentId);

      // Create and trigger download
      const blob = new Blob([content], {
        type: format === 'markdown' ? 'text/markdown;charset=utf-8' : 'text/plain;charset=utf-8'
      });
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `${documentName}-translated.${format === 'markdown' ? 'md' : 'txt'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(url);
      setExported(true);

      // Show success notification
      toast.success('Document exported successfully!');

    } catch (error) {
      console.error('Export failed:', error);
      toast.error(`Export failed: ${error.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleExport}
        disabled={disabled || exporting}
        className={`btn-primary w-full ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {exporting ? (
          <>
            <Spinner className="mr-2 h-4 w-4" />
            Preparing Download...
          </>
        ) : exported ? (
          <>
            <CheckCircleIcon className="mr-2 h-4 w-4" />
            Downloaded
          </>
        ) : (
          <>
            <DownloadIcon className="mr-2 h-4 w-4" />
            Download Translated Document
          </>
        )}
      </button>

      {exported && (
        <div className="text-sm text-gray-600 text-center">
          Document downloaded as Markdown file
        </div>
      )}
    </div>
  );
}
```

### Phase 4: Advanced UI Components (Week 4)

#### 4.1 Processing Mode Selector

**File**: `frontend/components/ProcessingModeSelector.tsx`
```typescript
import React from 'react';

type ProcessingMode = 'basic' | 'enhanced';

interface ProcessingModeProps {
  mode: ProcessingMode;
  onModeChange: (mode: ProcessingMode) => void;
  disabled?: boolean;
}

export function ProcessingModeSelector({ mode, onModeChange, disabled = false }: ProcessingModeProps) {
  const modes = [
    {
      id: 'basic' as ProcessingMode,
      title: 'Basic Processing',
      description: 'Fast processing for simple documents',
      features: [
        'Quick text extraction',
        'Standard translation',
        'Lower cost',
        'Best for simple PDFs'
      ],
      icon: '⚡',
      recommended: false
    },
    {
      id: 'enhanced' as ProcessingMode,
      title: 'Enhanced Processing',
      description: 'Advanced features for complex documents',
      features: [
        'Layout preservation',
        'Table detection',
        'Semantic analysis',
        'Format preservation',
        'Best quality results'
      ],
      icon: '🎯',
      recommended: true
    }
  ];

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900">Choose Processing Mode</h3>
        <p className="text-sm text-gray-600 mt-1">
          Select the processing approach that best fits your document
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {modes.map((modeOption) => (
          <div
            key={modeOption.id}
            className={`
              relative border-2 rounded-lg p-6 cursor-pointer transition-all
              ${mode === modeOption.id
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
            onClick={() => !disabled && onModeChange(modeOption.id)}
          >
            {modeOption.recommended && (
              <div className="absolute -top-2 -right-2">
                <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                  Recommended
                </span>
              </div>
            )}

            <div className="flex items-start space-x-3">
              <div className="text-2xl">{modeOption.icon}</div>
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">{modeOption.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{modeOption.description}</p>
              </div>
            </div>

            <ul className="mt-4 space-y-2">
              {modeOption.features.map((feature, index) => (
                <li key={index} className="flex items-center text-sm">
                  <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                  <span className={mode === modeOption.id ? 'text-blue-800' : 'text-gray-700'}>
                    {feature}
                  </span>
                </li>
              ))}
            </ul>

            {mode === modeOption.id && (
              <div className="mt-4 flex items-center text-sm text-blue-600">
                <RadioButtonChecked className="h-4 w-4 mr-2" />
                Selected
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 4.2 Persian Text Optimization

**File**: `frontend/components/PersianTextRenderer.tsx`
```typescript
import React from 'react';

interface Props {
  text: string;
  className?: string;
  size?: 'sm' | 'base' | 'lg' | 'xl';
  weight?: 'normal' | 'medium' | 'semibold' | 'bold';
}

export function PersianTextRenderer({
  text,
  className = "",
  size = 'base',
  weight = 'normal'
}: Props) {
  const sizeClasses = {
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  const weightClasses = {
    normal: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold'
  };

  return (
    <div
      className={`
        persian-text
        ${sizeClasses[size]}
        ${weightClasses[weight]}
        ${className}
      `}
      dir="rtl"
      lang="fa"
    >
      {text}
    </div>
  );
}

// Add to global CSS file
export const persianStyles = `
.persian-text {
  direction: rtl;
  unicode-bidi: embed;
  text-align: right;
  font-family: 'Iranian Sans', 'Vazir', 'B Nazanin', Tahoma, Arial, sans-serif;
  line-height: 1.8;
  text-rendering: optimizeLegibility;
  -webkit-font-feature-settings: "liga" 1, "kern" 1;
  font-feature-settings: "liga" 1, "kern" 1;
  word-spacing: 0.1em;
  letter-spacing: 0.02em;
}

.persian-text p {
  margin-bottom: 1em;
}

.persian-text h1,
.persian-text h2,
.persian-text h3,
.persian-text h4,
.persian-text h5,
.persian-text h6 {
  font-weight: 600;
  margin-bottom: 0.5em;
}

/* Handle mixed RTL/LTR content */
.persian-text .english {
  direction: ltr;
  display: inline-block;
  text-align: left;
}

/* Improve readability for long texts */
.persian-text.reading-mode {
  line-height: 2;
  font-size: 1.1em;
  max-width: 65ch;
  margin: 0 auto;
}
`;
```

### Phase 5: Integration Testing & Performance (Week 5)

#### 5.1 Comprehensive Integration Tests

**File**: `tests/integration/full-workflow.test.ts`
```typescript
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as api from '../lib/api';
import { FullWorkflowApp } from '../components/FullWorkflowApp';

jest.mock('../lib/api');

describe('Complete Translation Workflow Integration', () => {
  let mockApi: jest.Mocked<typeof api>;

  beforeEach(() => {
    mockApi = api as jest.Mocked<typeof api>;
    jest.clearAllMocks();
  });

  test('should handle complete end-to-end translation workflow', async () => {
    const user = userEvent.setup();

    // Mock the complete workflow
    const mockUploadResult = {
      document_id: 123,
      layout_preservation: true,
      enhanced_features: ['layout_analysis', 'table_detection']
    };

    const mockSample = {
      original_text: 'Test PDF content',
      translated_text: 'محتوای PDF تست',
      cost_estimate: 0.000176,
      quality_score: 0.9
    };

    const mockProgressStates = [
      { progress_percentage: 0, pages_processed: 0, total_pages: 1, status: 'started' },
      { progress_percentage: 50, pages_processed: 0, total_pages: 1, status: 'processing' },
      { progress_percentage: 100, pages_processed: 1, total_pages: 1, status: 'completed' }
    ];

    const mockExport = {
      content: '# Page 1\n\nمحتوای PDF تست',
      format: 'markdown'
    };

    mockApi.uploadEnhancedDocument.mockResolvedValue(mockUploadResult);
    mockApi.translateSample.mockResolvedValue(mockSample);
    mockApi.startGradualTranslation.mockResolvedValue({ task_id: 'abc123' });
    mockApi.fetchTranslationProgress
      .mockResolvedValueOnce(mockProgressStates[0])
      .mockResolvedValueOnce(mockProgressStates[1])
      .mockResolvedValueOnce(mockProgressStates[2]);
    mockApi.exportDocument.mockResolvedValue(mockExport);

    render(<FullWorkflowApp />);

    // 1. Upload document
    const fileInput = screen.getByLabelText(/upload file/i);
    const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await user.upload(fileInput, testFile);

    await waitFor(() => {
      expect(mockApi.uploadEnhancedDocument).toHaveBeenCalledWith(testFile);
    });

    // 2. Generate and approve sample
    const generateSampleBtn = await screen.findByText(/generate sample/i);
    await user.click(generateSampleBtn);

    await waitFor(() => {
      expect(screen.getByText('محتوای PDF تست')).toBeInTheDocument();
    });

    const approveBtn = await screen.findByText(/approve/i);
    await user.click(approveBtn);

    // 3. Start translation
    const startTranslationBtn = await screen.findByText(/start translation/i);
    await user.click(startTranslationBtn);

    await waitFor(() => {
      expect(mockApi.startGradualTranslation).toHaveBeenCalledWith(123);
    });

    // 4. Monitor progress
    await waitFor(() => {
      expect(screen.getByText(/100%/)).toBeInTheDocument();
    }, { timeout: 10000 });

    // 5. Export document
    const exportBtn = await screen.findByText(/download/i);
    await user.click(exportBtn);

    await waitFor(() => {
      expect(mockApi.exportDocument).toHaveBeenCalledWith(123);
    });

    // Verify success state
    expect(screen.getByText(/completed successfully/i)).toBeInTheDocument();
  });

  test('should handle errors gracefully throughout the workflow', async () => {
    const user = userEvent.setup();

    mockApi.uploadEnhancedDocument.mockRejectedValue(new Error('Upload failed'));

    render(<FullWorkflowApp />);

    const fileInput = screen.getByLabelText(/upload file/i);
    const testFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    await user.upload(fileInput, testFile);

    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
    });

    // Verify retry functionality
    const retryBtn = screen.getByText(/retry/i);
    expect(retryBtn).toBeInTheDocument();
  });
});
```

#### 5.2 Performance Testing

**File**: `tests/performance/translation-performance.test.ts`
```typescript
import { render, waitFor } from '@testing-library/react';
import { TranslationProgress } from '../components/TranslationProgress';
import * as api from '../lib/api';

jest.mock('../lib/api');

describe('Translation Performance Tests', () => {
  test('should handle rapid progress updates without performance degradation', async () => {
    const mockApi = api as jest.Mocked<typeof api>;

    // Simulate rapid progress updates
    const progressUpdates = Array.from({ length: 100 }, (_, i) => ({
      progress_percentage: i + 1,
      pages_processed: Math.floor((i + 1) / 10),
      total_pages: 10,
      actual_cost: (i + 1) * 0.000001,
      tokens_in_total: (i + 1) * 10,
      tokens_out_total: (i + 1) * 2,
      status: i === 99 ? 'completed' : 'processing'
    }));

    let callCount = 0;
    mockApi.fetchTranslationProgress.mockImplementation(() => {
      return Promise.resolve(progressUpdates[callCount++] || progressUpdates[99]);
    });

    const startTime = performance.now();

    render(<TranslationProgress documentId={123} />);

    await waitFor(() => {
      expect(callCount).toBeGreaterThan(50);
    }, { timeout: 15000 });

    const endTime = performance.now();
    const duration = endTime - startTime;

    // Should complete within reasonable time
    expect(duration).toBeLessThan(20000); // 20 seconds max

    // Should not have memory leaks or excessive re-renders
    expect(callCount).toBeLessThan(150); // Reasonable API call limit
  });

  test('should handle large document processing efficiently', async () => {
    const mockApi = api as jest.Mocked<typeof api>;

    const largeDocumentProgress = {
      progress_percentage: 45,
      pages_processed: 45,
      total_pages: 100,
      actual_cost: 0.0158,
      tokens_in_total: 45000,
      tokens_out_total: 8900,
      status: 'processing'
    };

    mockApi.fetchTranslationProgress.mockResolvedValue(largeDocumentProgress);

    const { rerender } = render(<TranslationProgress documentId={456} />);

    // Test component with large numbers
    await waitFor(() => {
      expect(screen.getByText('45,000 / 8,900')).toBeInTheDocument();
      expect(screen.getByText('$0.015800')).toBeInTheDocument();
    });

    // Test re-render performance
    const startTime = performance.now();

    for (let i = 0; i < 100; i++) {
      rerender(<TranslationProgress documentId={456} />);
    }

    const endTime = performance.now();
    expect(endTime - startTime).toBeLessThan(1000); // Should re-render quickly
  });
});
```

---

## 📊 Implementation Metrics & Success Criteria

### Test Coverage Targets
- **Unit Tests**: 95% coverage for all new components
- **Integration Tests**: 100% coverage for critical workflows
- **E2E Tests**: Complete user journey validation
- **Performance Tests**: Sub-second component render times

### UX/UI Quality Standards
- **Accessibility**: WCAG 2.1 AA compliance
- **Persian Support**: Proper RTL rendering and cultural formatting
- **Responsive Design**: Mobile-first approach with breakpoint testing
- **Loading States**: Skeleton screens and progress indicators
- **Error Handling**: Graceful degradation with retry mechanisms

### Performance Benchmarks
- **Initial Page Load**: <2 seconds
- **Component Render**: <100ms
- **API Response Display**: <500ms
- **Progress Updates**: Real-time without UI blocking
- **Export Download**: <3 seconds for typical documents

---

## 🎯 Timeline & Resource Allocation

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 1** | Week 1 | Foundation | Fixed tests, enhanced API client |
| **Phase 2** | Week 2 | Real-time UX | Progress monitoring, polling |
| **Phase 3** | Week 3 | Core Features | Sample preview, export system |
| **Phase 4** | Week 4 | UI Polish | Persian optimization, mode selector |
| **Phase 5** | Week 5 | Quality | Integration tests, performance |

### Resource Requirements
- **Frontend Developer**: Full-time (40 hours/week)
- **UX/UI Designer**: Part-time (10 hours/week for Phases 3-4)
- **QA Engineer**: Part-time (15 hours/week for Phase 5)

---

## 🔄 Maintenance & Future Enhancements

### Immediate Post-Implementation
1. **User Feedback Collection**: Analytics and user session recordings
2. **Performance Monitoring**: Real-time metrics dashboard
3. **A/B Testing Setup**: Feature flag system for UX experiments
4. **Documentation**: Component library and style guide

### Future Enhancement Opportunities
1. **Multi-language Support**: Additional language pairs beyond English-Persian
2. **Advanced Editor**: In-place translation editing with track changes
3. **Collaborative Features**: Multi-user document review and approval
4. **Mobile App**: React Native port for mobile translation workflow
5. **AI Quality Assessment**: Automated translation quality scoring

---

This comprehensive enhancement plan transforms the frontend from basic functionality to a **production-grade translation platform** with enterprise-level UX, comprehensive testing, and full utilization of the robust backend capabilities!

**🎉 Expected Outcome**: A world-class Persian translation platform with 100% test coverage, exceptional UX, and seamless integration with the powerful backend infrastructure.