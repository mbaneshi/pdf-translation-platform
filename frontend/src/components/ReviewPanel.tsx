// Enhanced Review Panel Component
// Side-by-side comparison with RTL optimization and accessibility
import React, { useState, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

interface PageData {
  id: number;
  page_number: number;
  original_text: string;
  translated_text: string | null;
  translation_status: 'pending' | 'processing' | 'completed' | 'error';
  quality_score?: number;
  tokens_used?: number;
  cost?: number;
}

interface ReviewPanelProps {
  pages: PageData[];
  currentPage: number;
  onPageChange: (page: number) => void;
  onApprove: (pageId: number) => void;
  onReject: (pageId: number) => void;
  onEditTranslation: (pageId: number, newText: string) => void;
  isLoading?: boolean;
  showDiff?: boolean;
  className?: string;
}

const PanelContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background: ${props => props.theme.colors.background};
  border-radius: ${props => props.theme.borderRadius.lg};
  box-shadow: ${props => props.theme.shadows.md};
  overflow: hidden;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: between;
  padding: ${props => props.theme.spacing.lg};
  background: ${props => props.theme.colors.surface};
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const PageNavigation = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const PageButton = styled.button<{ isActive?: boolean }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.isActive ? props.theme.colors.primary : props.theme.colors.border};
  background: ${props => props.isActive ? props.theme.colors.primary : 'transparent'};
  color: ${props => props.isActive ? 'white' : props.theme.colors.text};
  border-radius: ${props => props.theme.borderRadius.md};
  cursor: pointer;
  font-size: ${props => props.theme.typography.fontSize.sm};
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    background: ${props => props.isActive ? props.theme.colors.primary : props.theme.colors.surface};
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

const ViewControls = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const ToggleButton = styled.button<{ isActive?: boolean }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  background: ${props => props.isActive ? props.theme.colors.secondary : 'transparent'};
  color: ${props => props.isActive ? 'white' : props.theme.colors.text};
  border-radius: ${props => props.theme.borderRadius.md};
  cursor: pointer;
  font-size: ${props => props.theme.typography.fontSize.sm};
  transition: all 0.2s ease;

  &:hover {
    background: ${props => props.isActive ? props.theme.colors.secondary : props.theme.colors.surface};
  }

  &:focus {
    outline: 2px solid ${props => props.theme.colors.primary};
    outline-offset: 2px;
  }
`;

const ContentArea = styled.div`
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: ${props => props.theme.colors.border};
  overflow: hidden;
`;

const TextPanel = styled.div<{ isRTL?: boolean }>`
  background: ${props => props.theme.colors.background};
  padding: ${props => props.theme.spacing.lg};
  overflow-y: auto;
  direction: ${props => props.isRTL ? 'rtl' : 'ltr'};
  text-align: ${props => props.isRTL ? 'right' : 'left'};
  font-family: ${props => props.isRTL ? props.theme.typography.fontFamily.persian : props.theme.typography.fontFamily.sans};
  line-height: 1.6;
`;

const PanelTitle = styled.h3`
  margin: 0 0 ${props => props.theme.spacing.lg} 0;
  font-size: ${props => props.theme.typography.fontSize.lg};
  font-weight: 600;
  color: ${props => props.theme.colors.text};
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
`;

const QualityBadge = styled.span<{ score: number }>`
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius.sm};
  font-size: ${props => props.theme.typography.fontSize.xs};
  font-weight: 500;
  background: ${props => {
    if (props.score >= 0.9) return props.theme.colors.success;
    if (props.score >= 0.7) return props.theme.colors.warning;
    return props.theme.colors.error;
  }};
  color: white;
`;

const TextContent = styled.div<{ isEditable?: boolean }>`
  min-height: 200px;
  padding: ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.isEditable ? props.theme.colors.surface : 'transparent'};
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: ${props => props.theme.typography.fontSize.base};

  ${props => props.isEditable && `
    outline: none;
    cursor: text;

    &:focus {
      border-color: ${props.theme.colors.primary};
      box-shadow: 0 0 0 3px ${props.theme.colors.primary}20;
    }
  `}
`;

const EditableTextArea = styled.textarea<{ isRTL?: boolean }>`
  width: 100%;
  min-height: 200px;
  padding: ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  background: ${props => props.theme.colors.surface};
  font-family: ${props => props.isRTL ? props.theme.typography.fontFamily.persian : props.theme.typography.fontFamily.sans};
  font-size: ${props => props.theme.typography.fontSize.base};
  line-height: 1.6;
  direction: ${props => props.isRTL ? 'rtl' : 'ltr'};
  text-align: ${props => props.isRTL ? 'right' : 'left'};
  resize: vertical;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 3px ${props => props.theme.colors.primary}20;
  }
`;

const ActionBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${props => props.theme.spacing.lg};
  background: ${props => props.theme.colors.surface};
  border-top: 1px solid ${props => props.theme.colors.border};
`;

const ActionGroup = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
`;

const ActionButton = styled.button<{ variant?: 'approve' | 'reject' | 'secondary' }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.lg};
  border: 1px solid;
  border-radius: ${props => props.theme.borderRadius.md};
  font-size: ${props => props.theme.typography.fontSize.sm};
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  ${props => {
    switch (props.variant) {
      case 'approve':
        return `
          background: ${props.theme.colors.success};
          border-color: ${props.theme.colors.success};
          color: white;

          &:hover:not(:disabled) {
            background: ${props.theme.colors.success}dd;
          }
        `;
      case 'reject':
        return `
          background: ${props.theme.colors.error};
          border-color: ${props.theme.colors.error};
          color: white;

          &:hover:not(:disabled) {
            background: ${props.theme.colors.error}dd;
          }
        `;
      default:
        return `
          background: transparent;
          border-color: ${props.theme.colors.border};
          color: ${props.theme.colors.text};

          &:hover:not(:disabled) {
            background: ${props.theme.colors.surface};
          }
        `;
    }
  }}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:focus {
    outline: 2px solid ${props => props.theme.colors.primary};
    outline-offset: 2px;
  }
`;

