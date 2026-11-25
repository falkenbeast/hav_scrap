import React from 'react';

/**
 * StatusBadge: Tactical status badge with glowing indicators.
 * Variants:
 * - cyan: System/telemetry information
 * - orange: Primary state / alert
 * - success: Operational / Online
 * - warning: Caution / Closing soon
 * - danger: Critical / Error / Offline
 * - demo: Distinct demonstration data marker
 * - standby: Idle / Waiting
 */
export default function StatusBadge({
  children,
  variant = 'cyan',
  size = 'md',
  dot = true,
  className = '',
}) {
  const variants = {
    cyan: 'bg-[#00D4FF]/10 text-[#00D4FF] border-[#00D4FF]/40 shadow-glow-sm-cyan/30',
    orange: 'bg-[#FF6A00]/10 text-[#FF6A00] border-[#FF6A00]/40 shadow-glow-sm-orange/30',
    success: 'bg-emerald-950/40 text-emerald-400 border-emerald-600/50',
    warning: 'bg-amber-950/40 text-amber-400 border-amber-600/50',
    danger: 'bg-rose-950/40 text-rose-400 border-rose-600/50',
    demo: 'bg-[#1B2635] text-[#00D4FF] border-[#263244] tracking-widest font-bold',
    standby: 'bg-[#101620] text-[#8492A6] border-[#263244]',
  };

  const dotColors = {
    cyan: 'bg-[#00D4FF] shadow-glow-sm-cyan animate-pulse',
    orange: 'bg-[#FF6A00] shadow-glow-sm-orange animate-pulse',
    success: 'bg-emerald-400',
    warning: 'bg-amber-400',
    danger: 'bg-rose-400',
    demo: 'bg-[#00D4FF]',
    standby: 'bg-[#8492A6]',
  };

  const sizes = {
    xs: 'text-[9px] px-1.5 py-0.5 font-mono',
    sm: 'text-[10px] px-2 py-0.5 font-mono',
    md: 'text-xs px-2.5 py-1 font-mono',
    lg: 'text-sm px-3 py-1.5 font-mono',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium border rounded uppercase tracking-wider select-none ${variants[variant] || variants.cyan} ${sizes[size] || sizes.md} ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColors[variant] || dotColors.cyan}`}
        />
      )}
      <span>{children}</span>
    </span>
  );
}

