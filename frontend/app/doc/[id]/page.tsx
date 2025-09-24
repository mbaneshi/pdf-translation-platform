// Next.js App Router page for document reader
import { notFound } from 'next/navigation'
import ReaderPage from '@/components/ReaderPage'

interface PageProps {
  params: {
    id: string
  }
}

export default async function DocumentPage({ params }: PageProps) {
  const documentId = parseInt(params.id)
  
  if (isNaN(documentId)) {
    notFound()
  }

  // In a real app, you'd fetch document details here
  // For now, mock some data or fetch minimal info
  const documentData = {
    id: documentId,
    filename: `Document ${documentId}.pdf`,
    totalPages: 10, // Placeholder
    fileUrl: `/api/documents/${documentId}/pdf`, // Placeholder for PDF serving
    uploadedAt: new Date().toISOString(),
    status: 'processed'
  }

  if (!documentData) {
    notFound()
  }

  return (
    <ReaderPage 
      documentId={documentData.id}
      document={documentData}
    />
  )
}

export async function generateMetadata({ params }: PageProps) {
  const documentId = parseInt(params.id)
  
  return {
    title: `Document ${documentId}`,
    description: `PDF Translation Platform - Document ${documentId}`
  }
}
