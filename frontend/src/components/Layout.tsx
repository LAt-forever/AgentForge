import React from 'react';
import { useStore } from '../store/useStore';
import { SettingsPanel } from './SettingsPanel';

interface LayoutProps {
  sidebar: React.ReactNode;
  editor: React.ReactNode;
  agentPanel: React.ReactNode;
  terminal?: React.ReactNode;
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

export const Layout: React.FC<LayoutProps> = ({ sidebar, editor, agentPanel, terminal }) => {
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
        <div style={{ ...headerStyle, justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--accent-blue)' }}>🤖 DevAgent</span>
          <button
            onClick={() => useStore.getState().setSettingsOpen(true)}
            style={{ cursor: 'pointer', background: 'none', border: 'none', fontSize: 16 }}
            title="Settings"
          >
            ⚙️
          </button>
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
        {terminal && (
          <div
            style={{
              height: '180px',
              flexShrink: 0,
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div style={{ ...headerStyle, height: '32px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Terminal</span>
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>{terminal}</div>
          </div>
        )}
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

      <SettingsPanel />
    </div>
  );
};
