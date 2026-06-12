import React, { useState, useCallback } from 'react';
import { BottomBar } from './BottomBar';

interface EmptyStateProps {
  onSubmit: (requirement: string) => void;
}

/**
 * Light-themed launch screen. Centered terminal-style prompt input.
 */
export const EmptyState: React.FC<EmptyStateProps> = ({ onSubmit }) => {
  const [value, setValue] = useState('');

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue('');
  }, [value, onSubmit]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-primary)',
      }}
    >
      {/* Centered input */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            width: '100%',
            maxWidth: '720px',
            padding: '14px 18px',
            border: '1px solid var(--accent-blue)',
            borderRadius: '8px',
            background: 'var(--bg-primary)',
            boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          }}
        >
          <span
            style={{
              color: 'var(--accent-blue)',
              fontFamily: 'var(--font-mono)',
              fontSize: '18px',
              fontWeight: 700,
            }}
          >
            &gt;
          </span>
          <input
            autoFocus
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe what you want to build..."
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              background: 'transparent',
              fontSize: '16px',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
          />
        </div>

        <div
          style={{
            marginTop: '16px',
            fontSize: '12px',
            color: 'var(--text-secondary)',
          }}
        >
          Press{' '}
          <kbd
            style={{
              padding: '1px 6px',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              background: 'var(--bg-tertiary)',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
            }}
          >
            Enter
          </kbd>{' '}
          to submit · The agent team will plan, architect, code, and review
        </div>
      </div>

      <BottomBar />
    </div>
  );
};
