import React from 'react';
import {
  Building2,
  CheckCircle2,
  FileSpreadsheet,
  Cpu,
  Clock,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import { formatActivityTimestampIST } from '../../utils/formatters';

const EVENT_ICONS = {
  company_discovery: Building2,
  extraction_completed: CheckCircle2,
  export_generated: FileSpreadsheet,
  system_init: Cpu,
  warning: ShieldAlert,
};

const EVENT_COLORS = {
  company_discovery: 'text-[#00D4FF] border-[#00D4FF]/40 bg-[#00D4FF]/10',
  extraction_completed: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/30',
  export_generated: 'text-[#FF6A00] border-[#FF6A00]/40 bg-[#FF6A00]/10',
  system_init: 'text-purple-400 border-purple-500/40 bg-purple-950/30',
  warning: 'text-amber-400 border-amber-500/40 bg-amber-950/30',
};

/**
 * ActivityTimeline: Chronological HUD feed of intelligence events and system actions.
 * In LIVE mode, strictly renders verified database events or displays a clean empty state.
 * Demonstration events are isolated for DEMO PREVIEW mode only.
 */
export const DEMO_ACTIVITIES = [
  {
    id: 'demo-1',
    type: 'company_discovery',
    title: 'New Recruiter Profile Identified: Google LLC',
    description: 'Discovered SWE-1 / Campus Hire posting for 2025 batch (55.0 LPA CTC).',
    timestamp: '10 mins ago',
    badge: 'DISCOVERY',
    badgeVariant: 'cyan',
  },
  {
    id: 'demo-2',
    type: 'extraction_completed',
    title: 'Portal Reconnaissance Cycle Finished',
    description: 'Parsed 14 company listings, updated 6 job profile compensation ranges.',
    timestamp: '42 mins ago',
    badge: 'SUCCESS',
    badgeVariant: 'success',
  },
  {
    id: 'demo-3',
    type: 'export_generated',
    title: 'Placement Intelligence Spreadsheet Exported',
    description: 'Generated Excel deliverable: hav_scrap_2025_all_companies.xlsx.',
    timestamp: '2 hours ago',
    badge: 'DELIVERABLE',
    badgeVariant: 'orange',
  },
  {
    id: 'demo-4',
    type: 'system_init',
    title: 'Falkenbeast Core Engine Synchronized',
    description: 'FastAPI REST engine online, powered by Stark Systems Technology.',
    timestamp: '5 hours ago',
    badge: 'INITIALIZED',
    badgeVariant: 'standby',
  },
];

export default function ActivityTimeline({ events = [], isDemo = false, className = '' }) {
  const displayEvents = isDemo && (!events || events.length === 0) ? DEMO_ACTIVITIES : events;

  if (!displayEvents || displayEvents.length === 0) {
    return (
      <div
        className={`p-8 text-center bg-[#101620]/40 border border-[#263244] border-dashed rounded-lg font-mono ${className}`}
      >
        <div className="w-10 h-10 rounded-lg bg-[#151D29] border border-[#263244] flex items-center justify-center text-[#8492A6] mx-auto mb-3">
          <Clock className="w-5 h-5 text-[#8492A6]/60" />
        </div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#E6EDF3] mb-1">
          NO INTELLIGENCE ACTIVITY RECORDED
        </h4>
        <p className="text-[11px] text-[#8492A6] max-w-sm mx-auto leading-relaxed">
          No portal extraction, recruiter discoveries, or exports logged in data/hav_scrap.db yet. Launch a reconnaissance cycle in Scraper Control to generate live activity.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 font-mono ${className}`}>
      {displayEvents.map((evt, idx) => {
        const Icon = EVENT_ICONS[evt.type] || Clock;
        const colorStyles = EVENT_COLORS[evt.type] || EVENT_COLORS.system_init;
        const isLast = idx === displayEvents.length - 1;

        return (
          <div key={evt.id || idx} className="relative flex items-start gap-3.5 group">
            {/* Timeline Vertical Track */}
            {!isLast && (
              <div className="absolute left-[15px] top-[28px] bottom-[-16px] w-[1px] bg-[#263244] group-hover:bg-[#00D4FF]/30 transition-colors" />
            )}

            {/* Event Icon Node */}
            <div
              className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 z-10 transition-transform group-hover:scale-105 ${colorStyles}`}
            >
              <Icon className="w-4 h-4" />
            </div>

            {/* Event Content Box */}
            <div className="flex-1 bg-[#101620]/60 border border-[#263244] group-hover:border-[#384961] rounded-lg p-3 transition-colors">
              <div className="flex items-center justify-between gap-2 mb-1 flex-wrap">
                <span className="text-xs font-bold text-[#E6EDF3] group-hover:text-[#00D4FF] transition-colors">
                  {evt.title}
                </span>
                <div className="flex items-center gap-2">
                  {evt.badge && (
                    <StatusBadge variant={evt.badgeVariant || 'cyan'} size="xs" dot={false}>
                      {evt.badge}
                    </StatusBadge>
                  )}
                  <span className="text-[10px] text-[#8492A6]">{formatActivityTimestampIST(evt.timestamp)}</span>
                </div>
              </div>
              <p className="text-[11px] text-[#8492A6] leading-relaxed">
                {evt.description}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

