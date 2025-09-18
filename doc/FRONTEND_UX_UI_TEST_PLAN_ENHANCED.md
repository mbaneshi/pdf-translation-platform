# Enhanced Frontend UX/UI & Test Coverage Plan

**Document Version:** 2.0 (Enhanced)
**Date:** September 18, 2025
**Status:** Implementation Ready
**Based on:** System Analysis + Original UX/UI Test Plan

---

## 📋 Executive Summary

This enhanced plan builds upon the existing UX/UI foundation while addressing critical gaps identified through our comprehensive system analysis. The platform's backend capabilities ($0.000176/page cost tracking, 108/7 token monitoring, real-time progress) require frontend components that match this sophistication.

### Key Enhancements Over Original Plan
- **Side-by-side Review Panel**: Complete implementation with Persian RTL optimization
- **Richer Progress Header**: ETA calculation, cost prediction, model information
- **Advanced Upload UX**: Pre-processing validation, error recovery, progress indication
- **Export Menu System**: Multiple formats, batch operations, sharing capabilities
- **Comprehensive Testing**: MSW integration, E2E with Playwright, performance testing

---

## 🎯 Enhanced UX/UI Components

### 1. Translation Review Panel (Side-by-Side)

**Current Gap**: No visual comparison between original and translated content
**Enhancement**: Full-featured review interface with Persian optimization

#### Technical Implementation

**File**: `frontend/components/ReviewPanel.tsx`
```typescript
interface ReviewPanelProps {
  documentId: number;
  pageNumber: number;
  onApprove?: (pageId: number) => void;
  onReject?: (pageId: number, feedback: string) => void;
}

export function ReviewPanel({ documentId, pageNumber, onApprove, onReject }: ReviewPanelProps) {
  const [page, setPage] = useState<PageData | null>(null);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay' | 'diff'>('side-by-side');
  const [showDiff, setShowDiff] = useState(false);
  const [editMode, setEditMode] = useState(false);

  return (
    <div className="review-panel h-full flex flex-col">
      {/* Toolbar */}
      <div className="sticky top-0 bg-white border-b p-4 z-10">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <ViewModeSelector mode={viewMode} onChange={setViewMode} />
            <button
              onClick={() => setShowDiff(!showDiff)}
              className={`btn-outline ${showDiff ? 'bg-blue-50' : ''}`}
            >
              Show Changes
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <QualityScore score={page?.quality_score} />
            <CostIndicator cost={page?.cost_estimate} />
            <ActionButtons
              onApprove={() => onApprove?.(page?.id)}
              onReject={() => setEditMode(true)}
              onCopy={() => copyToClipboard(page?.translated_text)}
            />
          </div>
        </div>
      </div>

      {/* Content Panels */}
      <div className="flex-1 flex overflow-hidden">
        {viewMode === 'side-by-side' && (
          <>
            <OriginalPanel text={page?.original_text} showDiff={showDiff} />
            <TranslatedPanel
              text={page?.translated_text}
              editMode={editMode}
              onEdit={(text) => handleEdit(text)}
              showDiff={showDiff}
            />
          </>
        )}

        {viewMode === 'overlay' && (
          <OverlayPanel
            original={page?.original_text}
            translated={page?.translated_text}
          />
        )}

        {viewMode === 'diff' && (
          <DiffPanel
            original={page?.original_text}
            translated={page?.translated_text}
          />
        )}
      </div>
    </div>
  );
}

// Original content panel with English text
function OriginalPanel({ text, showDiff }: { text?: string; showDiff: boolean }) {
  return (
    <div className="flex-1 border-r bg-gray-50">
      <div className="p-4 border-b bg-white">
        <h3 className="font-medium text-gray-900">Original (English)</h3>
        <div className="text-sm text-gray-600 mt-1">
          Source content for translation
        </div>
      </div>
      <div className="p-6 overflow-auto h-full">
        <div className="prose max-w-none text-left" dir="ltr">
          {showDiff ? (
            <DiffHighlighter text={text} type="source" />
          ) : (
            <p className="text-gray-800 leading-relaxed">{text}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Translated content panel with Persian RTL optimization
function TranslatedPanel({
  text,
  editMode,
  onEdit,
  showDiff
}: {
  text?: string;
  editMode: boolean;
  onEdit: (text: string) => void;
  showDiff: boolean;
}) {
  return (
    <div className="flex-1 bg-blue-50">
      <div className="p-4 border-b bg-white">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-medium text-gray-900">Translation (Persian)</h3>
            <div className="text-sm text-gray-600 mt-1">
              AI-generated Persian translation
            </div>
          </div>
          <PersianTextSettings />
        </div>
      </div>
      <div className="p-6 overflow-auto h-full">
        {editMode ? (
          <PersianEditor
            text={text}
            onChange={onEdit}
            onSave={() => setEditMode(false)}
          />
        ) : (
          <div className="persian-content" dir="rtl">
            {showDiff ? (
              <DiffHighlighter text={text} type="target" />
            ) : (
              <PersianTextRenderer
                text={text}
                className="text-blue-900 leading-relaxed"
                size="lg"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Test Coverage**:
```typescript
// tests/components/ReviewPanel.test.tsx
describe('ReviewPanel', () => {
  test('renders side-by-side view correctly', async () => {
    const mockPage = {
      original_text: 'Test PDF content',
      translated_text: 'محتوای PDF تست',
      quality_score: 0.95,
      cost_estimate: 0.000176
    };

    render(<ReviewPanel documentId={123} pageNumber={1} />);

    expect(screen.getByText('Original (English)')).toBeInTheDocument();
    expect(screen.getByText('Translation (Persian)')).toBeInTheDocument();
    expect(screen.getByText('محتوای PDF تست')).toBeInTheDocument();
  });

  test('handles approve/reject actions', async () => {
    const onApprove = jest.fn();
    const onReject = jest.fn();

    render(
      <ReviewPanel
        documentId={123}
        pageNumber={1}
        onApprove={onApprove}
        onReject={onReject}
      />
    );

    await userEvent.click(screen.getByText('Approve'));
    expect(onApprove).toHaveBeenCalledWith(expect.any(Number));
  });

  test('supports Persian text editing', async () => {
    render(<ReviewPanel documentId={123} pageNumber={1} />);

    await userEvent.click(screen.getByText('Edit'));

    const editor = screen.getByRole('textbox');
    expect(editor).toHaveAttribute('dir', 'rtl');
    expect(editor).toHaveClass('persian-editor');
  });
});
```

### 2. Enhanced Progress & Cost Header

**Current Gap**: Basic progress indication without cost/ETA details
**Enhancement**: Comprehensive progress dashboard with predictions

#### Technical Implementation

**File**: `frontend/components/ProgressHeader.tsx`
```typescript
interface ProgressHeaderProps {
  documentId: number;
  progress: TranslationProgress;
  onPauseResume: () => void;
  isPaused: boolean;
}

