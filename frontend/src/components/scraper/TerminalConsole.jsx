import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Copy, Trash2, Check, ArrowDown } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

/**
 * TerminalConsole: Falkenbeast Labs tactical live telemetry console for crawler activity.
 * Powered by Stark Systems Technology.
 */
export default function TerminalConsole({
  logs = [],
  onClear,
  title = 'TACTICAL TELEMETRY STREAM',
  subtitle = 'Real-time crawler socket events & parser audit logs',
  className = '',
}) {
  const [copied, setCopied] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const viewportRef = useRef(null);

  // Keep internal terminal viewport scrolled to bottom without moving parent page scroll
  useEffect(() => {
    if (autoScroll && viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleCopy = () => {
    const text = logs
      .map((l) => (typeof l === 'string' ? l : `[${l.timestamp}] [${l.level}] ${l.message}`))
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLevelStyle = (level) => {
    switch (level?.toUpperCase()) {
      case 'SUCCESS':
      case 'COMPLETE':
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-600/40';
      case 'WARN':
      case 'WARNING':
        return 'text-amber-400 bg-amber-950/40 border-amber-600/40';
      case 'ERROR':
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-950/40 border-rose-600/40';
      case 'DISCOVER':
      case 'EXTRACT':
        return 'text-[#FF6A00] bg-[#FF6A00]/10 border-[#FF6A00]/30';
      case 'AUTH':
      case 'NETWORK':
        return 'text-purple-400 bg-purple-950/40 border-purple-600/40';
      case 'RECON':
      case 'PARSER':
      default:
        return 'text-[#00D4FF] bg-[#00D4FF]/10 border-[#00D4FF]/30';
    }
  };

  return (
    <div className={`bg-[#151D29] border border-[#263244] rounded-lg tech-corner flex flex-col font-mono ${className}`}>
      {/* Console Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#263244] bg-[#101620]">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-[#00D4FF]" />
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#E6EDF3]">
              {title}
            </h3>
            {subtitle && <p className="text-[10px] text-[#8492A6]">{subtitle}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-2 py-1 text-[10px] rounded border transition-colors flex items-center gap-1 ${
              autoScroll
                ? 'bg-[#00D4FF]/10 text-[#00D4FF] border-[#00D4FF]/40'
                : 'text-[#8492A6] border-[#263244] hover:text-[#E6EDF3]'
            }`}
            title="Toggle Auto-scroll"
          >
            <ArrowDown className="w-3 h-3" />
            <span>AUTO-SCROLL</span>
          </button>

          <button
            onClick={handleCopy}
            className="p-1.5 text-[#8492A6] hover:text-[#00D4FF] border border-[#263244] hover:border-[#00D4FF]/40 rounded transition-colors"
            title="Copy all telemetry logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {onClear && (
            <button
              onClick={onClear}
              className="p-1.5 text-[#8492A6] hover:text-[#FF6A00] border border-[#263244] hover:border-[#FF6A00]/40 rounded transition-colors"
              title="Clear telemetry buffer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Terminal Viewport */}
      <div
        ref={viewportRef}
        className="flex-1 bg-[#0B0E14] p-4 overflow-y-auto space-y-1.5 text-xs text-[#E6EDF3] max-h-96 min-h-[280px]"
      >
        {logs.length === 0 ? (
          <div className="text-center py-12 text-[#8492A6]">
            &gt; TELEMETRY STREAM IDLE. NO ACTIVE RECON TRANSMISSIONS.
          </div>
        ) : (
          logs.map((log, index) => {
            const isObj = typeof log === 'object' && log !== null;
            const timestamp = isObj ? log.timestamp : null;
            const level = isObj ? log.level : 'INFO';
            const message = isObj ? log.message : log;

            return (
              <div
                key={index}
                className="flex items-start gap-2 leading-relaxed hover:bg-[#101620]/60 p-0.5 rounded transition-colors"
              >
                <span className="text-[#8492A6]/50 select-none">&gt;</span>
                {timestamp && (
                  <span className="text-[#8492A6] text-[11px] shrink-0">
                    [{timestamp}]
                  </span>
                )}
                {level && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded border font-bold shrink-0 ${getLevelStyle(
                      level
                    )}`}
                  >
                    {level}
                  </span>
                )}
                <span className="text-[#E6EDF3] break-all flex-1">{message}</span>
              </div>
            );
          })
        )}
      </div>

      {/* Console Status Bar */}
      <div className="px-4 py-2 border-t border-[#263244] bg-[#101620] flex items-center justify-between text-[10px] text-[#8492A6]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-pulse"></span>
          <span>STREAM ENCRYPTED // TLS 1.3</span>
        </div>
        <span>BUFFER: {logs.length} EVENTS</span>
      </div>
    </div>
  );
}

