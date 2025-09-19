// Smart Progress Header Component
// Real-time progress tracking with ETA calculation and smart polling
import React, { useState, useEffect, useCallback, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

interface ProgressData {
  progress_percentage: number;
  pages_processed: number;
  total_pages: number;
  actual_cost: number;
  tokens_in_total: number;
  tokens_out_total: number;
  status: 'started' | 'processing' | 'completed' | 'error' | 'paused';
  started_at: string;
  completed_at?: string;
  estimated_total_cost?: number;
  current_operation?: string;
  error_message?: string;
}

interface SmartProgressHeaderProps {
  documentId: string;
  onProgressUpdate?: (progress: ProgressData) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
  pollingInterval?: number;
  maxRetries?: number;
  isPaused?: boolean;
  onTogglePause?: () => void;
  showAdvancedMetrics?: boolean;
  className?: string;
}

const HeaderContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.lg};
  box-shadow: ${props => props.theme.shadows.sm};
`;

const HeaderTop = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const StatusSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const StatusBadge = styled.div<{ status: ProgressData['status'] }>`
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius.sm};
  font-size: ${props => props.theme.typography.fontSize.xs};
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  ${props => {
    switch (props.status) {
      case 'completed':
        return `
          background: ${props.theme.colors.success}20;
          color: ${props.theme.colors.success};
          border: 1px solid ${props.theme.colors.success}40;
        `;
      case 'error':
        return `
          background: ${props.theme.colors.error}20;
          color: ${props.theme.colors.error};
          border: 1px solid ${props.theme.colors.error}40;
        `;
      case 'paused':
        return `
          background: ${props.theme.colors.warning}20;
          color: ${props.theme.colors.warning};
          border: 1px solid ${props.theme.colors.warning}40;
        `;
      default:
        return `
          background: ${props.theme.colors.primary}20;
          color: ${props.theme.colors.primary};
          border: 1px solid ${props.theme.colors.primary}40;
        `;
    }
  }}
`;

const ControlSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
`;

const ControlButton = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.variant === 'primary' ? props.theme.colors.primary : props.theme.colors.border};
  background: ${props => props.variant === 'primary' ? props.theme.colors.primary : 'transparent'};
  color: ${props => props.variant === 'primary' ? 'white' : props.theme.colors.text};
  border-radius: ${props => props.theme.borderRadius.md};
  font-size: ${props => props.theme.typography.fontSize.sm};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    background: ${props => props.variant === 'primary' ? `${props.theme.colors.primary}dd` : props.theme.colors.surface};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:focus {
    outline: 2px solid ${props => props.theme.colors.primary};
    outline-offset: 2px;
  }
`;

const ProgressBarContainer = styled.div`
  width: 100%;
  height: 8px;
  background: ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.sm};
  overflow: hidden;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const ProgressBar = styled(motion.div)<{ percentage: number }>`
  height: 100%;
  background: linear-gradient(90deg, ${props => props.theme.colors.primary}, ${props => `${props.theme.colors.primary}dd`});
  border-radius: ${props => props.theme.borderRadius.sm};
  position: relative;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s ease-in-out infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.md};
`;

const MetricCard = styled.div`
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
`;

const MetricLabel = styled.div`
  font-size: ${props => props.theme.typography.fontSize.xs};
  color: ${props => props.theme.colors.textSecondary};
  margin-bottom: ${props => props.theme.spacing.xs};
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;

const MetricValue = styled.div`
  font-size: ${props => props.theme.typography.fontSize.lg};
  font-weight: 600;
  color: ${props => props.theme.colors.text};
`;

const ETADisplay = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
`;

const ErrorMessage = styled.div`
  background: ${props => `${props.theme.colors.error}10`};
  border: 1px solid ${props => `${props.theme.colors.error}40`};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.theme.spacing.md};
  color: ${props => props.theme.colors.error};
  font-size: ${props => props.theme.typography.fontSize.sm};
  margin-top: ${props => props.theme.spacing.md};
`;

const CurrentOperation = styled.div`
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => props.theme.colors.textSecondary};
  font-style: italic;
`;