export function ProgressHeader({ documentId, progress, onPauseResume, isPaused }: ProgressHeaderProps) {
  const eta = calculateETA(progress);
  const costPerHour = calculateCostRate(progress);

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm">
      {/* Primary Status Row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <StatusBadge status={progress.status} />
          <ModelInfo model={progress.model || 'gpt-4o-mini'} />
          <div className="text-sm text-gray-600">
            Document ID: {documentId}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <PollingIndicator isActive={!isPaused} />
          <button
            onClick={onPauseResume}
            className="btn-outline text-sm"
          >
            {isPaused ? 'Resume' : 'Pause'} Updates
          </button>
        </div>
      </div>

      {/* Progress Bar with Details */}
      <div className="space-y-3">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Translation Progress</span>
          <span>{progress.pages_processed} of {progress.total_pages} pages</span>
        </div>

        <div className="relative">
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(progress.progress_percentage, 100)}%` }}
            />
          </div>
          <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
            {progress.progress_percentage.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <MetricCard
          title="Current Cost"
          value={`$${progress.actual_cost.toFixed(6)}`}
          subtitle="Actual spend"
          trend={calculateCostTrend(progress)}
        />

        <MetricCard
          title="Estimated Total"
          value={`$${(progress.actual_cost / progress.progress_percentage * 100).toFixed(6)}`}
          subtitle="Projected final cost"
          trend="neutral"
        />

        <MetricCard
          title="Processing Rate"
          value={`$${costPerHour.toFixed(4)}/hr`}
          subtitle="Current rate"
          trend="neutral"
        />

        <MetricCard
          title="ETA"
          value={eta.formatted}
          subtitle="Estimated completion"
          trend="neutral"
        />
      </div>

      {/* Token Usage Details */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center">
          <h4 className="font-medium text-gray-900">Token Usage</h4>
          <TokenEfficiencyIndicator
            inputTokens={progress.tokens_in_total}
            outputTokens={progress.tokens_out_total}
          />
        </div>

        <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
          <div>
            <span className="text-gray-600">Input:</span>
            <div className="font-medium">{progress.tokens_in_total.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-gray-600">Output:</span>
            <div className="font-medium">{progress.tokens_out_total.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-gray-600">Efficiency:</span>
            <div className="font-medium">
              {(progress.tokens_out_total / Math.max(progress.tokens_in_total, 1)).toFixed(2)}x
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function calculateETA(progress: TranslationProgress): { formatted: string; minutes: number } {
  if (progress.progress_percentage >= 100) {
    return { formatted: 'Completed', minutes: 0 };
  }

  const startTime = new Date(progress.started_at).getTime();
  const now = Date.now();
  const elapsed = (now - startTime) / 1000; // seconds

  const rate = progress.progress_percentage / elapsed; // percentage per second
  const remaining = (100 - progress.progress_percentage) / rate; // seconds

  const minutes = Math.ceil(remaining / 60);

  if (minutes < 60) {
    return { formatted: `${minutes}m`, minutes };
  } else {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return { formatted: `${hours}h ${mins}m`, minutes };
  }
}
```

