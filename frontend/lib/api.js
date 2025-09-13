// Environment-aware API client
// Handles build-time vs runtime environment detection

const getApiBaseUrl = () => {
  // Check if we're running in a browser (client-side)
  if (typeof window !== 'undefined') {
    // Browser environment - use the dedicated API subdomain
    // This should be set at build time via NEXT_PUBLIC_API_URL
    const browserUrl = process.env.NEXT_PUBLIC_API_URL;
    
    if (browserUrl && browserUrl !== 'http://localhost:8000') {
      return browserUrl;
    }
    
    // Fallback to dedicated API subdomain
    return 'https://apipdf.edcopo.info';
  }
  
  // Server-side (Docker container) - use dedicated API subdomain through Caddy
  // This ensures proper routing and HTTPS termination
  return process.env.NEXT_PUBLIC_API_URL || 'https://apipdf.edcopo.info';
};

// Get the appropriate API base URL for the current environment
const getApiUrl = () => {
  const baseUrl = getApiBaseUrl();
  
  // Debug logging (remove in production)
  if (typeof window !== 'undefined') {
    console.log('API Client - Browser environment detected, using:', baseUrl);
    console.log('API Client - NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
  } else {
    console.log('API Client - Server environment detected, using:', baseUrl);
  }
  
  return baseUrl;
};

// Enhanced fetch wrapper with better error handling
const apiFetch = async (endpoint, options = {}) => {
  const url = `${getApiUrl()}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `HTTP ${response.status}: ${response.statusText}` 
      }));
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  } catch (error) {
    console.error('API Fetch Error:', error);
    throw error;
  }
};

export const api = {
  // Document endpoints
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = `${getApiUrl()}/api/documents/upload`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type for FormData - let browser set it with boundary
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Upload failed' }));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error) {
      console.error('Upload Error:', error);
      throw error;
    }
  },

  getDocument: async (documentId) => {
    return apiFetch(`/api/documents/${documentId}`);
  },

  getDocumentPages: async (documentId) => {
    return apiFetch(`/api/documents/${documentId}/pages`);
  },

  startTranslation: async (documentId) => {
    return apiFetch(`/api/documents/${documentId}/translate`, {
      method: 'POST',
    });
  },

  translateTestPage: async (documentId, pageNumber) => {
    return apiFetch(`/api/documents/${documentId}/pages/${pageNumber}/test`, {
      method: 'POST',
    });
  },
};
