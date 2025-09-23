import React, { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useGlossary, GlossaryEntry } from '../../contexts/GlossaryContext';
import { PencilIcon, TrashIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface GlossaryEntryCardProps {
  entry: GlossaryEntry;
  onEdit: (entry: GlossaryEntry) => void;
  isSelected?: boolean;
  onSelect?: (id: number, selected: boolean) => void;
}

const GlossaryEntryCard: React.FC<GlossaryEntryCardProps> = ({
  entry,
  onEdit,
  isSelected = false,
  onSelect
}) => {
  const { theme } = useTheme();
  const { deleteEntry } = useGlossary();
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    const success = await deleteEntry(entry.id);
    setIsDeleting(false);
    
    if (success) {
      setShowDeleteConfirm(false);
    }
  };

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onSelect) {
      onSelect(entry.id, e.target.checked);
    }
  };

  return (
    <div className={`${theme.cardBg} rounded-lg border border-gray-200 p-4 transition-all hover:shadow-md ${
      isSelected ? 'ring-2 ring-blue-500' : ''
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3 flex-1">
          {onSelect && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={handleSelect}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          )}
          <div className="flex-1">
            <h3 className={`font-semibold ${theme.text} text-lg`}>{entry.term}</h3>
            <p className={`${theme.textSecondary} text-sm`}>{entry.translation}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onEdit(entry)}
            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
            title="Edit term"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          
          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="p-2 text-gray-400 hover:text-red-600 transition-colors"
              title="Delete term"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          ) : (
            <div className="flex items-center space-x-1">
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="p-1 text-green-600 hover:text-green-700 transition-colors disabled:opacity-50"
                title="Confirm delete"
              >
                <CheckIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="p-1 text-red-600 hover:text-red-700 transition-colors"
                title="Cancel delete"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Context */}
      {entry.context && (
        <div className="mb-3">
          <p className={`text-sm ${theme.textSecondary} italic`}>
            "{entry.context}"
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Created: {new Date(entry.created_at).toLocaleDateString()}</span>
        {entry.updated_at !== entry.created_at && (
          <span>Updated: {new Date(entry.updated_at).toLocaleDateString()}</span>
        )}
      </div>
    </div>
  );
};

export default GlossaryEntryCard;
