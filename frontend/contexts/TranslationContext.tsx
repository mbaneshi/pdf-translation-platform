import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

// Types
export interface TranslationJob {
  id: number;
  document_id: number;
  user_id: number;
  prompt_template_id?: number;
  celery_task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface TranslationSettings {
  target_language: string;
  translation_style: 'academic' | 'technical' | 'general';
  use_glossary: boolean;
  prompt_template_id?: number;
}

export interface TranslationResult {
  job_id: number;
  translated_text: string;
  quality_score: number;
  consistency_score: number;
  processing_time: number;
}

export interface TranslationContextType {
  currentJob: TranslationJob | null;
  translationResult: TranslationResult | null;
  isLoading: boolean;
  settings: TranslationSettings;
  setSettings: (settings: TranslationSettings) => void;
  startTranslation: (documentId: number, settings: TranslationSettings) => Promise<boolean>;
  getTranslationStatus: (jobId: number) => Promise<TranslationJob | null>;
  getTranslationResult: (jobId: number) => Promise<TranslationResult | null>;
  cancelTranslation: (jobId: number) => Promise<boolean>;
  getTranslationHistory: () => Promise<TranslationJob[]>;
}

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

export const useTranslation = (): TranslationContextType => {
  const context = useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslation must be used within a TranslationProvider');
  }
  return context;
};

interface TranslationProviderProps {
  children: ReactNode;
}

export const TranslationProvider: React.FC<TranslationProviderProps> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [currentJob, setCurrentJob] = useState<TranslationJob | null>(null);
  const [translationResult, setTranslationResult] = useState<TranslationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState<TranslationSettings>({
    target_language: 'persian',
    translation_style: 'academic',
    use_glossary: true,
  });

  // Start translation job
  const startTranslation = async (documentId: number, translationSettings: TranslationSettings): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      setIsLoading(true);
      const response = await fetch('/api/translation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          document_id: documentId,
          ...translationSettings
        })
      });

      if (response.ok) {
        const job = await response.json();
        setCurrentJob(job);
        setSettings(translationSettings);
        toast.success('Translation started successfully');
        
        // Start polling for status updates
        pollTranslationStatus(job.id);
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to start translation');
        return false;
      }
    } catch (error) {
      console.error('Error starting translation:', error);
      toast.error('Failed to start translation');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Get translation job status
  const getTranslationStatus = async (jobId: number): Promise<TranslationJob | null> => {
    if (!isAuthenticated || !token) return null;

    try {
      const response = await fetch(`/api/translation/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const job = await response.json();
        setCurrentJob(job);
        return job;
      } else {
        console.error('Failed to get translation status');
        return null;
      }
    } catch (error) {
      console.error('Error getting translation status:', error);
      return null;
    }
  };

  // Get translation result
  const getTranslationResult = async (jobId: number): Promise<TranslationResult | null> => {
    if (!isAuthenticated || !token) return null;

    try {
      const response = await fetch(`/api/translation/jobs/${jobId}/result`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        setTranslationResult(result);
        return result;
      } else {
        console.error('Failed to get translation result');
        return null;
      }
    } catch (error) {
      console.error('Error getting translation result:', error);
      return null;
    }
  };

  // Cancel translation job
  const cancelTranslation = async (jobId: number): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    try {
      const response = await fetch(`/api/translation/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setCurrentJob(null);
        toast.success('Translation cancelled');
        return true;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to cancel translation');
        return false;
      }
    } catch (error) {
      console.error('Error cancelling translation:', error);
      toast.error('Failed to cancel translation');
      return false;
    }
  };

  // Get translation history
  const getTranslationHistory = async (): Promise<TranslationJob[]> => {
    if (!isAuthenticated || !token) return [];

    try {
      const response = await fetch('/api/translation/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const history = await response.json();
        return history;
      } else {
        console.error('Failed to get translation history');
        return [];
      }
    } catch (error) {
      console.error('Error getting translation history:', error);
      return [];
    }
  };

  // Poll for translation status updates
  const pollTranslationStatus = async (jobId: number) => {
    const pollInterval = setInterval(async () => {
      const job = await getTranslationStatus(jobId);
      
      if (job) {
        if (job.status === 'completed') {
          clearInterval(pollInterval);
          await getTranslationResult(jobId);
          toast.success('Translation completed successfully');
        } else if (job.status === 'failed') {
          clearInterval(pollInterval);
          toast.error(job.error_message || 'Translation failed');
        }
      } else {
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 600000);
  };

  const value: TranslationContextType = {
    currentJob,
    translationResult,
    isLoading,
    settings,
    setSettings,
    startTranslation,
    getTranslationStatus,
    getTranslationResult,
    cancelTranslation,
    getTranslationHistory,
  };

  return (
    <TranslationContext.Provider value={value}>
      {children}
    </TranslationContext.Provider>
  );
};
