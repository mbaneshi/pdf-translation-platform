import React, { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import Navbar from '../Navigation/Navbar';
import Sidebar from '../Navigation/Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { theme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className={`min-h-screen ${theme.background}`}>
      <Navbar
        onSidebarToggle={() => setSidebarOpen((v) => !v)}
        isSidebarOpen={sidebarOpen}
      />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="pt-16 lg:pl-64 p-4 sm:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
};

export default AppLayout;

