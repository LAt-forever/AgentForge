import React from 'react';
import { useStore } from '../store/useStore';
import { TopNav } from './TopNav';
import { IconSidebar } from './IconSidebar';
import { SettingsPanel } from './SettingsPanel';

interface LayoutProps {
  children: React.ReactNode;
}

/**
 * Thin application shell: theme root + top nav + (optional) icon sidebar +
 * content slot + settings drawer. Each view defines its own internal layout.
 */
export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useStore((s) => s.theme);
  const activeView = useStore((s) => s.activeView);
  const showIconSidebar = activeView !== 'empty';

  return (
    <div
      className={`theme-${theme}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        background: 'var(--bg-primary)',
        color: 'var(--text-primary)',
        overflow: 'hidden',
      }}
    >
      <TopNav />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {showIconSidebar && <IconSidebar />}
        <main style={{ flex: 1, overflow: 'hidden', minWidth: 0 }}>{children}</main>
      </div>
      <SettingsPanel />
    </div>
  );
};
