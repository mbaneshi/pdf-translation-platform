# Final Frontend Implementation Strategy

**Document Version:** 3.0 (Refined with Insights)
**Date:** September 18, 2025
**Status:** Ready for Implementation
**Based on:** Enhanced UX/UI Plan + Strategic Insights

---

## 📋 Executive Summary

This final implementation strategy incorporates critical insights to ensure robust, maintainable, and flake-free frontend development. The approach prioritizes reliability, accessibility, and performance while delivering production-grade UX that matches our sophisticated backend capabilities.

### Key Refinements from Insights
- **MSW-First Testing**: Eliminate brittle mocks with realistic network simulation
- **Shared Infrastructure**: Reusable test utilities and components
- **Performance Guardrails**: Smart polling and virtualization with proper testing
- **Error Taxonomy**: Centralized, user-friendly error handling
- **Accessibility Excellence**: RTL optimization and keyboard navigation

---

## 🛠️ Implementation Infrastructure

### 1. MSW Testing Foundation

**Setup**: Global MSW server with per-suite handlers

```typescript
// tests/setup/msw-server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// Setup and teardown
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
```

**Standardized Handlers**:
```typescript
// tests/setup/handlers.ts
import { rest } from 'msw';
import { PERSIAN_FIXTURES } from './persian-corpus';

export const handlers = [
  // Upload handlers
  rest.post('/api/enhanced/upload-enhanced', (req, res, ctx) => {
    const formData = req.body as FormData;
    const file = formData.get('file') as File;

    if (!file || !file.name.endsWith('.pdf')) {
      return res(ctx.status(400), ctx.json({
        error: 'Only PDF files are allowed'
      }));
    }

    return res(ctx.json({
      document_id: 123,
      layout_preservation: true,
      enhanced_features: ['layout_analysis', 'table_detection', 'format_preservation']
    }));
  }),

  // Progress handlers with realistic progression
  rest.get('/api/enhanced/translation-progress/:id', (req, res, ctx) => {
    const progressStore = ctx.data || { step: 0 };
    const steps = [0, 25, 50, 75, 100];
    const currentStep = Math.min(progressStore.step++, steps.length - 1);

    ctx.data = progressStore;

    return res(ctx.json({
      document_id: parseInt(req.params.id as string),
      progress_percentage: steps[currentStep],
      pages_processed: Math.floor(steps[currentStep] / 25),
      total_pages: 4,
      actual_cost: steps[currentStep] * 0.000001,
      tokens_in_total: steps[currentStep] * 10,
      tokens_out_total: steps[currentStep] * 2,
      status: steps[currentStep] < 100 ? 'processing' : 'completed',
      started_at: '2025-09-18T10:00:00Z'
    }));
  }),

  // Sample translation with Persian content
  rest.post('/api/enhanced/translate-sample/:id/page/:page', (req, res, ctx) => {
    return res(ctx.json({
      original_text: 'Test PDF content for translation',
      translated_text: PERSIAN_FIXTURES.sampleTranslation,
      cost_estimate: 0.000176,
      quality_score: 0.95,
      processing_time: '2.3s',
      sample_id: 1
    }));
  }),

  // Export handlers
  rest.get('/api/enhanced/export/:id', (req, res, ctx) => {
    return res(ctx.json({
      document_id: parseInt(req.params.id as string),
      format: 'markdown',
      content: `# صفحه ۱\n\n${PERSIAN_FIXTURES.exportContent}`
    }));
  }),

  // Error simulation handlers
  rest.get('/api/enhanced/translation-progress/429', (req, res, ctx) => {
    return res(ctx.status(429), ctx.json({
      error: 'Rate limit exceeded',
      retry_after: 60
    }));
  })
];
```

### 2. Shared Test Utilities

**Test Render Wrapper**:
```typescript
// tests/utils/test-utils.tsx
import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../src/context/ThemeContext';
import { ToastProvider } from '../src/context/ToastContext';

interface CustomRenderOptions extends RenderOptions {
  initialRoute?: string;
  theme?: 'light' | 'dark';
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    initialRoute = '/',
    theme = 'light',
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    window.history.pushState({}, 'Test page', initialRoute);

    return (
      <BrowserRouter>
        <ThemeProvider defaultTheme={theme}>
          <ToastProvider>
            {children}
          </ToastProvider>
        </ThemeProvider>
      </BrowserRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Fake timer utilities
export function setupFakeTimers() {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });
}

