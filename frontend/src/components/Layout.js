import React, { useState } from 'react';
import CollapsibleSidebar from './CollapsibleSidebar';
import './Layout.css';

const Layout = ({ children }) => {
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  const handleSidebarExpandChange = (expanded) => {
    setSidebarExpanded(expanded);
  };

  return (
    <div className="layout-container">
      <CollapsibleSidebar onExpandChange={handleSidebarExpandChange} />
      <main className={`main-content ${sidebarExpanded ? 'sidebar-expanded' : 'sidebar-collapsed'}`}>
        {children}
      </main>
    </div>
  );
};

export default Layout;