import React from 'react';
import { useStore } from '../store/useStore';
import type { AgentStatus } from '../types';

interface AgentMeta {
  key: string;
  label: string;
  color: string;
  idleDesc: string;
}

const AGENTS: AgentMeta[] = [
  { key: 'pm', label: 'PM', color: 'var(--agent-pm)', idleDesc: 'Awaiting requirement.' },
  { key: 'architect', label: 'Architect', color: 'var(--agent-architect)', idleDesc: 'Awaiting spec.' },
  { key: 'coder', label: 'Coder', color: 'var(--agent-coder)', idleDesc: 'Awaiting architecture approval.' },
  { key: 'reviewer', label: 'Reviewer', color: 'var(--agent-reviewer)', idleDesc: 'Awaiting code implementation.' },
];

const BADGE: Record<string, { text: string; fg: string; bg: string }> = {
  running: { text: 'Running', fg: 'var(--accent-blue)', bg: 'rgba(88,166,255,0.15)' },
  completed: { text: 'Done', fg: 'var(--accent-green)', bg: 'rgba(63,185,80,0.15)' },
  failed: { text: 'Failed', fg: 'var(--accent-red)', bg: 'rgba(248,81,73,0.15)' },
  idle: { text: 'Waiting', fg: 'var(--text-muted)', bg: 'rgba(110,118,129,0.15)' },
};

const AgentRow: React.FC<{ meta: AgentMeta; status?: AgentStatus }> = ({ meta, status }) => {
  const state = status?.status ?? 'idle';
  const badge = BADGE[state] ?? BADGE.idle;
  const desc = status?.output?.summary || meta.idleDesc;
  const isRunning = state === 'running';

  return (
    <div
      style={{
        border: '1px solid var(--border-color)',
        borderLeft: `3px solid ${meta.color}`,
        borderRadius: '6px',
        background: 'var(--bg-secondary)',
        padding: '12px',
        marginBottom: '8px',
        opacity: state === 'idle' ? 0.65 : 1,
        boxShadow: isRunning ? '0 0 0 1px var(--accent-blue)' : 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: '4px',
              background: meta.color,
              color: '#fff',
              textTransform: 'uppercase',
            }}
          >
            {meta.label.slice(0, 4)}
          </span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {meta.label}
          </span>
        </span>
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '11px',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: '10px',
            color: badge.fg,
            background: badge.bg,
          }}
        >
          {isRunning && (
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'currentColor' }} />
          )}
          {badge.text}
        </span>
      </div>
      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{desc}</div>
      {status?.error && (
        <div
          style={{
            marginTop: '6px',
            fontSize: '12px',
            color: 'var(--accent-red)',
            background: 'rgba(248,81,73,0.1)',
            padding: '6px 8px',
            borderRadius: '4px',
          }}
        >
          {status.error}
        </div>
      )}
    </div>
  );
};

/** Vertical agent list with status badges. */
export const AgentStatusList: React.FC = () => {
  const agentStatuses = useStore((s) => s.agentStatuses);
  const workflowState = useStore((s) => s.workflowState);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: '10px 12px',
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          color: 'var(--text-secondary)',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        Agents
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
        {AGENTS.map((meta) => (
          <AgentRow key={meta.key} meta={meta} status={agentStatuses[meta.key]} />
        ))}
        {workflowState && workflowState.iteration_count > 0 && (
          <div
            style={{
              marginTop: '8px',
              textAlign: 'center',
              fontSize: '12px',
              color: 'var(--accent-yellow)',
            }}
          >
            ↻ Iteration {workflowState.iteration_count}
          </div>
        )}
      </div>
    </div>
  );
};
