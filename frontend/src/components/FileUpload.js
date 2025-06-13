import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { useUploadFile } from '../hooks/useApi';
import { progressApi } from '../services/api';

const FileUpload = ({ onUploadComplete }) => {
  const [uploadProgress, setUploadProgress] = useState({});
  const [processingStatus, setProcessingStatus] = useState({});
  
  const uploadMutation = useUploadFile();

  const onDrop = useCallback(async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      const fileId = `${file.name}-${Date.now()}`;
      
      setUploadProgress(prev => ({ ...prev, [fileId]: 0 }));
      setProcessingStatus(prev => ({ ...prev, [fileId]: { stage: 'Uploading...', progress: 0, status: 'uploading' } }));

      try {
        const response = await uploadMutation.mutateAsync({
          file,
          onProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => ({ ...prev, [fileId]: progress }));
          }
        });

        // Start listening for processing updates
        const eventSource = progressApi.streamProgress(response.file_id);
        
        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setProcessingStatus(prev => ({
            ...prev,
            [fileId]: {
              stage: data.stage,
              progress: data.progress,
              status: data.status
            }
          }));

          if (data.status === 'ready' || data.status === 'error') {
            eventSource.close();
            if (onUploadComplete) {
              onUploadComplete(response);
            }
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          setProcessingStatus(prev => ({
            ...prev,
            [fileId]: {
              stage: 'Connection error',
              progress: 0,
              status: 'error'
            }
          }));
        };

      } catch (error) {
        setProcessingStatus(prev => ({
          ...prev,
          [fileId]: {
            stage: `Upload failed: ${error.message}`,
            progress: 0,
            status: 'error'
          }
        }));
      }
    }
  }, [uploadMutation, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt']
    },
    maxSize: 5 * 1024 * 1024, // 5MB
    multiple: true
  });

  const hasActiveUploads = Object.keys(uploadProgress).length > 0;

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          dropzone border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          {isDragActive ? (
            'Drop the files here...'
          ) : (
            'Drag & drop PDF or TXT files here, or click to select files'
          )}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Maximum file size: 5MB
        </p>
      </div>

      {/* Upload Progress */}
      {hasActiveUploads && (
        <div className="mt-6 space-y-4">
          {Object.entries(uploadProgress).map(([fileId, progress]) => {
            const status = processingStatus[fileId];
            const fileName = fileId.split('-')[0];
            
            return (
              <div key={fileId} className="bg-white rounded-lg border p-4">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-3" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{fileName}</p>
                    <p className="text-xs text-gray-500">
                      {status?.stage || 'Preparing...'}
                    </p>
                  </div>
                  <div className="ml-4">
                    {status?.status === 'ready' && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                    {status?.status === 'error' && (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                  </div>
                </div>
                
                <div className="mt-2">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${status?.progress || progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {status?.progress || progress}% complete
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FileUpload; 