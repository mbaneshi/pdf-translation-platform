'use client'

import { useState, useEffect } from 'react'
import { useTheme } from '../../contexts/ThemeContext'
import SuggestionPopover from '../suggestions/SuggestionPopover'

interface TranslatePaneProps {
  pageId?: number
  pageNumber: number
  sourceText: string
  translatedText: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  provider?: string
  cost?: number
  isLoading: boolean
  onSuggest: (segmentId: string, text: string) => void
}

interface Segment {
  id: string
  text: string
  translatedText?: string
  isSelected: boolean
}

export default function TranslatePane({
  pageId,
  pageNumber,
  sourceText,
  translatedText,
  status,
  provider,
  cost,
  isLoading,
  onSuggest
}: TranslatePaneProps) {
  const [segments, setSegments] = useState<Segment[]>([])
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null)
  const [showSuggestionPopover, setShowSuggestionPopover] = useState(false)
  const [popoverPosition, setPopoverPosition] = useState({ x: 0, y: 0 })
  const { currentTheme } = useTheme()

  // Split text into segments (sentences)
  useEffect(() => {
    if (sourceText) {
      const sentences = sourceText
        .split(/[.!?]+/)
        .filter(s => s.trim().length > 0)
        .map((sentence, index) => ({
          id: `segment-${index}`,
          text: sentence.trim(),
          translatedText: translatedText ? translatedText.split('\n')[index]?.trim() : undefined,
          isSelected: false
        }))
      
      setSegments(sentences)
    }
  }, [sourceText, translatedText])

  const handleSegmentClick = (segmentId: string, event: React.MouseEvent) => {
    setSelectedSegment(segmentId)
    setPopoverPosition({ x: event.clientX, y: event.clientY })
    setShowSuggestionPopover(true)
  }

  const handleSegmentRightClick = (segmentId: string, event: React.MouseEvent) => {
    event.preventDefault()
    setSelectedSegment(segmentId)
    setPopoverPosition({ x: event.clientX, y: event.clientY })
    setShowSuggestionPopover(true)
  }

  const handleSuggestionAccept = (suggestionId: string) => {
    console.log('Suggestion accepted:', suggestionId)
    setShowSuggestionPopover(false)
  }

  const handleSuggestionReject = (suggestionId: string) => {
    console.log('Suggestion rejected:', suggestionId)
    setShowSuggestionPopover(false)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'processing':
        return 'text-blue-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'processing':
        return '⟳'
      case 'failed':
        return '✗'
      default:
        return '○'
    }
  }

  return (
    <div className={`h-full flex flex-col ${currentTheme === 'dark' ? 'bg-gray-900' : 'bg-white'}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Translation - Page {pageNumber}
          </h3>
          <div className="flex items-center space-x-4">
            <span className={`text-sm font-medium ${getStatusColor(status)}`}>
              {getStatusIcon(status)} {status}
            </span>
            {provider && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {provider}
              </span>
            )}
            {cost && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                ${cost.toFixed(4)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading translation...</p>
            </div>
          </div>
        ) : segments.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-gray-500 dark:text-gray-400">No content to translate</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {segments.map((segment) => (
              <div
                key={segment.id}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedSegment === segment.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
                onClick={(e) => handleSegmentClick(segment.id, e)}
                onContextMenu={(e) => handleSegmentRightClick(segment.id, e)}
              >
                {/* Source Text */}
                <div className="mb-2">
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Source</div>
                  <p className="text-gray-900 dark:text-white">{segment.text}</p>
                </div>

                {/* Translated Text */}
                {segment.translatedText && (
                  <div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Translation</div>
                    <p className="text-gray-700 dark:text-gray-300">{segment.translatedText}</p>
                  </div>
                )}

                {/* Translation Status */}
                {!segment.translatedText && status === 'completed' && (
                  <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                    No translation available
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Suggestion Popover */}
      {showSuggestionPopover && selectedSegment && (
        <SuggestionPopover
          segmentId={selectedSegment}
          suggestions={[
            {
              id: 'suggestion-1',
              type: 'improvement',
              originalText: segments.find(s => s.id === selectedSegment)?.text || '',
              suggestedText: 'Improved translation suggestion',
              confidence: 0.85,
              reason: 'Better terminology consistency'
            }
          ]}
          position={popoverPosition}
          onAccept={handleSuggestionAccept}
          onReject={handleSuggestionReject}
          onClose={() => setShowSuggestionPopover(false)}
        />
      )}
    </div>
  )
}