// Custom hook for smart polling with backoff
function useSmartPolling(
  fetchFunction: () => Promise<ProgressData>,
  interval: number,
  maxRetries: number,
  isPaused: boolean
) {
  const [data, setData] = useState<ProgressData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout>();
  const currentIntervalRef = useRef(interval);

  const poll = useCallback(async () => {
    try {
      const result = await fetchFunction();
      setData(result);
      setError(null);
      setRetryCount(0);
      currentIntervalRef.current = interval; // Reset interval on success

      // Stop polling if completed or error
      if (result.status === 'completed' || result.status === 'error') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setRetryCount(prev => prev + 1);

      // Apply exponential backoff
      currentIntervalRef.current = Math.min(currentIntervalRef.current * 1.5, 30000);

      // Stop polling if max retries reached
      if (retryCount >= maxRetries) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      }
    }
  }, [fetchFunction, interval, maxRetries, retryCount]);

  useEffect(() => {
    if (!isPaused && data?.status !== 'completed' && data?.status !== 'error') {
      intervalRef.current = setInterval(poll, currentIntervalRef.current);
      poll(); // Initial call
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [poll, isPaused, data?.status]);

  return { data, error, retryCount };
}

// ETA calculation utility
function calculateETA(progress: ProgressData): string | null {
  if (progress.pages_processed === 0 || progress.status === 'completed') {
    return null;
  }

  const startTime = new Date(progress.started_at);
  const currentTime = new Date();
  const elapsedMs = currentTime.getTime() - startTime.getTime();

  const averageTimePerPage = elapsedMs / progress.pages_processed;
  const remainingPages = progress.total_pages - progress.pages_processed;
  const etaMs = remainingPages * averageTimePerPage;

  const minutes = Math.ceil(etaMs / (1000 * 60));

  if (minutes < 1) return 'Less than a minute';
  if (minutes === 1) return '1 minute';
  if (minutes < 60) return `${minutes} minutes`;

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (hours === 1 && remainingMinutes === 0) return '1 hour';
  if (remainingMinutes === 0) return `${hours} hours`;

  return `${hours}h ${remainingMinutes}m`;
}

export const SmartProgressHeader: React.FC<SmartProgressHeaderProps> = ({
  documentId,
  onProgressUpdate,
  onComplete,
  onError,
  pollingInterval = 2000,
  maxRetries = 5,
  isPaused = false,
  onTogglePause,
  showAdvancedMetrics = false,
  className
}) => {
  const fetchProgress = useCallback(async (): Promise<ProgressData> => {
    const response = await fetch(`/api/enhanced/translation-progress/${documentId}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }, [documentId]);

  const { data: progress, error, retryCount } = useSmartPolling(
    fetchProgress,
    pollingInterval,
    maxRetries,
    isPaused
  );

  // Effect for progress updates
  useEffect(() => {
    if (progress && onProgressUpdate) {
      onProgressUpdate(progress);
    }
  }, [progress, onProgressUpdate]);

  // Effect for completion
  useEffect(() => {
    if (progress?.status === 'completed' && onComplete) {
      onComplete();
    }
  }, [progress?.status, onComplete]);

  // Effect for errors
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  const eta = progress ? calculateETA(progress) : null;
  const costPerPage = progress && progress.pages_processed > 0
    ? progress.actual_cost / progress.pages_processed
    : 0;
  const estimatedTotalCost = progress
    ? costPerPage * progress.total_pages
    : 0;

  if (!progress) {
    return (
      <HeaderContainer className={className}>
        <div>Loading progress...</div>
      </HeaderContainer>
    );
  }

  return (
    <HeaderContainer className={className} role="region" aria-label="Translation progress">
      <HeaderTop>
        <StatusSection>
          <StatusBadge status={progress.status}>
            {progress.status}
          </StatusBadge>

          {progress.current_operation && (
            <CurrentOperation>
              {progress.current_operation}
            </CurrentOperation>
          )}
        </StatusSection>

        <ControlSection>
          {onTogglePause && progress.status === 'processing' && (
            <ControlButton onClick={onTogglePause}>
              {isPaused ? '▶ Resume' : '⏸ Pause'}
            </ControlButton>
          )}

          <ETADisplay>
            {eta && (
              <span>
                ⏱ ETA: {eta}
              </span>
            )}
          </ETADisplay>
        </ControlSection>
      </HeaderTop>

      <ProgressBarContainer>
        <ProgressBar
          percentage={progress.progress_percentage}
          initial={{ width: 0 }}
          animate={{ width: `${progress.progress_percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </ProgressBarContainer>

      <MetricsGrid>
        <MetricCard>
          <MetricLabel>Pages</MetricLabel>
          <MetricValue>
            {progress.pages_processed} / {progress.total_pages}
          </MetricValue>
        </MetricCard>

        <MetricCard>
          <MetricLabel>Progress</MetricLabel>
          <MetricValue>
            {progress.progress_percentage}%
          </MetricValue>
        </MetricCard>

        <MetricCard>
          <MetricLabel>Current Cost</MetricLabel>
          <MetricValue>
            ${progress.actual_cost.toFixed(6)}
          </MetricValue>
        </MetricCard>

        {showAdvancedMetrics && (
          <>
            <MetricCard>
              <MetricLabel>Input Tokens</MetricLabel>
              <MetricValue>
                {progress.tokens_in_total.toLocaleString()}
              </MetricValue>
            </MetricCard>

            <MetricCard>
              <MetricLabel>Output Tokens</MetricLabel>
              <MetricValue>
                {progress.tokens_out_total.toLocaleString()}
              </MetricValue>
            </MetricCard>

            <MetricCard>
              <MetricLabel>Est. Total Cost</MetricLabel>
              <MetricValue>
                ${estimatedTotalCost.toFixed(6)}
              </MetricValue>
            </MetricCard>
          </>
        )}
      </MetricsGrid>

      <AnimatePresence>
        {(error || progress.error_message) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <ErrorMessage>
              {error || progress.error_message}
              {retryCount > 0 && ` (Retry ${retryCount}/${maxRetries})`}
            </ErrorMessage>
          </motion.div>
        )}
      </AnimatePresence>
    </HeaderContainer>
  );
};