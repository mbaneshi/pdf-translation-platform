// Next.js App Router page for document reader
import { notFound } from 'next/navigation'
import { getDocument } from '@/lib/api'
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

  try {
    const document = await getDocument(documentId)
    
    if (!document) {
      notFound()
    }

    return (
      <ReaderPage 
        documentId={documentId}
        document={document}
      />
    )
  } catch (error) {
    console.error('Error loading document:', error)
    notFound()
  }
}

export async function generateMetadata({ params }: PageProps) {
  const documentId = parseInt(params.id)
  
  try {
    const document = await getDocument(documentId)
    return {
      title: document?.filename || 'Document',
      description: `PDF Translation Platform - ${document?.filename || 'Document'}`
    }
  } catch {
    return {
      title: 'Document Not Found',
      description: 'The requested document could not be found'
    }
  }
}
