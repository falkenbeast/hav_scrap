import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  Terminal,
  Shield,
  Layers,
  AlertTriangle,
  CheckCircle2,
  HardDrive,
  Cpu,
  Wifi,
  Globe,
  Sliders,
  Sparkles,
  Info,
} from 'lucide-react';
import SectionHeader from '../components/common/SectionHeader';
import StatCard from '../components/common/StatCard';
import StatusBadge from '../components/common/StatusBadge';
import Button from '../components/common/Button';
import TerminalConsole from '../components/scraper/TerminalConsole';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import PortalConnectionCard from '../components/scraper/PortalConnectionCard';
import DataQualityPanel from '../components/dashboard/DataQualityPanel';
import JobDetailsModal from '../components/common/JobDetailsModal';
import { api } from '../services/api';
import { formatDateTimeIST } from '../utils/formatters';

export default function ScraperControl() {
  const [scraperStatus, setScraperStatus] = useState({
    session_id: null,
    status: 'IDLE',
    progress_percentage: 0.0,
    records_discovered: 0,
    records_processed: 0,
    started_at: null,
    error_message: null,
  });

  const [sessions, setSessions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sseConnected, setSseConnected] = useState(false);
  const [portalConnected, setPortalConnected] = useState(false);
  const [extractionLoading, setExtractionLoading] = useState(false);
  const [extractionStatus, setExtractionStatus] = useState(null);
  const [inspectedJob, setInspectedJob] = useState(null);

  // Poll status & fetch logs initially
  const loadInitialState = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statusData, sessionData, logData] = await Promise.all([
        api.getScraperStatus().catch(() => null),
        api.getSessions({ page: 1, page_size: 10 }).catch(() => ({ items: [] })),
        api.getScraperLogs(40).catch(() => []),
      ]);

      if (statusData) {
        setScraperStatus(statusData);
      }
      setSessions(sessionData.items || []);
      setLogs(
        logData.length > 0
          ? logData
          : [
              {
                timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
                level: 'SYSTEM',
                message: 'Scraper Engine & Controller initialized. Standing by for directives.',
              },
            ]
      );
    } catch (err) {
      setError(err.message || 'Failed to initialize scraper control deck.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialState();
  }, []);

  // Server-Sent Events (SSE) Live Telemetry Stream
  useEffect(() => {
    let eventSource = null;
    try {
      const sseUrl = api.getScraperEventsUrl();
      eventSource = new EventSource(sseUrl);

      eventSource.onopen = () => {
        setSseConnected(true);
      };

      eventSource.onerror = () => {
        setSseConnected(false);
      };

      // Handle generic message / keepalive
      eventSource.onmessage = (e) => {
        // SSE comments or generic message
      };

      const handleEvent = (eventType, e) => {
        try {
          const payload = JSON.parse(e.data);
          const time = new Date().toLocaleTimeString('en-US', { hour12: false });

          if (eventType === 'CONNECTED') {
            setScraperStatus((prev) => ({ ...prev, ...payload }));
          } else if (eventType === 'SESSION_STARTED') {
            setScraperStatus((prev) => ({
              ...prev,
              session_id: payload.session_id,
              status: 'RUNNING',
              progress_percentage: 0.0,
            }));
            setLogs((l) => [
              ...l,
              { timestamp: time, level: 'RECON', message: payload.message || 'Session started.' },
            ]);
          } else if (eventType === 'SESSION_PAUSED') {
            setScraperStatus((prev) => ({ ...prev, status: 'PAUSED' }));
            setLogs((l) => [
              ...l,
              { timestamp: time, level: 'WARN', message: payload.message || 'Session paused at checkpoint.' },
            ]);
          } else if (eventType === 'SESSION_RESUMED') {
            setScraperStatus((prev) => ({ ...prev, status: 'RUNNING' }));
            setLogs((l) => [
              ...l,
              { timestamp: time, level: 'RECON', message: payload.message || 'Session resumed.' },
            ]);
          } else if (eventType === 'SESSION_STOPPED') {
            setScraperStatus((prev) => ({ ...prev, status: 'CANCELLED' }));
            setLogs((l) => [
              ...l,
              { timestamp: time, level: 'ERROR', message: payload.message || 'Session stopped by operator.' },
            ]);
            api.getSessions({ page: 1, page_size: 10 }).then((res) => setSessions(res.items || []));
          } else if (eventType === 'PROGRESS_UPDATED') {
            setScraperStatus((prev) => ({
              ...prev,
              progress_percentage: payload.progress_percentage ?? prev.progress_percentage,
              records_discovered: payload.records_discovered ?? prev.records_discovered,
              records_processed: payload.records_processed ?? prev.records_processed,
            }));
          } else if (eventType === 'RECORD_DISCOVERED') {
            setLogs((l) => [
              ...l,
              {
                timestamp: time,
                level: 'DISCOVER',
                message: `Notice identified: ${payload.record_title} (Total: ${payload.records_discovered})`,
              },
            ]);
          } else if (eventType === 'RECORD_PROCESSED') {
            setLogs((l) => [
              ...l,
              {
                timestamp: time,
                level: 'PARSER',
                message: `Parsed & committed notice: ${payload.record_title} (Total: ${payload.records_processed})`,
              },
            ]);
          } else if (eventType === 'SESSION_COMPLETED') {
            setScraperStatus((prev) => ({
              ...prev,
              status: 'COMPLETED',
              progress_percentage: 100.0,
            }));
            setLogs((l) => [
              ...l,
              { timestamp: time, level: 'SUCCESS', message: payload.message || 'Session completed.' },
            ]);
            api.getSessions({ page: 1, page_size: 10 }).then((res) => setSessions(res.items || []));
          } else if (eventType === 'ERROR') {
            setScraperStatus((prev) => ({
              ...prev,
              status: 'FAILED',
              error_message: payload.error,
            }));
            setLogs((l) => [
              ...l,
              { timestamp: time, level: 'ERROR', message: payload.message || payload.error },
            ]);
            api.getSessions({ page: 1, page_size: 10 }).then((res) => setSessions(res.items || []));
          }
        } catch (err) {
          console.warn('Error parsing SSE event:', err);
        }
      };

      const eventList = [
        'CONNECTED',
        'SESSION_STARTED',
        'SESSION_PAUSED',
        'SESSION_RESUMED',
        'SESSION_STOPPED',
        'PROGRESS_UPDATED',
        'RECORD_DISCOVERED',
        'RECORD_PROCESSED',
        'SESSION_COMPLETED',
        'ERROR',
      ];

      eventList.forEach((evt) => {
        eventSource.addEventListener(evt, (e) => handleEvent(evt, e));
      });
    } catch (err) {
      console.warn('SSE connection fault:', err);
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  // Action handlers calling real FastAPI backend endpoints
  const handleStart = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await api.startScraper();
      // Status update will arrive via SSE stream
    } catch (err) {
      setError(err.message || 'Failed to start scraping session.');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await api.pauseScraper();
    } catch (err) {
      setError(err.message || 'Failed to pause session.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await api.resumeScraper();
    } catch (err) {
      setError(err.message || 'Failed to resume session.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await api.stopScraper();
    } catch (err) {
      setError(err.message || 'Failed to stop session.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartExtraction = async () => {
    try {
      setExtractionLoading(true);
      setError(null);
      await api.startDetailExtraction();
      const st = await api.getDetailExtractionStatus().catch(() => null);
      if (st) setExtractionStatus(st);
    } catch (err) {
      setError(err.message || 'Failed to start deep job details extraction.');
    } finally {
      setExtractionLoading(false);
    }
  };

  const currStatus = scraperStatus.status?.toUpperCase() || 'IDLE';
  const isRunning = currStatus === 'RUNNING' || currStatus === 'INITIALIZING';
  const isPaused = currStatus === 'PAUSED';

  return (
    <div className="space-y-6">
      {/* Header */}
      <SectionHeader
        title="SCRAPER RECONNAISSANCE ENGINE"
        subtitle="Automated background lifecycle orchestration, safe checkpoints (Pause / Resume / Stop), and Server-Sent Events (SSE) telemetry."
        badgeText={currStatus}
        badgeVariant={
          currStatus === 'RUNNING'
            ? 'orange'
            : currStatus === 'PAUSED'
            ? 'warning'
            : currStatus === 'COMPLETED'
            ? 'success'
            : currStatus === 'FAILED'
            ? 'danger'
            : 'cyan'
        }
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge variant={sseConnected ? 'cyan' : 'standby'} size="sm" dot={true}>
              {sseConnected ? 'SSE LIVE STREAM' : 'SSE POLLING'}
            </StatusBadge>
            <Button
              variant="secondary"
              size="sm"
              icon={RefreshCw}
              onClick={loadInitialState}
            >
              SYNC
            </Button>
          </div>
        }
      />

      {error && (
        <ErrorAlert
          title="SCRAPER CONTROL ERROR"
          message={error}
          onRetry={loadInitialState}
        />
      )}

      {/* Haveloc Portal Authentication & Session Gateway (Phase 5) */}
      <PortalConnectionCard onStatusChange={(st) => setPortalConnected(st.authentication_status === 'CONNECTED')} />

      {/* Engine Status Banner */}
      <div className="p-4 bg-[#151D29] border border-[#00D4FF]/40 rounded-lg tech-corner flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2.5 text-[#E6EDF3]">
          <Shield className="w-5 h-5 text-[#00D4FF] shrink-0" />
          <div>
            <span className="text-[#00D4FF] font-bold block">
              PHASE 4 & 5 ARCHITECTURE ACTIVE // PERSISTENT BROWSER SESSION READY
            </span>
            <p className="text-[#8492A6] text-[11px] mt-0.5">
              Engine exercises safe synchronization checkpoints, SQLite persistence, and real-time SSE event delivery with persistent Chromium browser profile management.
            </p>
          </div>
        </div>
        <StatusBadge variant="cyan" size="xs" dot={true}>
          ENGINE READY
        </StatusBadge>
      </div>

      {/* 4 Telemetry Metric KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Cpu}
          label="ENGINE STATE"
          value={currStatus}
          subtext={scraperStatus.session_id ? `Active Session #${scraperStatus.session_id}` : 'Engine Standing By'}
          trend={isRunning ? 'Processing Checkpoints' : isPaused ? 'Paused at Barrier' : 'Awaiting Directive'}
          trendPositive={isRunning}
          cyan={!isRunning}
          isDemo={false}
        />
        <StatCard
          icon={Layers}
          label="DISCOVERED NOTICES"
          value={scraperStatus.records_discovered ?? 0}
          subtext="Captured in current session"
          trend="Real SQLite Counters"
          trendPositive={true}
          cyan={true}
          isDemo={false}
        />
        <StatCard
          icon={HardDrive}
          label="PROCESSED RECORDS"
          value={scraperStatus.records_processed ?? 0}
          subtext="Committed to database"
          trend="Transaction Safe"
          trendPositive={true}
          cyan={false}
          isDemo={false}
        />
        <StatCard
          icon={Globe}
          label="PORTAL HARVEST STATE"
          value={isRunning ? 'DISCOVERING' : portalConnected ? 'PORTAL ACTIVE' : 'AWAITING GATEWAY'}
          subtext={isRunning ? 'Inspecting DOM & Pages' : portalConnected ? 'Ready for Extraction' : 'Connect Portal First'}
          trend={portalConnected ? 'Session Authenticated' : 'Manual Login Required'}
          trendPositive={portalConnected}
          cyan={portalConnected}
          isDemo={false}
        />
      </div>

      {/* Control Console Deck */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Control Panel */}
        <div className="lg:col-span-2 bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-3.5 rounded-sm bg-[#FF6A00]"></span>
              <h3 className="font-semibold text-xs sm:text-sm uppercase tracking-wider text-[#E6EDF3] font-mono">
                Lifecycle Orchestration Controls
              </h3>
            </div>
            <span className="text-[11px] font-mono text-[#8492A6]">
              SESSION ID: <span className="text-[#00D4FF] font-bold">#{scraperStatus.session_id ?? 'NONE'}</span>
            </span>
          </div>

          {/* Progress Indicator */}
          <div className="space-y-2 font-mono">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#8492A6]">EXECUTION PROGRESS:</span>
              <span className="text-[#00D4FF] font-bold">{scraperStatus.progress_percentage ?? 0}% COMPLETED</span>
            </div>
            <div className="w-full bg-[#0B0E14] h-3 rounded-full overflow-hidden border border-[#263244] p-0.5">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isPaused
                    ? 'bg-amber-400'
                    : 'bg-gradient-to-r from-[#FF6A00] via-[#00D4FF] to-emerald-400'
                }`}
                style={{ width: `${scraperStatus.progress_percentage ?? 0}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-between text-[10px] text-[#8492A6] pt-1">
              <span>INITIALIZING</span>
              <span>RUNNING (CHECKPOINTS)</span>
              <span>PAUSED / RESUMABLE</span>
              <span>COMPLETED</span>
            </div>
          </div>

          {/* Real Backend Control Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {!isRunning && !isPaused ? (
              <>
                <Button
                  variant="primary"
                  size="md"
                  icon={Play}
                  loading={actionLoading}
                  onClick={handleStart}
                >
                  START DISCOVERY
                </Button>
                <Button
                  variant="secondary"
                  size="md"
                  icon={Sparkles}
                  loading={extractionLoading}
                  onClick={handleStartExtraction}
                >
                  EXTRACT JOB DETAILS
                </Button>
              </>
            ) : null}

            {isRunning ? (
              <Button
                variant="secondary"
                size="md"
                icon={Pause}
                loading={actionLoading}
                onClick={handlePause}
              >
                PAUSE SESSION
              </Button>
            ) : null}

            {isPaused ? (
              <Button
                variant="primary"
                size="md"
                icon={Play}
                loading={actionLoading}
                onClick={handleResume}
              >
                RESUME SESSION
              </Button>
            ) : null}

            {isRunning || isPaused ? (
              <Button
                variant="danger"
                size="md"
                icon={Square}
                loading={actionLoading}
                onClick={handleStop}
              >
                STOP SESSION
              </Button>
            ) : null}
          </div>
        </div>

        {/* Engine Parameters & Isolation Specs */}
        <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner-cyan space-y-4 font-mono text-xs">
          <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3] pb-2 border-b border-[#263244]">
            Engine Parameters
          </h3>

          <div className="space-y-2 text-[#8492A6]">
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex justify-between">
              <span>SYNC BARRIER:</span>
              <span className="text-emerald-400 font-bold">asyncio.Event</span>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex justify-between">
              <span>SSE STREAM:</span>
              <span className="text-[#00D4FF] font-bold">/api/scraper/events</span>
            </div>
            <div className="p-2.5 bg-[#101620] border border-[#263244] rounded flex justify-between">
              <span>ISOLATED DIR:</span>
              <span className="text-[#FF6A00] truncate max-w-[120px]">./playwright-browsers</span>
            </div>
          </div>
        </div>
      </div>

      {/* Live Activity Terminal Console (Streaming real SSE logs) */}
      <TerminalConsole
        logs={logs}
        onClear={() => setLogs([])}
        title="REAL-TIME TELEMETRY STREAM (SSE)"
        subtitle="Live server-sent events dispatched from background scraper engine"
      />

      {/* Data Cleaning, Normalization & Quality Audit (Phase 8) */}
      <DataQualityPanel onSelectJob={(job) => setInspectedJob(job)} />

      {/* Scraping Sessions History Table (from /api/sessions) */}
      <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-3.5 rounded-sm bg-[#FF6A00]"></span>
            <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
              Persistent Scraping Sessions Audit
            </h3>
          </div>
          <StatusBadge variant="cyan" size="xs">
            {sessions.length} SESSIONS RECORDED
          </StatusBadge>
        </div>

        <div className="overflow-x-auto border border-[#263244] rounded-lg">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#263244] bg-[#101620] text-[#8492A6] uppercase text-[10px] tracking-wider">
                <th className="py-3 px-4">Session ID</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Started At</th>
                <th className="py-3 px-4">Completed At</th>
                <th className="py-3 px-4">Discovered</th>
                <th className="py-3 px-4">Processed</th>
                <th className="py-3 px-4">Diagnostic Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#263244]/60">
              {sessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#8492A6]">
                    NO PRIOR SCRAPING SESSIONS RECORDED IN SQLITE ARCHIVE.
                  </td>
                </tr>
              ) : (
                sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-[#101620]/60 transition-colors">
                    <td className="py-3 px-4 font-bold text-[#00D4FF]">#{s.id}</td>
                    <td className="py-3 px-4">
                      <StatusBadge
                        variant={
                          s.status === 'COMPLETED'
                            ? 'success'
                            : s.status === 'RUNNING'
                            ? 'orange'
                            : s.status === 'PAUSED'
                            ? 'warning'
                            : s.status === 'FAILED'
                            ? 'danger'
                            : s.status === 'CANCELLED'
                            ? 'danger'
                            : 'cyan'
                        }
                        size="xs"
                        dot={true}
                      >
                        {s.status}
                      </StatusBadge>
                    </td>
                    <td className="py-3 px-4 text-[#8492A6]">
                      {formatDateTimeIST(s.started_at)}
                    </td>
                    <td className="py-3 px-4 text-[#8492A6]">
                      {formatDateTimeIST(s.completed_at, { fallback: 'Active / Pending' })}
                    </td>
                    <td className="py-3 px-4 text-[#E6EDF3] font-bold">{s.records_discovered}</td>
                    <td className="py-3 px-4 text-[#00D4FF] font-bold">{s.records_processed}</td>
                    <td className="py-3 px-4 text-[#8492A6] text-[11px] max-w-xs truncate">
                      {s.error_message || 'Nominal execution'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deep Job Inspection Modal */}
      {inspectedJob && (
        <JobDetailsModal
          job={inspectedJob}
          onClose={() => setInspectedJob(null)}
        />
      )}
    </div>
  );
}
