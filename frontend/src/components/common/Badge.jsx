import React from 'react';

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
}) {
  const variants = {
    default: 'bg-[#101620] text-[#8492A6] border-[#263244]',
    orange: 'bg-[#FF6A00]/10 text-[#FF6A00] border-[#FF6A00]/40',
    cyan: 'bg-[#00D4FF]/10 text-[#00D4FF] border-[#00D4FF]/40',
    success: 'bg-emerald-950/40 text-emerald-400 border-emerald-700/50',
    warning: 'bg-amber-950/40 text-amber-400 border-amber-700/50',
    danger: 'bg-rose-950/40 text-rose-400 border-rose-700/50',
  };

  const dotColors = {
    default: 'bg-[#8492A6]',
    orange: 'bg-[#FF6A00] shadow-glow-sm-orange animate-pulse',
    cyan: 'bg-[#00D4FF] shadow-glow-sm-cyan animate-pulse',
    success: 'bg-emerald-400',
    warning: 'bg-amber-400',
    danger: 'bg-rose-400',
  };

  const sizes = {
    sm: 'text-[10px] px-2 py-0.5 font-mono',
    md: 'text-xs px-2.5 py-1 font-mono',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium border rounded uppercase tracking-wider ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`}></span>}
      {children}
    </span>
  );
}

