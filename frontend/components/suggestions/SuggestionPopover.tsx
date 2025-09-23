'use client'

import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

interface Suggestion {
  id: string
  type: 'improvement' | 'glossary' | 'style' | 'grammar'
  originalText: string
  suggestedText: string
  confidence: number
  reason: string
}

interface SuggestionPopoverProps {
  segmentId: string
  suggestions: Suggestion[]
  position: { x: number; y: number }
  onAccept: (suggestionId: string) => void
  onReject: (suggestionId: string) => void
  onClose: () => void
}

export default function SuggestionPopover({
  segmentId,
  suggestions,
  position,
  onAccept,
  onReject,
  onClose
}: SuggestionPopoverProps) {
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  // Close popover on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const getSuggestionTypeColor = (type: string) => {
    switch (type) {
      case 'improvement':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'glossary':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'style':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'grammar':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400'
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  if (suggestions.length === 0) {
    return null
  }

  return (
    <div
      ref={popoverRef}
      className="fixed z-50 w-96 max-h-96 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg"
      style={{
        left: Math.min(position.x, window.innerWidth - 400),
        top: Math.min(position.y, window.innerHeight - 300)
      }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Suggestions
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Suggestions List */}
      <div className="p-4 space-y-4">
        {suggestions.map((suggestion) => (
          <div
            key={suggestion.id}
            className={`p-3 rounded-lg border transition-colors ${
              selectedSuggestion === suggestion.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
            onClick={() => setSelectedSuggestion(suggestion.id)}
          >
            {/* Suggestion Header */}
            <div className="flex items-center justify-between mb-2">
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSuggestionTypeColor(suggestion.type)}`}>
                {suggestion.type}
              </span>
              <span className={`text-sm font-medium ${getConfidenceColor(suggestion.confidence)}`}>
                {Math.round(suggestion.confidence * 100)}%
              </span>
            </div>

            {/* Original Text */}
            <div className="mb-2">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Original</div>
              <p className="text-sm text-gray-700 dark:text-gray-300 line-through">
                {suggestion.originalText}
              </p>
            </div>

            {/* Suggested Text */}
            <div className="mb-2">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Suggestion</div>
              <p className="text-sm text-gray-900 dark:text-white">
                {suggestion.suggestedText}
              </p>
            </div>

            {/* Reason */}
            <div className="mb-3">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Reason</div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {suggestion.reason}
              </p>
            </div>

            {/* Actions */}
            <div className="flex space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onAccept(suggestion.id)
                }}
                className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 transition-colors"
              >
                Accept
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onReject(suggestion.id)
                }}
                className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center justify-between">
            <span>Segment: {segmentId}</span>
            <span>{suggestions.length} suggestion{suggestions.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
