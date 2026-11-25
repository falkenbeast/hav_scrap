import React, { useState, useEffect, useRef } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import Topbar from '../components/layout/Topbar';

export default function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const mainScrollRef = useRef(null);
  const location = useLocation();

  // Reset main content scroll position to top whenever navigating between routes
  useEffect(() => {
    if (mainScrollRef.current) {
      mainScrollRef.current.scrollTop = 0;
    }
  }, [location.pathname]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0E14] text-[#E6EDF3]">
      {/* Desktop / Collapsible Sidebar */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Mobile Drawer Sidebar */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="relative z-50">
            <Sidebar
              collapsed={false}
              onToggleCollapse={() => setMobileSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Viewport Shell */}
      <div className="flex flex-col flex-1 min-w-0 h-screen overflow-hidden">
        <Topbar
          onToggleSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          sidebarCollapsed={sidebarCollapsed}
        />

        {/* Scrollable HUD Workspace Container */}
        <main
          ref={mainScrollRef}
          className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 hud-grid relative"
        >
          <div className="max-w-7xl mx-auto space-y-6 flex flex-col min-h-full justify-between">
            {/* Subtle technology-inspired page transition module */}
            <div key={location.pathname} className="page-module-enter flex-1 space-y-6">
              <Outlet />
            </div>

            {/* Application Branding Footer */}
            <footer className="mt-12 pt-6 pb-2 border-t border-[#263244]/60 text-center text-[10px] font-mono text-[#8492A6] select-none tracking-wider">
              Developed by <span className="text-[#E6EDF3] font-semibold">Falkenbeast Labs</span> | Technology Contribution: <span className="text-[#00D4FF]">Stark Systems</span>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
