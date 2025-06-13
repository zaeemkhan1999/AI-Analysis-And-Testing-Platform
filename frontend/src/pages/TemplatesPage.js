import React, { useState } from 'react';
import { Plus, Edit, Trash2, Copy } from 'lucide-react';
import Editor from '@monaco-editor/react';
import {
  usePromptTemplates,
  useCreatePromptTemplate,
  useUpdatePromptTemplate,
  useDeletePromptTemplate,
  useInitializeDefaultTemplates
} from '../hooks/useApi';

const TemplatesPage = () => {
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt_text: '',
    category: 'custom',
    example_output: ''
  });

  const { data: templates = [], isLoading } = usePromptTemplates();
  const createMutation = useCreatePromptTemplate();
  const updateMutation = useUpdatePromptTemplate();
  const deleteMutation = useDeletePromptTemplate();
  const initMutation = useInitializeDefaultTemplates();

  const categories = [
    { value: 'summary', label: 'Summary' },
    { value: 'analysis', label: 'Analysis' },
    { value: 'extraction', label: 'Extraction' },
    { value: 'custom', label: 'Custom' }
  ];

  const handleSave = async () => {
    try {
      if (editingTemplate) {
        await updateMutation.mutateAsync({
          templateId: editingTemplate.id,
          template: formData
        });
      } else {
        await createMutation.mutateAsync(formData);
      }
      setShowModal(false);
      resetForm();
    } catch (error) {
      alert('Failed to save template: ' + error.message);
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      description: template.description || '',
      prompt_text: template.prompt_text,
      category: template.category || 'custom',
      example_output: template.example_output || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (templateId) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await deleteMutation.mutateAsync(templateId);
      } catch (error) {
        alert('Failed to delete template: ' + error.message);
      }
    }
  };

  const handleCopy = (template) => {
    navigator.clipboard.writeText(template.prompt_text);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      prompt_text: '',
      category: 'custom',
      example_output: ''
    });
    setEditingTemplate(null);
  };

  const handleInitDefaults = async () => {
    try {
      await initMutation.mutateAsync();
    } catch (error) {
      alert('Failed to initialize default templates: ' + error.message);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Prompt Templates</h1>
        <div className="flex items-center space-x-3">
          {templates.length === 0 && (
            <button
              onClick={handleInitDefaults}
              className="btn-secondary"
              disabled={initMutation.isLoading}
            >
              Initialize Defaults
            </button>
          )}
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Template
          </button>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  {template.name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {template.description}
                </p>
                <span className="inline-block mt-2 px-2 py-1 text-xs font-medium bg-primary-100 text-primary-800 rounded-full">
                  {template.category}
                </span>
              </div>
              <div className="flex items-center space-x-1 ml-4">
                <button
                  onClick={() => handleCopy(template)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  title="Copy prompt"
                >
                  <Copy className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleEdit(template)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  title="Edit template"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(template.id)}
                  className="p-1 text-red-400 hover:text-red-600"
                  title="Delete template"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <div className="mt-4">
              <p className="text-xs text-gray-500 mb-2">Prompt Preview:</p>
              <div className="bg-gray-50 rounded p-3 text-sm">
                <code className="text-gray-700">
                  {template.prompt_text.substring(0, 150)}
                  {template.prompt_text.length > 150 ? '...' : ''}
                </code>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
              <span>Used {template.usage_count} times</span>
              <span>{new Date(template.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="text-center py-12">
          <Plus className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No templates</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first prompt template.
          </p>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                {editingTemplate ? 'Edit Template' : 'Create Template'}
              </h3>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    placeholder="Template name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="input-field"
                  >
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input-field"
                  rows="2"
                  placeholder="Brief description of what this template does"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Text
                </label>
                <div className="border rounded-lg overflow-hidden">
                  <Editor
                    height="200px"
                    defaultLanguage="markdown"
                    value={formData.prompt_text}
                    onChange={(value) => setFormData({ ...formData, prompt_text: value || '' })}
                    theme="vs-light"
                    options={{
                      minimap: { enabled: false },
                      lineNumbers: 'on',
                      wordWrap: 'on',
                      fontSize: 14,
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Use {'{document_content}'} as a placeholder for the document text.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Example Output (Optional)
                </label>
                <textarea
                  value={formData.example_output}
                  onChange={(e) => setFormData({ ...formData, example_output: e.target.value })}
                  className="input-field"
                  rows="3"
                  placeholder="Example of what the AI response might look like"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowModal(false);
                  resetForm();
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!formData.name.trim() || !formData.prompt_text.trim()}
                className="btn-primary"
              >
                {editingTemplate ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplatesPage; 