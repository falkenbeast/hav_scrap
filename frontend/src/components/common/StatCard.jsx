import React from 'react';
import StatusBadge from './StatusBadge';

/**
 * StatCard: Falkenbeast Labs Placement Intelligence KPI Metric Card.
 * Powered by Stark Systems Technology.
 * Displays metric icon, label, value, description, trend, and optional demonstration badge.
 */
export default function StatCard({
  icon: Icon,
  label,
  value,
  subtext,
  trend,
  trendPositive = true,
  cyan = false,
  isDemo = false,
  className = '',
  loading = false,
}) {
  if (loading) {
    return (
      <div className="bg-[#151D29] border border-[#263244] rounded-lg p-5 tech-corner skeleton-shimmer h-36">
        <div className="h-4 w-24 bg-[#1B2635] rounded mb-3"></div>
        <div className="h-8 w-32 bg-[#1B2635] rounded mb-2"></div>
        <div className="h-3 w-40 bg-[#1B2635] rounded"></div>
      </div>
    );
  }

  const accentColor = cyan ? 'text-[#00D4FF]' : 'text-[#FF6A00]';
  const iconBorderColor = cyan
    ? 'bg-[#00D4FF]/10 border-[#00D4FF]/30 text-[#00D4FF]'
    : 'bg-[#FF6A00]/10 border-[#FF6A00]/30 text-[#FF6A00]';
  const hoverBorder = cyan ? 'hover:border-[#00D4FF]/50' : 'hover:border-[#FF6A00]/50';

  return (
    <div
      className={`relative bg-[#151D29] border border-[#263244] rounded-lg p-5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-hud-card ${hoverBorder} ${
        cyan ? 'tech-corner-cyan' : 'tech-corner'
      } ${className}`}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] uppercase font-mono tracking-wider text-[#8492A6]">
              {label}
            </span>
            {isDemo && (
              <span className="px-1.5 py-0.2 bg-[#1B2635] border border-[#263244] text-[9px] font-mono text-[#00D4FF] rounded">
                DEMO
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2 pt-1">
            <span className={`text-2xl lg:text-3xl font-extrabold font-mono tracking-tight ${accentColor}`}>
              {value}
            </span>
          </div>
        </div>

        {Icon && (
          <div className={`p-2.5 rounded-lg border shrink-0 transition-transform duration-300 group-hover:scale-110 ${iconBorderColor}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 pt-3 border-t border-[#263244]/80 flex items-center justify-between text-xs font-mono">
        {subtext && (
          <span className="text-[#8492A6] text-[11px] truncate">{subtext}</span>
        )}
        {trend && (
          <span
            className={`flex items-center gap-1 font-semibold text-[11px] ml-auto shrink-0 ${
              trendPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            <span>{trendPositive ? '▲' : '▼'}</span>
            <span>{trend}</span>
          </span>
        )}
      </div>
    </div>
  );
}

