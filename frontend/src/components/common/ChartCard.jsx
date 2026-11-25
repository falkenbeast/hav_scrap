import React from 'react';
import StatusBadge from './StatusBadge';

/**
 * ChartCard: Container for futuristic telemetry visualizations and Recharts displays.
 */
export default function ChartCard({
  title,
  subtitle,
  children,
  action,
  cyan = false,
  isDemo = true,
  className = '',
  height = 'h-72',
}) {
  const accentBar = cyan ? 'bg-[#00D4FF]' : 'bg-[#FF6A00]';
  const cornerClass = cyan ? 'tech-corner-cyan' : 'tech-corner';
  const hoverBorder = cyan ? 'hover:border-[#00D4FF]/40' : 'hover:border-[#FF6A00]/40';

  return (
    <div
      className={`relative bg-[#151D29] border border-[#263244] rounded-lg p-5 transition-all duration-300 ${hoverBorder} ${cornerClass} ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 mb-4 border-b border-[#263244]">
        <div>
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-3.5 rounded-sm ${accentBar}`}></span>
            <h3 className="font-semibold text-xs sm:text-sm uppercase tracking-wider text-[#E6EDF3] font-mono">
              {title}
            </h3>
            {isDemo && (
              <span className="px-1.5 py-0.5 bg-[#1B2635] border border-[#263244] text-[9px] font-mono text-[#00D4FF] rounded">
                DEMO DATA
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-[11px] text-[#8492A6] font-mono mt-0.5 pl-3.5">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="shrink-0 flex items-center gap-2">{action}</div>}
      </div>

      {/* Visualization Canvas */}
      <div className={`w-full ${height}`}>{children}</div>
    </div>
  );
}

