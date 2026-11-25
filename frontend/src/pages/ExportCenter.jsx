import React, { useState, useEffect } from 'react';
import {
  FileDown,
  FileSpreadsheet,
  Building2,
  Briefcase,
  TrendingUp,
  Clock,
  HardDrive,
  AlertCircle,
  CheckCircle2,
  Download,
  Info,
  X,
  Shield,
  Layers,
  Trash2,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import SectionHeader from '../components/common/SectionHeader';
import StatusBadge from '../components/common/StatusBadge';
import Button from '../components/common/Button';
import { api, API_BASE_URL } from '../services/api';
import { formatDateTimeIST } from '../utils/formatters';

export default function ExportCenter() {
  const [exportsList, setExportsList] = useState([]);
  const [totalExports, setTotalExports] = useState(0);
  const [loading, setLoading] = useState(false);
  const [generatingType, setGeneratingType] = useState(null);
  const [notification, setNotification] = useState(null);

  // Field selection toggles (retained for UI customization)
  const [fieldSelection, setFieldSelection] = useState({
    company_name: true,
    job_title: true,
    salary_lpa: true,
    ctc_clause: true,
    job_type: true,
    location: true,
    eligible_branches: true,
    min_cgpa: true,
  });

  const toggleField = (key) => {
    setFieldSelection((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Fetch exports registry on load
  const loadExports = async () => {
    try {
      setLoading(true);
      const res = await api.getExports({ page: 1, page_size: 50 });
      setExportsList(res.items || []);
      setTotalExports(res.total || 0);
    } catch (err) {
      console.error('Failed to load export registry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExports();
  }, []);

  // Format file sizes
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  // Trigger real backend workbook generation
  const handleTriggerExport = async (exportType, label) => {
    try {
      setGeneratingType(exportType);
      setNotification(null);

      const res = await api.generateExport({
        export_type: exportType,
      });

      setNotification({
        success: true,
        title: 'EXCEL WORKBOOK SYNTHESIZED',
        filename: res.filename,
        records: res.record_count,
        size: formatBytes(res.file_size_bytes),
        downloadUrl: `${API_BASE_URL}/exports/${res.id}/download`,
        message: `Successfully synthesized "${label}" deliverable into data/exports/${res.filename}. All 6 intelligence sheets, auto-filters, and formula sanitizations applied.`,
      });

      // Refresh registry
      await loadExports();
    } catch (err) {
      console.error('Export generation fault:', err);
      setNotification({
        success: false,
        title: 'EXPORT GENERATION FAILED',
        message: err.message || 'An unexpected error occurred while generating Excel workbook.',
      });
    } finally {
      setGeneratingType(null);
    }
  };

  // Handle export deletion
  const handleDeleteExport = async (id, filename) => {
    if (!window.confirm(`Delete export deliverable "${filename}" from server?`)) return;
    try {
      await api.deleteExport(id);
      await loadExports();
    } catch (err) {
      alert(`Failed to delete export: ${err.message || 'Error'}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <SectionHeader
        title="EXCEL EXPORT MANAGEMENT CENTER"
        subtitle="Automated synthesis of placement intelligence datasets, multi-sheet workbooks, and structured Excel deliverables."
        badgeText="OPENPYXL ENGINE"
        badgeVariant="cyan"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={RefreshCw}
              onClick={loadExports}
              disabled={loading}
              className={loading ? 'animate-spin' : ''}
            >
              REFRESH
            </Button>
            <StatusBadge variant="cyan" size="sm" dot={true}>
              PHASE 9 OPERATIONAL
            </StatusBadge>
          </div>
        }
      />

      {/* Notification Banner */}
      {notification && (
        <div
          className={`p-4 rounded-lg tech-corner border font-mono text-xs flex items-start justify-between gap-3 animate-fadeIn ${
            notification.success
              ? 'bg-[#151D29] border-emerald-500/60 shadow-glow-sm-cyan/20'
              : 'bg-[#151D29] border-red-500/60'
          }`}
        >
          <div className="flex items-start gap-3">
            {notification.success ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            )}
            <div className="space-y-1.5">
              <span
                className={`font-bold uppercase tracking-wider ${
                  notification.success ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {notification.title}
              </span>
              <p className="text-[#E6EDF3] leading-relaxed">{notification.message}</p>
              {notification.downloadUrl && (
                <div className="flex items-center gap-3 pt-1">
                  <a
                    href={notification.downloadUrl}
                    download
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#FF6A00] text-black font-bold text-xs hover:bg-[#FF8533] transition-colors shadow-glow-sm-orange/30"
                  >
                    <Download className="w-3.5 h-3.5" />
                    DOWNLOAD .XLSX ({notification.size})
                  </a>
                  <span className="text-[11px] text-[#8492A6]">
                    Artifact: <code>{notification.filename}</code>
                  </span>
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="p-1 rounded text-[#8492A6] hover:text-[#E6EDF3] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Primary Master Intelligence Workbook Hero Card */}
      <div className="bg-[#151D29] border border-[#00D4FF]/40 rounded-lg p-6 tech-corner shadow-glow-sm-cyan/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 uppercase tracking-wider">
              FLAGSHIP REPORT
            </span>
            <span className="text-xs text-[#8492A6] font-mono">ALL 6 WORKSHEETS INCLUDED</span>
          </div>
          <h2 className="text-lg font-bold text-[#E6EDF3] font-mono flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#00D4FF]" />
            Master Placement Intelligence Workbook
          </h2>
          <p className="text-xs text-[#8492A6] leading-relaxed">
            Synthesizes all corporate recruiters, full-time positions, normalized CTC packages, isolated
            internship stipends, academic eligibility criteria, and complete data quality audit into a single
            structured, formatted Excel (.xlsx) file.
          </p>
        </div>
        <div className="shrink-0 w-full md:w-auto">
          <Button
            variant="primary"
            size="md"
            icon={Download}
            disabled={generatingType !== null}
            onClick={() => handleTriggerExport('ALL', 'Master Placement Intelligence Report')}
            className="w-full md:w-auto font-mono text-xs font-bold"
          >
            {generatingType === 'ALL' ? 'SYNTHESIZING...' : 'GENERATE MASTER WORKBOOK'}
          </Button>
        </div>
      </div>

      {/* 4 Focused Export Option Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Export All Companies */}
        <div className="bg-[#151D29] border border-[#263244] hover:border-[#00D4FF]/50 rounded-lg p-5 tech-corner flex flex-col justify-between transition-all duration-200">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-[#00D4FF]/10 border border-[#00D4FF]/30 flex items-center justify-center text-[#00D4FF]">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#E6EDF3] font-mono">All Companies Directory</h3>
              <p className="text-xs text-[#8492A6] font-mono mt-1 leading-relaxed">
                Complete directory of corporate recruiters, portal URLs, offered roles, and verified drive counts.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-4 border-t border-[#263244]">
            <Button
              variant="secondary"
              size="sm"
              icon={Download}
              className="w-full font-mono text-xs"
              disabled={generatingType !== null}
              onClick={() => handleTriggerExport('COMPANIES', 'All Companies Directory')}
            >
              {generatingType === 'COMPANIES' ? 'SYNTHESIZING...' : 'GENERATE WORKBOOK'}
            </Button>
          </div>
        </div>

        {/* 2. Export Full-Time Jobs */}
        <div className="bg-[#151D29] border border-[#263244] hover:border-[#FF6A00]/50 rounded-lg p-5 tech-corner flex flex-col justify-between transition-all duration-200">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-[#FF6A00]/10 border border-[#FF6A00]/30 flex items-center justify-center text-[#FF6A00]">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#E6EDF3] font-mono">Full-Time Opportunities</h3>
              <p className="text-xs text-[#8492A6] font-mono mt-1 leading-relaxed">
                Complete dataset of direct FTE job notices, eligibility cutoffs, locations, and deadlines.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-4 border-t border-[#263244]">
            <Button
              variant="primary"
              size="sm"
              icon={Download}
              className="w-full font-mono text-xs"
              disabled={generatingType !== null}
              onClick={() => handleTriggerExport('JOBS', 'Full-Time Opportunities Dataset')}
            >
              {generatingType === 'JOBS' ? 'SYNTHESIZING...' : 'GENERATE WORKBOOK'}
            </Button>
          </div>
        </div>

        {/* 3. Export Internships */}
        <div className="bg-[#151D29] border border-[#263244] hover:border-purple-500/50 rounded-lg p-5 tech-corner flex flex-col justify-between transition-all duration-200">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-950/40 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#E6EDF3] font-mono">Internship Notices</h3>
              <p className="text-xs text-[#8492A6] font-mono mt-1 leading-relaxed">
                Dedicated isolation of summer & semester internships with monthly stipends and annualized INR equivalents.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-4 border-t border-[#263244]">
            <Button
              variant="secondary"
              size="sm"
              icon={Download}
              className="w-full font-mono text-xs"
              disabled={generatingType !== null}
              onClick={() => handleTriggerExport('INTERNSHIPS', 'Internship Opportunities')}
            >
              {generatingType === 'INTERNSHIPS' ? 'SYNTHESIZING...' : 'GENERATE WORKBOOK'}
            </Button>
          </div>
        </div>

        {/* 4. Export Salary Comparison */}
        <div className="bg-[#151D29] border border-[#263244] hover:border-emerald-500/50 rounded-lg p-5 tech-corner flex flex-col justify-between transition-all duration-200">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-950/40 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#E6EDF3] font-mono">Salary Benchmarks</h3>
              <p className="text-xs text-[#8492A6] font-mono mt-1 leading-relaxed">
                Granular compensation audit: Base pay, normalized LPA rankings, fixed vs variable CTC splits.
              </p>
            </div>
          </div>
          <div className="pt-4 mt-4 border-t border-[#263244]">
            <Button
              variant="primary"
              size="sm"
              icon={Download}
              className="w-full font-mono text-xs"
              disabled={generatingType !== null}
              onClick={() => handleTriggerExport('SALARY', 'Salary Comparison Audit')}
            >
              {generatingType === 'SALARY' ? 'SYNTHESIZING...' : 'GENERATE WORKBOOK'}
            </Button>
          </div>
        </div>
      </div>

      {/* Field Inclusion Customizer */}
      <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-3.5 rounded-sm bg-[#00D4FF]"></span>
            <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
              Excel Workbook Intelligence Features
            </h3>
          </div>
          <span className="text-[11px] text-[#8492A6]">
            Target Path: <code>./data/exports/</code>
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          {[
            { id: 'all_sheets', label: '6 Multi-Worksheets' },
            { id: 'formula_sec', label: 'Formula Injection Shield' },
            { id: 'salary_norm', label: 'Normalized LPA & INR Formats' },
            { id: 'stipend_iso', label: 'Strict Stipend Isolation' },
            { id: 'freeze_panes', label: 'Top-Row Frozen Panes' },
            { id: 'auto_filter', label: 'Enabled Range Auto-Filters' },
            { id: 'auto_width', label: 'Auto-Fitted Column Dimensions' },
            { id: 'audit_report', label: 'Quality Audit Sheet' },
          ].map((field) => (
            <div
              key={field.id}
              className="flex items-center gap-2.5 p-3 bg-[#101620] border border-[#263244] rounded text-emerald-400 select-none"
            >
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span className="text-xs text-[#E6EDF3]">{field.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Export History Registry */}
      <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#263244]">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-3.5 rounded-sm bg-[#FF6A00]"></span>
            <h3 className="font-semibold uppercase tracking-wider text-[#E6EDF3]">
              Export Deliverables Registry
            </h3>
          </div>
          <StatusBadge variant="cyan" size="xs">
            {totalExports} ARTIFACTS LOGGED
          </StatusBadge>
        </div>

        {exportsList.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-[#263244] rounded-lg">
            <FileSpreadsheet className="w-8 h-8 text-[#8492A6] mx-auto mb-2 opacity-50" />
            <p className="text-sm text-[#E6EDF3] font-bold">No Deliverables Generated Yet</p>
            <p className="text-xs text-[#8492A6] mt-1">
              Select one of the presets above to generate your first Haveloc placement Excel workbook.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto border border-[#263244] rounded-lg">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#263244] bg-[#101620] text-[#8492A6] uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-4">Artifact ID</th>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Scope</th>
                  <th className="py-3 px-4">Records</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Created At</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#263244]/60">
                {exportsList.map((exp) => (
                  <tr key={exp.id} className="hover:bg-[#101620]/60 transition-colors">
                    <td className="py-3 px-4 font-bold text-[#00D4FF]">#EXP-{exp.id}</td>
                    <td className="py-3 px-4 font-semibold text-[#E6EDF3] flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-[#FF6A00] shrink-0" />
                      <span className="truncate max-w-[240px]" title={exp.filename}>
                        {exp.filename}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-[#1B2635] text-[#00D4FF] border border-[#263244] font-bold">
                        {exp.export_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#00D4FF] font-bold">{exp.record_count}</td>
                    <td className="py-3 px-4 text-[#8492A6]">{formatBytes(exp.file_size_bytes)}</td>
                    <td className="py-3 px-4 text-[#8492A6]">
                      {formatDateTimeIST(exp.created_at, { fallback: 'Just now' })}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-[11px] font-mono ${
                          exp.status === 'COMPLETED' ? 'text-emerald-400' : 'text-red-400'
                        }`}
                      >
                        {exp.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <a
                          href={`${API_BASE_URL}/exports/${exp.id}/download`}
                          download={exp.filename}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#00D4FF]/10 border border-[#00D4FF]/40 text-[#00D4FF] hover:bg-[#00D4FF]/20 text-[11px] font-bold transition-colors"
                          title="Download Excel Workbook"
                        >
                          <Download className="w-3 h-3" />
                          DOWNLOAD
                        </a>
                        <button
                          onClick={() => handleDeleteExport(exp.id, exp.filename)}
                          className="p-1 rounded text-[#8492A6] hover:text-red-400 transition-colors"
                          title="Delete Artifact"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
