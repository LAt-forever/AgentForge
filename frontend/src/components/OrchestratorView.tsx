import React from 'react';
import { useStore } from '../store/useStore';
import { FileTreePanel } from './FileTreePanel';
import { AgentStatusList } from './AgentStatusList';
import { AgentWorkspace } from './AgentWorkspace';
import { LogsPanel } from './LogsPanel';
import { CodeEditor } from './CodeEditor';
import { ProjectHistory } from './ProjectHistory';

interface OrchestratorViewProps {
  onFollowUp: (message: string) => void;
  onSelectProject: (id: string) => void;
}

/**
 * Running-state view: 3 columns (file tree | workspace | agents) + bottom logs.
 * The center panel content depends on the active tab.
 */
export const OrchestratorView: React.FC<OrchestratorViewProps> = ({ onFollowUp, onSelectProject }) => {
  const activeTab = useStore((s) => s.activeTab);
  const currentFile = useStore((s) => s.currentFile);
  const setSelectedDiffFile = useStore((s) => s.setSelectedDiffFile);
  const setActiveView = useStore((s) => s.setActiveView);

  const openDiff = () => {
    if (currentFile) {
      setSelectedDiffFile(currentFile);
      setActiveView('diff');
    }
  };

  let center: React.ReactNode;
  if (activeTab === 'explorer') {
    center = (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {currentFile && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              padding: '4px 8px',
              borderBottom: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
            }}
          >
            <button
              onClick={openDiff}
              style={{
                fontSize: '11px',
                padding: '4px 10px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-tertiary)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              View Diff
            </button>
          </div>
        )}
        <div style={{ flex: 1, minHeight: 0 }}>
          <CodeEditor />
        </div>
      </div>
    );
  } else if (activeTab === 'logs') {
    center = <LogsPanel onFollowUp={onFollowUp} />;
  } else {
    center = <AgentWorkspace />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* Left: file tree + project history */}
        <div
          style={{
            width: '240px',
            flexShrink: 0,
            borderRight: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-secondary)',
          }}
        >
          <div style={{ flex: 1, minHeight: 0 }}>
            <FileTreePanel />
          </div>
          <ProjectHistory onSelect={onSelectProject} />
        </div>

        {/* Center */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>{center}</div>

        {/* Right: agents */}
        <div
          style={{
            width: '300px',
            flexShrink: 0,
            borderLeft: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
          }}
        >
          <AgentStatusList />
        </div>
      </div>

      {/* Bottom logs (hidden when center already shows logs) */}
      {activeTab !== 'logs' && (
        <div
          style={{
            height: '200px',
            flexShrink: 0,
            borderTop: '1px solid var(--border-color)',
          }}
        >
          <LogsPanel onFollowUp={onFollowUp} />
        </div>
      )}
    </div>
  );
};
