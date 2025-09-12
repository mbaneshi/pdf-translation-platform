const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  // Document endpoints
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },

  getDocument: async (documentId) => {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`);
    return response.json();
  },

  getDocumentPages: async (documentId) => {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/pages`);
    return response.json();
  },

  startTranslation: async (documentId) => {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/translate`, {
      method: 'POST',
    });
    return response.json();
  },

  translateTestPage: async (documentId, pageNumber) => {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/pages/${pageNumber}/test`, {
      method: 'POST',
    });
    return response.json();
  },
};
