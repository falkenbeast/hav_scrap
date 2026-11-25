import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Shield,
  Activity,
  Terminal,
  Clock,
  RefreshCw,
  User,
  Menu,
  ChevronRight,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { api } from '../../services/api';
import StatusBadge from '../common/StatusBadge';

const ROUTE_CONFIG = {
  '/': { title: 'Command Matrix', breadcrumb: 'FALKEN_NET // DASHBOARD' },
  '/scraper': { title: 'Scraper Engine', breadcrumb: 'SYSTEM // RECON CONTROL' },
  '/companies': { title: 'Organization Dossier', breadcrumb: 'INTELLIGENCE // RECRUITERS' },
  '/salary': { title: 'Salary Intelligence', breadcrumb: 'ANALYTICS // COMPENSATION' },
  '/analytics': { title: 'Analytical Matrix', breadcrumb: 'TELEMETRY // VISUALIZATIONS' },
  '/export': { title: 'Export Center', breadcrumb: 'DELIVERABLES // PACKAGER' },
  '/settings': { title: 'System Configuration', breadcrumb: 'ENVIRONMENT // SETTINGS' },
};

export default function Topbar({ onToggleSidebar, sidebarCollapsed }) {
  const location = useLocation();
  const currentRoute = ROUTE_CONFIG[location.pathname] || {
    title: 'Intelligence Center',
    breadcrumb: 'FALKEN_NET // ACTIVE',
  };

  const [time, setTime] = useState('');
  const [date, setDate] = useState('');
  const [backendHealth, setBackendHealth] = useState(null);
  const [latency, setLatency] = useState(null);
  const [checking, setChecking] = useState(false);

  const checkHealth = async () => {
    setChecking(true);
    const start = performance.now();
    try {
      const data = await api.getHealth();
      const end = performance.now();
      setBackendHealth(data);
      setLatency(Math.round(end - start));
    } catch {
      setBackendHealth({ status: 'unreachable' });
      setLatency(null);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();

    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { timeZone: 'Asia/Kolkata', hour12: false }));
      setDate(
        now.toLocaleDateString('en-US', {
          timeZone: 'Asia/Kolkata',
          weekday: 'short',
          month: 'short',
          day: 'numeric',
        })
      );
    };

    updateClock();
    const clockInterval = setInterval(updateClock, 1000);
    const healthInterval = setInterval(checkHealth, 25000);

    return () => {
      clearInterval(clockInterval);
      clearInterval(healthInterval);
    };
  }, []);

  const isHealthy = backendHealth?.status === 'healthy';

  return (
    <header className="h-16 bg-[#101620] border-b border-[#263244] px-4 sm:px-6 flex items-center justify-between select-none z-20 shrink-0">
      {/* Left: Breadcrumb & Title */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-md text-[#8492A6] hover:text-[#00D4FF] hover:bg-[#151D29] border border-[#263244]"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] font-mono text-[#8492A6] uppercase tracking-wider truncate">
            <span>{currentRoute.breadcrumb}</span>
            <ChevronRight className="w-3 h-3 text-[#263244]" />
            <span className="text-[#00D4FF] hidden sm:inline">LIVE FEED</span>
          </div>
          <h2 className="text-sm sm:text-base font-bold font-mono text-[#E6EDF3] tracking-tight truncate">
            {currentRoute.title}
          </h2>
        </div>
      </div>

      {/* Right: Telemetry Indicators, Live Clock & User Avatar */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Backend Connection Indicator */}
        <div className="flex items-center gap-2 pl-3 border-l border-[#263244]">
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isHealthy ? 'bg-[#00D4FF]' : 'bg-rose-500'
              }`}
            ></span>
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isHealthy ? 'bg-[#00D4FF]' : 'bg-rose-500'
              }`}
            ></span>
          </span>

          <span className="text-[11px] font-mono font-semibold tracking-wider text-[#E6EDF3] hidden md:inline">
            CORE: {isHealthy ? 'SYNCHRONIZED' : 'OFFLINE'}
          </span>

          {latency !== null && (
            <span className="text-[10px] font-mono text-[#00D4FF] hidden lg:inline">
              ({latency}ms)
            </span>
          )}

          <button
            onClick={checkHealth}
            disabled={checking}
            title="Ping Backend Telemetry"
            className="p-1 rounded hover:bg-[#151D29] text-[#8492A6] hover:text-[#00D4FF] border border-transparent hover:border-[#263244] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin text-[#00D4FF]' : ''}`} />
          </button>
        </div>

        {/* Live Date and Time */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-[#0B0E14] border border-[#263244] rounded text-xs font-mono text-[#FF6A00]">
          <Clock className="w-3.5 h-3.5" />
          <span className="hidden md:inline text-[#8492A6]">{date} //</span>
          <span>{time} IST</span>
        </div>

        {/* System Status Pill */}
        <div className="hidden xl:flex">
          <StatusBadge variant="cyan" size="sm" dot={true}>
            SYS: NOMINAL
          </StatusBadge>
        </div>

        {/* User Profile / Avatar Placeholder */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#263244]">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-[#151D29] border border-[#00D4FF]/40 shadow-glow-sm-cyan/30 text-[#00D4FF] font-mono font-bold text-xs cursor-pointer hover:border-[#00D4FF] transition-colors" title="Falkenbeast Labs">
            <span>FBL</span>
            <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-emerald-400 border border-[#101620]"></span>
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-[11px] font-mono font-bold text-[#E6EDF3] leading-tight">CHIEF OPERATIVE</p>
            <p className="text-[9px] font-mono text-[#00D4FF] leading-tight">FALKENBEAST LABS</p>
          </div>
        </div>
      </div>
    </header>
  );
}

