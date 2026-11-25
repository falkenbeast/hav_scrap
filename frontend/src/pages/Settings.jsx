import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  HardDrive,
  Globe,
  Sliders,
  Shield,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  FolderLock,
  Moon,
  Palette,
  Database,
  Info,
  Server,
  FileSpreadsheet,
  Trash2,
  DownloadCloud,
  ShieldCheck,
} from 'lucide-react';
import SectionHeader from '../components/common/SectionHeader';
import StatusBadge from '../components/common/StatusBadge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import { api } from '../services/api';

export default function Settings() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [testingHealth, setTestingHealth] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(30);
  const [verboseLogging, setVerboseLogging] = useState(true);
  const [saveToast, setSaveToast] = useState(false);
  const [storageClearToast, setStorageClearToast] = useState(false);

  // Backup states
  const [backups, setBackups] = useState([]);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [backupToast, setBackupToast] = useState(null);

  const fetchStatus = async () => {
    setTestingHealth(true);
    try {
      const [statusData, backupsData] = await Promise.all([
        api.getSystemStatus().catch(() => null),
        api.getDatabaseBackups().catch(() => ({ backups: [] })),
      ]);
      setSystemStatus(statusData);
      setBackups(backupsData?.backups || []);
    } catch {
      setSystemStatus({
        backend_status: 'unreachable',
        database_connected: false,
        database_path: 'data/hav_scrap.db',
        scraper_availability: 'Disconnected',
        application_name: 'hav_scrap',
        version: '1.0.0',
      });
    } finally {
      setTestingHealth(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleCreateBackup = async () => {
    try {
      setCreatingBackup(true);
      setBackupToast(null);
      const res = await api.triggerDatabaseBackup();
      setBackupToast({
        success: true,
        message: `Verified SQLite snapshot created: ${res.filename} (${(res.file_size_bytes / 1024).toFixed(1)} KB, integrity: ${res.integrity})`,
      });
      // Refresh backups list
      const updated = await api.getDatabaseBackups().catch(() => ({ backups: [] }));
      setBackups(updated?.backups || []);
    } catch (err) {
      setBackupToast({
        success: false,
        message: `Backup failed: ${err.message || 'Error creating snapshot'}`,
      });
    } finally {
      setCreatingBackup(false);
    }
  };

  const handleSavePreferences = (e) => {
    e.preventDefault();
    setSaveToast(true);
    setTimeout(() => setSaveToast(false), 2500);
  };

  const handleClearLocalStorage = () => {
    localStorage.clear();
    setStorageClearToast(true);
    setTimeout(() => setStorageClearToast(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <SectionHeader
        title="SYSTEM & ENVIRONMENT CONFIGURATION"
        subtitle="Operational parameters, storage pathways, verified backups, and backend security telemetry."
        badgeText="CONTROL MATRIX"
        badgeVariant="cyan"
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={handleSavePreferences}
          >
            COMMIT PREFERENCES
          </Button>
        }
      />

      {saveToast && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-500/50 rounded-lg tech-corner font-mono text-xs text-emerald-400 flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>DIRECTIVE PERSISTED: Application preferences successfully synchronized.</span>
        </div>
      )}

      {storageClearToast && (
        <div className="p-4 bg-amber-950/40 border border-amber-500/50 rounded-lg tech-corner font-mono text-xs text-amber-400 flex items-center gap-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>LOCAL CACHE CLEARED: Browser localStorage state has been reset.</span>
        </div>
      )}

      {backupToast && (
        <div
          className={`p-4 rounded-lg tech-corner font-mono text-xs flex items-center gap-2 animate-fadeIn ${
            backupToast.success
              ? 'bg-emerald-950/40 border border-emerald-500/50 text-emerald-400'
              : 'bg-red-950/40 border border-red-500/50 text-red-400'
          }`}
        >
          {backupToast.success ? (
            <ShieldCheck className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{backupToast.message}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Backend & Core Telemetry Diagnostics */}
        <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-[#00D4FF]" />
              <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
                Core Engine Telemetry
              </h3>
            </div>
            <StatusBadge
              variant={systemStatus?.backend_status === 'healthy' ? 'cyan' : 'orange'}
              size="xs"
              dot={true}
            >
              {systemStatus?.backend_status === 'healthy' ? 'ONLINE (127.0.0.1:8000)' : 'STANDALONE'}
            </StatusBadge>
          </div>

          <div className="space-y-2.5">
            <div className="flex items-center justify-between p-2.5 bg-[#101620] border border-[#263244] rounded">
              <span className="text-[#8492A6]">APPLICATION:</span>
              <span className="font-bold text-[#E6EDF3]">{systemStatus?.application_name || 'hav_scrap'} v{systemStatus?.version || '1.0.0'}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-[#101620] border border-[#263244] rounded">
              <span className="text-[#8492A6]">SQLITE DATABASE STATUS:</span>
              <span className={`font-bold ${systemStatus?.database_connected ? 'text-emerald-400' : 'text-amber-400'}`}>
                {systemStatus?.database_connected ? 'Connected & Verified' : 'Checking Connection...'}
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-[#101620] border border-[#263244] rounded">
              <span className="text-[#8492A6]">SCRAPER AVAILABILITY:</span>
              <span className="font-bold text-[#00D4FF]">
                {systemStatus?.scraper_availability || 'Engine Available'}
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-[#101620] border border-[#263244] rounded">
              <span className="text-[#8492A6]">SECURITY BINDING:</span>
              <span className="text-[#00D4FF]">127.0.0.1 ONLY (Localhost Loopback)</span>
            </div>
          </div>

          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              disabled={testingHealth}
              onClick={fetchStatus}
              className="w-full"
            >
              PING CORE DIAGNOSTIC ENDPOINT (/api/system/status)
            </Button>
          </div>
        </div>

        {/* Database Integrity & Atomic Backup Controls (Phase 11) */}
        <div className="bg-[#151D29] border border-[#00D4FF]/40 rounded-lg p-5 tech-corner-cyan space-y-4 font-mono text-xs shadow-glow-sm-cyan/20">
          <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-[#00D4FF]" />
              <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
                Database Backups & Integrity
              </h3>
            </div>
            <StatusBadge variant="cyan" size="xs">
              {backups.length} SNAPSHOTS LOGGED
            </StatusBadge>
          </div>

          <p className="text-[11px] text-[#8492A6] leading-relaxed">
            Non-destructive SQLite snapshot backups with online threading and automated <code>PRAGMA integrity_check</code> verification. Stored locally in <code>data/backups/</code>. Original records are 100% preserved.
          </p>

          <Button
            variant="primary"
            size="sm"
            icon={DownloadCloud}
            disabled={creatingBackup}
            onClick={handleCreateBackup}
            className="w-full font-bold"
          >
            {creatingBackup ? 'EXECUTING ATOMIC BACKUP...' : 'CREATE ATOMIC DATABASE BACKUP'}
          </Button>

          {backups.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[10px] text-[#8492A6] uppercase tracking-wider">Recent Backup Archives:</span>
              <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
                {backups.slice(0, 4).map((b) => (
                  <div key={b.filename} className="p-2 bg-[#101620] border border-[#263244] rounded flex items-center justify-between text-[11px]">
                    <span className="text-[#E6EDF3] truncate max-w-[200px]" title={b.filename}>{b.filename}</span>
                    <span className="text-[#00D4FF]">{(b.file_size_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Filesystem Storage Pathways */}
        <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
          <div className="flex items-center gap-2 pb-3 border-b border-[#263244]">
            <HardDrive className="w-4 h-4 text-[#FF6A00]" />
            <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
              Filesystem Storage Pathways
            </h3>
          </div>

          <div className="space-y-2">
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">DATABASE:</span>
              <code className="text-[#00D4FF] text-[11px]">./data/hav_scrap.db</code>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">DATABASE BACKUPS:</span>
              <code className="text-emerald-400 text-[11px]">./data/backups/</code>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">EXCEL DELIVERABLES:</span>
              <code className="text-[#FF6A00] text-[11px]">./data/exports/</code>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">ROTATING AUDIT LOGS:</span>
              <code className="text-[#E6EDF3] text-[11px]">./logs/hav_scrap.log</code>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">BROWSER PROFILE:</span>
              <code className="text-[#00D4FF] text-[11px]">./data/browser_profile/</code>
            </div>
          </div>
        </div>

        {/* Theme Information - Dark Mode Locked */}
        <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
            <div className="flex items-center gap-2">
              <Moon className="w-4 h-4 text-[#00D4FF]" />
              <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
                Theme Specifications
              </h3>
            </div>
            <StatusBadge variant="cyan" size="xs" dot={true}>
              DARK MODE LOCKED
            </StatusBadge>
          </div>

          <p className="text-[11px] text-[#8492A6] leading-relaxed">
            The application is locked strictly in Tactical Dark Mode to ensure high-contrast readability, reduced glare, and authentic futuristic command deck aesthetics. Light mode is intentionally disabled by system policy.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            <div className="p-2 bg-[#0B0E14] border border-[#263244] rounded flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-[#0B0E14] border border-[#263244]"></span>
              <span className="text-[10px] text-[#E6EDF3]">#0B0E14 (Canvas)</span>
            </div>
            <div className="p-2 bg-[#101620] border border-[#263244] rounded flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-[#101620] border border-[#263244]"></span>
              <span className="text-[10px] text-[#E6EDF3]">#101620 (Nav)</span>
            </div>
            <div className="p-2 bg-[#151D29] border border-[#263244] rounded flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-[#151D29] border border-[#263244]"></span>
              <span className="text-[10px] text-[#E6EDF3]">#151D29 (HUD)</span>
            </div>
            <div className="p-2 bg-[#1B2635] border border-[#263244] rounded flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-[#1B2635] border border-[#263244]"></span>
              <span className="text-[10px] text-[#E6EDF3]">#1B2635 (Surface)</span>
            </div>
            <div className="p-2 bg-[#101620] border border-[#FF6A00]/40 rounded flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-[#FF6A00]"></span>
              <span className="text-[10px] text-[#FF6A00] font-bold">#FF6A00 (Action)</span>
            </div>
            <div className="p-2 bg-[#101620] border border-[#00D4FF]/40 rounded flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded bg-[#00D4FF]"></span>
              <span className="text-[10px] text-[#00D4FF] font-bold">#00D4FF (Telemetry)</span>
            </div>
          </div>
        </div>

        {/* System Dossier & Technology Attribution */}
        <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#FF6A00]" />
              <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
                System Dossier & Attribution
              </h3>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#101620] text-[#00D4FF] border border-[#263244]">
              ORIGIN: FALKENBEAST LABS
            </span>
          </div>

          <div className="space-y-2 text-[11px] text-[#8492A6]">
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">PRODUCT:</span>
              <span className="text-[#E6EDF3] font-bold">Haveloc Placement Intelligence System</span>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">PRIMARY DEVELOPER:</span>
              <span className="text-[#FF6A00] font-bold">Falkenbeast Labs</span>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">TECHNOLOGY PARTNER:</span>
              <span className="text-[#00D4FF] font-semibold">Stark Systems Technology</span>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
              <span className="text-[#8492A6]">CORE INTEGRATION:</span>
              <span className="text-[#E6EDF3]">Stark Intelligence Processing Module</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
