import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';
import { useTheme } from '../contexts/ThemeContext';
import { useDocumentState } from '../contexts/DocumentContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Edit2, Save, Wand2, RotateCcw, Settings, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';

interface UserSettings {
  openai_api_key: string;
  default_model: string;
  system_prompt: string;
  translation_prompt: string;
  style_prompt: string;
  glossary_terms: Record<string, string>;
  sample_translations: Array<{id: string, original: string, translated: string}>;
  quality_level: string;
  preserve_formatting: boolean;
}

const ReviewPage: React.FC = () => {
  const { theme } = useTheme();
  const router = useRouter();
  const { documentId } = useDocumentState();
  const { page, preview } = router.query as { page?: string; preview?: string };
  const qc = useQueryClient();

  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setSaving] = useState(false);
  const [showPromptAdjustment, setShowPromptAdjustment] = useState(false);
  const [adjustmentPrompt, setAdjustmentPrompt] = useState('');
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Load user settings
    const savedSettings = localStorage.getItem('user-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }

    // Load preview text if available
    if (preview) {
      try {
        const sample = sessionStorage.getItem('pdftr.preview.sample');
        if (sample) {
          const parsed = JSON.parse(sample);
          setTranslatedText(parsed?.translated_text || '');
          setOriginalText(parsed?.original_text || '');
        }
      } catch {}
    }
  }, [preview]);

  // Resolve page_id by looking up document pages
  const pageNumber = page ? parseInt(page, 10) : undefined;
  const pagesQuery = useQuery({
    queryKey: ['pages', documentId],
    queryFn: () => api.getDocumentPages(documentId!),
    enabled: !!documentId && !preview,
  });

  const pageId = useMemo(() => {
    if (!Array.isArray(pagesQuery.data) || !pageNumber) return undefined;
    const match = pagesQuery.data.find((p) => p.page_number === pageNumber);
    return match?.id;
  }, [pagesQuery.data, pageNumber]);

  const detailQuery = useQuery({
    queryKey: ['page-detail', pageId],
    queryFn: () => api.getPageDetail(pageId!),
    enabled: !!pageId && !preview,
  });

  useEffect(() => {
    const data: any = detailQuery.data as any;
    if (data) {
      const orig = (data?.blocks || []).map((b: any) => b.text).join('\n\n');
      setOriginalText(orig || '');
      const initial = data?.blocks?.[0]?.segments?.[0]?.translated_text || '';
      if (!translatedText) setTranslatedText(initial);
    }
  }, [detailQuery.data]);

  const saveMutation = useMutation({
    mutationFn: async () => api.updatePageTranslation(pageId!, translatedText),
    onSuccess: () => {
      toast.success('Translation saved successfully!');
      setIsEditing(false);
      qc.invalidateQueries({ queryKey: ['page-detail', pageId] });
    },
    onError: () => toast.error('Failed to save changes'),
  });
  const saveChanges = async () => {
    if (!pageId) return;
    setSaving(true);
    try {
      await saveMutation.mutateAsync();
    } finally {
      setSaving(false);
    }
  };

  const adjustTranslation = async () => {
    if (!adjustmentPrompt.trim() || !settings?.openai_api_key) {
      toast.error('Please provide an adjustment prompt and API key');
      return;
    }

    setSaving(true);
    try {
      // Simulate API call with custom prompt
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Mock adjusted translation
      const adjustedText = translatedText + '\n\n[بر اساس درخواست تنظیم، ترجمه بازنگری شده است.]';
      setTranslatedText(adjustedText);
      setAdjustmentPrompt('');
      setShowPromptAdjustment(false);
      toast.success('Translation adjusted successfully!');
    } catch (error) {
      toast.error('Failed to adjust translation');
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(translatedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy text');
    }
  };

  const resetTranslation = () => {
    if (confirm('Are you sure you want to reset the translation?')) {
      // Reset to original translation
      setTranslatedText(translatedText);
      setIsEditing(false);
      setAdjustmentPrompt('');
    }
  };

  const applyGlossaryTerms = () => {
    if (!settings?.glossary_terms) return;

    let updatedText = translatedText;
    Object.entries(settings.glossary_terms).forEach(([source, target]) => {
      const regex = new RegExp(source, 'gi');
      updatedText = updatedText.replace(regex, target);
    });

    setTranslatedText(updatedText);
    toast.success('Glossary terms applied');
  };

  return (
    <div className={`min-h-screen ${theme.background}`}>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className={`text-2xl font-bold ${theme.text}`}>Document Review</h1>
            <p className={`text-sm ${theme.textSecondary}`}>
              Document {documentId} • Page {page || '1'}
            </p>
          </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => router.back()}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                >
                  Back to Documents
                </button>
                <button
                  onClick={async () => { if (pageId) { await api.approvePage(pageId); toast.success('Approved'); } }}
                  disabled={!pageId}
                  className="px-4 py-2 border border-green-300 text-green-700 rounded-lg hover:bg-green-50 text-sm"
                >
                  Approve
                </button>
                <button
                  onClick={async () => { if (pageId) { await api.rejectPage(pageId); toast.success('Rejected'); } }}
                  disabled={!pageId}
                  className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 text-sm"
                >
                  Reject
                </button>
                <button
                  onClick={() => setShowPromptAdjustment(!showPromptAdjustment)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm"
                >
                  <Settings size={16} /> Adjust
            </button>
          </div>
        </div>

        {/* Prompt Adjustment Panel */}
        {showPromptAdjustment && (
          <div className={`${theme.cardBg} p-6 rounded-xl mb-6 border`}>
            <h3 className={`text-lg font-semibold mb-4 ${theme.text}`}>Translation Adjustment</h3>
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme.text}`}>
                  Adjustment Instructions
                </label>
                <textarea
                  value={adjustmentPrompt}
                  onChange={(e) => setAdjustmentPrompt(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg text-gray-900 bg-white"
                  rows={3}
                  placeholder="Describe how you want the translation adjusted (e.g., 'Make it more formal', 'Use simpler language', 'Emphasize the philosophical terms')"
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={adjustTranslation}
                  disabled={isSaving || !adjustmentPrompt.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  <Wand2 size={16} />
                  {isSaving ? 'Adjusting...' : 'Apply Adjustment'}
                </button>
                <button
                  onClick={applyGlossaryTerms}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                >
                  Apply Glossary
                </button>
                <button
                  onClick={() => setShowPromptAdjustment(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Side-by-Side View */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Original Text Panel */}
          <div className={`${theme.cardBg} p-6 rounded-xl border`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`text-lg font-semibold ${theme.text}`}>Original Text</h2>
              <span className={`text-sm ${theme.textSecondary}`}>
                {originalText.length} characters
              </span>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
              <div className="text-sm leading-relaxed whitespace-pre-wrap text-gray-900">
                {originalText}
              </div>
            </div>
          </div>

          {/* Translated Text Panel */}
          <div className={`${theme.cardBg} p-6 rounded-xl border`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`text-lg font-semibold ${theme.text}`}>Persian Translation</h2>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${theme.textSecondary}`}>
                  {translatedText.length} characters
                </span>
                <button
                  onClick={copyToClipboard}
                  className="p-1.5 text-gray-500 hover:text-gray-700 rounded"
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            {isEditing ? (
              <div className="space-y-4">
                <textarea
                  value={translatedText}
                  onChange={(e) => setTranslatedText(e.target.value)}
                  className="w-full h-96 p-4 border rounded-lg text-gray-900 bg-white font-mono text-sm leading-relaxed"
                  style={{ direction: 'rtl' }}
                />
                <div className="flex items-center gap-3">
                  <button
                    onClick={saveChanges}
                    disabled={isSaving}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <Save size={16} />
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={resetTranslation}
                    className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 flex items-center gap-2"
                  >
                    <RotateCcw size={16} />
                    Reset
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                  <div
                    className="text-sm leading-relaxed whitespace-pre-wrap text-gray-900"
                    style={{ direction: 'rtl' }}
                  >
                    {translatedText}
                  </div>
                </div>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Edit2 size={16} />
                  Edit Translation
                </button>
              </div>
            )}
          </div>
        </div>

        {/* User Settings Info */}
        {settings && (
          <div className={`${theme.cardBg} p-4 rounded-xl border mt-6`}>
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <span className="font-medium">Active Settings:</span>
                {settings.default_model} • {settings.quality_level} quality •
                {Object.keys(settings.glossary_terms).length} glossary terms •
                {settings.sample_translations.length} style samples
              </div>
              <button
                onClick={() => router.push('/settings')}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                Configure Settings
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewPage;
