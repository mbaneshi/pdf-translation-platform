import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';

interface OnboardingModalProps {
  storageKey?: string;
}

const OnboardingModal: React.FC<OnboardingModalProps> = ({ storageKey = 'onboarding_seen_v1' }) => {
  const { theme } = useTheme();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const seen = typeof window !== 'undefined' && localStorage.getItem(storageKey);
    if (!seen) setOpen(true);
  }, [storageKey]);

  const close = () => {
    localStorage.setItem(storageKey, '1');
    setOpen(false);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/30" onClick={close} />
          <motion.div
            initial={{ y: 20, scale: 0.98, opacity: 0 }}
            animate={{ y: 0, scale: 1, opacity: 1 }}
            exit={{ y: 10, scale: 0.98, opacity: 0 }}
            className={`relative w-full max-w-lg ${theme.cardBg} rounded-2xl shadow-2xl border border-gray-200/60 p-6`}
          >
            <h2 className="text-xl font-semibold mb-2">Welcome to PDF Translator</h2>
            <p className="text-gray-600 mb-4">
              Upload a PDF, translate pages with AI, and review results. Use the sidebar to access Documents,
              Translations, History, and Settings.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-1 mb-6">
              <li>Drag & drop a PDF or click to upload</li>
              <li>Start translation and track progress</li>
              <li>Switch themes in the navbar menu</li>
            </ul>
            <div className="flex justify-end">
              <button onClick={close} className="px-4 py-2 bg-gray-900 text-white rounded-lg">
                Got it
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default OnboardingModal;