// Polling test helper
export async function waitForPollingCycles(cycles: number, interval: number = 2000) {
  for (let i = 0; i < cycles; i++) {
    act(() => {
      jest.advanceTimersByTime(interval);
    });
    await waitFor(() => {}, { timeout: 100 });
  }
}
```

### 3. Persian Content Corpus

**Centralized RTL Test Data**:
```typescript
// tests/fixtures/persian-corpus.ts
export const PERSIAN_FIXTURES = {
  // Sample translation content
  sampleTranslation: 'محتوای PDF تست برای ترجمه با دقت بالا',

  // Complex Persian text with punctuation
  complexText: `
این یک متن فارسی پیچیده است که شامل علائم نگارشی مختلف می‌باشد؛
از جمله ویرگول، نقطه‌ویرگول، و علامت سؤال؟ همچنین اعداد انگلیسی
مانند ۱۲۳۴ و کلمات انگلیسی مثل PDF نیز در آن وجود دارد.
  `.trim(),

  // Export content
  exportContent: 'این محتوای صادر شده به فرمت مارک‌داون است.',

  // Error messages in Persian
  errorMessages: {
    uploadFailed: 'آپلود فایل با شکست مواجه شد',
    translationError: 'خطا در ترجمه رخ داده است',
    networkError: 'خطا در اتصال به شبکه'
  },

  // UI labels in Persian (for future bilingual support)
  uiLabels: {
    original: 'متن اصلی',
    translated: 'ترجمه شده',
    approve: 'تأیید',
    reject: 'رد',
    export: 'صادرات',
    download: 'دانلود'
  },

  // Test cases for text processing
  textProcessingCases: [
    {
      name: 'simple_sentence',
      english: 'This is a test.',
      persian: 'این یک آزمایش است.'
    },
    {
      name: 'with_numbers',
      english: 'Page 123 of document.',
      persian: 'صفحه ۱۲۳ از سند.'
    },
    {
      name: 'with_punctuation',
      english: 'Question: How are you?',
      persian: 'سؤال: حال شما چطور است؟'
    }
  ]
};

// RTL testing utilities
export function validateRTLRendering(element: HTMLElement) {
  expect(element).toHaveAttribute('dir', 'rtl');
  expect(element).toHaveStyle('text-align: right');
  expect(element).toHaveClass(/persian-text/);
}
```

---

## 🎨 Enhanced UX Components Implementation

### 1. Review Panel with Insights Integration

```typescript
// components/ReviewPanel.tsx
import React, { useState, useEffect } from 'react';
import { useSampleTranslation } from '../hooks';
import { PERSIAN_FIXTURES } from '../tests/fixtures/persian-corpus';

interface ReviewPanelProps {
  documentId: number;
  pageNumber: number;
  onApprove?: (pageId: number) => void;
  onReject?: (pageId: number, feedback: string) => void;
}

