import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Briefcase,
  TrendingUp,
  Award,
  Play,
  Activity,
  Layers,
  ArrowRight,
  HardDrive,
  Cpu,
  Database,
  CheckCircle2,
  Clock,
  Sparkles,
  AlertTriangle,
  Info,
} from 'lucide-react';
import StatCard from '../components/common/StatCard';
import ChartCard from '../components/common/ChartCard';
import StatusBadge from '../components/common/StatusBadge';
import Button from '../components/common/Button';
import ActivityTimeline from '../components/dashboard/ActivityTimeline';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import { api } from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';

// Demonstration datasets for UI preview when database is initially unpopulated
const DEMO_SALARY_DIST = [
  { bracket: '< 6 LPA', count: 18, percentage: 16 },
  { bracket: '6 - 10 LPA', count: 36, percentage: 32 },
  { bracket: '10 - 15 LPA', count: 28, percentage: 25 },
  { bracket: '15 - 25 LPA', count: 20, percentage: 18 },
  { bracket: '25+ LPA', count: 10, percentage: 9 },
];

const DEMO_COMPANY_PACKAGES = [
  { name: 'Google', maxCtc: 55.0, avgCtc: 48.0 },
  { name: 'Microsoft', maxCtc: 51.5, avgCtc: 44.0 },
  { name: 'Amazon', maxCtc: 45.0, avgCtc: 32.5 },
  { name: 'DE Shaw', maxCtc: 42.0, avgCtc: 38.0 },
  { name: 'Oracle', maxCtc: 34.0, avgCtc: 24.0 },
  { name: 'Goldman Sachs', maxCtc: 32.0, avgCtc: 28.0 },
  { name: 'Cisco', maxCtc: 28.0, avgCtc: 19.5 },
];

