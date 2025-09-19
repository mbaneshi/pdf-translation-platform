import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';

const ProfilePage: React.FC = () => {
  const { theme } = useTheme();
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <h1 className={`text-2xl font-semibold mb-4 ${theme.text}`}>Profile</h1>
      <p className={`${theme.textSecondary}`}>Manage your account details.</p>
    </motion.div>
  );
};

export default ProfilePage;