### 3. Advanced Upload & Error UX

**Current Gap**: Basic file upload without validation or error recovery
**Enhancement**: Pre-processing validation, smart error handling, progress indication

#### Technical Implementation

**File**: `frontend/components/EnhancedFileUpload.tsx`
```typescript
export function EnhancedFileUpload({ onUpload, onError }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingMode, setProcessingMode] = useState<'basic' | 'enhanced'>('enhanced');

  const validateFile = (file: File): string[] => {
    const errors: string[] = [];

    // Type validation
    if (!file.type.includes('pdf')) {
      errors.push('Only PDF files are supported');
    }

    // Size validation with soft/hard limits
    const maxSize = 100 * 1024 * 1024; // 100MB
    const softLimit = 50 * 1024 * 1024; // 50MB

    if (file.size > maxSize) {
      errors.push(`File too large (${formatFileSize(file.size)}). Maximum size is 100MB.`);
    } else if (file.size > softLimit) {
      errors.push(`Large file detected (${formatFileSize(file.size)}). Processing may take longer.`);
    }

    // Content validation (basic)
    if (file.size < 1024) {
      errors.push('File appears to be too small. Please ensure it contains readable content.');
    }

    return errors;
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    const errors = validateFile(file);
    setValidationErrors(errors);
  };

  const handleUpload = async () => {
    if (!selectedFile || validationErrors.some(e => e.includes('too large'))) {
      return;
    }

    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const result = processingMode === 'enhanced'
        ? await uploadEnhancedDocument(selectedFile)
        : await uploadDocument(selectedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setTimeout(() => {
        onUpload(result);
        setSelectedFile(null);
        setUploadProgress(0);
      }, 500);

    } catch (error) {
      setUploadProgress(0);
      handleUploadError(error);
    }
  };

  const handleUploadError = (error: Error) => {
    let userMessage = 'Upload failed. Please try again.';
    let canRetry = true;
    let suggestions: string[] = [];

    if (error.message.includes('413')) {
      userMessage = 'File too large for server.';
      suggestions.push('Try compressing your PDF');
      suggestions.push('Split large documents into smaller files');
      canRetry = false;
    } else if (error.message.includes('unsupported')) {
      userMessage = 'File format not supported.';
      suggestions.push('Ensure file is a valid PDF');
      suggestions.push('Try re-saving the PDF from another application');
      canRetry = false;
    } else if (error.message.includes('network')) {
      userMessage = 'Network error. Check your connection.';
      suggestions.push('Check your internet connection');
      suggestions.push('Try again in a few moments');
    }

    onError({ message: userMessage, canRetry, suggestions });
  };

  return (
    <div className="enhanced-upload space-y-6">
      {/* Processing Mode Selection */}
      <ProcessingModeSelector
        mode={processingMode}
        onModeChange={setProcessingMode}
      />

      {/* File Drop Zone */}
      <div
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center transition-all
          ${dragActive
            ? 'border-blue-400 bg-blue-50'
            : selectedFile
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-gray-400'
          }
        `}
        onDragEnter={() => setDragActive(true)}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleFileDrop}
      >
        {uploadProgress > 0 ? (
          <UploadProgress progress={uploadProgress} />
        ) : selectedFile ? (
          <FilePreview
            file={selectedFile}
            validationErrors={validationErrors}
            onRemove={() => setSelectedFile(null)}
          />
        ) : (
          <DropZoneContent />
        )}
      </div>

      {/* Validation Messages */}
      {validationErrors.length > 0 && (
        <ValidationMessages
          errors={validationErrors}
          canProceed={!validationErrors.some(e => e.includes('too large'))}
        />
      )}

      {/* Upload Button */}
      {selectedFile && (
        <div className="flex justify-end space-x-3">
          <button
            onClick={() => setSelectedFile(null)}
            className="btn-outline"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={uploadProgress > 0 || validationErrors.some(e => e.includes('too large'))}
            className="btn-primary"
          >
            {uploadProgress > 0 ? 'Uploading...' : `Upload with ${processingMode} processing`}
          </button>
        </div>
      )}
    </div>
  );
}
```

### 4. Export Menu System

**Current Gap**: Single export format without user control
**Enhancement**: Multiple formats, batch operations, sharing options

#### Technical Implementation

**File**: `frontend/components/ExportMenu.tsx`
```typescript
interface ExportMenuProps {
  documentId: number;
  documentName: string;
  pages: PageData[];
  onExport?: (format: string, pages?: number[]) => void;
}

