'use client'

import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import PdfCanvas from './viewer/PdfCanvas'
import TranslatePane from './viewer/TranslatePane'
import MiniMap from './viewer/MiniMap'
import Toolbar from './viewer/Toolbar'
import { usePageData } from '../hooks/usePageData'
import { useTranslatePage } from '../hooks/useTranslatePage'
import { usePageChannel } from '../hooks/usePageChannel'

interface Document {
  id: number
  filename: string
  totalPages: number
  fileUrl: string
  uploadedAt: string
  status: string
}

interface ReaderPageProps {
  documentId: number
  document: Document
}

export default function ReaderPage({ documentId, document }: ReaderPageProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [zoom, setZoom] = useState(1)
  const [splitRatio, setSplitRatio] = useState(50)
  const [showMiniMap, setShowMiniMap] = useState(true)
  const { theme } = useTheme()

  // Get current page data
  const { data: pageData, isLoading, error } = usePageData(documentId, currentPage)
  
  // Translation hook
  const translatePage = useTranslatePage(documentId, currentPage)
  
  // WebSocket connection for real-time updates
  // const { isConnected, sendMessage } = usePageChannel({ pageId: documentId })
  const isConnected = false
  const sendMessage = () => {}

  // Handle page navigation
  const handlePageChange = (pageNumber: number) => {
    if (pageNumber >= 1 && pageNumber <= document.totalPages) {
      setCurrentPage(pageNumber)
    }
  }

  // Handle translation
  const handleTranslatePage = async () => {
    try {
      await translatePage.mutateAsync('openai') // Provide default provider
    } catch (error) {
      console.error('Translation failed:', error)
    }
  }

  // Handle zoom changes
  const handleZoomChange = (newZoom: number) => {
    setZoom(Math.max(0.5, Math.min(3, newZoom)))
  }

  // Handle split ratio changes
  const handleSplitChange = (ratio: number) => {
    setSplitRatio(Math.max(20, Math.min(80, ratio)))
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return // Don't handle shortcuts when typing
      }

      switch (event.key) {
        case 'j':
        case 'ArrowDown':
          event.preventDefault()
          handlePageChange(currentPage + 1)
          break
        case 'k':
        case 'ArrowUp':
          event.preventDefault()
          handlePageChange(currentPage - 1)
          break
        case 't':
          event.preventDefault()
          handleTranslatePage()
          break
        case 'm':
          event.preventDefault()
          setShowMiniMap(!showMiniMap)
          break
        case 'g':
          event.preventDefault()
          const pageNumber = prompt('Go to page:')
          if (pageNumber) {
            const page = parseInt(pageNumber)
            if (!isNaN(page)) {
              handlePageChange(page)
            }
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentPage, showMiniMap])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Page</h2>
          <p className="text-gray-600">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex bg-white dark:bg-gray-900">
      {/* Mini Map */}
      {showMiniMap && (
        <div className="w-64 border-r border-gray-200 dark:border-gray-700">
          <MiniMap
            pages={Array.from({ length: document.totalPages }, (_, i) => ({
              pageNumber: i + 1,
              status: i + 1 === currentPage ? 'current' : 'pending'
            }))}
            currentPage={currentPage}
            onPageChange={handlePageChange}
            documentId={documentId}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <Toolbar
          currentPage={currentPage}
          totalPages={document.totalPages}
          zoom={zoom}
          splitRatio={splitRatio}
          isTranslating={translatePage.isPending}
          onPageChange={handlePageChange}
          onTranslatePage={handleTranslatePage}
          onZoomChange={handleZoomChange}
          onSplitChange={handleSplitChange}
          onToggleMiniMap={() => setShowMiniMap(!showMiniMap)}
          showMiniMap={showMiniMap}
        />

        {/* Dual Pane Viewer */}
        <div className="flex-1 flex">
          {/* PDF Canvas */}
          <div 
            className="border-r border-gray-200 dark:border-gray-700"
            style={{ width: `${splitRatio}%` }}
          >
            <PdfCanvas
              documentId={documentId}
              pageNumber={currentPage}
              zoom={zoom}
              onPageRender={(page) => {
                // Handle page render events
                console.log(`Page ${page} rendered`)
              }}
            />
          </div>

          {/* Translation Pane */}
          <div style={{ width: `${100 - splitRatio}%` }}>
            <TranslatePane
              pageId={pageData?.page_id}
              pageNumber={currentPage}
              sourceText={pageData?.source_text || ''}
              translatedText={pageData?.translated_text || ''}
              status={pageData?.status || 'pending'}
              provider={pageData?.provider}
              cost={pageData?.cost_estimate}
              isLoading={isLoading}
              onSuggest={(segmentId, text) => {
                // Handle suggestion requests
                console.log('Suggestion requested:', segmentId, text)
              }}
            />
          </div>
        </div>

        {/* Status Bar */}
        <div className="h-8 bg-gray-100 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex items-center px-4 text-sm text-gray-600 dark:text-gray-400">
          <span>Page {currentPage} of {document.totalPages}</span>
          <span className="ml-4">Zoom: {Math.round(zoom * 100)}%</span>
          {isConnected && (
            <span className="ml-4 text-green-600">● Connected</span>
          )}
          {pageData?.provider && (
            <span className="ml-4">Provider: {pageData.provider}</span>
          )}
        </div>
      </div>
    </div>
  )
}
