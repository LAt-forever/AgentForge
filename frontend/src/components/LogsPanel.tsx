import React, { useEffect, useRef, useState } from 'react';
import { useStore } from '../store/useStore';

interface LogsPanelProps {
  onFollowUp: (message: string) => void;
}

const STREAM_COLORS: Record<string, string> = {
  stdout: 'var(--text-primary)',
  stderr: 'var(--accent-red)',
  agent: 'var(--accent-green)',
};

const SEVERITY_COLORS: Record<string, string> = {
  error: 'var(--accent-red)',
  warning: 'var(--accent-yellow)',
  suggestion: 'var(--accent-blue)',
};

/** Bottom panel: TERMINAL / PROBLEMS tabs + a follow-up input. */
export const LogsPanel: React.FC<LogsPanelProps> = ({ onFollowUp }) => {
  const terminalLines = useStore((s) => s.terminalLines);
  const problems = useStore((s) => s.problems);
  const activeLogTab = useStore((s) => s.activeLogTab);
  const setActiveLogTab = useStore((s) => s.setActiveLogTab);
  const isConnected = useStore((s) => s.isConnected);
  const isRunning = useStore((s) => s.isRunning);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (activeLogTab === 'terminal') {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLines, activeLogTab]);

  const submit = () => {
    const trimmed = input.trim();
    if (!trimmed || isRunning) return;
    onFollowUp(trimmed);
    setInput('');
  };

  const tabStyle = (active: boolean): React.CSSProperties => ({
    padding: '6px 12px',
    fontSize: '11px',
    fontWeight: 600,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
    cursor: 'pointer',
    color: active ? 'var(--text-primary)' : 'var(--text-muted)',
    borderBottom: active ? '2px solid var(--accent-blue)' : '2px solid transparent',
    background: 'none',
    border: 'none',
  });

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          flexShrink: 0,
        }}
      >
        <button style={tabStyle(activeLogTab === 'terminal')} onClick={() => setActiveLogTab('terminal')}>
          Terminal
        </button>
        <button style={tabStyle(activeLogTab === 'problems')} onClick={() => setActiveLogTab('problems')}>
          Problems{problems.length > 0 ? ` (${problems.length})` : ''}
        </button>
      </div>

      {/* Content */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
        }}
      >
        {activeLogTab === 'terminal' ? (
          terminalLines.length === 0 ? (
            <div style={{ color: 'var(--text-muted)' }}>No output yet.</div>
          ) : (
            <div style={{ whiteSpace: 'pre-wrap' }}>
              {terminalLines.map((line, i) => (
                <span key={i} style={{ color: STREAM_COLORS[line.stream] ?? 'var(--text-primary)' }}>
                  {line.content}
                </span>
              ))}
              <div ref={bottomRef} />
            </div>
          )
        ) : problems.length === 0 ? (
          <div style={{ color: 'var(--text-muted)' }}>No problems detected.</div>
        ) : (
          problems.map((p, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: '8px',
                padding: '4px 0',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              <span style={{ color: SEVERITY_COLORS[p.severity] ?? 'var(--text-muted)', fontWeight: 600 }}>
                {p.severity}
              </span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {p.file}
                {p.line ? `:${p.line}` : ''}
              </span>
              <span style={{ color: 'var(--text-primary)', flex: 1 }}>{p.message}</span>
            </div>
          ))
        )}
      </div>

      {/* Follow-up input */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px',
          borderTop: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          flexShrink: 0,
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask agents to modify code, run commands, or explain..."
          disabled={isRunning || !isConnected}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-tertiary)',
            color: 'var(--text-primary)',
            fontSize: '13px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />
        <button
          onClick={submit}
          disabled={isRunning || !input.trim()}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '4px',
            border: 'none',
            background: isRunning || !input.trim() ? 'var(--bg-tertiary)' : 'var(--accent-green)',
            color: '#fff',
            cursor: isRunning || !input.trim() ? 'not-allowed' : 'pointer',
            fontSize: '16px',
          }}
        >
          ➤
        </button>
      </div>
    </div>
  );
};