const StatusIndicator = styled.div<{ status: PageData['translation_status'] }>`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  font-size: ${props => props.theme.typography.fontSize.sm};
  color: ${props => {
    switch (props.status) {
      case 'completed': return props.theme.colors.success;
      case 'processing': return props.theme.colors.warning;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.textSecondary;
    }
  }};
`;

const LoadingSpinner = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid ${props => props.theme.colors.border};
  border-top: 2px solid ${props => props.theme.colors.primary};
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export const ReviewPanel: React.FC<ReviewPanelProps> = ({
  pages,
  currentPage,
  onPageChange,
  onApprove,
  onReject,
  onEditTranslation,
  isLoading = false,
  showDiff = false,
  className
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState('');

  const currentPageData = useMemo(() => {
    return pages.find(page => page.page_number === currentPage);
  }, [pages, currentPage]);

  const handleEditStart = useCallback(() => {
    if (currentPageData?.translated_text) {
      setEditText(currentPageData.translated_text);
      setIsEditing(true);
    }
  }, [currentPageData]);

  const handleEditSave = useCallback(() => {
    if (currentPageData && editText.trim()) {
      onEditTranslation(currentPageData.id, editText);
      setIsEditing(false);
    }
  }, [currentPageData, editText, onEditTranslation]);

  const handleEditCancel = useCallback(() => {
    setIsEditing(false);
    setEditText('');
  }, []);

  const handleApprove = useCallback(() => {
    if (currentPageData) {
      onApprove(currentPageData.id);
    }
  }, [currentPageData, onApprove]);

  const handleReject = useCallback(() => {
    if (currentPageData) {
      onReject(currentPageData.id);
    }
  }, [currentPageData, onReject]);

  const canNavigatePrev = currentPage > 1;
  const canNavigateNext = currentPage < pages.length;

  return (
    <PanelContainer className={className} role="main" aria-label="Translation Review Panel">
      <Header>
        <PageNavigation>
          <PageButton
            onClick={() => onPageChange(currentPage - 1)}
            disabled={!canNavigatePrev}
            aria-label="Previous page"
          >
            ← Previous
          </PageButton>

          <span aria-live="polite">
            Page {currentPage} of {pages.length}
          </span>

          <PageButton
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!canNavigateNext}
            aria-label="Next page"
          >
            Next →
          </PageButton>
        </PageNavigation>

        <ViewControls>
          <ToggleButton
            isActive={showDiff}
            onClick={() => {/* Parent component should handle this */}}
            aria-label="Toggle diff view"
          >
            Show Changes
          </ToggleButton>

          {currentPageData && (
            <StatusIndicator status={currentPageData.translation_status}>
              {currentPageData.translation_status === 'processing' && <LoadingSpinner />}
              {currentPageData.translation_status}
            </StatusIndicator>
          )}
        </ViewControls>
      </Header>

      <ContentArea>
        <TextPanel role="region" aria-label="Original text">
          <PanelTitle>
            Original Text
            {currentPageData?.tokens_used && (
              <span style={{ fontSize: '0.75rem', color: 'gray' }}>
                ({currentPageData.tokens_used} tokens)
              </span>
            )}
          </PanelTitle>

          <TextContent>
            {currentPageData?.original_text || 'No content available'}
          </TextContent>
        </TextPanel>

        <TextPanel isRTL role="region" aria-label="Persian translation">
          <PanelTitle>
            Persian Translation
            {currentPageData?.quality_score && (
              <QualityBadge score={currentPageData.quality_score}>
                Quality: {Math.round(currentPageData.quality_score * 100)}%
              </QualityBadge>
            )}
          </PanelTitle>

          <AnimatePresence mode="wait">
            {isEditing ? (
              <motion.div
                key="editing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <EditableTextArea
                  isRTL
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  placeholder="Enter Persian translation..."
                  dir="rtl"
                  lang="fa"
                />
              </motion.div>
            ) : (
              <motion.div
                key="viewing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <TextContent dir="rtl" lang="fa">
                  {currentPageData?.translated_text ||
                    (currentPageData?.translation_status === 'processing' ? 'Translation in progress...' : 'No translation available')}
                </TextContent>
              </motion.div>
            )}
          </AnimatePresence>
        </TextPanel>
      </ContentArea>

      <ActionBar>
        <ActionGroup>
          {isEditing ? (
            <>
              <ActionButton onClick={handleEditSave} disabled={!editText.trim()}>
                Save Changes
              </ActionButton>
              <ActionButton onClick={handleEditCancel}>
                Cancel
              </ActionButton>
            </>
          ) : (
            <>
              <ActionButton
                onClick={handleEditStart}
                disabled={!currentPageData?.translated_text || isLoading}
              >
                Edit Translation
              </ActionButton>

              <ActionButton
                variant="approve"
                onClick={handleApprove}
                disabled={!currentPageData?.translated_text || isLoading}
                aria-label="Approve this translation"
              >
                ✓ Approve
              </ActionButton>

              <ActionButton
                variant="reject"
                onClick={handleReject}
                disabled={!currentPageData?.translated_text || isLoading}
                aria-label="Reject this translation"
              >
                ✗ Reject
              </ActionButton>
            </>
          )}
        </ActionGroup>

        {currentPageData?.cost && (
          <div style={{ fontSize: '0.875rem', color: 'gray' }}>
            Cost: ${currentPageData.cost.toFixed(6)}
          </div>
        )}
      </ActionBar>
    </PanelContainer>
  );
};