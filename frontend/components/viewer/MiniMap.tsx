'use client'

import { useState } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

interface PageMeta {
  pageNumber: number
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'current'
}

interface MiniMapProps {
  pages: PageMeta[]
  currentPage: number
  onPageChange: (pageNumber: number) => void
  documentId: number
}

export default function MiniMap({ 
  pages, 
  currentPage, 
  onPageChange, 
  documentId 
}: MiniMapProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const { theme } = useTheme()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'processing':
        return 'bg-blue-500 animate-pulse'
      case 'failed':
        return 'bg-red-500'
      case 'current':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-300 dark:bg-gray-600'
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
      case 'current':
        return '●'
      default:
        return '○'
    }
  }

  const filteredPages = pages.filter(page =>
    page.pageNumber.toString().includes(searchTerm) ||
    page.status.includes(searchTerm)
  )

  return (
    <div className={`h-full flex flex-col ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          Pages
        </h3>
        
        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search pages..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Page List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-2">
          {filteredPages.map((page) => (
            <div
              key={page.pageNumber}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                page.pageNumber === currentPage
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
              onClick={() => onPageChange(page.pageNumber)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {/* Status Indicator */}
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(page.status)}`} />
                  
                  {/* Page Number */}
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Page {page.pageNumber}
                  </span>
                </div>

                {/* Status Icon */}
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {getStatusIcon(page.status)}
                </span>
              </div>

              {/* Status Text */}
              <div className="mt-1">
                <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                  {page.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center justify-between mb-2">
            <span>Total: {pages.length} pages</span>
            <span>Current: {currentPage}</span>
          </div>
          
          {/* Status Legend */}
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span>Completed</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <span>Processing</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-gray-300 dark:bg-gray-600 rounded-full" />
              <span>Pending</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-red-500 rounded-full" />
              <span>Failed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
