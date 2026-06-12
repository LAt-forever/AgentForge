import React from 'react';
import { useStore } from '../store/useStore';

/**
 * Terminal-style central workspace: renders the user requirement and the
 * agents' outputs (thinking, plan, generated files) as stacked blocks.
 */
export const AgentWorkspace: React.FC = () => {
  const currentProject = useStore((s) => s.currentProject);
  const agentStatuses = useStore((s) => s.agentStatuses);
  const projectList = useStore((s) => s.projectList);
  const projectId = useStore((s) => s.projectId);
  const isRunning = useStore((s) => s.isRunning);

  const outputs = currentProject?.outputs ?? {};
  const requirement =
    projectList.find((p) => p.project_id === projectId)?.requirement ?? '';

  const runningAgent = Object.values(agentStatuses).find((a) => a.status === 'running');

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '16px 20px' }}>
      {/* User requirement */}
      {requirement && (
        <Block icon="👤">
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '12px 16px',
              background: 'var(--bg-secondary)',
            }}
          >
            <span style={{ color: 'var(--accent-green)', marginRight: '6px' }}>&gt;</span>
            {requirement}
          </div>
        </Block>
      )}

      {/* Thinking indicator */}
      {isRunning && runningAgent && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '16px 0', color: 'var(--accent-yellow)' }}>
          <span style={{ fontSize: '16px' }}>✻</span>
          <span style={{ fontSize: '14px', fontWeight: 600 }}>
            {runningAgent.output?.summary || `${runningAgent.agent} thinking...`}
          </span>
        </div>
      )}

      {/* PM Plan */}
      {outputs.pm && (
        <Block icon="📋">
          <OutputCard label="PM Agent" color="var(--agent-pm)" title="Plan" content={outputs.pm} />
        </Block>
      )}

      {/* Architecture */}
      {outputs.architect && (
        <Block icon="🏗️">
          <OutputCard
            label="Architect"
            color="var(--agent-architect)"
            title="Architecture"
            content={outputs.architect}
          />
        </Block>
      )}

      {/* Generated code */}
      {outputs.coder && (
        <Block icon="</>">
          <CodeCard content={outputs.coder} />
        </Block>
      )}

      {!requirement && !outputs.pm && (
        <div style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '24px 0' }}>
          Waiting for the agent team to start...
        </div>
      )}
    </div>
  );
};

const Block: React.FC<{ icon: string; children: React.ReactNode }> = ({ icon, children }) => (
  <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
    <div
      style={{
        width: '28px',
        height: '28px',
        borderRadius: '6px',
        background: 'var(--bg-tertiary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '13px',
        flexShrink: 0,
      }}
    >
      {icon}
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
  </div>
);

const OutputCard: React.FC<{ label: string; color: string; title: string; content: string }> = ({
  label,
  color,
  title,
  content,
}) => (
  <div
    style={{
      border: '1px solid var(--border-color)',
      borderRadius: '6px',
      background: 'var(--bg-secondary)',
      overflow: 'hidden',
    }}
  >
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        borderBottom: '1px solid var(--border-color)',
      }}
    >
      <span
        style={{
          fontSize: '10px',
          fontWeight: 700,
          padding: '2px 6px',
          borderRadius: '4px',
          background: color,
          color: '#fff',
          textTransform: 'uppercase',
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{title}</span>
    </div>
    <pre
      style={{
        margin: 0,
        padding: '12px 16px',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        lineHeight: 1.6,
        color: 'var(--text-secondary)',
        whiteSpace: 'pre-wrap',
        maxHeight: '320px',
        overflow: 'auto',
      }}
    >
      {content}
    </pre>
  </div>
);

const CodeCard: React.FC<{ content: string }> = ({ content }) => (
  <div
    style={{
      border: '1px solid var(--accent-green)',
      borderRadius: '6px',
      background: 'var(--bg-secondary)',
      overflow: 'hidden',
    }}
  >
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '8px 12px',
        borderBottom: '1px solid var(--border-color)',
        color: 'var(--accent-green)',
        fontSize: '13px',
        fontWeight: 600,
      }}
    >
      <span>⊕ Code generated</span>
    </div>
    <pre
      style={{
        margin: 0,
        padding: '12px 16px',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        lineHeight: 1.6,
        color: 'var(--text-primary)',
        whiteSpace: 'pre-wrap',
        maxHeight: '360px',
        overflow: 'auto',
      }}
    >
      {content}
    </pre>
  </div>
);