export function ReviewPanel({ documentId, pageNumber, onApprove, onReject }: ReviewPanelProps) {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay' | 'diff'>('side-by-side');
  const [showDiff, setShowDiff] = useState(false);
  const { sample, generateSample, loading, error } = useSampleTranslation();

  // Keyboard navigation support
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'd':
            e.preventDefault();
            setShowDiff(!showDiff);
            break;
          case 'Enter':
            e.preventDefault();
            if (sample && onApprove) {
              onApprove(sample.sample_id);
            }
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [showDiff, sample, onApprove]);

  return (
    <div
      className="review-panel h-full flex flex-col"
      role="main"
      aria-label="Translation Review Panel"
    >
      {/* Accessible toolbar */}
      <div className="sticky top-0 bg-white border-b p-4 z-10">
        <div className="flex justify-between items-center">
          <ViewModeSelector
            mode={viewMode}
            onChange={setViewMode}
            aria-label="Select view mode"
          />

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowDiff(!showDiff)}
              className={`btn-outline ${showDiff ? 'bg-blue-50' : ''}`}
              aria-pressed={showDiff}
              aria-label={showDiff ? 'Hide differences' : 'Show differences'}
              title="Toggle diff view (Ctrl+D)"
            >
              {showDiff ? 'Hide' : 'Show'} Changes
            </button>

            <QualityScore score={sample?.quality_score} />
            <CostIndicator cost={sample?.cost_estimate} />
          </div>
        </div>
      </div>

      {/* Status announcements for screen readers */}
      <div
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      >
        {loading && 'Generating translation sample...'}
        {error && `Error: ${error}`}
        {sample && 'Translation sample ready for review'}
      </div>

      {/* Content panels with proper accessibility */}
      <div className="flex-1 flex overflow-hidden">
        {viewMode === 'side-by-side' && (
          <>
            <OriginalPanel
              text={sample?.original_text}
              showDiff={showDiff}
              aria-label="Original English text"
            />
            <TranslatedPanel
              text={sample?.translated_text}
              showDiff={showDiff}
              aria-label="Persian translation"
            />
          </>
        )}
      </div>

      {/* Action buttons with keyboard support */}
      {sample && (
        <div className="border-t p-4 bg-gray-50">
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => onReject?.(sample.sample_id, 'Needs revision')}
              className="btn-outline"
              aria-label="Reject this translation"
            >
              Reject
            </button>
            <button
              onClick={() => onApprove?.(sample.sample_id)}
              className="btn-primary"
              aria-label="Approve this translation (Ctrl+Enter)"
            >
              Approve & Continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Original content panel with enhanced accessibility
function OriginalPanel({
  text,
  showDiff,
  'aria-label': ariaLabel
}: {
  text?: string;
  showDiff: boolean;
  'aria-label': string;
}) {
  return (
    <div className="flex-1 border-r bg-gray-50">
      <div className="p-4 border-b bg-white">
        <h3 className="font-medium text-gray-900" id="original-heading">
          Original (English)
        </h3>
        <div className="text-sm text-gray-600 mt-1">
          Source content for translation
        </div>
      </div>
      <div
        className="p-6 overflow-auto h-full"
        role="region"
        aria-labelledby="original-heading"
        aria-label={ariaLabel}
      >
        <div className="prose max-w-none text-left" dir="ltr">
          {showDiff ? (
            <DiffHighlighter text={text} type="source" />
          ) : (
            <p
              className="text-gray-800 leading-relaxed"
              tabIndex={0}
              aria-label="Original text content"
            >
              {text}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// Persian panel with RTL optimization
function TranslatedPanel({
  text,
  showDiff,
  'aria-label': ariaLabel
}: {
  text?: string;
  showDiff: boolean;
  'aria-label': string;
}) {
  return (
    <div className="flex-1 bg-blue-50">
      <div className="p-4 border-b bg-white">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-medium text-gray-900" id="translation-heading">
              Translation (Persian)
            </h3>
            <div className="text-sm text-gray-600 mt-1">
              AI-generated Persian translation
            </div>
          </div>
          <PersianTextSettings />
        </div>
      </div>
      <div
        className="p-6 overflow-auto h-full"
        role="region"
        aria-labelledby="translation-heading"
        aria-label={ariaLabel}
      >
        <div className="persian-content" dir="rtl" lang="fa">
          {showDiff ? (
            <DiffHighlighter text={text} type="target" />
          ) : (
            <PersianTextRenderer
              text={text}
              className="text-blue-900 leading-relaxed"
              size="lg"
              tabIndex={0}
              aria-label="Persian translation content"
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

### 2. Smart Progress Header with ETA

```typescript
// components/SmartProgressHeader.tsx
import React, { useState, useCallback } from 'react';
import { useTranslationProgress } from '../hooks';

interface SmartProgressHeaderProps {
  documentId: number;
  pollingInterval?: number; // Configurable for testing
  onPauseResume?: (isPaused: boolean) => void;
}

export function SmartProgressHeader({
  documentId,
  pollingInterval = 2000,
  onPauseResume
}: SmartProgressHeaderProps) {
  const [isPaused, setIsPaused] = useState(false);
  const { progress, error, retryCount } = useTranslationProgress(
    documentId,
    isPaused ? null : pollingInterval
  );

  const handlePauseResume = useCallback(() => {
    const newPausedState = !isPaused;
    setIsPaused(newPausedState);
    onPauseResume?.(newPausedState);

    // Announce state change for accessibility
    const announcement = newPausedState
      ? 'Progress monitoring paused'
      : 'Progress monitoring resumed';
    announceToScreenReader(announcement);
  }, [isPaused, onPauseResume]);

  const eta = calculateETA(progress);
  const costPerHour = calculateCostRate(progress);

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm">
      {/* Status announcements */}
      <div
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
        id="progress-announcements"
      >
        {progress && `Progress: ${progress.progress_percentage.toFixed(1)}%`}
        {error && `Error: ${error}`}
      </div>

      {/* Primary status row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <StatusBadge
            status={progress?.status || 'pending'}
            aria-describedby="progress-announcements"
          />
          <ModelInfo model={progress?.model || 'gpt-4o-mini'} />
          <div className="text-sm text-gray-600">
            Document ID: {documentId}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <PollingIndicator
            isActive={!isPaused && !error}
            retryCount={retryCount}
            aria-label="Progress update status"
          />
          <button
            onClick={handlePauseResume}
            className="btn-outline text-sm"
            aria-label={isPaused ? 'Resume progress updates' : 'Pause progress updates'}
            disabled={!!error}
          >
            {isPaused ? (
              <>
                <PlayIcon className="h-3 w-3 mr-1" />
                Resume
              </>
            ) : (
              <>
                <PauseIcon className="h-3 w-3 mr-1" />
                Pause
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error handling with retry */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <AlertTriangleIcon className="h-4 w-4 text-red-500 mr-2" />
              <span className="text-red-800 text-sm">
                {getErrorMessage(error)}
              </span>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="text-red-600 hover:text-red-700 text-sm underline"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Enhanced progress visualization */}
      {progress && (
        <>
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
                  role="progressbar"
                  aria-valuenow={progress.progress_percentage}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Translation progress"
                />
              </div>
              <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
                {progress.progress_percentage.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Comprehensive metrics grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <MetricCard
              title="Current Cost"
              value={`$${progress.actual_cost.toFixed(6)}`}
              subtitle="Actual spend"
              trend="neutral"
              aria-label={`Current cost: ${progress.actual_cost.toFixed(6)} dollars`}
            />

            <MetricCard
              title="Estimated Total"
              value={eta.costProjection}
              subtitle="Projected final cost"
              trend="neutral"
              aria-label={`Estimated total cost: ${eta.costProjection}`}
            />

            <MetricCard
              title="Processing Rate"
              value={`$${costPerHour.toFixed(4)}/hr`}
              subtitle="Current rate"
              trend="neutral"
              aria-label={`Processing rate: ${costPerHour.toFixed(4)} dollars per hour`}
            />

            <MetricCard
              title="ETA"
              value={eta.formatted}
              subtitle="Estimated completion"
              trend="neutral"
              aria-label={`Estimated completion time: ${eta.formatted}`}
            />
          </div>

          {/* Token usage with efficiency indicator */}
          <TokenUsagePanel
            inputTokens={progress.tokens_in_total}
            outputTokens={progress.tokens_out_total}
            efficiency={calculateTokenEfficiency(progress)}
          />
        </>
      )}
    </div>
  );
}

// Helper functions
function calculateETA(progress: TranslationProgress | null) {
  if (!progress || progress.progress_percentage >= 100) {
    return { formatted: 'Completed', costProjection: '$0.00' };
  }

  const startTime = new Date(progress.started_at).getTime();
  const now = Date.now();
  const elapsed = (now - startTime) / 1000;

  const rate = progress.progress_percentage / elapsed;
  const remaining = (100 - progress.progress_percentage) / rate;

  const minutes = Math.ceil(remaining / 60);
  const projectedCost = (progress.actual_cost / progress.progress_percentage * 100).toFixed(6);

  if (minutes < 60) {
    return {
      formatted: `${minutes}m`,
      costProjection: `$${projectedCost}`
    };
  } else {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return {
      formatted: `${hours}h ${mins}m`,
      costProjection: `$${projectedCost}`
    };
  }
}

function announceToScreenReader(message: string) {
  const announcer = document.createElement('div');
  announcer.setAttribute('aria-live', 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  announcer.className = 'sr-only';
  announcer.textContent = message;

  document.body.appendChild(announcer);
  setTimeout(() => document.body.removeChild(announcer), 1000);
}
```

---

## 🧪 Refined Testing Strategy

### 1. MSW Integration Tests

```typescript
// tests/integration/translation-workflow.test.ts
import { screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { server } from '../setup/msw-server';
import { renderWithProviders, setupFakeTimers, waitForPollingCycles } from '../utils/test-utils';
import { PERSIAN_FIXTURES } from '../fixtures/persian-corpus';
import { TranslationWorkflow } from '../../components/TranslationWorkflow';

setupFakeTimers();

describe('Translation Workflow Integration', () => {
  test('complete workflow with realistic polling', async () => {
    const user = userEvent.setup({ delay: null });

    renderWithProviders(<TranslationWorkflow />);

    // 1. Upload document
    const fileInput = screen.getByLabelText(/upload file/i);
    const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await user.upload(fileInput, testFile);

    await waitFor(() => {
      expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument();
    });

    // 2. Generate sample with Persian validation
    await user.click(screen.getByText(/generate sample/i));

    await waitFor(() => {
      const persianText = screen.getByText(PERSIAN_FIXTURES.sampleTranslation);
      validateRTLRendering(persianText.closest('[dir="rtl"]'));
    });

    // 3. Start translation
    await user.click(screen.getByText(/start translation/i));

    // 4. Test polling progression with fake timers
    await waitForPollingCycles(4, 2000); // 4 cycles of 2-second polling

    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });

    // 5. Verify final state
    expect(screen.getByLabelText(/download/i)).toBeEnabled();
  });

  test('handles rate limiting with smart backoff', async () => {
    // Override handler to simulate rate limiting
    server.use(
      rest.get('/api/enhanced/translation-progress/:id', (req, res, ctx) => {
        return res(ctx.status(429), ctx.json({
          error: 'Rate limit exceeded',
          retry_after: 60
        }));
      })
    );

    renderWithProviders(<TranslationWorkflow />);

    // Start a process that would trigger polling
    const user = userEvent.setup({ delay: null });
    await user.click(screen.getByText(/start monitoring/i));

    // Advance timers to trigger polling
    act(() => jest.advanceTimersByTime(2000));

    await waitFor(() => {
      expect(screen.getByText(/rate limit exceeded/i)).toBeInTheDocument();
      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });

    // Verify backoff behavior
    act(() => jest.advanceTimersByTime(5000)); // Should use backoff, not immediate retry

    // Should show backoff indicator
    expect(screen.getByText(/retrying in/i)).toBeInTheDocument();
  });
});
```

### 2. Accessibility Testing

```typescript
// tests/accessibility/review-panel.test.ts
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReviewPanel } from '../../components/ReviewPanel';
import { PERSIAN_FIXTURES } from '../fixtures/persian-corpus';

describe('ReviewPanel Accessibility', () => {
  test('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    const onApprove = jest.fn();

    render(
      <ReviewPanel
        documentId={123}
        pageNumber={1}
        onApprove={onApprove}
      />
    );

    // Tab through interactive elements
    await user.tab();
    expect(document.activeElement).toHaveAttribute('aria-label', 'Select view mode');

    await user.tab();
    expect(document.activeElement).toHaveAttribute('aria-label', /show differences/i);

    // Test keyboard shortcuts
    await user.keyboard('{Control>}d{/Control}');
    expect(screen.getByLabelText(/hide differences/i)).toBeInTheDocument();

    // Test approval shortcut
    await user.keyboard('{Control>}{Enter}{/Control}');
    expect(onApprove).toHaveBeenCalled();
  });

  test('provides proper ARIA announcements', async () => {
    render(<ReviewPanel documentId={123} pageNumber={1} />);

    const liveRegion = screen.getByLabelText(/translation sample ready/i);
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
  });

  test('validates RTL text rendering', () => {
    render(<ReviewPanel documentId={123} pageNumber={1} />);

    const persianContent = screen.getByText(PERSIAN_FIXTURES.sampleTranslation);
    const container = persianContent.closest('[dir="rtl"]');

    validateRTLRendering(container);
    expect(container).toHaveAttribute('lang', 'fa');
  });
});
```

### 3. Performance Testing with Virtualization

```typescript
// tests/performance/virtualized-list.test.ts
import { render, screen, fireEvent } from '@testing-library/react';
import { VirtualizedPageList } from '../../components/VirtualizedPageList';

// Mock IntersectionObserver for virtualization testing
global.IntersectionObserver = jest.fn().mockImplementation((callback) => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
  trigger: (entries) => callback(entries)
}));

describe('VirtualizedPageList Performance', () => {
  test('only renders visible items', () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      page_number: i + 1,
      translation_status: 'completed',
      original_text: `Page ${i + 1}`,
      translated_text: `صفحه ${i + 1}`
    }));

    const startTime = performance.now();

    render(
      <VirtualizedPageList
        pages={largeDataset}
        height={400}
        itemHeight={100}
        data-testid="virtual-list"
      />
    );

    const endTime = performance.now();

    // Should render quickly
    expect(endTime - startTime).toBeLessThan(100);

    // Should only render visible items (viewport can show ~4 items)
    const renderedItems = screen.getAllByTestId(/page-item-/);
    expect(renderedItems.length).toBeLessThan(10);
    expect(renderedItems.length).toBeGreaterThan(0);
  });

  test('maintains performance during scrolling', () => {
    const pages = Array.from({ length: 100 }, (_, i) => ({
      id: i + 1,
      page_number: i + 1,
      translation_status: 'completed'
    }));

    render(<VirtualizedPageList pages={pages} height={400} itemHeight={100} />);

    const scrollContainer = screen.getByTestId('virtual-scroll-container');

    // Measure scroll performance
    const startTime = performance.now();

    // Simulate rapid scrolling
    for (let i = 0; i < 50; i++) {
      fireEvent.scroll(scrollContainer, { target: { scrollTop: i * 20 } });
    }

    const endTime = performance.now();

    // Should handle rapid scrolling efficiently
    expect(endTime - startTime).toBeLessThan(500);
  });
});
```

---

## 📊 Success Metrics & Deliverables

### Deliverables Checklist

#### **Infrastructure**
- ✅ MSW server with global setup and per-suite handlers
- ✅ Shared test utilities with provider wrappers
- ✅ Persian content corpus for consistent RTL testing
- ✅ Fake timer utilities with polling helpers

#### **Components**
- ✅ ReviewPanel with accessibility and keyboard navigation
- ✅ SmartProgressHeader with ETA calculation and error handling
- ✅ EnhancedFileUpload with validation and error recovery
- ✅ ExportMenu with multiple formats and page selection
- ✅ VirtualizedPageList with performance optimization

#### **Testing**
- ✅ Unit tests for all components with >90% coverage
- ✅ MSW integration tests for realistic API simulation
- ✅ Accessibility tests with keyboard navigation and ARIA
- ✅ Performance tests with virtualization validation
- ✅ E2E tests with Playwright for complete workflows

### Success Metrics

#### **Quality Targets**
- **Global Test Coverage**: ≥ 80% (maintained)
- **Component Coverage**: ≥ 90% for new components
- **Flaky Test Rate**: < 1% (no flaky tests in 2 consecutive runs)
- **CI Performance**: < 5 minutes for frontend jobs

#### **Performance Benchmarks**
- **Component Render**: < 100ms for all components
- **Virtual List**: 60fps scrolling with 1000+ items
- **Progress Polling**: < 50ms API response processing
- **Export Generation**: < 3 seconds for typical documents

#### **Accessibility Standards**
- **WCAG 2.1 AA**: 100% compliance for critical flows
- **Keyboard Navigation**: Complete workflow accessible via keyboard
- **Screen Reader**: Proper ARIA labels and live regions
- **RTL Support**: Validated Persian text rendering

---

## 🎯 Final Implementation Plan

### Week 1: Foundation & Infrastructure
- **Day 1-2**: MSW setup, shared test utilities, Persian corpus
- **Day 3-4**: ReviewPanel implementation with accessibility
- **Day 5**: Unit and integration tests for ReviewPanel

### Week 2: Progress & Performance
- **Day 1-2**: SmartProgressHeader with ETA and smart polling
- **Day 3-4**: VirtualizedPageList with performance testing
- **Day 5**: Integration tests with fake timers and MSW

### Week 3: Upload & Export
- **Day 1-2**: EnhancedFileUpload with validation and error taxonomy
- **Day 3-4**: ExportMenu with multiple formats and accessibility
- **Day 5**: E2E tests with Playwright

### Week 4: Polish & Validation
- **Day 1-2**: Accessibility audit and compliance fixes
- **Day 3-4**: Performance optimization and flaky test elimination
- **Day 5**: Final integration testing and documentation

This refined strategy ensures robust, maintainable, and flake-free frontend development while delivering a world-class Persian translation platform! 🚀