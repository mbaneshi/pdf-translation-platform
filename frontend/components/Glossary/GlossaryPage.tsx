import React, { useState, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useGlossary, GlossaryEntry } from '../../contexts/GlossaryContext';
import GlossaryEntryForm from './GlossaryEntryForm';
import GlossaryEntryCard from './GlossaryEntryCard';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  TrashIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';

const GlossaryPage: React.FC = () => {
  const { theme } = useTheme();
  const { 
    filteredEntries, 
    isLoading, 
    searchTerm, 
    setSearchTerm, 
    createEntry, 
    updateEntry, 
    deleteEntries,
    exportGlossary,
    importGlossary 
  } = useGlossary();
  
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<GlossaryEntry | null>(null);
  const [selectedEntries, setSelectedEntries] = useState<Set<number>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAddEntry = () => {
    setEditingEntry(null);
    setIsFormOpen(true);
  };

  const handleEditEntry = (entry: GlossaryEntry) => {
    setEditingEntry(entry);
    setIsFormOpen(true);
  };

  const handleFormSubmit = async (entryData: { term: string; translation: string; context?: string }) => {
    if (editingEntry) {
      return await updateEntry(editingEntry.id, entryData);
    } else {
      return await createEntry(entryData);
    }
  };

  const handleSelectEntry = (id: number, selected: boolean) => {
    const newSelected = new Set(selectedEntries);
    if (selected) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedEntries(newSelected);
    setShowBulkActions(newSelected.size > 0);
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedEntries(new Set(filteredEntries.map(e => e.id)));
    } else {
      setSelectedEntries(new Set());
    }
    setShowBulkActions(selected);
  };

  const handleBulkDelete = async () => {
    if (selectedEntries.size === 0) return;
    
    const success = await deleteEntries(Array.from(selectedEntries));
    if (success) {
      setSelectedEntries(new Set());
      setShowBulkActions(false);
    }
  };

  const handleImport = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await importGlossary(file);
      e.target.value = ''; // Reset input
    }
  };

  const handleExport = () => {
    exportGlossary();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className={`text-3xl font-bold ${theme.text} mb-2`}>Glossary</h1>
        <p className={`${theme.textSecondary}`}>
          Manage your translation terms and maintain consistency across documents.
        </p>
      </div>

      {/* Actions Bar */}
      <div className={`${theme.cardBg} rounded-lg p-4 mb-6 shadow-sm`}>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search terms, translations, or context..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleAddEntry}
              className={`inline-flex items-center px-4 py-2 bg-gradient-to-r ${theme.primary} text-white rounded-lg hover:opacity-90 transition-all`}
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Term
            </button>

            <button
              onClick={handleImport}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
              Import
            </button>

            <button
              onClick={handleExport}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        </div>

        {/* Bulk Actions */}
        {showBulkActions && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {selectedEntries.size} term{selectedEntries.size !== 1 ? 's' : ''} selected
              </span>
              <button
                onClick={handleBulkDelete}
                className="inline-flex items-center px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <TrashIcon className="h-4 w-4 mr-2" />
                Delete Selected
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Select All */}
      {filteredEntries.length > 0 && (
        <div className="mb-4">
          <label className="inline-flex items-center">
            <input
              type="checkbox"
              checked={selectedEntries.size === filteredEntries.length && filteredEntries.length > 0}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-600">Select all</span>
          </label>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className={`mt-4 ${theme.textSecondary}`}>Loading glossary...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredEntries.length === 0 && (
        <div className="text-center py-12">
          <FunnelIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className={`text-lg font-medium ${theme.text} mb-2`}>
            {searchTerm ? 'No matching terms found' : 'No terms in your glossary'}
          </h3>
          <p className={`${theme.textSecondary} mb-6`}>
            {searchTerm 
              ? 'Try adjusting your search terms or clear the search to see all terms.'
              : 'Start building your glossary by adding your first term.'
            }
          </p>
          {!searchTerm && (
            <button
              onClick={handleAddEntry}
              className={`inline-flex items-center px-4 py-2 bg-gradient-to-r ${theme.primary} text-white rounded-lg hover:opacity-90 transition-all`}
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Your First Term
            </button>
          )}
        </div>
      )}

      {/* Glossary Entries Grid */}
      {!isLoading && filteredEntries.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEntries.map((entry) => (
            <GlossaryEntryCard
              key={entry.id}
              entry={entry}
              onEdit={handleEditEntry}
              isSelected={selectedEntries.has(entry.id)}
              onSelect={handleSelectEntry}
            />
          ))}
        </div>
      )}

      {/* Entry Form Modal */}
      <GlossaryEntryForm
        isOpen={isFormOpen}
        onClose={() => {
          setIsFormOpen(false);
          setEditingEntry(null);
        }}
        onSubmit={handleFormSubmit}
        initialData={editingEntry ? {
          term: editingEntry.term,
          translation: editingEntry.translation,
          context: editingEntry.context || ''
        } : undefined}
        title={editingEntry ? 'Edit Term' : 'Add Term'}
      />

      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
};

export default GlossaryPage;
