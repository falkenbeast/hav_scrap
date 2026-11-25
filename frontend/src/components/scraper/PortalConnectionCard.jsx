import React, { useState, useEffect } from 'react';
import {
  Globe,
  ExternalLink,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Lock,
  RefreshCw,
  LogOut,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  HardDrive,
  Radio,
  Clock,
  Sparkles,
  Info,
} from 'lucide-react';
import Button from '../common/Button';
import StatusBadge from '../common/StatusBadge';
import { api } from '../../services/api';
import { formatTimeIST } from '../../utils/formatters';

export default function PortalConnectionCard({ onStatusChange }) {
  const [portalStatus, setPortalStatus] = useState({
    portal_url: 'https://haveloc.com/',
    target_dashboard_url:
      'https://placements.haveloc.com/jobs?sort=jobApplyBy%2Cdesc&jobView=eligible',
    browser_status: 'DISCONNECTED',
    authentication_status: 'DISCONNECTED',
    connection_status: 'DISCONNECTED',
    last_connected_at: null,
    last_error_message: null,
    playwright_installed: false,
    chromium_installed: false,
    profile_path: './data/browser_profile',
  });

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  // Poll status periodically (every 4 seconds) to detect manual login in Chromium
  const fetchStatus = async () => {
    try {
      const data = await api.getPortalStatus();
      setPortalStatus(data);
      if (onStatusChange) onStatusChange(data);
      setError(null);
    } catch (err) {
      console.warn('Portal status fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleConnect = async () => {
    try {
      setActionLoading(true);
      setError(null);
      const res = await api.connectPortal();
      if (!res.success && res.data?.last_error_message) {
        setError(res.data.last_error_message);
      }
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Failed to initiate portal connection.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReconnect = async () => {
    try {
      setActionLoading(true);
      setError(null);
      const res = await api.reconnectPortal();
      if (!res.success && res.data?.last_error_message) {
        setError(res.data.last_error_message);
      }
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Failed to reconnect session.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await api.disconnectPortal();
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Failed to disconnect portal.');
    } finally {
      setActionLoading(false);
    }
  };

  // Render auth badge with glowing tactical states
  const renderAuthBadge = () => {
    const s = portalStatus.authentication_status;
    switch (s) {
      case 'CONNECTED':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
            AUTHENTICATED & ACTIVE
          </div>
        );
      case 'AWAITING_LOGIN':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-xs">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            AWAITING OPERATOR LOGIN
          </div>
        );
      case 'VERIFYING':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            VERIFYING DASHBOARD
          </div>
        );
      case 'BROWSER_LAUNCHING':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 font-mono text-xs">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            LAUNCHING CHROMIUM
          </div>
        );
      case 'SESSION_EXPIRED':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-400 font-mono text-xs">
            <ShieldAlert className="w-3.5 h-3.5 text-orange-400" />
            SESSION EXPIRED
          </div>
        );
      case 'UNKNOWN':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 font-mono text-xs">
            <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
            STATUS UNKNOWN
          </div>
        );
      case 'ERROR':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 font-mono text-xs">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            CONFIGURATION ERROR
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700 text-slate-400 font-mono text-xs">
            <Radio className="w-3.5 h-3.5 text-slate-500" />
            STANDBY / DISCONNECTED
          </div>
        );
    }
  };

  const isConnected = portalStatus.authentication_status === 'CONNECTED';
  const isAwaiting = portalStatus.authentication_status === 'AWAITING_LOGIN';
  const isBrowserRunning = portalStatus.browser_status === 'RUNNING';

  return (
    <div className="bg-[#151D29] border border-[#263244] rounded-xl p-6 shadow-xl relative overflow-hidden backdrop-blur-md">
      {/* Top glowing ambient accent */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#FF6A00] to-transparent opacity-80" />

      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#263244]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#101620] to-[#1B2635] border border-[#263244] flex items-center justify-center shadow-inner relative group">
            <Shield className="w-6 h-6 text-[#FF6A00] group-hover:scale-110 transition-transform" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              {isConnected ? (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00D4FF] opacity-75" />
              ) : null}
              <span
                className={`relative inline-flex rounded-full h-3 w-3 ${
                  isConnected ? 'bg-[#00D4FF]' : 'bg-slate-600'
                }`}
              />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-[#E6EDF3] tracking-wide uppercase font-mono">
                HAVELOC PORTAL GATEWAY
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[#1B2635] text-[#00D4FF] border border-[#263244] font-mono">
                SECURE PERSISTENT SESSION
              </span>
            </div>
            <p className="text-xs text-[#8492A6] mt-0.5">
              Persistent Chromium browser bridge. Manual operator authentication & secure local cookie store.
            </p>
          </div>
        </div>

        {/* Live status badge */}
        <div>{renderAuthBadge()}</div>
      </div>

      {/* Portal URLs & Configuration Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-5">
        {/* Login Portal Target */}
        <div className="bg-[#101620] border border-[#263244] rounded-lg p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-[#8492A6] mb-1.5 font-mono">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Globe className="w-3.5 h-3.5 text-[#FF6A00]" />
              AUTHENTICATION PORTAL
            </span>
            <span className="text-[11px] text-slate-500">MANUAL LOGIN GATEWAY</span>
          </div>
          <div className="flex items-center justify-between gap-2 bg-[#0B0E14] px-3 py-2 rounded border border-[#263244]/80">
            <code className="text-xs text-[#00D4FF] truncate font-mono">
              {portalStatus.portal_url}
            </code>
            <a
              href={portalStatus.portal_url}
              target="_blank"
              rel="noreferrer"
              className="text-[#8492A6] hover:text-[#FF6A00] transition-colors"
              title="Open portal in system browser"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Target Dashboard */}
        <div className="bg-[#101620] border border-[#263244] rounded-lg p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-[#8492A6] mb-1.5 font-mono">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Lock className="w-3.5 h-3.5 text-[#00D4FF]" />
              TARGET PLACEMENT DASHBOARD
            </span>
            <span className="text-[11px] text-[#00D4FF]/80">PROTECTED ENDPOINT</span>
          </div>
          <div className="flex items-center justify-between gap-2 bg-[#0B0E14] px-3 py-2 rounded border border-[#263244]/80">
            <code className="text-xs text-emerald-400 truncate font-mono">
              {portalStatus.target_dashboard_url}
            </code>
            <ShieldCheck className="w-3.5 h-3.5 text-[#00D4FF]" />
          </div>
        </div>
      </div>

      {/* Instruction alert when awaiting login */}
      {isAwaiting && (
        <div className="mb-5 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200">
            <p className="font-semibold text-amber-300 mb-1">
              Manual Operator Login in Progress
            </p>
            <p>
              A visible Chromium browser window has opened. Please enter your Haveloc credentials manually.
              The application will automatically detect successful login and verify target dashboard accessibility.
            </p>
          </div>
        </div>
      )}

      {/* Error alert if missing dependencies or faults */}
      {error && (
        <div className="mb-5 p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-xs text-rose-200">
            <p className="font-semibold text-rose-300 mb-0.5">Gateway Alert</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Telemetry and Diagnostics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-t border-b border-[#263244] text-xs font-mono">
        <div>
          <span className="text-[#8492A6] block text-[11px]">BROWSER PROCESS</span>
          <span
            className={`font-semibold ${
              isBrowserRunning ? 'text-[#00D4FF]' : 'text-slate-400'
            }`}
          >
            {portalStatus.browser_status}
          </span>
        </div>
        <div>
          <span className="text-[#8492A6] block text-[11px]">AUTHENTICATION</span>
          <span className="text-slate-200 font-semibold">
            {portalStatus.authentication_status}
          </span>
        </div>
        <div>
          <span className="text-[#8492A6] block text-[11px]">LAST CONNECTED</span>
          <span className="text-slate-300">
            {portalStatus.last_connected_at
              ? formatTimeIST(portalStatus.last_connected_at)
              : 'NEVER'}
          </span>
        </div>
        <div>
          <span className="text-[#8492A6] block text-[11px]">LOCAL PROFILE</span>
          <span className="text-emerald-400 truncate block" title={portalStatus.profile_path}>
            PERSISTENT ACTIVE
          </span>
        </div>
      </div>

      {/* Action Controls Section */}
      <div className="flex flex-wrap items-center justify-between gap-3 mt-5">
        <div className="flex items-center gap-2">
          {/* Connect Button (Orange) */}
          <button
            onClick={handleConnect}
            disabled={actionLoading || isConnected}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-mono text-xs font-semibold tracking-wider uppercase transition-all shadow-lg ${
              isConnected
                ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                : 'bg-[#FF6A00] hover:bg-[#e05d00] text-white shadow-[0_0_15px_rgba(255,106,0,0.3)] hover:shadow-[0_0_20px_rgba(255,106,0,0.5)] active:scale-95'
            }`}
          >
            <Shield className="w-4 h-4" />
            {actionLoading ? 'CONNECTING...' : 'CONNECT TO HAVELOC'}
          </button>

          {/* Reconnect Button (Cyan) */}
          <button
            onClick={handleReconnect}
            disabled={actionLoading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#151D29] hover:bg-[#1B2635] text-[#00D4FF] border border-[#00D4FF]/40 hover:border-[#00D4FF] font-mono text-xs font-semibold tracking-wider uppercase transition-all shadow-sm active:scale-95 disabled:opacity-50"
            title="Probe existing persistent profile cookies to reconnect"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            RECONNECT SESSION
          </button>
        </div>

        {/* Disconnect Button (Red/Ghost) */}
        {isBrowserRunning && (
          <button
            onClick={handleDisconnect}
            disabled={actionLoading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:border-rose-500/50 font-mono text-xs font-semibold tracking-wider uppercase transition-all active:scale-95 disabled:opacity-50"
          >
            <LogOut className="w-3.5 h-3.5" />
            DISCONNECT
          </button>
        )}
      </div>
    </div>
  );
}

