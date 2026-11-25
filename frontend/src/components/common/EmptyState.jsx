import React from 'react';
import { Database, RefreshCw } from 'lucide-react';
import Button from './Button';

/**
 * EmptyState: Displayed when no data/records match active filters or telemetry buffers are empty.
 */
export default function EmptyState({
  icon: Icon = Database,
  title = 'NO TELEMETRY RECORDS LOCATED',
  message = 'The query yielded zero matches. Adjust your filter parameters or initiate a fresh reconnaissance cycle.',
  actionLabel,
  onAction,
  className = '',
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-10 text-center bg-[#151D29]/40 border border-[#263244] border-dashed rounded-lg font-mono ${className}`}
    >
      <div className="w-12 h-12 rounded-lg bg-[#101620] border border-[#263244] flex items-center justify-center text-[#FF6A00] mb-4 shadow-glow-sm-orange/20">
        <Icon className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-bold uppercase tracking-wider text-[#E6EDF3] mb-1">
        {title}
      </h4>
      <p className="text-xs text-[#8492A6] max-w-md leading-relaxed mb-4">
        {message}
      </p>
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" icon={RefreshCw} onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

