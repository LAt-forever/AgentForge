import React from 'react';

interface ProgressBarProps {
  progress: number;
  label?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, label }) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div style={{ padding: '12px' }}>
      {/* Label row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <span
          style={{
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
          }}
        >
          {label || 'Overall Progress'}
        </span>
        <span
          style={{
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--accent-blue)',
          }}
        >
          {Math.round(clampedProgress)}%
        </span>
      </div>

      {/* Bar */}
      <div
        style={{
          height: '6px',
          background: 'var(--bg-tertiary)',
          borderRadius: '3px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${clampedProgress}%`,
            background: 'var(--accent-blue)',
            borderRadius: '3px',
            transition: 'width 0.3s ease',
          }}
        />
      </div>
    </div>
  );
};
