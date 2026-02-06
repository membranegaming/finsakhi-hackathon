import { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import './Layout.css';

function Layout({ children, userName = "User Name", onLogout, onNavigate, activePage }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-layout">
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <Sidebar onNavigate={(id) => { setSidebarOpen(false); onNavigate?.(id); }} activePage={activePage} mobileOpen={sidebarOpen} />
      <Header userName={userName} onLogout={onLogout} onMenuToggle={() => setSidebarOpen(o => !o)} />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

export default Layout;

