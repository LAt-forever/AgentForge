import React from 'react';
import type { AgentStatus } from '../types';

interface AgentCardProps {
  status: AgentStatus;
}

const statusBadgeColors: Record<string, string> = {
  running: 'var(--accent-blue)',
  completed: 'var(--accent-green)',
  failed: 'var(--accent-red)',
  idle: 'var(--text-muted)',
};

const statusBadgeBgs: Record<string, string> = {
  running: 'rgba(88, 166, 255, 0.15)',
  completed: 'rgba(35, 134, 54, 0.15)',
  failed: 'rgba(218, 54, 51, 0.15)',
  idle: 'rgba(110, 118, 129, 0.15)',
};

export const AgentCard: React.FC<AgentCardProps> = ({ status }) => {
  return (
    <div
      style={{
        border: '1px solid var(--border-color)',
        borderRadius: '8px',
        background: 'var(--bg-secondary)',
        padding: '12px',
        marginBottom: '8px',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <span
          style={{
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          {status.agent}
        </span>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            padding: '2px 8px',
            borderRadius: '4px',
            color: statusBadgeColors[status.status] || statusBadgeColors.idle,
            background: statusBadgeBgs[status.status] || statusBadgeBgs.idle,
          }}
        >
          {status.status}
        </span>
      </div>

      {/* Summary */}
      {status.output?.summary && (
        <div
          style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            marginBottom: '6px',
            lineHeight: 1.4,
          }}
        >
          {status.output.summary}
        </div>
      )}

      {/* Files */}
      {status.output?.files && status.output.files.length > 0 && (
        <div
          style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            marginBottom: '6px',
          }}
        >
          {status.output.files.join(', ')}
        </div>
      )}

      {/* Error */}
      {status.error && (
        <div
          style={{
            fontSize: '12px',
            color: 'var(--accent-red)',
            background: 'rgba(218, 54, 51, 0.1)',
            padding: '6px 8px',
            borderRadius: '4px',
            marginTop: '4px',
          }}
        >
          {status.error}
        </div>
      )}
    </div>
  );
};
