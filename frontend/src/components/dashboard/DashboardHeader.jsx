import React from 'react';
import Badge from '../common/Badge';

export default function DashboardHeader({ title, subtitle, badgeText, badgeVariant = 'orange' }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#263244]">
      <div>
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold font-mono tracking-tight text-[#E6EDF3]">{title}</h2>
          {badgeText && (
            <Badge variant={badgeVariant} size="sm" dot={true}>
              {badgeText}
            </Badge>
          )}
        </div>
        {subtitle && <p className="text-xs text-[#8492A6] font-mono mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

