import React from 'react';
import Card from './Card';

export default function MetricCard({
  label,
  value,
  subvalue,
  icon: Icon,
  trend,
  trendPositive = true,
  cyan = false,
}) {
  return (
    <Card
      cornerTech={true}
      cyan={cyan}
      className="overflow-hidden hover:scale-[1.01] transition-transform duration-200"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase font-mono tracking-wider text-[#8492A6]">{label}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span
              className={`text-2xl lg:text-3xl font-extrabold font-mono tracking-tight ${
                cyan ? 'text-[#00D4FF]' : 'text-[#FF6A00]'
              }`}
            >
              {value}
            </span>
            {subvalue && (
              <span className="text-xs text-[#8492A6] font-mono">{subvalue}</span>
            )}
          </div>
          {trend && (
            <p
              className={`mt-2 text-xs flex items-center gap-1 font-mono ${
                trendPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              <span>{trendPositive ? '▲' : '▼'}</span>
              <span>{trend}</span>
            </p>
          )}
        </div>
        {Icon && (
          <div
            className={`p-2.5 rounded-lg border ${
              cyan
                ? 'bg-[#00D4FF]/10 border-[#00D4FF]/30 text-[#00D4FF]'
                : 'bg-[#FF6A00]/10 border-[#FF6A00]/30 text-[#FF6A00]'
            }`}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </Card>
  );
}

