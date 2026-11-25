import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import Button from './Button';

export default function ErrorAlert({
  title = 'TELEMETRY FAULT DETECTED',
  message,
  onRetry,
}) {
  return (
    <div className="bg-rose-950/20 border border-rose-800/50 rounded-lg p-5 tech-corner">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-rose-500 mt-0.5 shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold uppercase font-mono tracking-wider text-rose-400">
            {title}
          </h4>
          <p className="mt-1 text-xs text-[#E6EDF3]/80 font-mono">
            {message || 'Unable to establish link with HAV_SCRAP core telemetry service.'}
          </p>
          {onRetry && (
            <div className="mt-4">
              <Button
                variant="danger"
                size="sm"
                icon={RefreshCw}
                onClick={onRetry}
              >
                RE-ENGAGE SYSTEM
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

