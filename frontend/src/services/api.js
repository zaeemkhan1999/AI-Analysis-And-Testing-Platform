import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// File upload API
export const fileApi = {
  upload: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress,
    });
    
    return response.data;
  },
  
  getDocuments: async (skip = 0, limit = 100) => {
    const response = await api.get(`/documents?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  getDocument: async (documentId) => {
    const response = await api.get(`/documents/${documentId}`);
    return response.data;
  },
  
  deleteDocument: async (documentId) => {
    const response = await api.delete(`/documents/${documentId}`);
    return response.data;
  },
};

// Progress tracking API
export const progressApi = {
  streamProgress: (fileId) => {
    return new EventSource(`${api.defaults.baseURL}/progress/${fileId}`);
  },
};

// AI Analysis API
export const aiApi = {
  getPromptTemplates: async (category = null, skip = 0, limit = 100) => {
    const params = new URLSearchParams({ skip, limit });
    if (category) params.append('category', category);
    
    const response = await api.get(`/prompt-templates?${params}`);
    return response.data;
  },
  
  createPromptTemplate: async (template) => {
    const response = await api.post('/prompt-templates', template);
    return response.data;
  },
  
  getPromptTemplate: async (templateId) => {
    const response = await api.get(`/prompt-templates/${templateId}`);
    return response.data;
  },
  
  updatePromptTemplate: async (templateId, template) => {
    const response = await api.put(`/prompt-templates/${templateId}`, template);
    return response.data;
  },
  
  deletePromptTemplate: async (templateId) => {
    const response = await api.delete(`/prompt-templates/${templateId}`);
    return response.data;
  },
  
  analyzeDocument: async (documentId, prompt, promptTemplateId = null) => {
    const response = await api.post('/analyze', {
      document_id: documentId,
      prompt,
      prompt_template_id: promptTemplateId,
    });
    return response.data;
  },
  
  getAnalyses: async (documentId = null, skip = 0, limit = 100) => {
    const params = new URLSearchParams({ skip, limit });
    if (documentId) params.append('document_id', documentId);
    
    const response = await api.get(`/analyses?${params}`);
    return response.data;
  },
  
  getAnalysis: async (analysisId) => {
    const response = await api.get(`/analyses/${analysisId}`);
    return response.data;
  },
  
  initializeDefaultTemplates: async () => {
    const response = await api.post('/init-default-templates');
    return response.data;
  },
};

export default api; 