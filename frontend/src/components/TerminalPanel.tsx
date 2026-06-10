import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';

const STREAM_COLORS: Record<string, string> = {
  stdout: '#d4d4d4',
  stderr: '#f48771',
  agent: '#6a9955',
};

export function TerminalPanel() {
  const terminalLines = useStore((state) => state.terminalLines);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLines]);

  return (
    <div
      style={{
        height: '100%',
        overflow: 'auto',
        background: '#1e1e1e',
        color: '#d4d4d4',
        fontFamily: 'monospace',
        fontSize: 12,
        padding: 8,
        whiteSpace: 'pre-wrap',
      }}
    >
      {terminalLines.length === 0 ? (
        <div style={{ color: '#666' }}>No output yet.</div>
      ) : (
        terminalLines.map((line, i) => (
          <span key={i} style={{ color: STREAM_COLORS[line.stream] ?? '#d4d4d4' }}>
            {line.content}
          </span>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