const DEMO_JOB_DISTRIBUTION = [
  { name: 'Software Development', value: 48, color: '#00D4FF' },
  { name: 'Data & Machine Learning', value: 22, color: '#FF6A00' },
  { name: 'Cloud & Infrastructure', value: 16, color: '#10B981' },
  { name: 'Consulting & Analytics', value: 14, color: '#A855F7' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [scraperState, setScraperState] = useState('DISCONNECTED');
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('LIVE'); // 'LIVE' or 'DEMO'

  const fetchTelemetry = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, sysData, scraperData, activityData] = await Promise.all([
        api.getDashboardStats().catch(() => null),
        api.getSystemStatus().catch(() => null),
        api.getScraperStatus().catch(() => null),
        api.getDashboardActivity(10).catch(() => []),
      ]);

      if (statsData) {
        setStats(statsData);
        setBackendOnline(true);
      } else {
        setBackendOnline(false);
        // Default zero state
        setStats({
          total_companies: 0,
          total_jobs: 0,
          average_ctc: 0.0,
          highest_ctc: 0.0,
          lowest_ctc: 0.0,
          full_time_jobs: 0,
          internship_jobs: 0,
          total_scraping_sessions: 0,
        });
      }

      setSystemStatus(sysData);
      setScraperState(scraperData?.status || sysData?.scraper_status || (statsData ? 'IDLE' : 'DISCONNECTED'));
      setRecentActivity(Array.isArray(activityData) ? activityData : []);
    } catch (err) {
      setError(err.message || 'Could not connect to FastAPI backend service.');
      setBackendOnline(false);
      setScraperState('DISCONNECTED');
      setRecentActivity([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  const isDatabaseEmpty = (stats?.total_companies || 0) === 0 && (stats?.total_jobs || 0) === 0;

  if (loading) return <LoadingSpinner text="SYNCHRONIZING WITH BACKEND DATABASE..." />;

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero Header */}
      <div className="relative bg-[#151D29] border border-[#263244] rounded-xl p-6 tech-corner shadow-hud-card overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-[#00D4FF]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-72 h-72 bg-[#FF6A00]/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#FF6A00]/20 text-[#FF6A00] border border-[#FF6A00]/40">
                HAV_SCRAP // OPERATIONAL
              </span>
              <StatusBadge variant={backendOnline ? 'success' : 'danger'} size="xs" dot={true}>
                {backendOnline ? 'BACKEND LINKED (127.0.0.1:8000)' : 'BACKEND DISCONNECTED'}
              </StatusBadge>
              {isDatabaseEmpty && viewMode === 'LIVE' ? (
                <StatusBadge variant="standby" size="xs" dot={false}>
                  DATABASE: 0 RECORDS (EMPTY)
                </StatusBadge>
              ) : (
                <StatusBadge variant={viewMode === 'LIVE' ? 'cyan' : 'demo'} size="xs" dot={false}>
                  {viewMode === 'LIVE' ? 'ACTUAL DATABASE RECORDS' : 'DEMO TELEMETRY PREVIEW'}
                </StatusBadge>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold font-mono tracking-tight text-[#E6EDF3]">
              HAV_SCRAP PLACEMENT INTELLIGENCE SYSTEM
            </h1>
            <p className="text-xs sm:text-sm text-[#8492A6] font-mono max-w-2xl">
              Your centralized placement data intelligence platform developed by Falkenbeast Labs. Real-time recruiter tracking, compensation distribution, and portal reconnaissance engine.
            </p>
          </div>

          {/* Toggle View Mode between Actual Database and Demo Preview */}
          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <div className="flex items-center bg-[#101620] border border-[#263244] rounded-md p-1 font-mono text-xs">
              <button
                onClick={() => setViewMode('LIVE')}
                className={`px-3 py-1.5 rounded transition-all font-semibold ${
                  viewMode === 'LIVE'
                    ? 'bg-[#00D4FF] text-black shadow-glow-sm-cyan'
                    : 'text-[#8492A6] hover:text-[#E6EDF3]'
                }`}
              >
                LIVE DATABASE
              </button>
              <button
                onClick={() => setViewMode('DEMO')}
                className={`px-3 py-1.5 rounded transition-all font-semibold ${
                  viewMode === 'DEMO'
                    ? 'bg-[#FF6A00] text-black shadow-glow-sm-orange'
                    : 'text-[#8492A6] hover:text-[#E6EDF3]'
                }`}
              >
                DEMO PREVIEW
              </button>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={fetchTelemetry}
            >
              SYNC
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={Play}
              onClick={() => navigate('/scraper')}
            >
              SCRAPER DECK
            </Button>
          </div>
        </div>
      </div>

      {/* Database Empty Warning Banner */}
      {isDatabaseEmpty && viewMode === 'LIVE' && (
        <div className="p-4 bg-[#151D29] border border-[#FF6A00]/50 rounded-lg tech-corner flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2.5 text-[#E6EDF3]">
            <Info className="w-5 h-5 text-[#FF6A00] shrink-0" />
            <div>
              <span className="text-[#FF6A00] font-bold block">
                SQLITE DATABASE IS CURRENTLY EMPTY (data/hav_scrap.db)
              </span>
              <p className="text-[#8492A6] text-[11px] mt-0.5">
                The database tables exist but no portal extraction has occurred yet. Showing verified empty state. Switch to "DEMO PREVIEW" above to inspect visual charts.
              </p>
            </div>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setViewMode('DEMO')}
          >
            SHOW DEMO CHARTS
          </Button>
        </div>
      )}

      {/* 4 Primary KPI Stat Cards (Displaying Actual Backend Values) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Building2}
          label="Total Companies"
          value={viewMode === 'LIVE' ? stats?.total_companies ?? 0 : 42}
          subtext={viewMode === 'LIVE' ? 'Entities in data/hav_scrap.db' : 'Demonstration portfolio'}
          trend={viewMode === 'LIVE' ? 'Actual Database Records' : '+8 this cycle'}
          trendPositive={true}
          cyan={false}
          isDemo={viewMode === 'DEMO'}
        />
        <StatCard
          icon={Briefcase}
          label="Job Opportunities"
          value={viewMode === 'LIVE' ? stats?.total_jobs ?? 0 : 112}
          subtext={
            viewMode === 'LIVE'
              ? `FTE: ${stats?.full_time_jobs || 0} | Intern: ${stats?.internship_jobs || 0}`
              : 'Indexed notices'
          }
          trend={viewMode === 'LIVE' ? 'Persistent Postings' : '+14 new notices'}
          trendPositive={true}
          cyan={true}
          isDemo={viewMode === 'DEMO'}
        />
        <StatCard
          icon={TrendingUp}
          label="Average CTC"
          value={
            viewMode === 'LIVE'
              ? `${(stats?.average_ctc || stats?.avg_salary_lpa || 0.0).toFixed(2)} LPA`
              : '14.80 LPA'
          }
          subtext="Computed from verified records"
          trend={viewMode === 'LIVE' ? 'Live Mean LPA' : 'Campus Mean'}
          trendPositive={true}
          cyan={false}
          isDemo={viewMode === 'DEMO'}
        />
        <StatCard
          icon={Award}
          label="Highest Package"
          value={
            viewMode === 'LIVE'
              ? `${(stats?.highest_ctc || stats?.highest_salary_lpa || 0.0).toFixed(2)} LPA`
              : '55.00 LPA'
          }
          subtext="Pinnacle compensation offer"
          trend={viewMode === 'LIVE' ? `Lowest: ${(stats?.lowest_ctc || 0.0).toFixed(2)} LPA` : 'Google LLC'}
          trendPositive={true}
          cyan={true}
          isDemo={viewMode === 'DEMO'}
        />
      </div>

      {/* Primary Analytics Grid */}
      {isDatabaseEmpty && viewMode === 'LIVE' ? (
        <EmptyState
          title="DATABASE AWAITING HARVESTED PLACEMENT DATA"
          message="No companies or job offers are logged in data/hav_scrap.db yet. Connect to the Haveloc placement portal in Scraper Control and start discovery to populate real-time visualizers."
          actionLabel="VIEW SAMPLE VISUALIZERS (DEMO MODE)"
          onAction={() => setViewMode('DEMO')}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart 1: Salary Distribution */}
            <div className="lg:col-span-2">
              <ChartCard
                title="Compensation Bracket Distribution"
                subtitle="Frequency of offers grouped across salary bands (LPA)"
                cyan={true}
                isDemo={viewMode === 'DEMO'}
              >
                <div className="h-64 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={DEMO_SALARY_DIST} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <XAxis
                        dataKey="bracket"
                        stroke="#8492A6"
                        fontSize={11}
                        tickLine={false}
                        fontFamily="JetBrains Mono"
                      />
                      <YAxis
                        stroke="#8492A6"
                        fontSize={11}
                        tickLine={false}
                        fontFamily="JetBrains Mono"
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#101620',
                          borderColor: '#00D4FF',
                          borderRadius: '6px',
                          fontFamily: 'JetBrains Mono',
                          fontSize: '12px',
                        }}
                        cursor={{ fill: 'rgba(0, 212, 255, 0.05)' }}
                      />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]} name="Opportunities Count">
                        {DEMO_SALARY_DIST.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={index % 2 === 0 ? '#00D4FF' : '#FF6A00'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-3 pt-2 border-t border-[#263244] flex items-center justify-between text-[11px] font-mono text-[#8492A6]">
                  <span>MEDIAN BRACKET: 6 - 10 LPA</span>
                  <span className="text-[#00D4FF]">32% TOTAL POPULATION</span>
                </div>
              </ChartCard>
            </div>

            {/* Chart 3: Profile Distribution */}
            <ChartCard
              title="Profile Specializations"
              subtitle="Breakdown of drives categorized by technical discipline"
              cyan={false}
              isDemo={viewMode === 'DEMO'}
            >
              <div className="h-60 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={DEMO_JOB_DISTRIBUTION}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {DEMO_JOB_DISTRIBUTION.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke="#101620" strokeWidth={2} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#101620',
                        borderColor: '#FF6A00',
                        borderRadius: '6px',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '12px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#263244] text-[10px] font-mono">
                {DEMO_JOB_DISTRIBUTION.map((item) => (
                  <div key={item.name} className="flex items-center gap-1.5 truncate">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                    <span className="text-[#8492A6] truncate">{item.name} ({item.value}%)</span>
                  </div>
                ))}
              </div>
            </ChartCard>
          </div>

          {/* Chart 2: Company-wise Package Comparison */}
          <ChartCard
            title="Tier-1 Recruiter Package Benchmark"
            subtitle="Comparison of pinnacle offer (Peak CTC) versus mean package across marquee tech giants"
            cyan={true}
            isDemo={viewMode === 'DEMO'}
          >
            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={DEMO_COMPANY_PACKAGES} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis
                    dataKey="name"
                    stroke="#8492A6"
                    fontSize={11}
                    tickLine={false}
                    fontFamily="JetBrains Mono"
                  />
                  <YAxis
                    stroke="#8492A6"
                    fontSize={11}
                    tickLine={false}
                    fontFamily="JetBrains Mono"
                    unit=" LPA"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#101620',
                      borderColor: '#00D4FF',
                      borderRadius: '6px',
                      fontFamily: 'JetBrains Mono',
                      fontSize: '12px',
                    }}
                    cursor={{ fill: 'rgba(0, 212, 255, 0.05)' }}
                  />
                  <Bar dataKey="maxCtc" fill="#FF6A00" radius={[4, 4, 0, 0]} name="Peak Package (LPA)" />
                  <Bar dataKey="avgCtc" fill="#00D4FF" radius={[4, 4, 0, 0]} name="Mean Package (LPA)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 pt-2 border-t border-[#263244] flex items-center justify-between text-[11px] font-mono text-[#8492A6]">
              <span className="flex items-center gap-2 text-[#FF6A00]">
                <span className="w-2 h-2 rounded-full bg-[#FF6A00]"></span> PEAK COMPENSATION
              </span>
              <span className="flex items-center gap-2 text-[#00D4FF]">
                <span className="w-2 h-2 rounded-full bg-[#00D4FF]"></span> MEAN COMPENSATION
              </span>
            </div>
          </ChartCard>
        </>
      )}

      {/* Bottom Row: Recent Activity Timeline & System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Timeline */}
        <div className="lg:col-span-2 bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#263244]">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-3.5 rounded-sm bg-[#00D4FF]"></span>
              <h3 className="font-semibold text-xs sm:text-sm uppercase tracking-wider text-[#E6EDF3] font-mono">
                Recent Intelligence Activity
              </h3>
            </div>
            <StatusBadge variant="cyan" size="xs" dot={true}>
              AUDIT FEED
            </StatusBadge>
          </div>

          <ActivityTimeline
            events={viewMode === 'LIVE' ? recentActivity : []}
            isDemo={viewMode === 'DEMO'}
          />
        </div>

        {/* System Status Matrix (Using actual /system/status telemetry) */}
        <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner-cyan flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#263244]">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-3.5 rounded-sm bg-[#FF6A00]"></span>
                <h3 className="font-semibold text-xs sm:text-sm uppercase tracking-wider text-[#E6EDF3] font-mono">
                  System Diagnostics
                </h3>
              </div>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* Frontend Status */}
              <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-[#8492A6]">FRONTEND CLIENT</p>
                  <p className="text-xs font-bold text-[#E6EDF3]">React 18 + Vite</p>
                </div>
                <StatusBadge variant="success" size="xs" dot={true}>
                  OPERATIONAL
                </StatusBadge>
              </div>

              {/* Backend Connection */}
              <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-[#8492A6]">FASTAPI CORE</p>
                  <p className="text-xs font-bold text-[#E6EDF3]">
                    {systemStatus?.version ? `v${systemStatus.version} [ONLINE]` : '127.0.0.1:8000'}
                  </p>
                </div>
                <StatusBadge variant={backendOnline ? 'success' : 'danger'} size="xs" dot={true}>
                  {backendOnline ? 'CONNECTED' : 'DISCONNECTED'}
                </StatusBadge>
              </div>

              {/* Database Status */}
              <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-[#8492A6]">DATABASE FILE</p>
                  <p className="text-xs font-bold text-[#E6EDF3] truncate max-w-[140px]">
                    {systemStatus?.database_connected ? 'hav_scrap.db (Active)' : 'Connecting...'}
                  </p>
                </div>
                <StatusBadge variant={systemStatus?.database_connected ? 'cyan' : 'warning'} size="xs" dot={true}>
                  {systemStatus?.database_connected ? 'CONNECTED' : 'STANDBY'}
                </StatusBadge>
              </div>

              {/* Scraper Status */}
              <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-[#8492A6]">SCRAPER AVAILABILITY</p>
                  <p className="text-xs font-bold text-[#FF6A00]">
                    {!backendOnline
                      ? 'CORE OFFLINE'
                      : scraperState === 'RUNNING'
                      ? 'RECON ACTIVE'
                      : scraperState === 'PAUSED'
                      ? 'RECON PAUSED'
                      : scraperState === 'COMPLETED'
                      ? 'SESSION COMPLETED'
                      : 'IDLE (READY)'}
                  </p>
                </div>
                <StatusBadge
                  variant={
                    !backendOnline
                      ? 'danger'
                      : scraperState === 'RUNNING'
                      ? 'warning'
                      : scraperState === 'PAUSED'
                      ? 'warning'
                      : scraperState === 'COMPLETED'
                      ? 'success'
                      : 'cyan'
                  }
                  size="xs"
                  dot={true}
                >
                  {!backendOnline ? 'DISCONNECTED' : scraperState || 'READY'}
                </StatusBadge>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[#263244]">
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              icon={ArrowRight}
              onClick={() => navigate('/settings')}
            >
              INSPECT SYSTEM PARAMETERS
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
