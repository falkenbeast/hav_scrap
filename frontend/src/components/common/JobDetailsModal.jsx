import React from 'react';
import {
  X,
  Building2,
  ExternalLink,
  DollarSign,
  TrendingUp,
  MapPin,
  Calendar,
  Clock,
  Briefcase,
  GraduationCap,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  FileText,
  Sparkles,
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import { formatDateIST, formatDateTimeIST } from '../../utils/formatters';

export default function JobDetailsModal({ job, onClose }) {
  if (!job) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#151D29] border border-[#263244] w-full max-w-3xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden relative tech-corner">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00D4FF] to-transparent opacity-80" />

        {/* Modal Header */}
        <div className="p-6 border-b border-[#263244] flex items-start justify-between gap-4 bg-[#101620]/80">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-[#1B2635] border border-[#263244] flex items-center justify-center text-[#FF6A00] font-bold text-lg shrink-0">
              {job.company_name ? job.company_name.charAt(0) : 'J'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-[#E6EDF3] tracking-wide">
                  {job.job_title}
                </h3>
                {job.work_mode && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-[#00D4FF] border border-cyan-500/30">
                    {job.work_mode}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-[#8492A6] mt-1">
                <span className="text-slate-300 font-semibold">{job.company_name}</span>
                {job.job_role && <span>• {job.job_role}</span>}
                {job.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-[#FF6A00]" />
                    {job.location}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-[#8492A6] hover:text-white rounded-lg hover:bg-[#1B2635] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm font-sans">
          {/* Compensation Intelligence Card */}
          <div className="bg-[#101620] border border-[#263244] rounded-xl p-5 relative overflow-hidden">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#263244]/80">
              <span className="text-xs font-mono text-[#00D4FF] tracking-wider uppercase flex items-center gap-1.5 font-bold">
                <DollarSign className="w-4 h-4 text-[#FF6A00]" />
                COMPENSATION INTELLIGENCE
              </span>
              {job.salary_lpa ? (
                <div className="text-xl font-bold font-mono text-[#FF6A00]">
                  {job.salary_lpa} <span className="text-xs text-slate-400 font-normal">LPA</span>
                </div>
              ) : job.stipend_amount ? (
                <div className="text-xl font-bold font-mono text-emerald-400">
                  ₹{job.stipend_amount.toLocaleString()}{' '}
                  <span className="text-xs text-slate-400 font-normal">/{job.stipend_period || 'month'}</span>
                </div>
              ) : (
                <span className="text-xs font-mono text-[#8492A6]">Undisclosed Compensation</span>
              )}
            </div>

            {/* Breakdown Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">MIN / MAX CTC</span>
                <span className="text-slate-200 font-semibold">
                  {job.minimum_ctc ? `${job.minimum_ctc} - ${job.maximum_ctc || job.minimum_ctc} LPA` : 'N/A'}
                </span>
              </div>
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">FIXED BASE</span>
                <span className="text-slate-200 font-semibold">
                  {job.fixed_ctc ? `${job.fixed_ctc} LPA` : 'Standard'}
                </span>
              </div>
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">VARIABLE / BONUS</span>
                <span className="text-slate-200 font-semibold">
                  {job.variable_ctc ? `${job.variable_ctc} LPA` : 'None / Not Stated'}
                </span>
              </div>
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">SIGN-ON BONUS</span>
                <span className="text-slate-200 font-semibold">
                  {job.joining_bonus ? `${job.joining_bonus} LPA` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Original Salary Text Clause */}
            {job.original_salary_text && (
              <div className="mt-3 pt-3 border-t border-[#263244]/60 text-[11px] font-mono text-[#8492A6]">
                <span className="text-[#00D4FF] font-semibold">Source Clause: </span>
                <span className="text-slate-300">"{job.original_salary_text}"</span>
              </div>
            )}
          </div>

          {/* Eligibility & Academic Requirements */}
          <div className="bg-[#101620] border border-[#263244] rounded-xl p-5 space-y-4">
            <span className="text-xs font-mono text-[#00D4FF] tracking-wider uppercase flex items-center gap-1.5 font-bold">
              <GraduationCap className="w-4 h-4 text-[#00D4FF]" />
              ELIGIBILITY & ACADEMIC CRITERIA
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">MINIMUM CGPA</span>
                <span className="text-emerald-400 font-semibold text-sm">
                  {job.minimum_cgpa ? `${job.minimum_cgpa} / 10.0` : 'No Minimum Stated'}
                </span>
              </div>
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">BACKLOG POLICY</span>
                <span className="text-slate-200 font-semibold">
                  {job.backlog_criteria || 'Not Specified'}
                </span>
              </div>
              <div className="p-2.5 rounded bg-[#151D29] border border-[#263244]">
                <span className="text-[#8492A6] block text-[10px]">TARGET BATCH</span>
                <span className="text-slate-200 font-semibold">
                  {job.batch || 'All Eligible'}
                </span>
              </div>
            </div>

            {job.eligible_branches && (
              <div className="text-xs">
                <span className="text-[#8492A6] block font-mono text-[11px] mb-1">ELIGIBLE BRANCHES:</span>
                <div className="flex flex-wrap gap-1.5">
                  {job.eligible_branches.split(',').map((b, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded bg-[#1B2635] text-[#00D4FF] border border-[#263244] font-mono text-[11px]"
                    >
                      {b.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {job.eligibility && (
              <div className="text-xs text-slate-300 bg-[#151D29] p-3 rounded border border-[#263244] leading-relaxed">
                {job.eligibility}
              </div>
            )}
          </div>

          {/* Job Description */}
          {job.job_description && (
            <div className="space-y-2">
              <span className="text-xs font-mono text-[#8492A6] uppercase tracking-wider block">
                Job Overview & Details
              </span>
              <div className="text-xs text-slate-300 leading-relaxed bg-[#101620] border border-[#263244] p-4 rounded-xl whitespace-pre-wrap max-h-48 overflow-y-auto font-sans">
                {job.job_description}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#101620] border-t border-[#263244] flex items-center justify-between gap-4">
          <div className="text-[11px] font-mono text-[#8492A6]">
            {job.application_deadline ? (
              <span className="text-amber-400">
                Deadline: {formatDateIST(job.application_deadline)}
              </span>
            ) : (
              <span>Last Verified: {formatDateTimeIST(job.last_verified_at, { fallback: 'Recent' })}</span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {job.source_url && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#1B2635] hover:bg-[#263244] text-[#00D4FF] border border-[#00D4FF]/30 font-mono text-xs transition-colors"
              >
                View on Haveloc <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-[#263244] hover:bg-slate-700 text-white font-mono text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

