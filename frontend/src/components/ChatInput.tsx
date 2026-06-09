import React, { useState, useCallback } from 'react';
import { useStore } from '../store/useStore';

interface ChatInputProps {
  onSubmit: (requirement: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSubmit }) => {
  const [requirement, setRequirement] = useState('');
  const isConnected = useStore((state) => state.isConnected);
  const isRunning = useStore((state) => state.isRunning);

  const handleSubmit = useCallback(() => {
    const trimmed = requirement.trim();
    if (!trimmed || isRunning) return;
    onSubmit(trimmed);
    setRequirement('');
  }, [requirement, isRunning, onSubmit]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const isDisabled = isRunning || !requirement.trim();

  return (
    <div
      style={{
        padding: '12px',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)',
      }}
    >
      {/* Status row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
          fontSize: '12px',
        }}
      >
        <span style={{ color: isConnected ? 'var(--accent-green)' : 'var(--accent-red)' }}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </span>
        {isRunning && (
          <span style={{ color: 'var(--accent-yellow)' }}>Running...</span>
        )}
      </div>

      {/* Textarea */}
      <textarea
        value={requirement}
        onChange={(e) => setRequirement(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe your project requirement... (Cmd+Enter to submit)"
        disabled={isRunning}
        style={{
          width: '100%',
          minHeight: '80px',
          padding: '8px 12px',
          borderRadius: '6px',
          border: '1px solid var(--border-color)',
          background: 'var(--bg-primary)',
          color: 'var(--text-primary)',
          fontSize: '13px',
          fontFamily: 'var(--font-sans)',
          resize: 'vertical',
          outline: 'none',
          marginBottom: '8px',
        }}
      />

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={isDisabled}
        style={{
          width: '100%',
          padding: '8px 16px',
          borderRadius: '6px',
          border: 'none',
          background: isDisabled ? 'var(--bg-tertiary)' : 'var(--accent-green)',
          color: isDisabled ? 'var(--text-muted)' : '#fff',
          fontSize: '13px',
          fontWeight: 600,
          cursor: isDisabled ? 'not-allowed' : 'pointer',
          transition: 'background 0.15s ease',
        }}
      >
        {isRunning ? 'Running...' : 'Start Project'}
      </button>
    </div>
  );
};
