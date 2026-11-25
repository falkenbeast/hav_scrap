import React from 'react';

export default function Card({
  children,
  className = '',
  title,
  subtitle,
  action,
  glow = false,
  cyan = false,
  cornerTech = true,
}) {
  const glowClass = glow
    ? cyan
      ? 'border-[#00D4FF]/40 shadow-glow-sm-cyan'
      : 'border-[#FF6A00]/40 shadow-glow-sm-orange'
    : 'border-[#263244]';

  return (
    <div
      className={`relative bg-[#151D29] border rounded-lg p-5 transition-all duration-300 hover:border-[#384860] ${glowClass} ${
        cornerTech ? 'tech-corner' : ''
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#263244]">
          <div>
            {title && (
              <h3 className="font-semibold text-sm uppercase tracking-wider text-[#E6EDF3] flex items-center gap-2">
                <span className={`w-1.5 h-3.5 rounded-sm ${cyan ? 'bg-[#00D4FF]' : 'bg-[#FF6A00]'}`}></span>
                {title}
              </h3>
            )}
            {subtitle && <p className="text-xs text-[#8492A6] mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

