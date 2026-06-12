import React from 'react';

interface AgentSwarmCardProps {
  label: string;
  title: string;
  color: string;
  description: string;
  completed: boolean;
}

/** A single agent summary card in the completed-state Agent Swarm. */
export const AgentSwarmCard: React.FC<AgentSwarmCardProps> = ({
  label,
  title,
  color,
  description,
  completed,
}) => (
  <div
    style={{
      border: '1px solid var(--border-color)',
      borderRadius: '8px',
      background: 'var(--bg-secondary)',
      padding: '14px 16px',
      marginBottom: '12px',
    }}
  >
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '4px',
            background: color,
            color: '#fff',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </span>
        <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>{title}</span>
      </span>
      {completed && (
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--accent-green)',
            background: 'rgba(63,185,80,0.15)',
            padding: '2px 8px',
            borderRadius: '10px',
          }}
        >
          ✓ Completed
        </span>
      )}
    </div>
    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{description}</div>
  </div>
);
