import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Brain, Settings, BarChart3 } from 'lucide-react';
import FileUpload from '../components/FileUpload';
import { useDocuments } from '../hooks/useApi';

const HomePage = () => {
  const { data: documents = [], isLoading, error, refetch } = useDocuments(0, 5);

  const handleUploadComplete = (response) => {
    // Refresh documents list
    refetch();
  };

  // Ensure documents is always an array
  const documentsList = Array.isArray(documents) ? documents : [];

  const stats = [
    { name: 'Total Documents', value: documentsList.length, icon: FileText },
    { name: 'AI Analyses', value: '0', icon: Brain },
    { name: 'Templates', value: '5', icon: Settings },
    { name: 'Success Rate', value: '95%', icon: BarChart3 },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Document AI Analysis Platform
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Upload your documents and let AI analyze them with customizable prompts. 
          Extract insights, summarize content, and discover patterns automatically.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="card text-center">
              <Icon className="mx-auto h-8 w-8 text-primary-600 mb-2" />
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-600">{stat.name}</p>
            </div>
          );
        })}
      </div>

      {/* File Upload */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Upload Documents
        </h2>
        <FileUpload onUploadComplete={handleUploadComplete} />
      </div>

      {/* Recent Documents */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Recent Documents
          </h2>
          <Link to="/documents" className="btn-primary">
            View All
          </Link>
        </div>
        
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading documents...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-sm text-red-600">Error loading documents. Please try again.</p>
          </div>
        ) : documentsList.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              No documents uploaded yet. Start by uploading your first document above.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documentsList.slice(0, 5).map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(doc.upload_time).toLocaleDateString()} • {(doc.file_size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`
                    px-2 py-1 text-xs rounded-full
                    ${doc.status === 'ready' ? 'bg-green-100 text-green-800' : 
                      doc.status === 'error' ? 'bg-red-100 text-red-800' : 
                      'bg-yellow-100 text-yellow-800'}
                  `}>
                    {doc.status}
                  </span>
                  {doc.status === 'ready' && (
                    <Link 
                      to={`/analysis/${doc.id}`}
                      className="text-primary-600 hover:text-primary-900 text-sm font-medium"
                    >
                      Analyze
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/documents" className="card hover:shadow-md transition-shadow">
          <FileText className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Manage Documents
          </h3>
          <p className="text-gray-600">
            View, organize, and manage all your uploaded documents
          </p>
        </Link>

        <Link to="/analysis" className="card hover:shadow-md transition-shadow">
          <Brain className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            AI Analysis
          </h3>
          <p className="text-gray-600">
            Analyze documents with AI using custom prompts and templates
          </p>
        </Link>

        <Link to="/templates" className="card hover:shadow-md transition-shadow">
          <Settings className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Prompt Templates
          </h3>
          <p className="text-gray-600">
            Create and manage reusable prompt templates for analysis
          </p>
        </Link>
      </div>
    </div>
  );
};

export default HomePage; 