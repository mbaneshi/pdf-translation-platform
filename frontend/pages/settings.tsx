import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { Eye, EyeOff, Save, Plus, Trash2 } from 'lucide-react';

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

const SettingsPage: React.FC = () => {
  const { theme, themes, changeTheme } = useTheme();
  const [showApiKey, setShowApiKey] = useState(false);
  const [settings, setSettings] = useState<UserSettings>({
    openai_api_key: '',
    default_model: 'gpt-4o',
    system_prompt: 'You are a professional translator specializing in Persian translation of academic and philosophical texts.',
    translation_prompt: 'Translate the following English text to Persian, maintaining academic tone and philosophical precision:',
    style_prompt: 'Adapt your translation style based on the provided sample translations.',
    glossary_terms: {},
    sample_translations: [],
    quality_level: 'standard',
    preserve_formatting: true
  });
  const [newGlossaryTerm, setNewGlossaryTerm] = useState({ source: '', target: '' });
  const [newSampleTranslation, setNewSampleTranslation] = useState({ original: '', translated: '' });

  useEffect(() => {
    const savedSettings = localStorage.getItem('user-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const saveSettings = () => {
    localStorage.setItem('user-settings', JSON.stringify(settings));
    alert('Settings saved successfully!');
  };

  const addGlossaryTerm = () => {
    if (newGlossaryTerm.source && newGlossaryTerm.target) {
      setSettings(prev => ({
        ...prev,
        glossary_terms: {
          ...prev.glossary_terms,
          [newGlossaryTerm.source]: newGlossaryTerm.target
        }
      }));
      setNewGlossaryTerm({ source: '', target: '' });
    }
  };

  const removeGlossaryTerm = (term: string) => {
    setSettings(prev => {
      const newTerms = { ...prev.glossary_terms };
      delete newTerms[term];
      return { ...prev, glossary_terms: newTerms };
    });
  };

  const addSampleTranslation = () => {
    if (newSampleTranslation.original && newSampleTranslation.translated) {
      setSettings(prev => ({
        ...prev,
        sample_translations: [
          ...prev.sample_translations,
          { id: Date.now().toString(), ...newSampleTranslation }
        ]
      }));
      setNewSampleTranslation({ original: '', translated: '' });
    }
  };

  const removeSampleTranslation = (id: string) => {
    setSettings(prev => ({
      ...prev,
      sample_translations: prev.sample_translations.filter(s => s.id !== id)
    }));
  };

  const quickThemes = ['white', 'black'];

  return (
    <div className={`min-h-screen ${theme.background}`}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto p-6"
      >
        <h1 className={`text-3xl font-bold mb-6 ${theme.text}`}>Settings</h1>

        {/* Theme Selection */}
        <div className={`${theme.cardBg} p-6 rounded-xl mb-6`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text}`}>Theme</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(themes).map(([key, t]) => (
              <button
                key={key}
                onClick={() => changeTheme(key)}
                className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                  t.name === theme.name
                    ? 'border-blue-600 bg-blue-50 text-blue-900'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400 hover:bg-gray-50'
                }`}
              >
                <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${t.primary} border-2 border-white shadow-sm`} />
                <div className="text-left">
                  <div className="font-medium text-sm">{t.name}</div>
                  {t.name === theme.name && (
                    <div className="text-xs text-blue-600">Active</div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* API Configuration */}
        <div className={`${theme.cardBg} p-6 rounded-xl mb-6`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text}`}>API Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className={`block text-sm font-medium mb-2 ${theme.text}`}>OpenAI API Key</label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={settings.openai_api_key}
                  onChange={(e) => setSettings(prev => ({ ...prev, openai_api_key: e.target.value }))}
                  className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="sk-..."
                />
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-2.5 text-gray-500 hover:text-gray-700"
                >
                  {showApiKey ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
            <div>
              <label className={`block text-sm font-medium mb-2 ${theme.text}`}>Default Model</label>
              <select
                value={settings.default_model}
                onChange={(e) => setSettings(prev => ({ ...prev, default_model: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </select>
            </div>
          </div>
        </div>

        {/* Custom Prompts */}
        <div className={`${theme.cardBg} p-6 rounded-xl mb-6`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text}`}>Custom Prompts</h2>
          <div className="space-y-4">
            <div>
              <label className={`block text-sm font-medium mb-2 ${theme.text}`}>System Prompt</label>
              <textarea
                value={settings.system_prompt}
                onChange={(e) => setSettings(prev => ({ ...prev, system_prompt: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Define the translator's role and expertise..."
              />
            </div>
            <div>
              <label className={`block text-sm font-medium mb-2 ${theme.text}`}>Translation Prompt</label>
              <textarea
                value={settings.translation_prompt}
                onChange={(e) => setSettings(prev => ({ ...prev, translation_prompt: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={2}
                placeholder="Instructions for how to translate text..."
              />
            </div>
            <div>
              <label className={`block text-sm font-medium mb-2 ${theme.text}`}>Style Prompt</label>
              <textarea
                value={settings.style_prompt}
                onChange={(e) => setSettings(prev => ({ ...prev, style_prompt: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={2}
                placeholder="Instructions for adapting translation style..."
              />
            </div>
          </div>
        </div>

        {/* Glossary Terms */}
        <div className={`${theme.cardBg} p-6 rounded-xl mb-6`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text}`}>Glossary Terms</h2>
          <div className="space-y-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={newGlossaryTerm.source}
                onChange={(e) => setNewGlossaryTerm(prev => ({ ...prev, source: e.target.value }))}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="English term"
              />
              <input
                type="text"
                value={newGlossaryTerm.target}
                onChange={(e) => setNewGlossaryTerm(prev => ({ ...prev, target: e.target.value }))}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Persian translation"
              />
              <button
                onClick={addGlossaryTerm}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Plus size={16} /> Add
              </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {Object.entries(settings.glossary_terms).map(([source, target]) => (
                <div key={source} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="flex-1 font-medium">{source}</span>
                  <span className="flex-1">{target}</span>
                  <button
                    onClick={() => removeGlossaryTerm(source)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sample Translations */}
        <div className={`${theme.cardBg} p-6 rounded-xl mb-6`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text}`}>Sample Translations</h2>
          <div className="space-y-4">
            <div className="space-y-3">
              <textarea
                value={newSampleTranslation.original}
                onChange={(e) => setNewSampleTranslation(prev => ({ ...prev, original: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Original English text..."
              />
              <textarea
                value={newSampleTranslation.translated}
                onChange={(e) => setNewSampleTranslation(prev => ({ ...prev, translated: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="High-quality Persian translation..."
              />
              <button
                onClick={addSampleTranslation}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <Plus size={16} /> Add Sample
              </button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {settings.sample_translations.map((sample) => (
                <div key={sample.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Original:</label>
                      <p className="text-sm">{sample.original}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Translation:</label>
                      <p className="text-sm">{sample.translated}</p>
                    </div>
                    <button
                      onClick={() => removeSampleTranslation(sample.id)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-1"
                    >
                      <Trash2 size={14} /> Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Translation Settings */}
        <div className={`${theme.cardBg} p-6 rounded-xl mb-6`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text}`}>Translation Settings</h2>
          <div className="space-y-4">
            <div>
              <label className={`block text-sm font-medium mb-2 ${theme.text}`}>Quality Level</label>
              <select
                value={settings.quality_level}
                onChange={(e) => setSettings(prev => ({ ...prev, quality_level: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="fast">Fast</option>
                <option value="standard">Standard</option>
                <option value="high">High Quality</option>
                <option value="premium">Premium</option>
              </select>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={settings.preserve_formatting}
                onChange={(e) => setSettings(prev => ({ ...prev, preserve_formatting: e.target.checked }))}
                className="w-4 h-4"
              />
              <label className={`text-sm font-medium ${theme.text}`}>Preserve Formatting</label>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={saveSettings}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 font-medium"
          >
            <Save size={20} /> Save Settings
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default SettingsPage;