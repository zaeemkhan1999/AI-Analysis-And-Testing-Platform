import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Brain, Play, Copy, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Editor from '@monaco-editor/react';
import {
  useDocument,
  usePromptTemplates,
  useAnalyzeDocument,
  useAnalyses
} from '../hooks/useApi';

const AnalysisPage = () => {
  const { documentId } = useParams();
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [customPrompt, setCustomPrompt] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const { data: document } = useDocument(documentId);
  const { data: templates = [] } = usePromptTemplates();
  const { data: analyses = [] } = useAnalyses(documentId);
  const analyzeMutation = useAnalyzeDocument();

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setCustomPrompt(template.prompt_text.replace('{document_content}', '{document_content}'));
    }
  };

  const handleAnalyze = async () => {
    if (!documentId || !customPrompt.trim()) return;

    setIsAnalyzing(true);
    try {
      const result = await analyzeMutation.mutateAsync({
        documentId,
        prompt: customPrompt,
        promptTemplateId: selectedTemplate || null
      });
      setAnalysisResult(result);
    } catch (error) {
      alert('Analysis failed: ' + error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (!documentId) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <Brain className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No document selected</h3>
          <p className="mt-1 text-sm text-gray-500">
            Please select a document to analyze.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">AI Analysis</h1>
        {document && (
          <div className="text-sm text-gray-500">
            Analyzing: {document.filename}
          </div>
        )}
      </div>

      {document?.status !== 'ready' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <p className="text-sm text-yellow-800">
            Document is not ready for analysis. Status: {document?.status}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Prompt Editor */}
        <div className="space-y-6">
          {/* Template Selection */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Prompt Templates
            </h2>
            <select
              value={selectedTemplate}
              onChange={(e) => handleTemplateSelect(e.target.value)}
              className="input-field"
            >
              <option value="">Select a template...</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name} - {template.category}
                </option>
              ))}
            </select>
          </div>

          {/* Prompt Editor */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Custom Prompt
              </h2>
              <button
                onClick={handleAnalyze}
                disabled={!customPrompt.trim() || document?.status !== 'ready' || isAnalyzing}
                className="btn-primary flex items-center"
              >
                {isAnalyzing ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {isAnalyzing ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
            
            <div className="border rounded-lg overflow-hidden">
              <Editor
                height="300px"
                defaultLanguage="markdown"
                value={customPrompt}
                onChange={(value) => setCustomPrompt(value || '')}
                theme="vs-light"
                options={{
                  minimap: { enabled: false },
                  lineNumbers: 'on',
                  wordWrap: 'on',
                  fontSize: 14,
                }}
              />
            </div>
            
            <p className="text-xs text-gray-500 mt-2">
              Use {'{document_content}'} as a placeholder for the document text.
            </p>
          </div>
        </div>

        {/* Right Column - Results */}
        <div className="space-y-6">
          {/* Current Analysis Result */}
          {analysisResult && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Analysis Result
                </h2>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => copyToClipboard(analysisResult.response)}
                    className="btn-secondary flex items-center"
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </button>
                  <button className="btn-secondary flex items-center">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </button>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <div className="markdown-content">
                  <ReactMarkdown>{analysisResult.response}</ReactMarkdown>
                </div>
              </div>
              
              <div className="mt-4 text-xs text-gray-500 flex items-center justify-between">
                <span>
                  Execution time: {analysisResult.execution_time_ms}ms
                </span>
                {analysisResult.tokens_used && (
                  <span>
                    Tokens used: {analysisResult.tokens_used}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Previous Analyses */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Previous Analyses
            </h2>
            
            {analyses.length === 0 ? (
              <div className="text-center py-8">
                <Brain className="mx-auto h-8 w-8 text-gray-400" />
                <p className="mt-2 text-sm text-gray-600">
                  No previous analyses found.
                </p>
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {analyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                    onClick={() => setAnalysisResult(analysis)}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(analysis.created_at).toLocaleDateString()}
                      </p>
                      <span className="text-xs text-gray-500">
                        {analysis.execution_time_ms}ms
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1 truncate">
                      {analysis.final_prompt.substring(0, 100)}...
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage; 