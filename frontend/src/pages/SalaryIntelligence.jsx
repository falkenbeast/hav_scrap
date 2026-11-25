import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  TrendingUp,
  Award,
  DollarSign,
  ArrowUpDown,
  BarChart3,
  Layers,
  Sparkles,
  HelpCircle,
  Briefcase,
  Info,
  Search,
  Filter,
  RefreshCw,
  Building2,
  CheckSquare,
  Square,
  X,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  ArrowUpRight,
} from 'lucide-react';
import SectionHeader from '../components/common/SectionHeader';
import StatCard from '../components/common/StatCard';
import ChartCard from '../components/common/ChartCard';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import Button from '../components/common/Button';
import { api } from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';

export default function SalaryIntelligence() {
  // Filter & Search States
  const [searchTerm, setSearchTerm] = useState('');
  const [salaryTypeFilter, setSalaryTypeFilter] = useState('');
  const [jobTypeFilter, setJobTypeFilter] = useState('');
  const [sortBy, setSortBy] = useState('salary_lpa');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Company Selection for Comparison
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);

  // Data States
  const [salaryOverview, setSalaryOverview] = useState(null);
  const [salaryDist, setSalaryDist] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [recordsData, setRecordsData] = useState({ items: [], total: 0, total_pages: 1 });
  const [filterOptions, setFilterOptions] = useState({ companies: [], job_types: [], salary_types: [] });

  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load filter options on mount
  useEffect(() => {
    async function loadFilters() {
      try {
        const f = await api.getAnalyticsFilters();
        setFilterOptions(f);
      } catch (err) {
        console.warn('Could not load filters:', err);
      }
    }
    loadFilters();
  }, []);

  // Fetch overview & distribution benchmarks
  const fetchOverviewData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewData, distData, topCompaniesData] = await Promise.all([
        api.getAnalyticsOverview().catch(() => null),
        api.getSalaryDistribution().catch(() => null),
        api.getCompanyRankings({ sort_by: 'highest_ctc', page_size: 10 }).catch(() => ({ items: [] })),
      ]);

      setSalaryOverview(overviewData);
      setSalaryDist(distData);
      setRankings(topCompaniesData?.items || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch compensation data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverviewData();
  }, []);

  // Fetch paginated salary intelligence records
  const fetchSalaryRecords = useCallback(async () => {
    try {
      setTableLoading(true);
      const res = await api.getSalaryIntelligence({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        search: searchTerm || undefined,
        salary_type: salaryTypeFilter || undefined,
        job_type: jobTypeFilter || undefined,
      });
      setRecordsData(res || { items: [], total: 0, total_pages: 1 });
    } catch (err) {
      console.error('Records fetch error:', err);
    } finally {
      setTableLoading(false);
    }
  }, [page, sortBy, sortOrder, searchTerm, salaryTypeFilter, jobTypeFilter]);

  useEffect(() => {
    fetchSalaryRecords();
  }, [fetchSalaryRecords]);

  // Handle Sort Toggle
  const handleSort = (col) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
    setPage(1);
  };

  // Toggle company selection for comparison
  const toggleCompanySelection = (compName) => {
    setSelectedCompanies((prev) =>
      prev.includes(compName)
        ? prev.filter((c) => c !== compName)
        : [...prev, compName]
    );
  };

  // Compare metrics for selected companies
  const comparisonData = useMemo(() => {
    if (selectedCompanies.length === 0) return [];
    return rankings.filter((r) => selectedCompanies.includes(r.company_name));
  }, [selectedCompanies, rankings]);

  const isEmpty = !loading && (!salaryOverview || salaryOverview.total_jobs === 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <SectionHeader
        title="Compensation & Salary Intelligence"
        subtitle="Granular analysis of campus CTC packages, fixed vs variable compensation, and percentile rankings."
        badgeText="VERIFIED CTC CORPUS"
        badgeVariant="orange"
        actions={
          <div className="flex items-center gap-2">
            {selectedCompanies.length > 0 && (
              <Button
                variant="primary"
                size="sm"
                icon={Building2}
                onClick={() => setComparisonModalOpen(true)}
              >
                COMPARE ({selectedCompanies.length})
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              onClick={() => {
                fetchOverviewData();
                fetchSalaryRecords();
              }}
              disabled={loading || tableLoading}
            >
              REFRESH
            </Button>
            <StatusBadge variant="cyan" size="sm" dot={true}>
              {salaryOverview?.disclosed_salaries ?? 0} DISCLOSED PACKAGES
            </StatusBadge>
          </div>
        }
      />

      {error && (
        <ErrorAlert
          title="SALARY MATRIX TELEMETRY FAULT"
          message={error}
          onRetry={fetchOverviewData}
        />
      )}

      {loading ? (
        <LoadingSpinner text="PARSING COMPENSATION TELEMETRY FROM BACKEND..." />
      ) : isEmpty ? (
        <EmptyState
          title="NO SALARY RECORDS IN DATABASE YET"
          message="data/hav_scrap.db contains 0 job postings with normalized salary clauses. Run extraction from Scraper Control to populate salary intelligence."
          actionLabel="OPEN SCRAPER CONSOLE"
          onAction={() => window.location.assign('/scraper')}
        />
      ) : (
        <>
          {/* 1. Core Salary Overview KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <StatCard
              icon={Award}
              label="Highest Package"
              value={salaryOverview?.highest_ctc_lpa ? `${salaryOverview.highest_ctc_lpa} LPA` : 'N/A'}
              subtext="Pinnacle verified CTC"
              trend="Maximum Offer"
              cyan={true}
            />
            <StatCard
              icon={TrendingUp}
              label="Average Package"
              value={salaryOverview?.average_ctc_lpa ? `${salaryOverview.average_ctc_lpa} LPA` : 'N/A'}
              subtext="Arithmetic mean CTC"
              trend="Mean Compensation"
              cyan={false}
            />
            <StatCard
              icon={BarChart3}
              label="Median Package"
              value={salaryOverview?.median_ctc_lpa ? `${salaryOverview.median_ctc_lpa} LPA` : 'N/A'}
              subtext="50th percentile CTC tier"
              trend="Robust Midpoint"
              cyan={true}
            />
            <StatCard
              icon={Briefcase}
              label="Lowest Package"
              value={salaryOverview?.lowest_ctc_lpa ? `${salaryOverview.lowest_ctc_lpa} LPA` : 'N/A'}
              subtext="Floor compensation"
              trend="Floor Threshold"
              cyan={false}
            />
            <StatCard
              icon={DollarSign}
              label="Disclosure Rate"
              value={
                salaryOverview?.total_jobs
                  ? `${Math.round(((salaryOverview.disclosed_salaries || 0) / salaryOverview.total_jobs) * 100)}%`
                  : '0%'
              }
              subtext={`${salaryOverview?.disclosed_salaries ?? 0} of ${salaryOverview?.total_jobs ?? 0} notices`}
              trend="Transparency Score"
              cyan={true}
            />
            <StatCard
              icon={ShieldAlert}
              label="Review Queue"
              value={salaryOverview?.data_transparency?.records_needing_review ?? 0}
              subtext="Ambiguous CTC clauses"
              trend="Manual Clearance"
              cyan={false}
            />
          </div>

          {/* 2. Visual Benchmarks: Salary Distribution & Fixed vs Maximum CTC */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Offer Distribution by CTC Brackets */}
            <ChartCard
              title="Full-Time Offer Distribution by CTC Brackets"
              subtitle="Relative frequency of campus opportunities grouped into 7 standardized LPA tiers"
              cyan={true}
            >
              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={salaryDist?.brackets || []}
                    margin={{ top: 10, right: 10, left: -15, bottom: 20 }}
                  >
                    <XAxis
                      dataKey="bracket"
                      stroke="#8492A6"
                      fontSize={10}
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                      angle={-15}
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
                        `${val} notices (${item.payload.percentage}%) • Avg: ${item.payload.average_salary ? `${item.payload.average_salary} LPA` : 'N/A'}`,
                        'Opportunities',
                      ]}
                    />
                    <Bar dataKey="count" fill="#00D4FF" radius={[4, 4, 0, 0]} name="Opportunities" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            {/* Top Recruiters by Highest CTC League Table */}
            <ChartCard
              title="Top Recruiters by Peak Disclosed Package"
              subtitle="Corporate recruiters offering the highest verified CTC packages (LPA)"
              cyan={false}
            >
              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={rankings.slice(0, 8)}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 35, bottom: 5 }}
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
                      dataKey="company_name"
                      stroke="#8492A6"
                      fontSize={10.5}
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                      width={100}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#101620',
                        borderColor: '#FF6A00',
                        borderRadius: '6px',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '12px',
                      }}
                      formatter={(val, name, item) => [
                        `Highest: ${val} LPA • Avg: ${item.payload.average_ctc_lpa ? `${item.payload.average_ctc_lpa} LPA` : 'N/A'}`,
                        'Compensation',
                      ]}
                    />
                    <Bar dataKey="highest_ctc_lpa" fill="#FF6A00" radius={[0, 4, 4, 0]} name="Peak Package (LPA)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          </div>

          {/* 3. Detailed Salary Comparison Table & Control Bar */}
          <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-[#263244]">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-3.5 rounded-sm bg-[#00D4FF]"></span>
                  <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3] text-sm">
                    Detailed Salary Comparison Records
                  </h3>
                </div>
                <p className="text-[11px] text-[#8492A6]">
                  Verified campus roles with fixed vs variable split, normalized LPA values, and raw salary clauses
                </p>
              </div>

              {/* Search & Filter Bar */}
              <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
                <div className="relative flex-1 md:w-56">
                  <Search className="w-3.5 h-3.5 text-[#8492A6] absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search company or role..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setPage(1);
                    }}
                    className="w-full pl-8 pr-3 py-1.5 bg-[#101620] border border-[#263244] rounded text-xs text-[#E6EDF3] placeholder-[#8492A6] focus:outline-none focus:border-[#00D4FF] transition-colors"
                  />
                </div>

                <select
                  value={salaryTypeFilter}
                  onChange={(e) => {
                    setSalaryTypeFilter(e.target.value);
                    setPage(1);
                  }}
                  className="px-2.5 py-1.5 bg-[#101620] border border-[#263244] rounded text-xs text-[#E6EDF3] focus:outline-none focus:border-[#00D4FF]"
                >
                  <option value="">All Salary Types</option>
                  {filterOptions.salary_types.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>

                <select
                  value={jobTypeFilter}
                  onChange={(e) => {
                    setJobTypeFilter(e.target.value);
                    setPage(1);
                  }}
                  className="px-2.5 py-1.5 bg-[#101620] border border-[#263244] rounded text-xs text-[#E6EDF3] focus:outline-none focus:border-[#FF6A00]"
                >
                  <option value="">All Classifications</option>
                  {filterOptions.job_types.map((jt) => (
                    <option key={jt} value={jt}>
                      {jt}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto border border-[#263244] rounded-lg">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#263244] bg-[#101620] text-[#8492A6] uppercase text-[10px] tracking-wider">
                    <th className="py-3 px-3 text-center w-10">Select</th>
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-[#E6EDF3] transition-colors"
                      onClick={() => handleSort('company_name')}
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Company</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-[#E6EDF3] transition-colors"
                      onClick={() => handleSort('job_title')}
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Job Role / Designation</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-[#E6EDF3] transition-colors"
                      onClick={() => handleSort('minimum_ctc')}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>Min CTC</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-[#E6EDF3] transition-colors"
                      onClick={() => handleSort('maximum_ctc')}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>Max CTC</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-[#E6EDF3] transition-colors"
                      onClick={() => handleSort('fixed_ctc')}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>Fixed CTC</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th className="py-3 px-4 text-right">Variable</th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-[#E6EDF3] transition-colors"
                      onClick={() => handleSort('salary_lpa')}
                    >
                      <div className="flex items-center justify-end gap-1.5 text-[#00D4FF]">
                        <span>Normalized LPA</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th className="py-3 px-4">Raw Portal Salary Clause</th>
                    <th className="py-3 px-4 text-center">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#263244]/60">
                  {tableLoading ? (
                    <tr>
                      <td colSpan={10} className="py-8 text-center text-[#8492A6]">
                        <LoadingSpinner text="UPDATING SALARY COMPARISON RECORDS..." />
                      </td>
                    </tr>
                  ) : recordsData.items.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="py-8 text-center text-[#8492A6]">
                        No matching salary records found for the applied search criteria.
                      </td>
                    </tr>
                  ) : (
                    recordsData.items.map((row) => (
                      <tr key={row.id} className="hover:bg-[#101620]/60 transition-colors">
                        <td className="py-3 px-3 text-center">
                          <button
                            onClick={() => toggleCompanySelection(row.company_name)}
                            className="text-[#8492A6] hover:text-[#00D4FF] transition-colors"
                          >
                            {selectedCompanies.includes(row.company_name) ? (
                              <CheckSquare className="w-4 h-4 text-[#00D4FF]" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                        <td className="py-3 px-4 font-bold text-[#E6EDF3] flex items-center gap-1.5">
                          <Building2 className="w-3.5 h-3.5 text-[#8492A6] shrink-0" />
                          <span>{row.company_name}</span>
                        </td>
                        <td className="py-3 px-4 text-[#E6EDF3]">{row.job_role}</td>
                        <td className="py-3 px-4 text-right text-[#8492A6]">
                          {row.minimum_ctc ? `${row.minimum_ctc} LPA` : '-'}
                        </td>
                        <td className="py-3 px-4 text-right text-[#8492A6]">
                          {row.maximum_ctc ? `${row.maximum_ctc} LPA` : '-'}
                        </td>
                        <td className="py-3 px-4 text-right text-[#8492A6]">
                          {row.fixed_ctc ? `${row.fixed_ctc} LPA` : '-'}
                        </td>
                        <td className="py-3 px-4 text-right text-[#8492A6]">
                          {row.variable_ctc ? `${row.variable_ctc} LPA` : '-'}
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-emerald-400">
                          {row.normalized_salary_lpa ? (
                            `${row.normalized_salary_lpa} LPA`
                          ) : (
                            <span className="text-[#8492A6] font-normal text-[11px]">Undisclosed</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-[#8492A6] truncate max-w-[200px]" title={row.original_salary_text || ''}>
                          {row.original_salary_text || <span className="italic">Not Stated</span>}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-[#1B2635] text-[#00D4FF] border border-[#263244]">
                            {row.salary_type || 'STANDARD'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 text-[#8492A6] text-xs">
              <div>
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, recordsData.total)} of {recordsData.total} records
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  icon={ChevronLeft}
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  PREVIOUS
                </Button>
                <span className="px-2 font-bold text-[#E6EDF3]">
                  Page {page} of {recordsData.total_pages || 1}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  icon={ChevronRight}
                  disabled={page >= recordsData.total_pages}
                  onClick={() => setPage((p) => Math.min(recordsData.total_pages, p + 1))}
                >
                  NEXT
                </Button>
              </div>
            </div>
          </div>

          {/* 4. Company Side-by-Side Comparison Modal */}
          {comparisonModalOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
              <div className="bg-[#151D29] border border-[#00D4FF]/60 rounded-lg p-6 max-w-4xl w-full tech-corner space-y-4 font-mono shadow-glow-sm-cyan/40">
                <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-[#00D4FF]" />
                    <h3 className="text-base font-bold text-[#E6EDF3] uppercase tracking-wider">
                      Side-by-Side Recruiter CTC Comparison
                    </h3>
                  </div>
                  <button
                    onClick={() => setComparisonModalOpen(false)}
                    className="p-1 rounded text-[#8492A6] hover:text-[#E6EDF3] transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="overflow-x-auto border border-[#263244] rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#263244] bg-[#101620] text-[#8492A6] uppercase text-[10px]">
                        <th className="py-3 px-4">Metric Indicator</th>
                        {comparisonData.map((c) => (
                          <th key={c.company_name} className="py-3 px-4 text-[#00D4FF] font-bold">
                            {c.company_name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#263244]/60">
                      <tr>
                        <td className="py-3 px-4 text-[#8492A6]">Total Notices</td>
                        {comparisonData.map((c) => (
                          <td key={c.company_name} className="py-3 px-4 font-bold text-[#E6EDF3]">
                            {c.opportunities_count}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-3 px-4 text-[#8492A6]">Peak Package (LPA)</td>
                        {comparisonData.map((c) => (
                          <td key={c.company_name} className="py-3 px-4 font-bold text-emerald-400">
                            {c.highest_ctc_lpa ? `${c.highest_ctc_lpa} LPA` : 'Undisclosed'}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-3 px-4 text-[#8492A6]">Average CTC (LPA)</td>
                        {comparisonData.map((c) => (
                          <td key={c.company_name} className="py-3 px-4 font-bold text-[#00D4FF]">
                            {c.average_ctc_lpa ? `${c.average_ctc_lpa} LPA` : '-'}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-3 px-4 text-[#8492A6]">Floor Package (LPA)</td>
                        {comparisonData.map((c) => (
                          <td key={c.company_name} className="py-3 px-4 text-[#E6EDF3]">
                            {c.lowest_ctc_lpa ? `${c.lowest_ctc_lpa} LPA` : '-'}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-3 px-4 text-[#8492A6]">Internships</td>
                        {comparisonData.map((c) => (
                          <td key={c.company_name} className="py-3 px-4 text-purple-400 font-semibold">
                            {c.offers_internships ? `${c.internships_count} Offered` : 'None Listed'}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="flex justify-end pt-2">
                  <Button variant="secondary" size="sm" onClick={() => setComparisonModalOpen(false)}>
                    CLOSE COMPARISON
                  </Button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
