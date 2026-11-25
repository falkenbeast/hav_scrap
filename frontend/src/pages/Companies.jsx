import React, { useState, useEffect, useMemo } from 'react';
import {
  Building2,
  ExternalLink,
  Briefcase,
  TrendingUp,
  MapPin,
  Calendar,
  Layers,
  Sparkles,
  Filter,
  CheckCircle2,
  AlertCircle,
  X,
  Info,
} from 'lucide-react';
import SectionHeader from '../components/common/SectionHeader';
import SearchBar from '../components/common/SearchBar';
import FilterDropdown from '../components/common/FilterDropdown';
import DataTable from '../components/common/DataTable';
import StatusBadge from '../components/common/StatusBadge';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import { api } from '../services/api';
import { formatDateIST } from '../utils/formatters';

// Demonstration fallback records if database is empty or user toggles demo mode
const DEMO_COMPANIES_DATA = [
  {
    id: 1,
    company_name: 'Google LLC',
    website: 'https://careers.google.com',
    job_role: 'Software Engineer - Campus Hire',
    ctc: 55.0,
    ctc_text: '55.0 LPA (Base: 22L, Stocks: 30L, Joining: 3L)',
    location: 'Bengaluru / Hyderabad',
    job_type: 'Full-Time',
    posted_date: '2024-11-01',
    status: 'Active',
    eligibility: 'B.Tech / M.Tech (CSE, IT, ECE, AI/DS)',
    min_cgpa: 8.0,
    batch: '2025',
  },
  {
    id: 2,
    company_name: 'Microsoft IDC',
    website: 'https://careers.microsoft.com',
    job_role: 'Software Development Engineer - I',
    ctc: 51.5,
    ctc_text: '51.5 LPA (Base: 24L, Bonus: 5L, Stock Units: 22.5L)',
    location: 'Hyderabad / Noida',
    job_type: 'Full-Time',
    posted_date: '2024-10-28',
    status: 'Interviewing',
    eligibility: 'B.Tech all circuital branches',
    min_cgpa: 7.5,
    batch: '2025',
  },
  {
    id: 3,
    company_name: 'Amazon Web Services',
    website: 'https://amazon.jobs',
    job_role: 'Cloud Support / SDE Intern + FTE',
    ctc: 45.0,
    ctc_text: '45.0 LPA (Base: 20L, Sign-on: 8L, RSUs: 17L)',
    location: 'Bengaluru',
    job_type: '6M Intern + FTE',
    posted_date: '2024-10-25',
    status: 'Shortlisting',
    eligibility: 'B.Tech CSE, IT, ECE, EEE',
    min_cgpa: 7.0,
    batch: '2025',
  },
  {
    id: 4,
    company_name: 'D.E. Shaw India',
    website: 'https://deshawindia.com',
    job_role: 'Member Technical (Quantitative Systems)',
    ctc: 42.0,
    ctc_text: '42.0 LPA (Base: 25L, Guaranteed Bonus: 10L, Relocation: 7L)',
    location: 'Hyderabad',
    job_type: 'Full-Time',
    posted_date: '2024-10-20',
    status: 'Closed',
    eligibility: 'B.Tech CSE, Math & Computing',
    min_cgpa: 8.5,
    batch: '2025',
  },
  {
    id: 5,
    company_name: 'Uber Technologies',
    website: 'https://uber.com/careers',
    job_role: 'Software Engineer - Infrastructure',
    ctc: 40.5,
    ctc_text: '40.5 LPA (Base: 21L, Stock Equity: 16L, Bonus: 3.5L)',
    location: 'Bengaluru / Hyderabad',
    job_type: 'Full-Time',
    posted_date: '2024-10-18',
    status: 'Active',
    eligibility: 'B.Tech / Dual Degree CSE/IT',
    min_cgpa: 8.0,
    batch: '2025',
  },
  {
    id: 6,
    company_name: 'Atlassian India',
    website: 'https://atlassian.com/company/careers',
    job_role: 'Associate Software Engineer',
    ctc: 38.0,
    ctc_text: '38.0 LPA (Base: 20L, Equity: 14L, Sign-on: 4L)',
    location: 'Bengaluru (Remote Friendly)',
    job_type: 'Full-Time',
    posted_date: '2024-10-15',
    status: 'Interviewing',
    eligibility: 'All Engineering Branches with coding track',
    min_cgpa: 7.5,
    batch: '2025',
  },
];

