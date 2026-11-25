import React from 'react';
import StatusBadge from './StatusBadge';

/**
 * SectionHeader: Standardized tactical top banner for every view.
 */
export default function SectionHeader({
  title,
  subtitle,
  badgeText,
  badgeVariant = 'orange',
  actions,
  className = '',
}) {
  return (
    <div
      className={`flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-[#263244] ${className}`}
    >
      <div>
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-[#E6EDF3]">
            {title}
          </h1>
          {badgeText && (
            <StatusBadge variant={badgeVariant} size="sm" dot={true}>
              {badgeText}
            </StatusBadge>
          )}
        </div>
        {subtitle && (
          <p className="text-xs text-[#8492A6] font-mono mt-1 max-w-3xl leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          {actions}
        </div>
      )}
    </div>
  );
}

