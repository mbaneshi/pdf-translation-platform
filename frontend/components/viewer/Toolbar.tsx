'use client'

import { useState } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

interface ToolbarProps {
  currentPage: number
  totalPages: number
  zoom: number
  splitRatio: number
  isTranslating: boolean
  onPageChange: (page: number) => void
  onTranslatePage: () => void
  onZoomChange: (zoom: number) => void
  onSplitChange: (ratio: number) => void
  onToggleMiniMap: () => void
  showMiniMap: boolean
}

export default function Toolbar({
  currentPage,
  totalPages,
  zoom,
  splitRatio,
  isTranslating,
  onPageChange,
  onTranslatePage,
  onZoomChange,
  onSplitChange,
  onToggleMiniMap,
  showMiniMap
}: ToolbarProps) {
  const [showZoomMenu, setShowZoomMenu] = useState(false)
  const [showSplitMenu, setShowSplitMenu] = useState(false)
  const { theme, toggleTheme } = useTheme()

  const handleZoomIn = () => {
    onZoomChange(zoom + 0.25)
  }

  const handleZoomOut = () => {
    onZoomChange(zoom - 0.25)
  }

  const handleZoomFit = () => {
    onZoomChange(1)
  }

  const handleSplitRatio = (ratio: number) => {
    onSplitChange(ratio)
    setShowSplitMenu(false)
  }

  return (
    <div className={`h-16 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 ${
      theme === 'dark' ? 'bg-gray-800' : 'bg-white'
    }`}>
      {/* Left Section */}
      <div className="flex items-center space-x-4">
        {/* Page Navigation */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {currentPage} / {totalPages}
          </span>
          
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Translation Button */}
        <button
          onClick={onTranslatePage}
          disabled={isTranslating}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isTranslating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Translating...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
              <span>Translate Page</span>
            </>
          )}
        </button>
      </div>

      {/* Center Section */}
      <div className="flex items-center space-x-4">
        {/* Zoom Controls */}
        <div className="relative">
          <button
            onClick={() => setShowZoomMenu(!showZoomMenu)}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2"
          >
            <span>{Math.round(zoom * 100)}%</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showZoomMenu && (
            <div className="absolute top-full left-0 mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg z-10">
              <div className="p-2">
                <button
                  onClick={handleZoomOut}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  Zoom Out
                </button>
                <button
                  onClick={handleZoomIn}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  Zoom In
                </button>
                <button
                  onClick={handleZoomFit}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  Fit to Width
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Split Ratio Controls */}
        <div className="relative">
          <button
            onClick={() => setShowSplitMenu(!showSplitMenu)}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2"
          >
            <span>{splitRatio}%</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showSplitMenu && (
            <div className="absolute top-full left-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg z-10">
              <div className="p-2">
                <button
                  onClick={() => handleSplitRatio(30)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  30% / 70%
                </button>
                <button
                  onClick={() => handleSplitRatio(50)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  50% / 50%
                </button>
                <button
                  onClick={() => handleSplitRatio(70)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  70% / 30%
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-4">
        {/* Mini Map Toggle */}
        <button
          onClick={onToggleMiniMap}
          className={`p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 ${
            showMiniMap ? 'bg-blue-100 dark:bg-blue-900' : ''
          }`}
          title="Toggle Mini Map"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Toggle Theme"
        >
          {theme === 'dark' ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        {/* Export Button */}
        <button
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2"
          title="Export Translation"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>Export</span>
        </button>
      </div>
    </div>
  )
}
