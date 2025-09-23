import React, { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface GlossaryEntryFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (entry: { term: string; translation: string; context?: string }) => Promise<boolean>;
  initialData?: {
    term: string;
    translation: string;
    context?: string;
  };
  title?: string;
}

const GlossaryEntryForm: React.FC<GlossaryEntryFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  title = 'Add Term'
}) => {
  const { theme } = useTheme();
  const [formData, setFormData] = useState({
    term: initialData?.term || '',
    translation: initialData?.translation || '',
    context: initialData?.context || '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.term.trim()) {
      newErrors.term = 'Term is required';
    }

    if (!formData.translation.trim()) {
      newErrors.translation = 'Translation is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    const success = await onSubmit(formData);
    setIsSubmitting(false);

    if (success) {
      setFormData({ term: '', translation: '', context: '' });
      setErrors({});
      onClose();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleClose = () => {
    setFormData({ term: '', translation: '', context: '' });
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={handleClose}
        />
        
        {/* Modal */}
        <div className="relative transform overflow-hidden rounded-xl shadow-xl transition-all max-w-md w-full">
          <div className={`${theme.cardBg} p-6`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-lg font-semibold ${theme.text}`}>{title}</h3>
              <button
                onClick={handleClose}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="term" className={`block text-sm font-medium ${theme.text} mb-2`}>
                  Term *
                </label>
                <input
                  type="text"
                  id="term"
                  name="term"
                  value={formData.term}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 rounded-lg border ${
                    errors.term ? 'border-red-500' : 'border-gray-300'
                  } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${theme.cardBg}`}
                  placeholder="Enter the term"
                  disabled={isSubmitting}
                />
                {errors.term && (
                  <p className="mt-1 text-sm text-red-600">{errors.term}</p>
                )}
              </div>

              <div>
                <label htmlFor="translation" className={`block text-sm font-medium ${theme.text} mb-2`}>
                  Translation *
                </label>
                <input
                  type="text"
                  id="translation"
                  name="translation"
                  value={formData.translation}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 rounded-lg border ${
                    errors.translation ? 'border-red-500' : 'border-gray-300'
                  } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${theme.cardBg}`}
                  placeholder="Enter the translation"
                  disabled={isSubmitting}
                />
                {errors.translation && (
                  <p className="mt-1 text-sm text-red-600">{errors.translation}</p>
                )}
              </div>

              <div>
                <label htmlFor="context" className={`block text-sm font-medium ${theme.text} mb-2`}>
                  Context
                </label>
                <textarea
                  id="context"
                  name="context"
                  value={formData.context}
                  onChange={handleInputChange}
                  rows={3}
                  className={`w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${theme.cardBg}`}
                  placeholder="Enter context (optional)"
                  disabled={isSubmitting}
                />
              </div>

              {/* Actions */}
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`flex-1 px-4 py-2 text-white bg-gradient-to-r ${theme.primary} rounded-lg hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isSubmitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlossaryEntryForm;
