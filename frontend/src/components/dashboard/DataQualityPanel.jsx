import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Layers,
  FileText,
  DollarSign,
  Copy,
  ExternalLink,
  ChevronRight,
  Info,
} from 'lucide-react';
import Button from '../common/Button';
import StatusBadge from '../common/StatusBadge';
import { api } from '../../services/api';

export default function DataQualityPanel({ onSelectJob }) {
  const [qualityReport, setQualityReport] = useState(null);
  const [reviewRecords, setReviewRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [report, reviews] = await Promise.all([
        api.getQualityReport().catch(() => null),
        api.getReviewRecords({ page: 1, page_size: 10 }).catch(() => ({ items: [] })),
      ]);
      setQualityReport(report);
      setReviewRecords(reviews?.items || []);
    } catch (err) {
      console.warn('Error fetching quality report:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunPipeline = async () => {
    try {
      setPipelineRunning(true);
      setError(null);
      await api.startProcessing();
      // Poll briefly for completion
      setTimeout(async () => {
        await fetchData();
        setPipelineRunning(false);
      }, 3000);
    } catch (err) {
      setError(err.message || 'Failed to run data processing pipeline.');
      setPipelineRunning(false);
    }
  };

  const score = qualityReport?.data_quality_percentage ?? 100.0;
  const scoreColor =
    score >= 85
      ? 'text-emerald-400'
      : score >= 65
      ? 'text-[#00D4FF]'
      : score >= 50
      ? 'text-amber-400'
      : 'text-rose-400';

  return (
    <div className="bg-[#151D29] border border-[#263244] rounded-2xl p-6 space-y-6 shadow-xl relative overflow-hidden backdrop-blur-md">
      {/* Top Ambient Glow */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00D4FF] to-transparent opacity-80" />

      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#263244]">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-[#101620] border border-[#263244] flex items-center justify-center text-[#00D4FF] shadow-inner">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-[#E6EDF3] tracking-wide uppercase font-mono">
                DATA QUALITY & VALIDATION AUDIT
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[#1B2635] text-emerald-400 border border-[#263244] font-mono">
                PHASE 8 PIPELINE
              </span>
            </div>
            <p className="text-xs text-[#8492A6] mt-0.5">
              Idempotent text cleaning, Indian CTC normalization, duplicate resolution, and rule verification.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            loading={loading}
            onClick={fetchData}
          >
            REFRESH
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={Sparkles}
            loading={pipelineRunning}
            onClick={handleRunPipeline}
          >
            RUN PIPELINE
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs text-rose-300 font-mono">
          {error}
        </div>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* Quality Score Card */}
        <div className="col-span-2 sm:col-span-1 bg-[#101620] border border-[#263244] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#8492A6] uppercase tracking-wider block">
            QUALITY RATING
          </span>
          <div className="my-2">
            <span className={`text-3xl font-extrabold font-mono tracking-tight ${scoreColor}`}>
              {score}%
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {score >= 80 ? 'Optimal Production Health' : 'Review Required'}
          </span>
        </div>

        {/* Cleaned Records */}
        <div className="bg-[#101620] border border-[#263244] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#8492A6] uppercase tracking-wider block">
            CLEANED RECORDS
          </span>
          <div className="my-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {qualityReport?.cleaned_records ?? 0}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">
            Of {qualityReport?.total_jobs ?? 0} Total Listings
          </span>
        </div>

        {/* Needs Review */}
        <div className="bg-[#101620] border border-[#263244] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#8492A6] uppercase tracking-wider block">
            NEEDS REVIEW
          </span>
          <div className="my-2">
            <span className="text-2xl font-bold font-mono text-amber-400">
              {qualityReport?.records_needing_review ?? 0}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">Ambiguous Clauses</span>
        </div>

        {/* Duplicates Identified */}
        <div className="bg-[#101620] border border-[#263244] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#8492A6] uppercase tracking-wider block">
            DUPLICATES
          </span>
          <div className="my-2">
            <span className="text-2xl font-bold font-mono text-[#00D4FF]">
              {qualityReport?.duplicate_jobs_detected ?? 0}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">Isolated & Resolved</span>
        </div>

        {/* Undisclosed Salary */}
        <div className="bg-[#101620] border border-[#263244] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#8492A6] uppercase tracking-wider block">
            UNDISCLOSED SALARY
          </span>
          <div className="my-2">
            <span className="text-2xl font-bold font-mono text-slate-300">
              {qualityReport?.records_without_salary ?? 0}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">Kept Cleanly NULL</span>
        </div>
      </div>

      {/* Manual Review Table Section */}
      <div className="bg-[#101620] border border-[#263244] rounded-xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-[#263244] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#E6EDF3]">
              Listings Flagged For Operator Review
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[#8492A6]">
            {reviewRecords.length} Flagged Entries
          </span>
        </div>

        {reviewRecords.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-[#8492A6]">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            No records currently require manual review. All entries satisfy data validation standards.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#151D29]/60 text-[#8492A6] text-[10px] uppercase border-b border-[#263244]">
                <tr>
                  <th className="py-2.5 px-4">Company</th>
                  <th className="py-2.5 px-4">Job Designation</th>
                  <th className="py-2.5 px-4">Salary Clause</th>
                  <th className="py-2.5 px-4">Issue Description</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#263244]/60 text-slate-200">
                {reviewRecords.map((item) => (
                  <tr key={item.id} className="hover:bg-[#1B2635]/40 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white truncate max-w-[150px]">
                      {item.cleaned_company_name || item.company_name}
                    </td>
                    <td className="py-3 px-4 text-[#00D4FF] truncate max-w-[180px]">
                      {item.cleaned_job_title || item.job_title}
                    </td>
                    <td className="py-3 px-4 text-amber-300 truncate max-w-[200px]">
                      {item.original_salary_text || 'No Clause Stated'}
                    </td>
                    <td className="py-3 px-4 text-rose-300 text-[11px] truncate max-w-[220px]">
                      {item.validation_notes || 'Ambiguous compensation clause'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onSelectJob && onSelectJob(item)}
                        className="text-xs text-[#00D4FF] hover:text-[#FF6A00] transition-colors inline-flex items-center gap-1"
                      >
                        Inspect <ChevronRight className="w-3 h-3" />
                      </button>
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

