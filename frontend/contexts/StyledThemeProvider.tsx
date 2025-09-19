// Styled Components Theme Provider
// Bridges Tailwind theme system with styled-components
import React from 'react';
import { ThemeProvider as StyledThemeProvider } from 'styled-components';
import { useTheme } from './ThemeContext';

// Convert Tailwind-based theme to styled-components theme
function convertTheme(tailwindTheme: any) {
  return {
    colors: {
      primary: '#3b82f6',
      secondary: '#64748b',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      background: '#ffffff',
      surface: '#f8fafc',
      text: '#1e293b',
      textSecondary: '#64748b',
      border: '#e2e8f0'
    },
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '2rem',
      xxl: '3rem'
    },
    typography: {
      fontFamily: {
        sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        persian: '"Vazir", "Tahoma", "Segoe UI", sans-serif'
      },
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        base: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem'
      }
    },
    borderRadius: {
      sm: '0.125rem',
      md: '0.375rem',
      lg: '0.5rem',
      xl: '0.75rem'
    },
    shadows: {
      sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
      md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
      lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
    }
  };
}

interface StyledThemeProviderWrapperProps {
  children: React.ReactNode;
}

export const StyledThemeProviderWrapper: React.FC<StyledThemeProviderWrapperProps> = ({ children }) => {
  const { theme } = useTheme();
  const styledTheme = convertTheme(theme);

  return (
    <StyledThemeProvider theme={styledTheme}>
      {children}
    </StyledThemeProvider>
  );
};