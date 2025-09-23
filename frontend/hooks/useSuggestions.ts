import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { api } from '../lib/api'

interface Suggestion {
  id: string
  type: 'improvement' | 'glossary' | 'style' | 'grammar'
  original_text: string
  suggested_text: string
  confidence: number
  reason: string
  status: 'pending' | 'accepted' | 'rejected'
  created_at: string
  updated_at: string
}

interface SuggestionsResponse {
  page_id: number
  page_number: number
  suggestions: Suggestion[]
  total_count: number
}

interface AcceptSuggestionResponse {
  suggestion_id: string
  status: 'accepted'
  message: string
  updated_at: string
}

interface RejectSuggestionResponse {
  suggestion_id: string
  status: 'rejected'
  message: string
  updated_at: string
}

export function useSuggestions(documentId: number, pageNumber: number) {
  const queryClient = useQueryClient()

  // Query for suggestions
  const suggestionsQuery = useQuery({
    queryKey: ['suggestions', documentId, pageNumber],
    queryFn: async (): Promise<SuggestionsResponse> => {
      return api.getPageSuggestions(documentId, pageNumber)
    },
    enabled: !!documentId && !!pageNumber,
    staleTime: 30000, // Consider data stale after 30 seconds
    retry: 2
  })

  // Accept suggestion mutation
  const acceptSuggestion = useMutation({
    mutationFn: async (suggestionId: string): Promise<AcceptSuggestionResponse> => {
      return api.acceptSuggestion(suggestionId)
    },
    onSuccess: (data) => {
      // Invalidate suggestions and page data
      queryClient.invalidateQueries({ queryKey: ['suggestions', documentId, pageNumber] })
      queryClient.invalidateQueries({ queryKey: ['page', documentId, pageNumber] })
      
      toast.success('Suggestion accepted successfully!')
    },
    onError: (error: Error) => {
      toast.error(`Failed to accept suggestion: ${error.message}`)
    }
  })

  // Reject suggestion mutation
  const rejectSuggestion = useMutation({
    mutationFn: async (suggestionId: string): Promise<RejectSuggestionResponse> => {
      return api.rejectSuggestion(suggestionId)
    },
    onSuccess: (data) => {
      // Invalidate suggestions
      queryClient.invalidateQueries({ queryKey: ['suggestions', documentId, pageNumber] })
      
      toast.success('Suggestion rejected')
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject suggestion: ${error.message}`)
    }
  })

  return {
    suggestions: suggestionsQuery.data?.suggestions || [],
    totalCount: suggestionsQuery.data?.total_count || 0,
    isLoading: suggestionsQuery.isLoading,
    error: suggestionsQuery.error,
    refetch: suggestionsQuery.refetch,
    acceptSuggestion: acceptSuggestion.mutate,
    rejectSuggestion: rejectSuggestion.mutate,
    isAccepting: acceptSuggestion.isPending,
    isRejecting: rejectSuggestion.isPending
  }
}
