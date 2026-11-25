import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  Building2,
  TrendingUp,
  BarChart3,
  FileDown,
  Settings,
  Radio,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, tag: 'CORE' },
  { path: '/scraper', label: 'Scraper Control', icon: Cpu, tag: 'RECON' },
  { path: '/companies', label: 'Companies', icon: Building2, tag: 'INTEL' },
  { path: '/salary', label: 'Salary Intelligence', icon: TrendingUp, tag: 'LPA' },
  { path: '/analytics', label: 'Analytics Matrix', icon: BarChart3, tag: 'CHARTS' },
  { path: '/export', label: 'Export Center', icon: FileDown, tag: 'XLSX' },
  { path: '/settings', label: 'Settings', icon: Settings, tag: 'CONFIG' },
];

export default function Sidebar({ collapsed, onToggleCollapse }) {
  return (
    <aside
      className={`bg-[#101620] border-r border-[#263244] flex flex-col justify-between shrink-0 h-screen select-none transition-all duration-300 z-30 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand & Falkenbeast Header */}
      <div>
        <div className="h-16 px-4 flex items-center justify-between border-b border-[#263244]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-[#151D29] border border-[#FF6A00]/50 shadow-glow-sm-orange shrink-0">
              <Radio className="w-5 h-5 text-[#FF6A00]" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#00D4FF] animate-pulse"></span>
            </div>
            {!collapsed && (
              <div className="transition-opacity duration-200">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold tracking-widest text-sm text-[#E6EDF3] font-mono">HAV_SCRAP</span>
                  <span className="px-1 py-0.2 bg-[#FF6A00]/20 text-[#FF6A00] text-[9px] font-mono font-bold rounded">
                    MK-2
                  </span>
                </div>
                <p className="text-[10px] text-[#8492A6] font-mono tracking-tight font-semibold">FALKENBEAST LABS</p>
              </div>
            )}
          </div>

          <button
            onClick={onToggleCollapse}
            className="p-1 rounded-md text-[#8492A6] hover:text-[#00D4FF] hover:bg-[#151D29] border border-transparent hover:border-[#263244] transition-colors"
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Directives */}
        <div className="px-3 py-6 space-y-1.5">
          {!collapsed && (
            <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-widest text-[#8492A6]/70">
              SYSTEM DIRECTIVES
            </div>
          )}
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-3 py-2.5 rounded-md text-xs font-semibold uppercase tracking-wider font-mono transition-all duration-200 group relative ${
                    isActive
                      ? 'bg-[#151D29] text-[#FF6A00] border-l-2 border-[#FF6A00] shadow-[0_0_12px_rgba(255,106,0,0.25)] font-bold'
                      : 'text-[#8492A6] hover:text-[#E6EDF3] hover:bg-[#151D29]/70'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive ? 'text-[#FF6A00]' : 'text-[#8492A6] group-hover:text-[#00D4FF]'
                        }`}
                      />
                      {!collapsed && <span>{item.label}</span>}
                    </div>
                    {!collapsed && isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FF6A00] shadow-[0_0_6px_#FF6A00] animate-pulse"></span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Protocol Specs & Version Footer */}
      <div className="p-3 m-2 bg-[#151D29]/70 border border-[#263244] rounded-lg">
        {!collapsed ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-[#8492A6]">
              <span>CORE ARCHITECTURE</span>
              <span className="text-[#00D4FF] font-semibold">STARK SYSTEMS CORE</span>
            </div>
            <div className="w-full bg-[#0B0E14] h-1.5 rounded-full overflow-hidden border border-[#263244]">
              <div className="bg-gradient-to-r from-[#FF6A00] to-[#00D4FF] h-full w-4/5 rounded-full"></div>
            </div>
            <div className="flex items-center justify-between text-[10px] font-mono text-[#8492A6]/80 pt-1">
              <span>BUILD: 2.0.4-PRO</span>
              <span className="text-[#FF6A00] font-bold">ARMED</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-1" title="v2.0.4-PRO">
            <Shield className="w-4 h-4 text-[#00D4FF]" />
            <span className="text-[9px] font-mono text-[#8492A6] mt-1">v2.0</span>
          </div>
        )}
      </div>
    </aside>
  );
}
