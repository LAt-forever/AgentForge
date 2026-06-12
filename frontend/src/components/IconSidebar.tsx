import React from 'react';
import { useStore } from '../store/useStore';
import type { ActiveTab } from '../store/useStore';

interface IconItem {
  icon: string;
  title: string;
  tab?: ActiveTab;
  action?: 'settings';
}

const ITEMS: IconItem[] = [
  { icon: '📁', title: 'Explorer', tab: 'explorer' },
  { icon: '🤖', title: 'Orchestrator', tab: 'orchestrator' },
  { icon: '📋', title: 'Logs', tab: 'logs' },
  { icon: '⚙️', title: 'Settings', action: 'settings' },
];

/**
 * Narrow icon-only sidebar on the far left. Visible in dark (working) views,
 * hidden in the empty state.
 */
export const IconSidebar: React.FC = () => {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const setActiveView = useStore((s) => s.setActiveView);
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);

  const handleClick = (item: IconItem) => {
    if (item.action === 'settings') {
      setSettingsOpen(true);
    } else if (item.tab) {
      setActiveTab(item.tab);
      setActiveView('orchestrator');
    }
  };

  return (
    <div
      style={{
        width: 'var(--icon-sidebar-width)',
        flexShrink: 0,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: '12px',
        gap: '4px',
      }}
    >
      {ITEMS.map((item) => {
        const active = item.tab && item.tab === activeTab;
        return (
          <button
            key={item.title}
            onClick={() => handleClick(item)}
            title={item.title}
            style={{
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: active ? 'var(--bg-hover)' : 'none',
              border: 'none',
              borderLeft: active
                ? '2px solid var(--accent-blue)'
                : '2px solid transparent',
              cursor: 'pointer',
              fontSize: '18px',
              borderRadius: '4px',
              opacity: active ? 1 : 0.7,
            }}
          >
            {item.icon}
          </button>
        );
      })}
    </div>
  );
};
