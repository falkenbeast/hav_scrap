import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Filter } from 'lucide-react';

/**
 * FilterDropdown: Custom dark HUD dropdown selector.
 */
export default function FilterDropdown({
  label,
  value,
  options = [],
  onChange,
  icon: Icon = Filter,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find((opt) => opt.value === value) || options[0];

  return (
    <div className={`relative inline-block ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-[#151D29] border border-[#263244] hover:border-[#00D4FF]/50 rounded-md text-xs font-mono text-[#E6EDF3] transition-colors focus:outline-none focus:border-[#00D4FF]"
      >
        <Icon className="w-3.5 h-3.5 text-[#00D4FF]" />
        {label && <span className="text-[#8492A6]">{label}:</span>}
        <span className="font-semibold text-[#00D4FF]">{selectedOption?.label || value}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-[#8492A6] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-48 bg-[#101620] border border-[#263244] rounded-md shadow-hud-card z-50 py-1 tech-corner-cyan max-h-60 overflow-y-auto">
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  onChange(opt.value);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2 text-xs font-mono flex items-center justify-between transition-colors ${
                  isSelected
                    ? 'bg-[#151D29] text-[#00D4FF] font-bold border-l-2 border-[#00D4FF]'
                    : 'text-[#8492A6] hover:text-[#E6EDF3] hover:bg-[#1B2635]'
                }`}
              >
                <span>{opt.label}</span>
                {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF]"></span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

