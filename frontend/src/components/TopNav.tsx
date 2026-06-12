import React from 'react';
import { useStore } from '../store/useStore';
import type { ActiveView } from '../store/useStore';

const NAV_TABS: { id: ActiveView; label: string }[] = [
  { id: 'orchestrator', label: 'Explorer' },
  { id: 'orchestrator', label: 'Orchestrator' },
  { id: 'completed', label: 'Logs' },
];

/**
 * Top navigation bar: logo + main-view tabs + connection status + settings.
 * In the empty (light) view, only the logo and settings gear are shown.
 */
export const TopNav: React.FC = () => {
  const activeView = useStore((s) => s.activeView);
  const isConnected = useStore((s) => s.isConnected);
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);
  const setActiveView = useStore((s) => s.setActiveView);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const reset = useStore((s) => s.reset);

  const activeTab = useStore((s) => s.activeTab);

  const isEmpty = activeView === 'empty';
  const showTabs = !isEmpty;

  const handleTab = (label: string) => {
    if (label === 'Explorer') {
      setActiveView('orchestrator');
      setActiveTab('explorer');
    } else if (label === 'Orchestrator') {
      setActiveView('orchestrator');
      setActiveTab('orchestrator');
    } else if (label === 'Logs') {
      setActiveView('orchestrator');
      setActiveTab('logs');
    }
  };

  return (
    <div
      style={{
        height: 'var(--topnav-height)',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-color)',
        gap: '24px',
      }}
    >
      {/* Logo */}
      <button
        onClick={() => reset()}
        title="New project"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--accent-blue)',
          fontSize: '16px',
          fontWeight: 700,
          padding: 0,
        }}
      >
        <span style={{ fontSize: '18px' }}>🤖</span>
        devagent
      </button>

      {/* Main view tabs */}
      {showTabs && (
        <div style={{ display: 'flex', gap: '4px', height: '100%' }}>
          {NAV_TABS.map((tab) => {
            const active = activeTab === tab.label.toLowerCase();
            return (
              <button
                key={tab.label}
                onClick={() => handleTab(tab.label)}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: active
                    ? '2px solid var(--accent-blue)'
                    : '2px solid transparent',
                  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: active ? 600 : 400,
                  cursor: 'pointer',
                  padding: '0 8px',
                  height: '100%',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Right side */}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '16px' }}>
        {showTabs && (
          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              padding: '4px 10px',
              borderRadius: '12px',
              background: 'var(--bg-tertiary)',
              color: isConnected ? 'var(--accent-green)' : 'var(--accent-red)',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'currentColor',
              }}
            />
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        )}
        <button
          onClick={() => setSettingsOpen(true)}
          title="Settings"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
            color: 'var(--text-secondary)',
            padding: 0,
          }}
        >
          ⚙️
        </button>
      </div>
    </div>
  );
};