export function ExportMenu({ documentId, documentName, pages, onExport }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('markdown');
  const [selectedPages, setSelectedPages] = useState<number[]>([]);
  const [exporting, setExporting] = useState(false);

  const exportFormats: ExportFormat[] = [
    {
      id: 'markdown',
      name: 'Markdown',
      description: 'Structured text with Persian content',
      extension: 'md',
      icon: '📝',
      available: true
    },
    {
      id: 'json',
      name: 'JSON',
      description: 'Raw data with metadata',
      extension: 'json',
      icon: '📊',
      available: true
    },
    {
      id: 'txt',
      name: 'Plain Text',
      description: 'Simple text file',
      extension: 'txt',
      icon: '📄',
      available: true
    },
    {
      id: 'pdf',
      name: 'PDF',
      description: 'Formatted PDF document',
      extension: 'pdf',
      icon: '📋',
      available: false,
      comingSoon: true
    }
  ];

  const handleExport = async () => {
    setExporting(true);

    try {
      const exportData = await exportDocument(documentId, {
        format: selectedFormat.id,
        pages: selectedPages.length > 0 ? selectedPages : undefined
      });

      // Generate filename
      const timestamp = new Date().toISOString().slice(0, 10);
      const pagesSuffix = selectedPages.length > 0 ? `-pages-${selectedPages.join('-')}` : '';
      const filename = `${documentName}${pagesSuffix}-${timestamp}.${selectedFormat.extension}`;

      // Trigger download
      downloadFile(exportData.content, filename, selectedFormat.mimeType);

      // Analytics and feedback
      onExport?.(selectedFormat.id, selectedPages);
      toast.success(`Exported as ${selectedFormat.name}`);

    } catch (error) {
      toast.error(`Export failed: ${error.message}`);
    } finally {
      setExporting(false);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-primary flex items-center space-x-2"
      >
        <DownloadIcon className="h-4 w-4" />
        <span>Export</span>
        <ChevronDownIcon className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border z-50">
          <div className="p-4 border-b">
            <h3 className="font-medium">Export Options</h3>
            <p className="text-sm text-gray-600 mt-1">
              Choose format and pages to export
            </p>
          </div>

          <div className="p-4 space-y-4">
            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">Format</label>
              <div className="space-y-2">
                {exportFormats.map((format) => (
                  <div
                    key={format.id}
                    className={`
                      p-3 border rounded-lg cursor-pointer transition-all
                      ${selectedFormat.id === format.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                      }
                      ${!format.available ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                    onClick={() => format.available && setSelectedFormat(format)}
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{format.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{format.name}</span>
                          {format.comingSoon && (
                            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                              Coming Soon
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{format.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Page Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">Pages</label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="pageSelection"
                    checked={selectedPages.length === 0}
                    onChange={() => setSelectedPages([])}
                    className="mr-2"
                  />
                  <span>All pages ({pages.length})</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="radio"
                    name="pageSelection"
                    checked={selectedPages.length > 0}
                    onChange={() => setSelectedPages([1])}
                    className="mr-2"
                  />
                  <span>Select specific pages</span>
                </label>

                {selectedPages.length > 0 && (
                  <PageSelector
                    totalPages={pages.length}
                    selected={selectedPages}
                    onChange={setSelectedPages}
                  />
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="border-t pt-4">
              <div className="flex justify-between items-center text-sm">
                <button
                  onClick={() => copyToClipboard(getContentPreview())}
                  className="text-blue-600 hover:text-blue-700"
                >
                  📋 Copy to Clipboard
                </button>

                <button
                  onClick={() => shareDocument()}
                  className="text-blue-600 hover:text-blue-700"
                >
                  🔗 Share Link
                </button>
              </div>
            </div>
          </div>

          <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
            <button
              onClick={() => setIsOpen(false)}
              className="btn-outline text-sm"
            >
              Cancel
            </button>

            <button
              onClick={handleExport}
              disabled={exporting || !selectedFormat.available}
              className="btn-primary text-sm"
            >
              {exporting ? (
                <>
                  <Spinner className="mr-2 h-3 w-3" />
                  Exporting...
                </>
              ) : (
                `Export ${selectedFormat.name}`
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🧪 Comprehensive Testing Strategy

### Enhanced Unit/Component Testing

#### API Client Testing with MSW
```typescript
// tests/lib/api.test.ts
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const server = setupServer(
  rest.post('/api/enhanced/upload-enhanced', (req, res, ctx) => {
    return res(ctx.json({
      document_id: 123,
      layout_preservation: true,
      enhanced_features: ['layout_analysis', 'table_detection']
    }));
  }),

  rest.get('/api/enhanced/translation-progress/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(ctx.json({
      document_id: parseInt(id),
      progress_percentage: 75,
      pages_processed: 3,
      total_pages: 4,
      actual_cost: 0.000528,
      tokens_in_total: 324,
      tokens_out_total: 21,
      status: 'processing'
    }));
  }),

  rest.get('/api/enhanced/export/:id', (req, res, ctx) => {
    return res(ctx.json({
      document_id: parseInt(req.params.id),
      format: 'markdown',
      content: '# Page 1\n\nتست محتوای فارسی'
    }));
  }),

  rest.post('/api/enhanced/gradual-translate/:id', (req, res, ctx) => {
    return res(ctx.json({
      message: 'Translation started',
      task_id: 'abc-123',
      document_id: parseInt(req.params.id)
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('API Client with MSW', () => {
  test('handles progress polling with token accumulation', async () => {
    const progress = await fetchTranslationProgress(123);

    expect(progress).toMatchObject({
      progress_percentage: 75,
      tokens_in_total: 324,
      tokens_out_total: 21,
      actual_cost: 0.000528
    });
  });

  test('handles export download flow', async () => {
    const exportData = await exportDocument(123);

    expect(exportData.format).toBe('markdown');
    expect(exportData.content).toContain('تست محتوای فارسی');
  });

  test('handles rate limiting with 429 responses', async () => {
    server.use(
      rest.get('/api/enhanced/translation-progress/:id', (req, res, ctx) => {
        return res(ctx.status(429), ctx.json({ error: 'Rate limited' }));
      })
    );

    await expect(fetchTranslationProgress(123)).rejects.toThrow('Rate limited');
  });
});
```

#### Advanced Hook Testing
```typescript
// tests/hooks/useTranslationProgress.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useTranslationProgress } from '../hooks/useTranslationProgress';

jest.useFakeTimers();

describe('useTranslationProgress', () => {
  test('polls progress and calculates ETA', async () => {
    const mockProgressSequence = [
      { progress_percentage: 25, started_at: '2025-09-18T10:00:00Z' },
      { progress_percentage: 50, started_at: '2025-09-18T10:00:00Z' },
      { progress_percentage: 100, started_at: '2025-09-18T10:00:00Z' }
    ];

    let callCount = 0;
    jest.spyOn(api, 'fetchTranslationProgress').mockImplementation(() => {
      return Promise.resolve(mockProgressSequence[callCount++] || mockProgressSequence[2]);
    });

    const { result } = renderHook(() => useTranslationProgress(123, 1000));

    // Fast-forward through polling intervals
    act(() => jest.advanceTimersByTime(1000));
    await waitFor(() => expect(result.current.progress?.progress_percentage).toBe(25));

    act(() => jest.advanceTimersByTime(1000));
    await waitFor(() => expect(result.current.progress?.progress_percentage).toBe(50));

    act(() => jest.advanceTimersByTime(1000));
    await waitFor(() => expect(result.current.isComplete).toBe(true));
  });

  test('handles smart backoff on errors', async () => {
    let failCount = 0;
    jest.spyOn(api, 'fetchTranslationProgress').mockImplementation(() => {
      if (failCount++ < 3) {
        return Promise.reject(new Error('Network error'));
      }
      return Promise.resolve({ progress_percentage: 100 });
    });

    const { result } = renderHook(() => useTranslationProgress(123, 1000));

    // Should retry with backoff
    act(() => jest.advanceTimersByTime(5000));

    await waitFor(() => {
      expect(result.current.progress?.progress_percentage).toBe(100);
    });
  });
});
```

### Performance Testing

#### Virtualized Page List Testing
```typescript
// tests/performance/VirtualizedPageList.test.ts
import { render, screen } from '@testing-library/react';
import { VirtualizedPageList } from '../components/VirtualizedPageList';

describe('VirtualizedPageList Performance', () => {
  test('handles large page lists efficiently', async () => {
    const largePagesData = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      page_number: i + 1,
      translation_status: 'completed',
      original_text: `Page ${i + 1} content`,
      translated_text: `محتوای صفحه ${i + 1}`
    }));

    const startTime = performance.now();

    render(
      <VirtualizedPageList
        pages={largePagesData}
        height={400}
        itemHeight={100}
      />
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render quickly even with 1000 items
    expect(renderTime).toBeLessThan(100); // 100ms threshold

    // Should only render visible items
    const visibleItems = screen.getAllByTestId(/page-item-/);
    expect(visibleItems.length).toBeLessThan(20); // Only visible items
  });

  test('maintains smooth scrolling performance', async () => {
    const pages = Array.from({ length: 100 }, (_, i) => ({
      id: i + 1,
      page_number: i + 1,
      translation_status: 'completed'
    }));

    render(<VirtualizedPageList pages={pages} height={400} itemHeight={100} />);

    const scrollContainer = screen.getByTestId('virtual-scroll-container');

    // Simulate rapid scrolling
    const scrollEvents = Array.from({ length: 50 }, (_, i) => i * 20);

    const startTime = performance.now();

    for (const scrollTop of scrollEvents) {
      fireEvent.scroll(scrollContainer, { target: { scrollTop } });
    }

    const endTime = performance.now();
    expect(endTime - startTime).toBeLessThan(500); // Should handle rapid scrolling
  });
});
```

### E2E Testing with Playwright

#### Complete Workflow E2E Test
```typescript
// tests/e2e/translation-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Complete Translation Workflow', () => {
  test('user can upload, translate, and export document', async ({ page }) => {
    await page.goto('/');

    // 1. Upload document
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/sample.pdf');
    await expect(page.locator('.upload-success')).toBeVisible();

    // 2. Select enhanced processing
    await page.click('text=Enhanced Processing');
    await page.click('text=Start Processing');

    // 3. Generate sample translation
    await page.click('text=Generate Sample');
    await expect(page.locator('.persian-text')).toBeVisible();
    await expect(page.locator('.persian-text')).toHaveAttribute('dir', 'rtl');

    // 4. Approve and start full translation
    await page.click('text=Approve & Continue');
    await page.click('text=Start Full Translation');

    // 5. Monitor progress
    await expect(page.locator('.progress-bar')).toBeVisible();
    await expect(page.locator('.cost-tracker')).toContainText('$');

    // Wait for completion (with timeout)
    await expect(page.locator('text=Translation completed')).toBeVisible({ timeout: 30000 });

    // 6. Export document
    await page.click('text=Export');
    await page.click('text=Markdown');
    await page.click('text=Export Markdown');

    // Verify download
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toMatch(/\.md$/);
  });

  test('handles errors gracefully', async ({ page }) => {
    await page.goto('/');

    // Upload invalid file
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/invalid.txt');

    await expect(page.locator('.error-message')).toContainText('Only PDF files are supported');
    await expect(page.locator('text=Retry')).toBeVisible();
  });

  test('accessibility compliance', async ({ page }) => {
    await page.goto('/');

    // Check keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();

    // Check ARIA labels
    const uploadButton = page.locator('[aria-label*="upload"]');
    await expect(uploadButton).toBeVisible();

    // Check color contrast (would need axe-playwright)
    // await injectAxe(page);
    // const results = await checkA11y(page);
    // expect(results.violations).toHaveLength(0);
  });
});
```

### Integration Testing Strategy

#### MSW-backed Integration Tests
```typescript
// tests/integration/translation-flow.test.ts
import { setupServer } from 'msw/node';
import { render, screen, waitFor, userEvent } from '@testing-library/react';
import { rest } from 'msw';
import { TranslationWorkflow } from '../components/TranslationWorkflow';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Translation Flow Integration', () => {
  test('complete workflow with real-time updates', async () => {
    // Mock the entire API flow
    let progressStep = 0;
    const progressSteps = [25, 50, 75, 100];

    server.use(
      rest.post('/api/enhanced/upload-enhanced', (req, res, ctx) => {
        return res(ctx.json({ document_id: 123 }));
      }),

      rest.get('/api/enhanced/translation-progress/123', (req, res, ctx) => {
        const currentProgress = progressSteps[progressStep++] || 100;
        return res(ctx.json({
          progress_percentage: currentProgress,
          actual_cost: currentProgress * 0.000001,
          tokens_in_total: currentProgress * 10,
          status: currentProgress < 100 ? 'processing' : 'completed'
        }));
      })
    );

    const user = userEvent.setup();
    render(<TranslationWorkflow />);

    // Upload file
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/upload/i);
    await user.upload(input, file);

    // Start translation
    await user.click(screen.getByText(/start translation/i));

    // Watch progress updates
    await waitFor(() => expect(screen.getByText('25%')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('50%')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('100%')).toBeInTheDocument());

    // Verify completion
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });
});
```

---

## 📊 Success Criteria & Metrics

### Test Coverage Targets
- **Global Coverage**: ≥ 80% (maintained from original plan)
- **Component Coverage**: ≥ 90% for new UX components
- **Integration Coverage**: 100% for critical user paths
- **E2E Coverage**: Complete workflow + error scenarios

### Performance Benchmarks
- **Component Render**: < 100ms for all new components
- **Virtual List Scrolling**: 60fps with 1000+ items
- **Progress Polling**: < 50ms API response processing
- **Export Generation**: < 3 seconds for typical documents

### UX Quality Metrics
- **Accessibility**: WCAG 2.1 AA compliance (100%)
- **Persian Support**: Proper RTL rendering validation
- **Error Recovery**: 100% of error states have retry mechanisms
- **User Feedback**: Loading states for all async operations

### Reliability Targets
- **Test Stability**: < 1% flaky test rate
- **Mock Determinism**: 100% consistent MSW responses
- **Cross-browser**: Chrome, Firefox, Safari compatibility
- **Mobile**: Responsive design validation

---

## 🚀 Implementation Timeline

### Week 1: Core UX Components
- **Days 1-2**: ReviewPanel component with Persian RTL optimization
- **Days 3-4**: Enhanced ProgressHeader with ETA/cost calculations
- **Day 5**: Unit tests for new components

### Week 2: Advanced Features & Testing
- **Days 1-2**: EnhancedFileUpload with validation and error recovery
- **Days 3-4**: ExportMenu with multiple formats and page selection
- **Day 5**: MSW integration tests for all new components

### Week 3: Performance & Accessibility
- **Days 1-2**: VirtualizedPageList implementation and testing
- **Days 3-4**: Accessibility audit and compliance fixes
- **Day 5**: Performance optimization and benchmarking

### Week 4: E2E & Polish
- **Days 1-3**: Playwright E2E test suite
- **Days 4-5**: Bug fixes, polish, and documentation

---

This enhanced plan provides a comprehensive roadmap for transforming your frontend into a production-grade translation platform that fully utilizes your sophisticated backend capabilities while maintaining excellent test coverage and user experience! 🎯