import React, { useEffect, useState } from 'react';

/**
 * Bottom status bar for the empty state: current model + keyboard shortcuts.
 */
export const BottomBar: React.FC = () => {
  const [model, setModel] = useState<string>('—');

  useEffect(() => {
    fetch('/api/settings')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.settings?.default_model) setModel(data.settings.default_model);
      })
      .catch(() => {});
  }, []);

  return (
    <div
      style={{
        height: '32px',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        color: 'var(--text-muted)',
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span>🖥️</span>
        {model}
      </span>
      <span>⌘K settings · ⌘N new project</span>
    </div>
  );
};
