import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  PieChart as PieIcon,
  MapPin,
  Briefcase,
  Layers,
  Sparkles,
  Calendar,
  Filter,
  RefreshCw,
  Building2,
  TrendingUp,
  Award,
  Clock,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  GraduationCap,
} from 'lucide-react';
import SectionHeader from '../components/common/SectionHeader';
import StatCard from '../components/common/StatCard';
import ChartCard from '../components/common/ChartCard';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button';
import { api } from '../services/api';
import { formatDateTimeIST } from '../utils/formatters';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from 'recharts';

export default function Analytics() {
  // Global Filters
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedJobType, setSelectedJobType] = useState('');
  const [filterOptions, setFilterOptions] = useState({ companies: [], job_types: [], locations: [] });

  // Data States
  const [overview, setOverview] = useState(null);
  const [salaryDist, setSalaryDist] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [locations, setLocations] = useState([]);
  const [jobTypes, setJobTypes] = useState(null);
  const [trends, setTrends] = useState(null);
  const [eligibility, setEligibility] = useState(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [companyRankSort, setCompanyRankSort] = useState('highest_ctc');

  // Load available filter values on mount
  useEffect(() => {
    async function loadFilters() {
      try {
        const f = await api.getAnalyticsFilters();
        setFilterOptions(f);
      } catch (err) {
        console.warn('Could not load analytics filters:', err);
      }
    }
    loadFilters();
  }, []);

  // Fetch all analytics datasets concurrently from backend
  const loadAnalytics = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      const params = {};
      if (selectedCompany) params.company = selectedCompany;
      if (selectedJobType) params.job_type = selectedJobType;

      const [
        overviewData,
        distData,
        rankingsData,
        locData,
        jobTypeData,
        trendData,
        eligData,
      ] = await Promise.all([
        api.getAnalyticsOverview(params).catch(() => null),
        api.getSalaryDistribution(params).catch(() => null),
        api.getCompanyRankings({ ...params, sort_by: companyRankSort, page_size: 10 }).catch(() => ({ items: [] })),
        api.getLocationDistribution({ ...params, limit: 8 }).catch(() => []),
        api.getJobTypeDistribution(params).catch(() => null),
        api.getOpportunityTrends(params).catch(() => null),
        api.getEligibilityInsights(params).catch(() => null),
      ]);

      setOverview(overviewData);
      setSalaryDist(distData);
      setRankings(rankingsData?.items || []);
      setLocations(locData || []);
      setJobTypes(jobTypeData);
      setTrends(trendData);
      setEligibility(eligData);
    } catch (err) {
      console.error('Analytics fetch fault:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedCompany, selectedJobType, companyRankSort]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const isEmpty = !loading && (!overview || overview.total_jobs === 0);

  // Palette constants
  const PIE_COLORS = ['#00D4FF', '#FF6A00', '#10B981', '#A855F7', '#F59E0B', '#3B82F6'];

  return (
    <div className="space-y-6">
      {/* A. PAGE HEADER */}
      <SectionHeader
        title="Placement Analytics"
        subtitle="Data-driven insights into company opportunities and compensation."
        badgeText="SQLITE INTELLIGENCE"
        badgeVariant="cyan"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {/* Company Filter Dropdown */}
            <select
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="px-3 py-1.5 text-xs font-mono bg-[#151D29] text-[#E6EDF3] border border-[#263244] rounded hover:border-[#00D4FF]/50 focus:outline-none focus:border-[#00D4FF] transition-colors"
            >
              <option value="">All Companies</option>
              {filterOptions.companies.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>

            {/* Job Type Filter Dropdown */}
            <select
              value={selectedJobType}
              onChange={(e) => setSelectedJobType(e.target.value)}
              className="px-3 py-1.5 text-xs font-mono bg-[#151D29] text-[#E6EDF3] border border-[#263244] rounded hover:border-[#FF6A00]/50 focus:outline-none focus:border-[#FF6A00] transition-colors"
            >
              <option value="">All Job Types</option>
              {filterOptions.job_types.map((jt) => (
                <option key={jt} value={jt}>
                  {jt}
                </option>
              ))}
            </select>

            {/* Refresh Button */}
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              onClick={() => loadAnalytics(true)}
              disabled={refreshing || loading}
              className={refreshing ? 'animate-spin' : ''}
            >
              REFRESH
            </Button>

            <StatusBadge variant="cyan" size="sm" dot={true}>
              {overview ? `${overview.total_jobs} POSTINGS AUDITED` : 'ONLINE'}
            </StatusBadge>
          </div>
        }
      />

      {loading ? (
        <LoadingSpinner text="CALCULATING PLACEMENT ANALYTICS & SALARY METRICS..." />
      ) : isEmpty ? (
        <EmptyState
          title="DATABASE HAS NO COLLECTED PLACEMENT DATA"
          message="data/hav_scrap.db contains 0 discovered job opportunities. Run discovery or extraction from the Scraper Control console to populate analytics."
          actionLabel="OPEN SCRAPER CONSOLE"
          onAction={() => window.location.assign('/scraper')}
        />
      ) : (
        <>
          {/* B. KPI CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <StatCard
              icon={Building2}
              label="Total Companies"
              value={overview?.total_companies ?? 0}
              subtext="Recruiters indexed"
              trend="Corporate Partners"
              cyan={true}
            />
            <StatCard
              icon={Briefcase}
              label="Total Opportunities"
              value={overview?.total_jobs ?? 0}
              subtext="Active job notices"
              trend="Live Postings"
              cyan={false}
            />
            <StatCard
              icon={Award}
              label="Highest Package"
              value={overview?.highest_ctc_lpa ? `${overview.highest_ctc_lpa} LPA` : 'N/A'}
              subtext="Pinnacle verified CTC"
              trend="Maximum Offer"
              cyan={true}
            />
            <StatCard
              icon={TrendingUp}
              label="Average Package"
              value={overview?.average_ctc_lpa ? `${overview.average_ctc_lpa} LPA` : 'N/A'}
              subtext="Arithmetic mean CTC"
              trend="Mean Compensation"
              cyan={false}
            />
            <StatCard
              icon={CheckCircle2}
              label="Full-Time Roles"
              value={overview?.total_fulltime ?? 0}
              subtext="Direct FTE positions"
              trend="Full-Time Offers"
              cyan={true}
            />
            <StatCard
              icon={Layers}
              label="Internships"
              value={overview?.total_internships ?? 0}
              subtext="Summer / 6M notices"
              trend={`${overview?.companies_offering_internships ?? 0} companies`}
              cyan={false}
            />
          </div>

          {/* C. SALARY DISTRIBUTION & KEY PERCENTILES */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ChartCard
                title="Salary Distribution Across Companies (LPA)"
                subtitle="Frequency of full-time verified job opportunities classified into 7 standardized compensation brackets"
                cyan={true}
              >
                <div className="h-72 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={salaryDist?.brackets || []}
                      margin={{ top: 15, right: 15, left: -10, bottom: 25 }}
                    >
                      <XAxis
                        dataKey="bracket"
                        stroke="#8492A6"
                        fontSize={10.5}
                        tickLine={false}
                        fontFamily="JetBrains Mono"
                        angle={-20}
                        textAnchor="end"
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
                        formatter={(val, name, item) => [
                          `${val} notices (${item.payload.percentage}%)`,
                          'Volume',
                        ]}
                      />
                      <Bar dataKey="count" fill="#00D4FF" radius={[4, 4, 0, 0]} name="Notices" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>

            {/* Salary Key Indicators Card */}
            <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner flex flex-col justify-between space-y-4 font-mono">
              <div className="space-y-1 pb-3 border-b border-[#263244]">
                <span className="text-[10px] font-bold text-[#00D4FF] tracking-wider uppercase">
                  COMPENSATION AUDIT METRICS
                </span>
                <h3 className="text-sm font-bold text-[#E6EDF3]">Benchmark Percentiles</h3>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                  <span className="text-[#8492A6]">Highest Disclosed:</span>
                  <span className="text-emerald-400 font-bold text-sm">
                    {salaryDist?.highest_salary ? `${salaryDist.highest_salary} LPA` : 'N/A'}
                  </span>
                </div>

                <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                  <span className="text-[#8492A6]">Median Package (50th %):</span>
                  <span className="text-[#00D4FF] font-bold text-sm">
                    {salaryDist?.median_salary ? `${salaryDist.median_salary} LPA` : 'N/A'}
                  </span>
                </div>

                <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                  <span className="text-[#8492A6]">Average Disclosed:</span>
                  <span className="text-[#FF6A00] font-bold text-sm">
                    {overview?.average_ctc_lpa ? `${overview.average_ctc_lpa} LPA` : 'N/A'}
                  </span>
                </div>

                <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                  <span className="text-[#8492A6]">Floor / Lowest Disclosed:</span>
                  <span className="text-[#E6EDF3] font-bold text-sm">
                    {salaryDist?.lowest_salary ? `${salaryDist.lowest_salary} LPA` : 'N/A'}
                  </span>
                </div>

                <div className="p-3 bg-[#101620] border border-[#263244] rounded flex items-center justify-between">
                  <span className="text-[#8492A6]">Total Disclosed Packages:</span>
                  <span className="text-[#00D4FF] font-bold">
                    {salaryDist?.total_disclosed ?? 0} notices
                  </span>
                </div>
              </div>

              <div className="pt-2 text-[11px] text-[#8492A6] leading-relaxed">
                * Note: Internship stipends and unverified / pending review records are strictly excluded from all CTC benchmarks.
              </div>
            </div>
          </div>

          {/* D. COMPANY INTELLIGENCE & LEAGUE TABLE */}
          <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-[#263244]">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-3.5 rounded-sm bg-[#FF6A00]"></span>
                  <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3] text-sm">
                    Recruiter Rankings & League Table
                  </h3>
                </div>
                <p className="text-[11px] text-[#8492A6]">
                  Verified campus drive statistics and corporate placement performance
                </p>
              </div>

              {/* Sorting selector */}
              <div className="flex items-center gap-1.5 bg-[#101620] p-1 border border-[#263244] rounded text-[11px]">
                <button
                  onClick={() => setCompanyRankSort('highest_ctc')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    companyRankSort === 'highest_ctc'
                      ? 'bg-[#FF6A00] text-black font-bold'
                      : 'text-[#8492A6] hover:text-[#E6EDF3]'
                  }`}
                >
                  HIGHEST CTC
                </button>
                <button
                  onClick={() => setCompanyRankSort('average_ctc')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    companyRankSort === 'average_ctc'
                      ? 'bg-[#00D4FF] text-black font-bold'
                      : 'text-[#8492A6] hover:text-[#E6EDF3]'
                  }`}
                >
                  AVERAGE CTC
                </button>
                <button
                  onClick={() => setCompanyRankSort('opportunities_count')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    companyRankSort === 'opportunities_count'
                      ? 'bg-[#E6EDF3] text-black font-bold'
                      : 'text-[#8492A6] hover:text-[#E6EDF3]'
                  }`}
                >
                  MOST OPPORTUNITIES
                </button>
              </div>
            </div>

            <div className="overflow-x-auto border border-[#263244] rounded-lg">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#263244] bg-[#101620] text-[#8492A6] uppercase text-[10px] tracking-wider">
                    <th className="py-3 px-4">Rank</th>
                    <th className="py-3 px-4">Recruiter / Corporate Partner</th>
                    <th className="py-3 px-4 text-center">Active Opportunities</th>
                    <th className="py-3 px-4 text-right">Highest CTC (LPA)</th>
                    <th className="py-3 px-4 text-right">Average CTC (LPA)</th>
                    <th className="py-3 px-4 text-center">Internships</th>
                    <th className="py-3 px-4 text-center">Disclosed Records</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#263244]/60">
                  {rankings.map((c, idx) => (
                    <tr key={c.company_name} className="hover:bg-[#101620]/60 transition-colors">
                      <td className="py-3 px-4 font-bold text-[#00D4FF]">#{idx + 1}</td>
                      <td className="py-3 px-4 font-semibold text-[#E6EDF3] flex items-center gap-2">
                        <Building2 className="w-3.5 h-3.5 text-[#8492A6] shrink-0" />
                        <span>{c.company_name}</span>
                      </td>
                      <td className="py-3 px-4 text-center font-bold text-[#E6EDF3]">
                        {c.opportunities_count}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-emerald-400">
                        {c.highest_ctc_lpa ? `${c.highest_ctc_lpa} LPA` : <span className="text-[#8492A6] font-normal">Undisclosed</span>}
                      </td>
                      <td className="py-3 px-4 text-right text-[#00D4FF] font-semibold">
                        {c.average_ctc_lpa ? `${c.average_ctc_lpa} LPA` : <span className="text-[#8492A6] font-normal">-</span>}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {c.offers_internships ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-purple-950/60 text-purple-300 border border-purple-500/30">
                            {c.internships_count} Available
                          </span>
                        ) : (
                          <span className="text-[#8492A6] text-[11px]">No</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center text-[#8492A6]">
                        {c.disclosed_salary_records} / {c.opportunities_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* E. OPPORTUNITY ANALYTICS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Employment Classification */}
            <ChartCard
              title="Employment Classification"
              subtitle="Full-Time roles vs Internships vs Dual models"
              cyan={true}
            >
              <div className="h-60 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={jobTypes?.job_types || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={75}
                      paddingAngle={4}
                      dataKey="count"
                      nameKey="job_type"
                    >
                      {(jobTypes?.job_types || []).map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={PIE_COLORS[index % PIE_COLORS.length]}
                          stroke="#101620"
                          strokeWidth={2}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#101620',
                        borderColor: '#00D4FF',
                        borderRadius: '6px',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '11px',
                      }}
                      formatter={(val, name, item) => [`${val} notices (${item.payload.percentage}%)`, name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            {/* Work Mode Breakdown */}
            <ChartCard
              title="Work Mode Distribution"
              subtitle="Onsite, Hybrid, and Remote workplace policies"
              cyan={false}
            >
              <div className="h-60 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={jobTypes?.work_modes || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={75}
                      paddingAngle={4}
                      dataKey="count"
                      nameKey="work_mode"
                    >
                      {(jobTypes?.work_modes || []).map((entry, index) => (
                        <Cell
                          key={`wm-${index}`}
                          fill={PIE_COLORS[(index + 2) % PIE_COLORS.length]}
                          stroke="#101620"
                          strokeWidth={2}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#101620',
                        borderColor: '#FF6A00',
                        borderRadius: '6px',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '11px',
                      }}
                      formatter={(val, name, item) => [`${val} roles (${item.payload.percentage}%)`, name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            {/* Geographical Hiring Hubs */}
            <div className="lg:col-span-2">
              <ChartCard
                title="Geographical Hiring Hubs"
                subtitle="Distribution of corporate drives mapped by employment location"
                cyan={true}
              >
                <div className="h-60 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={locations}
                      layout="vertical"
                      margin={{ top: 5, right: 25, left: 35, bottom: 5 }}
                    >
                      <XAxis
                        type="number"
                        stroke="#8492A6"
                        fontSize={10.5}
                        tickLine={false}
                        fontFamily="JetBrains Mono"
                      />
                      <YAxis
                        type="category"
                        dataKey="location"
                        stroke="#8492A6"
                        fontSize={10.5}
                        tickLine={false}
                        fontFamily="JetBrains Mono"
                        width={95}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#101620',
                          borderColor: '#00D4FF',
                          borderRadius: '6px',
                          fontFamily: 'JetBrains Mono',
                          fontSize: '11px',
                        }}
                        formatter={(val, name, item) => [`${val} roles (${item.payload.percentage}%)`, 'Jobs']}
                      />
                      <Bar dataKey="count" fill="#00D4FF" radius={[0, 4, 4, 0]} name="Opportunities" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>
          </div>

          {/* Monthly Discovery Trends */}
          <ChartCard
            title="Monthly Discovery & Notice Trajectory"
            subtitle="Aggregated temporal timeline of newly released placement drives and notices"
            cyan={false}
          >
            <div className="h-60 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={trends?.discovery_trends || []}
                  margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorTrends" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FF6A00" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#FF6A00" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="period"
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
                      borderColor: '#FF6A00',
                      borderRadius: '6px',
                      fontFamily: 'JetBrains Mono',
                      fontSize: '12px',
                    }}
                    formatter={(val) => [`${val} notices`, 'Discovered']}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#FF6A00"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorTrends)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* F. ELIGIBILITY INSIGHTS */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Branch-wise Opportunity Chart */}
            <ChartCard
              title="Eligible Branch Inclusions"
              subtitle="Demand frequency mapped across engineering and sciences departments"
              cyan={true}
            >
              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={eligibility?.branch_distribution || []}
                    layout="vertical"
                    margin={{ top: 5, right: 20, left: 35, bottom: 5 }}
                  >
                    <XAxis
                      type="number"
                      stroke="#8492A6"
                      fontSize={10.5}
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                    />
                    <YAxis
                      type="category"
                      dataKey="branch"
                      stroke="#8492A6"
                      fontSize={10}
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                      width={100}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#101620',
                        borderColor: '#00D4FF',
                        borderRadius: '6px',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#00D4FF" radius={[0, 4, 4, 0]} name="Eligible Opportunities" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            {/* CGPA & Academic Cutoffs */}
            <ChartCard
              title="Academic CGPA Thresholds"
              subtitle="Distribution of corporate minimum CGPA benchmarks"
              cyan={false}
            >
              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={eligibility?.cgpa_distribution || []}
                    margin={{ top: 10, right: 10, left: -15, bottom: 10 }}
                  >
                    <XAxis
                      dataKey="bracket"
                      stroke="#8492A6"
                      fontSize={10}
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
                        borderColor: '#FF6A00',
                        borderRadius: '6px',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#FF6A00" radius={[4, 4, 0, 0]} name="Roles" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          </div>

          {/* G. DATA TRANSPARENCY & QUALITY HEALTH */}
          <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-3.5 rounded-sm bg-[#00D4FF]"></span>
                <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
                  Data Hygiene & Transparency Audit
                </h3>
              </div>
              <span className="text-[11px] text-[#8492A6]">
                Audit Timestamp: {formatDateTimeIST(overview?.data_transparency?.last_processing_timestamp, { fallback: 'Live SQLite' })}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 bg-[#101620] border border-[#263244] rounded space-y-1">
                <span className="text-[#8492A6] text-[10px] uppercase">Disclosed CTC Notices</span>
                <p className="text-base font-bold text-emerald-400">
                  {overview?.data_transparency?.disclosed_salary_count ?? 0}
                </p>
                <span className="text-[10px] text-[#8492A6]">Verified compensation</span>
              </div>

              <div className="p-3 bg-[#101620] border border-[#263244] rounded space-y-1">
                <span className="text-[#8492A6] text-[10px] uppercase">Undisclosed Salaries</span>
                <p className="text-base font-bold text-[#E6EDF3]">
                  {overview?.data_transparency?.undisclosed_salary_count ?? 0}
                </p>
                <span className="text-[10px] text-[#8492A6]">Omitted by recruiter</span>
              </div>

              <div className="p-3 bg-[#101620] border border-[#263244] rounded space-y-1">
                <span className="text-[#8492A6] text-[10px] uppercase">Records Needing Review</span>
                <p className="text-base font-bold text-amber-400">
                  {overview?.data_transparency?.records_needing_review ?? 0}
                </p>
                <span className="text-[10px] text-[#8492A6]">Ambiguous / complex clause</span>
              </div>

              <div className="p-3 bg-[#101620] border border-[#263244] rounded space-y-1">
                <span className="text-[#8492A6] text-[10px] uppercase">Invalid Entries</span>
                <p className="text-base font-bold text-red-400">
                  {overview?.data_transparency?.invalid_salary_count ?? 0}
                </p>
                <span className="text-[10px] text-[#8492A6]">Failed business rules</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
