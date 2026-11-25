import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';

export default function TelemetryPanel({ status, sessionsCount, activeTarget }) {
  return (
    <Card title="RUNTIME TELEMETRY MATRIX" cyan={true}>
      <div className="space-y-3 font-mono text-xs">
        <div className="flex justify-between items-center p-2.5 bg-[#0B0E14] rounded border border-[#263244]">
          <span className="text-[#8492A6]">SOCKET STATUS:</span>
          <Badge variant="cyan" size="sm" dot={true}>
            READY
          </Badge>
        </div>
        <div className="flex justify-between items-center p-2.5 bg-[#0B0E14] rounded border border-[#263244]">
          <span className="text-[#8492A6]">CONCURRENT THREADS:</span>
          <span className="text-[#FF6A00] font-bold">1 (ISOLATED)</span>
        </div>
        <div className="flex justify-between items-center p-2.5 bg-[#0B0E14] rounded border border-[#263244]">
          <span className="text-[#8492A6]">HARVEST TARGET:</span>
          <span className="text-[#E6EDF3]">{activeTarget || 'Haveloc Portal Notices'}</span>
        </div>
      </div>
    </Card>
  );
}

