import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';

interface DiffRow {
  left: string | null;
  right: string | null;
  type: 'context' | 'add' | 'del' | 'change' | 'header';
}

/** Parse a unified git diff into side-by-side rows. */
function parseDiff(diff: string): DiffRow[] {
  const rows: DiffRow[] = [];
  const lines = diff.split('\n');
  let pendingDel: string[] = [];

  const flushDels = () => {
    pendingDel.forEach((l) => rows.push({ left: l, right: null, type: 'del' }));
    pendingDel = [];
  };

  for (const line of lines) {
    if (
      line.startsWith('diff ') ||
      line.startsWith('index ') ||
      line.startsWith('+++') ||
      line.startsWith('---')
    ) {
      continue;
    }
    if (line.startsWith('@@')) {
      flushDels();
      rows.push({ left: line, right: line, type: 'header' });
      continue;
    }
    if (line.startsWith('-')) {
      pendingDel.push(line.slice(1));
    } else if (line.startsWith('+')) {
      const add = line.slice(1);
      if (pendingDel.length > 0) {
        const left = pendingDel.shift() ?? null;
        rows.push({ left, right: add, type: 'change' });
      } else {
        rows.push({ left: null, right: add, type: 'add' });
      }
    } else {
      flushDels();
      const content = line.startsWith(' ') ? line.slice(1) : line;
      rows.push({ left: content, right: content, type: 'context' });
    }
  }
  flushDels();
  return rows;
}

/** Side-by-side diff view with an active-agents panel and action buttons. */
export const DiffView: React.FC = () => {
  const projectId = useStore((s) => s.projectId);
  const selectedDiffFile = useStore((s) => s.selectedDiffFile);
  const setActiveView = useStore((s) => s.setActiveView);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const setCurrentFile = useStore((s) => s.setCurrentFile);

  const [rows, setRows] = useState<DiffRow[]>([]);

  useEffect(() => {
    if (!projectId) return;
    fetch(`/api/projects/${projectId}/git/diff`)
      .then((r) => (r.ok ? r.json() : { diff: '' }))
      .then((d) => setRows(parseDiff(d.diff ?? '')))
      .catch(() => setRows([]));
  }, [projectId]);

  const back = () => setActiveView('orchestrator');

  const editManually = () => {
    if (selectedDiffFile) setCurrentFile(selectedDiffFile);
    setActiveTab('explorer');
    setActiveView('orchestrator');
  };

  const addStats = rows.filter((r) => r.type === 'add').length;
  const delStats = rows.filter((r) => r.type === 'del').length;

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      {/* Left: active agents */}
      <div
        style={{
          width: '240px',
          flexShrink: 0,
          borderRight: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          padding: '12px',
        }}
      >
        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '12px' }}>Active Agents</div>
        <div
          style={{
            border: '1px solid var(--border-color)',
            borderLeft: '3px solid var(--agent-coder)',
            borderRadius: '6px',
            padding: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600 }}>&lt;/&gt; CoderAgent</span>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)' }} />
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Awaiting Review</div>
        </div>
      </div>

      {/* Center: diff */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '10px 16px',
            borderBottom: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
          }}
        >
          <button
            onClick={back}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            ←
          </button>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-primary)' }}>
            📄 {selectedDiffFile ?? 'changes'}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--accent-green)' }}>+{addStats}</span>
          <span style={{ fontSize: '12px', color: 'var(--accent-red)' }}>-{delStats}</span>
        </div>

        {/* Column headers */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
          <ColHeader>Original</ColHeader>
          <ColHeader>Proposed Changes</ColHeader>
        </div>

        {/* Rows */}
        <div style={{ flex: 1, overflow: 'auto', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
          {rows.length === 0 ? (
            <div style={{ padding: '16px', color: 'var(--text-muted)' }}>No pending changes.</div>
          ) : (
            rows.map((row, i) => (
              <div key={i} style={{ display: 'flex' }}>
                <DiffCell content={row.left} side="left" type={row.type} />
                <DiffCell content={row.right} side="right" type={row.type} />
              </div>
            ))
          )}
        </div>

        {/* Action bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px',
            padding: '10px 16px',
            borderTop: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
          }}
        >
          <ActionBtn onClick={editManually}>✎ Edit Manually</ActionBtn>
          <ActionBtn onClick={back} variant="reject">
            ✕ Reject
          </ActionBtn>
          <ActionBtn onClick={back} variant="accept">
            ✓ Accept Changes
          </ActionBtn>
        </div>
      </div>
    </div>
  );
};

const ColHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      flex: 1,
      padding: '8px 16px',
      fontSize: '12px',
      fontWeight: 600,
      textAlign: 'center',
      color: 'var(--text-secondary)',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-color)',
    }}
  >
    {children}
  </div>
);

const DiffCell: React.FC<{ content: string | null; side: 'left' | 'right'; type: DiffRow['type'] }> = ({
  content,
  side,
  type,
}) => {
  let bg = 'transparent';
  if (type === 'header') bg = 'var(--bg-tertiary)';
  else if (side === 'left' && (type === 'del' || type === 'change')) bg = 'var(--diff-del-bg)';
  else if (side === 'right' && (type === 'add' || type === 'change')) bg = 'var(--diff-add-bg)';

  const color = type === 'header' ? 'var(--accent-blue)' : 'var(--text-primary)';

  return (
    <div
      style={{
        flex: 1,
        padding: '1px 16px',
        background: bg,
        borderRight: '1px solid var(--border-color)',
        whiteSpace: 'pre-wrap',
        color,
        minHeight: '18px',
      }}
    >
      {content ?? ''}
    </div>
  );
};

const ActionBtn: React.FC<{
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'accept' | 'reject';
}> = ({ children, onClick, variant }) => {
  const bg =
    variant === 'accept' ? 'var(--accent-green)' : variant === 'reject' ? 'var(--accent-red)' : 'var(--bg-tertiary)';
  const color = variant ? '#fff' : 'var(--text-primary)';
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 16px',
        borderRadius: '6px',
        border: variant ? 'none' : '1px solid var(--border-color)',
        background: bg,
        color,
        fontSize: '13px',
        fontWeight: 600,
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  );
};
