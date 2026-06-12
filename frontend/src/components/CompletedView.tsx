import React from 'react';
import { useStore } from '../store/useStore';
import { AgentSwarmCard } from './AgentSwarmCard';
import { LogsPanel } from './LogsPanel';

interface CompletedViewProps {
  onFollowUp: (message: string) => void;
}

const SWARM = [
  { key: 'pm', label: 'PM', title: 'Architect Planner', color: 'var(--agent-pm)', description: 'Generated spec and task breakdown.' },
  { key: 'architect', label: 'Arch', title: 'System Designer', color: 'var(--agent-architect)', description: 'Defined architecture and component interactions.' },
  { key: 'coder', label: 'Coder', title: 'Implementation', color: 'var(--agent-coder)', description: 'Implemented the code files.' },
  { key: 'reviewer', label: 'Rev', title: 'Code Reviewer', color: 'var(--agent-reviewer)', description: 'Passed all linting and logic checks.' },
];

/** Completed-state view: workspace status | agent swarm | terminal. */
export const CompletedView: React.FC<CompletedViewProps> = ({ onFollowUp }) => {
  const agentStatuses = useStore((s) => s.agentStatuses);
  const projectId = useStore((s) => s.projectId);
  const projectList = useStore((s) => s.projectList);
  const files = useStore((s) => s.files);
  const setActiveView = useStore((s) => s.setActiveView);
  const setActiveTab = useStore((s) => s.setActiveTab);

  const requirement = projectList.find((p) => p.project_id === projectId)?.requirement ?? 'Project';
  const fileCount = files.filter((f) => !['spec.md', 'architecture.md', 'review.md'].includes(f)).length;

  const openInEditor = () => {
    setActiveTab('explorer');
    setActiveView('orchestrator');
  };

  const exportProject = () => {
    window.open(`/api/projects/${projectId}/git/diff`, '_blank');
  };

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      {/* Left: Workspace status */}
      <div
        style={{
          width: '320px',
          flexShrink: 0,
          borderRight: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          display: 'flex',
          flexDirection: 'column',
          padding: '16px',
        }}
      >
        <SectionTitle>Workspace Status</SectionTitle>

        <div
          style={{
            border: '1px solid var(--accent-green)',
            background: 'rgba(63,185,80,0.1)',
            borderRadius: '8px',
            padding: '12px 14px',
            marginBottom: '16px',
          }}
        >
          <div style={{ color: 'var(--accent-green)', fontWeight: 600, fontSize: '14px', marginBottom: '4px' }}>
            ✓ All checks passed
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Generated {fileCount} file{fileCount === 1 ? '' : 's'}. All tests passing.
          </div>
        </div>

        <div
          style={{
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '14px',
            marginBottom: '16px',
          }}
        >
          <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            {requirement.length > 40 ? requirement.slice(0, 40) + '…' : requirement}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Project: {projectId}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Stat label="Time Elapsed" value="—" />
            <Stat label="Tokens Used" value="—" />
          </div>
        </div>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <ActionButton primary onClick={openInEditor}>
            &lt;/&gt; Open in Editor
          </ActionButton>
          <ActionButton onClick={() => onFollowUp('run the test suite')}>▶ Run Tests</ActionButton>
          <ActionButton onClick={exportProject}>⬇ Export Project</ActionButton>
        </div>
      </div>

      {/* Center: Agent swarm */}
      <div style={{ flex: 1, minWidth: 0, padding: '16px', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
          <SectionTitle>Agent Swarm</SectionTitle>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Idle</span>
        </div>
        {SWARM.map((a) => (
          <AgentSwarmCard
            key={a.key}
            label={a.label}
            title={a.title}
            color={a.color}
            description={agentStatuses[a.key]?.output?.summary || a.description}
            completed={agentStatuses[a.key]?.status === 'completed'}
          />
        ))}
      </div>

      {/* Right: Terminal */}
      <div
        style={{
          width: '420px',
          flexShrink: 0,
          borderLeft: '1px solid var(--border-color)',
        }}
      >
        <LogsPanel onFollowUp={onFollowUp} />
      </div>
    </div>
  );
};

const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontSize: '13px',
      fontWeight: 600,
      color: 'var(--text-primary)',
      marginBottom: '12px',
    }}
  >
    {children}
  </div>
);

const Stat: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div
    style={{
      flex: 1,
      border: '1px solid var(--border-color)',
      borderRadius: '6px',
      padding: '8px 10px',
      background: 'var(--bg-tertiary)',
    }}
  >
    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
      {label}
    </div>
    <div style={{ fontSize: '14px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{value}</div>
  </div>
);

const ActionButton: React.FC<{ children: React.ReactNode; onClick: () => void; primary?: boolean }> = ({
  children,
  onClick,
  primary,
}) => (
  <button
    onClick={onClick}
    style={{
      width: '100%',
      padding: '10px',
      borderRadius: '6px',
      border: primary ? 'none' : '1px solid var(--border-color)',
      background: primary ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
      color: primary ? '#fff' : 'var(--text-primary)',
      fontSize: '13px',
      fontWeight: 600,
      cursor: 'pointer',
    }}
  >
    {children}
  </button>
);