export default function Companies() {
  const [dbCompanies, setDbCompanies] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [jobTypeFilter, setJobTypeFilter] = useState('ALL');
  const [tierFilter, setTierFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [useDemoFallback, setUseDemoFallback] = useState(false);

  const fetchCompaniesFromBackend = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCompanies({
        page: 1,
        page_size: 50,
        search: search || undefined,
      });

      if (data && Array.isArray(data.items)) {
        setDbCompanies(data.items);
        setTotalCount(data.total);
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to backend companies endpoint.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompaniesFromBackend();
  }, [search]);

  const isDatabaseEmpty = !loading && dbCompanies.length === 0 && !search && !useDemoFallback;

  // Active data selection: real DB records or demo fallback
  const displayData = useMemo(() => {
    if (useDemoFallback) {
      return DEMO_COMPANIES_DATA.filter((item) => {
        const s = search.toLowerCase();
        const matchesSearch =
          !search ||
          item.company_name.toLowerCase().includes(s) ||
          item.job_role.toLowerCase().includes(s);
        const matchesType = jobTypeFilter === 'ALL' || item.job_type === jobTypeFilter;
        let matchesTier = true;
        if (tierFilter === 'SUPER_DREAM') matchesTier = item.ctc >= 20;
        else if (tierFilter === 'DREAM') matchesTier = item.ctc >= 10 && item.ctc < 20;
        else if (tierFilter === 'REGULAR') matchesTier = item.ctc < 10;
        const matchesStatus = statusFilter === 'ALL' || item.status === statusFilter;
        return matchesSearch && matchesType && matchesTier && matchesStatus;
      });
    }

    return dbCompanies.map((c) => ({
      id: c.id,
      company_name: c.company_name,
      website: c.website,
      job_role:
        c.job_role ||
        (c.job_roles && c.job_roles.length > 0
          ? c.job_roles.join(', ')
          : c.total_jobs > 0
          ? `${c.total_jobs} Active Profiles`
          : 'Placement Opportunity'),
      ctc: c.max_ctc != null && c.max_ctc > 0 ? c.max_ctc : null,
      location:
        c.location ||
        (c.locations && c.locations.length > 0
          ? c.locations.join(', ')
          : 'Haveloc Portal'),
      job_type: c.job_type || 'Full Time',
      posted_date: c.posted_date ? formatDateIST(c.posted_date) : (c.created_at ? formatDateIST(c.created_at) : 'Recent'),
      status: c.job_status || 'Discovered',
      eligibility: 'Refer to company notice',
      min_cgpa: 7.0,
      batch: '2025',
    }));
  }, [dbCompanies, useDemoFallback, search, jobTypeFilter, tierFilter, statusFilter]);

  const columns = [
    {
      header: 'Company Name',
      accessor: 'company_name',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#101620] border border-[#263244] flex items-center justify-center text-[#FF6A00] font-bold text-xs shrink-0">
            {row.company_name.charAt(0)}
          </div>
          <div>
            <span className="font-bold text-[#E6EDF3] group-hover:text-[#00D4FF] block">
              {row.company_name}
            </span>
            {row.website ? (
              <a
                href={row.website}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-[10px] text-[#00D4FF] hover:underline flex items-center gap-1 font-mono"
              >
                Website <ExternalLink className="w-2.5 h-2.5" />
              </a>
            ) : (
              <span className="text-[10px] text-[#8492A6]">No URL</span>
            )}
          </div>
        </div>
      ),
    },
    {
      header: 'Job Role / Notice',
      accessor: 'job_role',
      sortable: true,
      render: (row) => (
        <div>
          <span className="text-[#E6EDF3] font-semibold block">{row.job_role}</span>
          <span className="text-[10px] text-[#8492A6]">Target Batch: {row.batch}</span>
        </div>
      ),
    },
    {
      header: 'Peak Package (LPA)',
      accessor: 'ctc',
      sortable: true,
      render: (row) => (
        <div>
          <span
            className={`font-extrabold text-sm ${
              row.ctc != null && row.ctc >= 20
                ? 'text-[#FF6A00]'
                : row.ctc != null && row.ctc >= 10
                ? 'text-[#00D4FF]'
                : row.ctc != null && row.ctc > 0
                ? 'text-[#E6EDF3]'
                : 'text-[#8492A6]'
            }`}
          >
            {row.ctc != null && row.ctc > 0 ? `${Number(row.ctc).toFixed(1)} LPA` : 'Not Available'}
          </span>
        </div>
      ),
    },
    {
      header: 'Location',
      accessor: 'location',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-1 text-[#8492A6]">
          <MapPin className="w-3 h-3 text-[#00D4FF] shrink-0" />
          <span className="truncate max-w-[150px]">{row.location}</span>
        </div>
      ),
    },
    {
      header: 'Job Type',
      accessor: 'job_type',
      sortable: true,
      render: (row) => (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono border bg-[#101620] text-[#00D4FF] border-[#263244] font-semibold">
          {row.job_type}
        </span>
      ),
    },
    {
      header: 'Indexed Date',
      accessor: 'posted_date',
      sortable: true,
      render: (row) => <span className="text-[#8492A6] text-[11px]">{row.posted_date}</span>,
    },
    {
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (row) => (
        <StatusBadge variant="cyan" size="xs" dot={true}>
          {row.status}
        </StatusBadge>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <SectionHeader
        title="RECRUITER INTELLIGENCE DOSSIER"
        subtitle="Searchable master directory of registered placement notices, compensation breakdowns, and hiring criteria."
        badgeText={useDemoFallback ? 'DEMO PREVIEW' : `DATABASE: ${totalCount} COMPANIES`}
        badgeVariant={useDemoFallback ? 'demo' : 'cyan'}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setUseDemoFallback(!useDemoFallback)}
              className={`px-3 py-1.5 text-xs font-mono font-semibold rounded border transition-colors ${
                useDemoFallback
                  ? 'bg-[#FF6A00] text-black border-[#FF6A00]'
                  : 'bg-[#151D29] text-[#8492A6] border-[#263244] hover:text-[#E6EDF3]'
              }`}
            >
              {useDemoFallback ? 'SWITCH TO LIVE DATABASE' : 'VIEW DEMO DIRECTORY'}
            </button>
          </div>
        }
      />

      {error && (
        <ErrorAlert
          title="BACKEND COMMUNICATION FAULT"
          message={error}
          onRetry={fetchCompaniesFromBackend}
        />
      )}

      {/* Filter and Search Bar Controls */}
      <div className="bg-[#151D29] border border-[#263244] rounded-lg p-4 tech-corner flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex-1 max-w-md">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search company or profile in database..."
            onClear={() => setSearch('')}
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <FilterDropdown
            label="Type"
            value={jobTypeFilter}
            onChange={setJobTypeFilter}
            options={[
              { value: 'ALL', label: 'All Types' },
              { value: 'Full-Time', label: 'Full-Time' },
              { value: 'Internship', label: 'Internship' },
              { value: '6M Intern + FTE', label: '6M + FTE' },
            ]}
          />

          <FilterDropdown
            label="CTC Tier"
            value={tierFilter}
            onChange={setTierFilter}
            options={[
              { value: 'ALL', label: 'All Tiers' },
              { value: 'SUPER_DREAM', label: 'Super Dream (20+ LPA)' },
              { value: 'DREAM', label: 'Dream (10-20 LPA)' },
              { value: 'REGULAR', label: 'Regular (< 10 LPA)' },
            ]}
          />

          <Button
            variant="secondary"
            size="sm"
            onClick={fetchCompaniesFromBackend}
          >
            REFRESH
          </Button>
        </div>
      </div>

      {/* Main Table or Empty State */}
      {loading ? (
        <LoadingSpinner text="QUERYING CORPORATE DIRECTORY FROM SQLITE DATABASE..." />
      ) : isDatabaseEmpty ? (
        <EmptyState
          title="SQLITE DATABASE CONTAINS 0 COMPANY RECORDS"
          message="The backend database data/hav_scrap.db is currently empty. Run a scraper session in Scraper Control to populate real recruiter notices, or switch to Demo Preview to explore the directory."
          actionLabel="LOAD SAMPLE DEMO RECRUITERS"
          onAction={() => setUseDemoFallback(true)}
        />
      ) : (
        <DataTable
          columns={columns}
          data={displayData}
          pageSize={8}
          onRowClick={(row) => setSelectedRecord(row)}
          emptyTitle="NO MATCHING COMPANIES"
          emptyMessage="No company records match your search criteria in the database."
        />
      )}

      {/* Detail Dossier Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fadeIn">
          <div className="bg-[#101620] border border-[#00D4FF]/50 rounded-xl max-w-2xl w-full p-6 tech-corner shadow-glow-cyan max-h-[85vh] overflow-y-auto space-y-6">
            <div className="flex items-start justify-between border-b border-[#263244] pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-[#00D4FF] bg-[#151D29] border border-[#263244] px-2 py-0.5 rounded font-bold">
                    RECORD #{selectedRecord.id}
                  </span>
                  <StatusBadge variant="cyan" size="xs">
                    {selectedRecord.status}
                  </StatusBadge>
                  {useDemoFallback && (
                    <StatusBadge variant="demo" size="xs" dot={false}>
                      DEMO RECORD
                    </StatusBadge>
                  )}
                </div>
                <h2 className="text-xl font-bold font-mono text-[#E6EDF3]">
                  {selectedRecord.company_name}
                </h2>
                <p className="text-xs font-mono text-[#00D4FF]">
                  {selectedRecord.job_role}
                </p>
              </div>

              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1 rounded text-[#8492A6] hover:text-[#E6EDF3] bg-[#151D29] border border-[#263244] transition-colors"
                title="Close Dossier"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 bg-[#151D29] border border-[#263244] rounded-lg tech-corner space-y-2 font-mono">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#8492A6]">RECORDED CTC:</span>
                <span className="text-xl font-extrabold text-[#FF6A00]">
                  {selectedRecord.ctc > 0 ? `${Number(selectedRecord.ctc).toFixed(1)} LPA` : 'Pending Normalization'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-[#263244] font-mono text-xs">
              {selectedRecord.website ? (
                <a
                  href={selectedRecord.website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#00D4FF] hover:underline flex items-center gap-1.5"
                >
                  Visit Corporate Portal <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : (
                <span className="text-[#8492A6]">No External Link Available</span>
              )}

              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSelectedRecord(null)}
              >
                CLOSE DOSSIER [ESC]
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
