'use client'

import { useEffect, useRef, useState } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

interface PdfCanvasProps {
  documentId: number
  pageNumber: number
  zoom: number
  onPageRender?: (page: number) => void
}

export default function PdfCanvas({ 
  documentId, 
  pageNumber, 
  zoom, 
  onPageRender 
}: PdfCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { currentTheme } = useTheme()

  useEffect(() => {
    const loadPdfPage = async () => {
      if (!canvasRef.current) return

      setIsLoading(true)
      setError(null)

      try {
        // For now, we'll create a placeholder canvas
        // In the future, this will integrate with pdf.js
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')
        
        if (!ctx) {
          throw new Error('Could not get canvas context')
        }

        // Set canvas size based on zoom
        const baseWidth = 800
        const baseHeight = 1000
        const scaledWidth = baseWidth * zoom
        const scaledHeight = baseHeight * zoom

        canvas.width = scaledWidth
        canvas.height = scaledHeight

        // Clear canvas
        ctx.clearRect(0, 0, scaledWidth, scaledHeight)

        // Draw placeholder content
        ctx.fillStyle = currentTheme === 'dark' ? '#374151' : '#ffffff'
        ctx.fillRect(0, 0, scaledWidth, scaledHeight)

        // Draw border
        ctx.strokeStyle = currentTheme === 'dark' ? '#6b7280' : '#d1d5db'
        ctx.lineWidth = 1
        ctx.strokeRect(0, 0, scaledWidth, scaledHeight)

        // Draw placeholder text
        ctx.fillStyle = currentTheme === 'dark' ? '#9ca3af' : '#6b7280'
        ctx.font = `${16 * zoom}px Arial`
        ctx.textAlign = 'center'
        ctx.fillText(
          `PDF Page ${pageNumber}`,
          scaledWidth / 2,
          scaledHeight / 2 - 20
        )
        
        ctx.font = `${12 * zoom}px Arial`
        ctx.fillText(
          `Document ID: ${documentId}`,
          scaledWidth / 2,
          scaledHeight / 2 + 20
        )
        
        ctx.fillText(
          `Zoom: ${Math.round(zoom * 100)}%`,
          scaledWidth / 2,
          scaledHeight / 2 + 40
        )

        // Draw page number indicator
        ctx.fillStyle = currentTheme === 'dark' ? '#3b82f6' : '#2563eb'
        ctx.font = `${14 * zoom}px Arial`
        ctx.fillText(
          `Page ${pageNumber}`,
          scaledWidth / 2,
          30 * zoom
        )

        onPageRender?.(pageNumber)
        setIsLoading(false)

      } catch (err) {
        console.error('Error loading PDF page:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
        setIsLoading(false)
      }
    }

    loadPdfPage()
  }, [documentId, pageNumber, zoom, currentTheme, onPageRender])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading PDF</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-800">
      {isLoading ? (
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading PDF page...</p>
        </div>
      ) : (
        <div className="max-w-full max-h-full overflow-auto">
          <canvas
            ref={canvasRef}
            className="border border-gray-200 dark:border-gray-700 shadow-lg"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </div>
      )}
    </div>
  )
}
