import React from 'react';
import { Search, X } from 'lucide-react';

/**
 * SearchBar: Futuristic HUD search component with instant clear and hotkey hint.
 */
export default function SearchBar({
  value,
  onChange,
  placeholder = 'Query intelligence records...',
  className = '',
  onClear,
}) {
  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="w-4 h-4 absolute left-3 text-[#8492A6] pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-[#151D29] border border-[#263244] focus:border-[#00D4FF] focus:shadow-glow-sm-cyan/30 rounded-md pl-9 pr-9 py-2 text-xs font-mono text-[#E6EDF3] placeholder-[#8492A6] outline-none transition-all duration-200"
      />
      {value && (
        <button
          type="button"
          onClick={() => {
            if (onClear) onClear();
            else onChange('');
          }}
          className="absolute right-2.5 p-0.5 rounded text-[#8492A6] hover:text-[#FF6A00] transition-colors"
          title="Clear search"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}

