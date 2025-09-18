// Environment-aware API client
// Handles build-time vs runtime environment detection

const getApiBaseUrl = () => {
  // Check if we're running in a browser (client-side)
  if (typeof window !== 'undefined') {
    // Browser environment - use the dedicated API subdomain
    // This should be set at build time via NEXT_PUBLIC_API_URL
    const browserUrl = process.env.NEXT_PUBLIC_API_URL;
    
    if (browserUrl) return browserUrl;
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

// Enhanced fetch wrapper with comprehensive error handling and logging
const apiFetch = async (endpoint, options = {}) => {
  const url = `${getApiUrl()}${endpoint}`;
  
  // Log request details (lightweight)
  console.log('[API] Making request:', { url, method: options.method || 'GET' });
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: (options && options.body instanceof FormData)
        ? { ...(options.headers || {}) }
        : { 'Content-Type': 'application/json', ...(options.headers || {}) },
    });
    
    // Log response status
    console.log('[API] Response received:', { url, status: response.status });
    
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (parseError) {
        console.warn('[API] Failed to parse error response as JSON:', parseError);
        errorData = { 
          message: `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
          statusText: response.statusText
        };
      }
      
      // Enhanced error with more context
      const enhancedError = new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      enhancedError.status = response.status;
      enhancedError.statusText = response.statusText;
      enhancedError.url = url;
      enhancedError.response = errorData;
      enhancedError.timestamp = new Date().toISOString();
      
      console.error('[API] Request failed:', {
        url,
        status: response.status,
        statusText: response.statusText,
        errorData,
        timestamp: new Date().toISOString()
      });
      
      throw enhancedError;
    }
    
    // Parse body safely (supports plain text/json)
    let data;
    try {
      const text = await response.text();
      data = text ? JSON.parse(text) : {};
    } catch (_) {
      data = {};
    }
    return data;
  } catch (error) {
    // Enhanced error logging with network detection
    const isNetworkError = error.name === 'TypeError' && (
      error.message.includes('fetch') || 
      error.message.includes('Failed to fetch') ||
      error.message.includes('NetworkError')
    );
    
    const errorContext = {
      url,
      errorName: error.name,
      errorMessage: error.message,
      isNetworkError,
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      online: typeof navigator !== 'undefined' ? navigator.onLine : 'unknown'
    };
    
    console.error('[API] Fetch Error:', errorContext);
    
    // Enhance error with additional context
    if (isNetworkError) {
      error.isNetworkError = true;
      error.possibleCauses = [
        'Server is down or unreachable',
        'CORS configuration issue',
        'Network connectivity problem',
        'DNS resolution failure',
        'Firewall blocking the request'
      ];
    }
    
    error.url = url;
    error.timestamp = errorContext.timestamp;
    
    throw error;
  }
};

export const api = {
  // Document endpoints
  uploadDocument: async (file) => {
    // Enhanced file validation and debugging
    console.log('[API] File object details:', {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      constructor: file.constructor.name,
      isFile: file instanceof File,
      isBlob: file instanceof Blob,
      hasContent: file.size > 0,
      timestamp: new Date().toISOString()
    });

    // Check if file is actually a File object
    if (!(file instanceof File)) {
      throw new Error('Invalid file object: not a File instance');
    }

    // Check if file has content
    if (file.size === 0) {
      throw new Error('File is empty');
    }

    const formData = new FormData();
    formData.append('file', file);
    
    // Debug FormData contents
    console.log('[API] FormData entries:');
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}:`, {
        type: typeof value,
        constructor: value.constructor.name,
        size: value.size || 'N/A',
        name: value.name || 'N/A'
      });
    }
    
    // Use apiFetch to handle response uniformly; ensure headers logic keeps FormData boundary
    return apiFetch('/api/documents/upload', { method: 'POST', body: formData });
  },

  getDocument: async (documentId) => {
    return apiFetch(`/api/documents/${documentId}`);
  },

  getDocumentPages: async (documentId) => {
    return apiFetch(`/api/documents/${documentId}/pages`);
  },

  getProgress: async (documentId) => {
    return apiFetch(`/api/enhanced/translation-progress/${documentId}`);
  },

  exportMarkdown: async (documentId) => {
    return apiFetch(`/api/enhanced/export/${documentId}`);
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
