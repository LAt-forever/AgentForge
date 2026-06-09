import React from 'react';

interface LayoutProps {
  sidebar: React.ReactNode;
  editor: React.ReactNode;
  agentPanel: React.ReactNode;
}

const headerStyle: React.CSSProperties = {
  height: '48px',
  borderBottom: '1px solid var(--border-color)',
  background: 'var(--bg-secondary)',
  padding: '0 16px',
  display: 'flex',
  alignItems: 'center',
  fontSize: '14px',
  fontWeight: 600,
  flexShrink: 0,
};

const contentStyle: React.CSSProperties = {
  flex: 1,
  overflow: 'auto',
};

export const Layout: React.FC<LayoutProps> = ({ sidebar, editor, agentPanel }) => {
  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        background: 'var(--bg-primary)',
        overflow: 'hidden',
      }}
    >
      {/* Sidebar (left) */}
      <div
        style={{
          width: '240px',
          minWidth: '200px',
          borderRight: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={headerStyle}>
          <span style={{ color: 'var(--accent-blue)' }}>🤖 DevAgent</span>
        </div>
        <div style={contentStyle}>{sidebar}</div>
      </div>

      {/* Editor (center) */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        <div style={headerStyle}>
          <span style={{ color: 'var(--text-secondary)' }}>Code Editor</span>
        </div>
        <div style={contentStyle}>{editor}</div>
      </div>

      {/* AgentPanel (right) */}
      <div
        style={{
          width: '360px',
          minWidth: '280px',
          borderLeft: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={headerStyle}>
          <span style={{ color: 'var(--text-secondary)' }}>Agent Workspace</span>
        </div>
        <div style={contentStyle}>{agentPanel}</div>
      </div>
    </div>
  );
};
