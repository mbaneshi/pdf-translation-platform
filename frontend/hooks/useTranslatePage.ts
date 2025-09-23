import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { api } from '../lib/api'

interface TranslatePageResponse {
  job_id: string
  status: 'completed' | 'processing' | 'failed'
  message: string
}

export function useTranslatePage(documentId: number, pageNumber: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (provider?: string): Promise<TranslatePageResponse> => {
      return api.translatePageLazy(documentId, pageNumber, provider)
    },
    onMutate: async () => {
      // Optimistically update the page status
      const queryKey = ['page', documentId, pageNumber]
      
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey })

      // Snapshot the previous value
      const previousPageData = queryClient.getQueryData(queryKey)

      // Optimistically update to processing
      queryClient.setQueryData(queryKey, (old: any) => ({
        ...old,
        status: 'processing'
      }))

      return { previousPageData, queryKey }
    },
    onSuccess: (data) => {
      // Invalidate and refetch page data
      queryClient.invalidateQueries({ queryKey: ['page', documentId, pageNumber] })
      
      // Show success message
      if (data.status === 'completed') {
        toast.success('Page translated successfully!')
      } else if (data.status === 'processing') {
        toast.loading('Translation started...', { id: 'translate-page' })
      }
    },
    onError: (error: Error, variables, context) => {
      // Revert optimistic update
      if (context?.previousPageData) {
        queryClient.setQueryData(context.queryKey, context.previousPageData)
      }
      
      // Show error message
      toast.error(`Translation failed: ${error.message}`)
    },
    onSettled: () => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['page', documentId, pageNumber] })
    }
  })
}
