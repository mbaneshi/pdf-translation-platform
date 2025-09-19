import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Theme interface
export interface Theme {
  name: string;
  background: string;
  cardBg: string;
  primary: string;
  secondary: string;
  accent: string;
  text: string;
  textSecondary: string;
}

// Theme context type
interface ThemeContextType {
  currentTheme: string;
  theme: Theme;
  themes: Record<string, Theme>;
  changeTheme: (themeName: string) => void;
}

// Provider props
interface ThemeProviderProps {
  children: ReactNode;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

const themes: Record<string, Theme> = {
  ocean: {
    name: 'Ocean Breeze',
    background: 'bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-100',
    cardBg: 'bg-white/90 backdrop-blur-sm',
    primary: 'from-blue-500 to-cyan-600',
    secondary: 'from-cyan-500 to-teal-600',
    accent: 'from-teal-500 to-emerald-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  sunset: {
    name: 'Sunset Glow',
    background: 'bg-gradient-to-br from-orange-50 via-red-50 to-pink-100',
    cardBg: 'bg-white/90 backdrop-blur-sm',
    primary: 'from-orange-500 to-red-600',
    secondary: 'from-red-500 to-pink-600',
    accent: 'from-pink-500 to-rose-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  forest: {
    name: 'Forest Mist',
    background: 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100',
    cardBg: 'bg-white/90 backdrop-blur-sm',
    primary: 'from-green-500 to-emerald-600',
    secondary: 'from-emerald-500 to-teal-600',
    accent: 'from-teal-500 to-cyan-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  cosmic: {
    name: 'Cosmic Night',
    background: 'bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-100',
    cardBg: 'bg-white/90 backdrop-blur-sm',
    primary: 'from-purple-500 to-indigo-600',
    secondary: 'from-indigo-500 to-blue-600',
    accent: 'from-blue-500 to-cyan-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  aurora: {
    name: 'Aurora Lights',
    background: 'bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-100',
    cardBg: 'bg-white/90 backdrop-blur-sm',
    primary: 'from-emerald-500 to-teal-600',
    secondary: 'from-teal-500 to-cyan-600',
    accent: 'from-cyan-500 to-blue-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  lavender: {
    name: 'Lavender Dreams',
    background: 'bg-gradient-to-br from-purple-50 via-violet-50 to-pink-100',
    cardBg: 'bg-white/90 backdrop-blur-sm',
    primary: 'from-purple-500 to-violet-600',
    secondary: 'from-violet-500 to-pink-600',
    accent: 'from-pink-500 to-rose-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  // Brand Theme with your colors
  brand: {
    name: 'Brand Colors',
    background: 'bg-gradient-to-br from-gray-50 via-white to-gray-100',
    cardBg: 'bg-white/95 backdrop-blur-sm',
    primary: 'from-[#BBD8B3] to-[#A29F15]', // Celadon to Old Gold
    secondary: 'from-[#F3B61F] to-[#A29F15]', // Xanthous to Old Gold
    accent: 'from-[#510D0A] to-[#191102]', // Rosewood to Smoky Black
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  // White Theme
  white: {
    name: 'White',
    background: 'bg-white',
    cardBg: 'bg-white border border-gray-200',
    primary: 'from-gray-700 to-gray-900',
    secondary: 'from-gray-500 to-gray-700',
    accent: 'from-gray-400 to-gray-600',
    text: 'text-gray-900',
    textSecondary: 'text-gray-600',
  },
  // Dark Theme
  dark: {
    name: 'Dark',
    background: 'bg-gray-900',
    cardBg: 'bg-gray-800 border border-gray-600',
    primary: 'from-blue-400 to-blue-600',
    secondary: 'from-gray-400 to-gray-600',
    accent: 'from-green-400 to-green-600',
    text: 'text-gray-100',
    textSecondary: 'text-gray-300',
  },
  // High Contrast
  contrast: {
    name: 'High Contrast',
    background: 'bg-black',
    cardBg: 'bg-gray-900 border border-gray-700',
    primary: 'from-yellow-400 to-yellow-500',
    secondary: 'from-blue-400 to-blue-500',
    accent: 'from-green-400 to-green-500',
    text: 'text-white',
    textSecondary: 'text-gray-200',
  }
};

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState<string>('brand');

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('pdf-translation-theme');
    if (savedTheme && themes[savedTheme]) {
      setCurrentTheme(savedTheme);
    }
  }, []);

  // Save theme to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('pdf-translation-theme', currentTheme);
  }, [currentTheme]);

  const changeTheme = (themeName: string): void => {
    if (themes[themeName]) {
      setCurrentTheme(themeName);
    }
  };

  const value: ThemeContextType = {
    currentTheme,
    theme: themes[currentTheme],
    themes,
    changeTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export { themes };
export type { ThemeContextType };