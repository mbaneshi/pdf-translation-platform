import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

interface PageData {
  page_id: number
  page_number: number
  document_id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  source_text: string
  translated_text: string | null
  provider: string
  cost_estimate: number
  translation_time: number | null
  quality_score: number | null
  tokens_used: number | null
  created_at: string
  updated_at: string
}

export function usePageData(documentId: number, pageNumber: number) {
  return useQuery({
    queryKey: ['page', documentId, pageNumber],
    queryFn: async (): Promise<PageData> => {
      return api.getPageWithTranslation(documentId, pageNumber)
    },
    enabled: !!documentId && !!pageNumber,
    refetchInterval: (data) => {
      // Refetch every 2 seconds if page is processing
      return data?.status === 'processing' ? 2000 : false
    },
    staleTime: 1000, // Consider data stale after 1 second
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })
}