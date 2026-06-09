import React from 'react';
import { useStore } from '../store/useStore';

function getFileIcon(filename: string): string {
  if (filename.endsWith('.py')) return '🐍';
  if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx')) return '📜';
  if (filename.endsWith('.json')) return '📋';
  if (filename.endsWith('.md')) return '📝';
  if (filename.endsWith('.html')) return '🌐';
  if (filename.endsWith('.css')) return '🎨';
  return '📄';
}

export const FileTree: React.FC = () => {
  const files = useStore((state) => state.files);
  const currentFile = useStore((state) => state.currentFile);
  const setCurrentFile = useStore((state) => state.setCurrentFile);

  if (files.length === 0) {
    return (
      <div
        style={{
          padding: '16px',
          color: 'var(--text-muted)',
          fontSize: '13px',
        }}
      >
        No files yet
      </div>
    );
  }

  return (
    <div style={{ padding: '4px 0' }}>
      {files.map((file) => {
        const isActive = file === currentFile;
        return (
          <div
            key={file}
            onClick={() => setCurrentFile(file)}
            style={{
              padding: '4px 12px 4px 28px',
              cursor: 'pointer',
              fontSize: '13px',
              fontFamily: 'var(--font-mono)',
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'var(--bg-tertiary)' : 'transparent',
              borderRadius: '4px',
              margin: '0 4px',
              transition: 'background 0.15s ease',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'var(--bg-hover)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            <span style={{ marginRight: '6px' }}>{getFileIcon(file)}</span>
            {file}
          </div>
        );
      })}
    </div>
  );
};
