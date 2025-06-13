import { useQuery, useMutation, useQueryClient } from 'react-query';
import { fileApi, aiApi } from '../services/api';

// Document hooks
export const useDocuments = (skip = 0, limit = 100) => {
  return useQuery(
    ['documents', skip, limit],
    () => fileApi.getDocuments(skip, limit),
    {
      staleTime: 30000, // 30 seconds
      refetchOnWindowFocus: false,
    }
  );
};

export const useDocument = (documentId) => {
  return useQuery(
    ['document', documentId],
    () => fileApi.getDocument(documentId),
    {
      enabled: !!documentId,
      staleTime: 60000, // 1 minute
    }
  );
};

export const useUploadFile = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ file, onProgress }) => fileApi.upload(file, onProgress),
    {
      onSuccess: () => {
        // Invalidate documents list to refresh it
        queryClient.invalidateQueries(['documents']);
      },
    }
  );
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (documentId) => fileApi.deleteDocument(documentId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['documents']);
      },
    }
  );
};

// Prompt template hooks
export const usePromptTemplates = (category = null, skip = 0, limit = 100) => {
  return useQuery(
    ['promptTemplates', category, skip, limit],
    () => aiApi.getPromptTemplates(category, skip, limit),
    {
      staleTime: 300000, // 5 minutes
      refetchOnWindowFocus: false,
    }
  );
};

export const usePromptTemplate = (templateId) => {
  return useQuery(
    ['promptTemplate', templateId],
    () => aiApi.getPromptTemplate(templateId),
    {
      enabled: !!templateId,
      staleTime: 300000, // 5 minutes
    }
  );
};

export const useCreatePromptTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (template) => aiApi.createPromptTemplate(template),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['promptTemplates']);
      },
    }
  );
};

export const useUpdatePromptTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ templateId, template }) => aiApi.updatePromptTemplate(templateId, template),
    {
      onSuccess: (data, { templateId }) => {
        queryClient.invalidateQueries(['promptTemplates']);
        queryClient.invalidateQueries(['promptTemplate', templateId]);
      },
    }
  );
};

export const useDeletePromptTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (templateId) => aiApi.deletePromptTemplate(templateId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['promptTemplates']);
      },
    }
  );
};

// AI Analysis hooks
export const useAnalyzeDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ documentId, prompt, promptTemplateId }) => 
      aiApi.analyzeDocument(documentId, prompt, promptTemplateId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['analyses']);
      },
    }
  );
};

export const useAnalyses = (documentId = null, skip = 0, limit = 100) => {
  return useQuery(
    ['analyses', documentId, skip, limit],
    () => aiApi.getAnalyses(documentId, skip, limit),
    {
      staleTime: 60000, // 1 minute
      refetchOnWindowFocus: false,
    }
  );
};

export const useAnalysis = (analysisId) => {
  return useQuery(
    ['analysis', analysisId],
    () => aiApi.getAnalysis(analysisId),
    {
      enabled: !!analysisId,
      staleTime: 300000, // 5 minutes
    }
  );
};

export const useInitializeDefaultTemplates = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    () => aiApi.initializeDefaultTemplates(),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['promptTemplates']);
      },
    }
  );
}; 