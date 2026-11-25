import React from 'react';

export default function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon: Icon,
  className = '',
  type = 'button',
}) {
  const baseClasses =
    'inline-flex items-center justify-center font-medium transition-all duration-200 uppercase tracking-wider rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#0B0E14] disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const sizes = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-xs px-4 py-2.5 gap-2 font-semibold',
    lg: 'text-sm px-6 py-3 gap-2.5 font-bold',
  };

  const variants = {
    primary:
      'bg-[#FF6A00] hover:bg-[#E55F00] text-black font-bold shadow-glow-sm-orange hover:shadow-glow-orange border border-[#FF6A00]',
    secondary:
      'bg-transparent hover:bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/60 hover:border-[#00D4FF] hover:shadow-glow-sm-cyan',
    outline:
      'bg-transparent hover:bg-[#1B2433] text-[#E6EDF3] border border-[#263244] hover:border-[#8492A6]',
    danger:
      'bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-700/60 hover:border-red-500',
    ghost:
      'bg-transparent hover:bg-[#151D29] text-[#8492A6] hover:text-[#E6EDF3]',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClasses} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-1"></span>
      ) : (
        Icon && <Icon className="w-4 h-4" />
      )}
      {children}
    </button>
  );
}

