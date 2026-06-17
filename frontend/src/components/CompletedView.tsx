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
  const currentProject = useStore((s) => s.currentProject);
  const files = useStore((s) => s.files);
  const setActiveView = useStore((s) => s.setActiveView);
  const setActiveTab = useStore((s) => s.setActiveTab);

  const requirement = projectList.find((p) => p.project_id === projectId)?.requirement ?? 'Project';
  const fileCount = files.filter((f) => !['spec.md', 'architecture.md', 'review.md'].includes(f)).length;
  const isWebApp = currentProject?.workflow_profile === 'static_web';
  const artifactStatus = currentProject?.artifact_status;
  const previewReady = artifactStatus?.status === 'ready' && Boolean(artifactStatus.preview_url);
  const successTitle = isWebApp
    ? previewReady
      ? '✓ Preview ready'
      : 'Preview not ready'
    : '✓ All checks passed';
  const successDescription = isWebApp
    ? previewReady
      ? `Static web app validated. Generated ${fileCount} file${fileCount === 1 ? '' : 's'}.`
      : `Static web app generated, but preview status is ${artifactStatus?.status ?? 'unknown'}.`
    : `Generated ${fileCount} file${fileCount === 1 ? '' : 's'}. All tests passing.`;

  const openInEditor = () => {
    setActiveTab('explorer');
    setActiveView('orchestrator');
  };

  const previewApp = () => {
    if (artifactStatus?.preview_url) {
      window.open(artifactStatus.preview_url, '_blank', 'noopener,noreferrer');
    }
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
            {successTitle}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {successDescription}
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
            <Stat label="Mode" value={isWebApp ? 'Web App' : 'Default'} />
            <Stat label="Time Elapsed" value="—" />
            <Stat label="Tokens Used" value="—" />
          </div>
        </div>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {isWebApp && (
            <ActionButton primary={previewReady} disabled={!previewReady} onClick={previewApp}>
              ▶ Preview App
            </ActionButton>
          )}
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

const ActionButton: React.FC<{ children: React.ReactNode; onClick: () => void; primary?: boolean; disabled?: boolean }> = ({
  children,
  onClick,
  primary,
  disabled,
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      width: '100%',
      padding: '10px',
      borderRadius: '6px',
      border: primary && !disabled ? 'none' : '1px solid var(--border-color)',
      background: disabled
        ? 'var(--bg-secondary)'
        : primary
          ? 'var(--accent-blue)'
          : 'var(--bg-tertiary)',
      color: disabled ? 'var(--text-muted)' : primary ? '#fff' : 'var(--text-primary)',
      fontSize: '13px',
      fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.65 : 1,
    }}
  >
    {children}
  </button>
);
