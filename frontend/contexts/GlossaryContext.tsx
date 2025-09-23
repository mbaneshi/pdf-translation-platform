import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

// Types
export interface GlossaryEntry {
  id: number;
  term: string;
  translation: string;
  context?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateGlossaryEntry {
  term: string;
  translation: string;
  context?: string;
}

export interface UpdateGlossaryEntry {
  term?: string;
  translation?: string;
  context?: string;
}

export interface GlossaryContextType {
  entries: GlossaryEntry[];
  isLoading: boolean;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  filteredEntries: GlossaryEntry[];
  createEntry: (entry: CreateGlossaryEntry) => Promise<boolean>;
  updateEntry: (id: number, entry: UpdateGlossaryEntry) => Promise<boolean>;
  deleteEntry: (id: number) => Promise<boolean>;
  deleteEntries: (ids: number[]) => Promise<boolean>;
  extractTerms: (text: string) => Promise<string[]>;
  exportGlossary: () => Promise<void>;
  importGlossary: (file: File) => Promise<boolean>;
  refreshEntries: () => Promise<void>;
}

const GlossaryContext = createContext<GlossaryContextType | undefined>(undefined);

export const useGlossary = (): GlossaryContextType => {
  const context = useContext(GlossaryContext);
  if (!context) {
    throw new Error('useGlossary must be used within a GlossaryProvider');
  }
  return context;
};

interface GlossaryProviderProps {
  children: ReactNode;
}

export const GlossaryProvider: React.FC<GlossaryProviderProps> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [entries, setEntries] = useState<GlossaryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter entries based on search term
  const filteredEntries = entries.filter(entry =>
    entry.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.translation.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (entry.context && entry.context.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Fetch entries from API
  const fetchEntries = async (): Promise<void> => {
    if (!isAuthenticated || !token) return;

    try {
      setIsLoading(true);
      const response = await fetch('/api/glossary/entries', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEntries(data);
      } else {
        console.error('Failed to fetch glossary entries');
      }
    } catch (error) {
      console.error('Error fetching glossary entries:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Create new entry
  const createEntry = async (entry: CreateGlossaryEntry): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      setIsLoading(true);
      const response = await fetch('/api/glossary/entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(entry)
      });

      if (response.ok) {
        const newEntry = await response.json();
        setEntries(prev => [...prev, newEntry]);
        toast.success('Term added successfully');
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to add term');
        return false;
      }
    } catch (error) {
      console.error('Error creating glossary entry:', error);
      toast.error('Failed to add term');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Update entry
  const updateEntry = async (id: number, entry: UpdateGlossaryEntry): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/glossary/entries/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(entry)
      });

      if (response.ok) {
        const updatedEntry = await response.json();
        setEntries(prev => prev.map(e => e.id === id ? updatedEntry : e));
        toast.success('Term updated successfully');
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update term');
        return false;
      }
    } catch (error) {
      console.error('Error updating glossary entry:', error);
      toast.error('Failed to update term');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Delete single entry
  const deleteEntry = async (id: number): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/glossary/entries/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setEntries(prev => prev.filter(e => e.id !== id));
        toast.success('Term deleted successfully');
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete term');
        return false;
      }
    } catch (error) {
      console.error('Error deleting glossary entry:', error);
      toast.error('Failed to delete term');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Delete multiple entries
  const deleteEntries = async (ids: number[]): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      setIsLoading(true);
      const response = await fetch('/api/glossary/entries/bulk-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ ids })
      });

      if (response.ok) {
        setEntries(prev => prev.filter(e => !ids.includes(e.id)));
        toast.success('Terms deleted successfully');
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete terms');
        return false;
      }
    } catch (error) {
      console.error('Error deleting glossary entries:', error);
      toast.error('Failed to delete terms');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Extract terms from text
  const extractTerms = async (text: string): Promise<string[]> => {
    if (!isAuthenticated || !token) return [];

    try {
      const response = await fetch('/api/glossary/extract-terms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text })
      });

      if (response.ok) {
        const data = await response.json();
        return data.terms || [];
      } else {
        console.error('Failed to extract terms');
        return [];
      }
    } catch (error) {
      console.error('Error extracting terms:', error);
      return [];
    }
  };

  // Export glossary
  const exportGlossary = async (): Promise<void> => {
    if (!isAuthenticated || !token) return;

    try {
      const response = await fetch('/api/glossary/export', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'glossary.json';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Glossary exported successfully');
      } else {
        toast.error('Failed to export glossary');
      }
    } catch (error) {
      console.error('Error exporting glossary:', error);
      toast.error('Failed to export glossary');
    }
  };

  // Import glossary
  const importGlossary = async (file: File): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/glossary/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        await fetchEntries(); // Refresh entries
        toast.success('Glossary imported successfully');
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to import glossary');
        return false;
      }
    } catch (error) {
      console.error('Error importing glossary:', error);
      toast.error('Failed to import glossary');
      return false;
    }
  };

  // Refresh entries
  const refreshEntries = async (): Promise<void> => {
    await fetchEntries();
  };

  // Fetch entries when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchEntries();
    } else {
      setEntries([]);
    }
  }, [isAuthenticated, token]);

  const value: GlossaryContextType = {
    entries,
    isLoading,
    searchTerm,
    setSearchTerm,
    filteredEntries,
    createEntry,
    updateEntry,
    deleteEntry,
    deleteEntries,
    extractTerms,
    exportGlossary,
    importGlossary,
    refreshEntries,
  };

  return (
    <GlossaryContext.Provider value={value}>
      {children}
    </GlossaryContext.Provider>
  );
};