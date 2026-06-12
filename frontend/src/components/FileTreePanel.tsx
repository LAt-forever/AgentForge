import React, { useMemo, useState } from 'react';
import { useStore } from '../store/useStore';

function getFileIcon(filename: string): string {
  if (filename.endsWith('.py')) return '🐍';
  if (filename.endsWith('.tsx') || filename.endsWith('.ts')) return '📘';
  if (filename.endsWith('.js') || filename.endsWith('.jsx')) return '📙';
  if (filename.endsWith('.json')) return '📋';
  if (filename.endsWith('.md')) return '📝';
  if (filename.endsWith('.html')) return '🌐';
  if (filename.endsWith('.css')) return '🎨';
  return '📄';
}

interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: TreeNode[];
}

/** Build a nested tree from flat relative paths. */
function buildTree(files: string[]): TreeNode {
  const root: TreeNode = { name: '', path: '', isDir: true, children: [] };
  for (const file of files) {
    const parts = file.split('/');
    let node = root;
    let accum = '';
    parts.forEach((part, idx) => {
      accum = accum ? `${accum}/${part}` : part;
      const isLast = idx === parts.length - 1;
      let child = node.children.find((c) => c.name === part);
      if (!child) {
        child = { name: part, path: accum, isDir: !isLast, children: [] };
        node.children.push(child);
      }
      node = child;
    });
  }
  // Sort: directories first, then alpha
  const sortRec = (n: TreeNode) => {
    n.children.sort((a, b) => {
      if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    n.children.forEach(sortRec);
  };
  sortRec(root);
  return root;
}

interface RowProps {
  node: TreeNode;
  depth: number;
  touched: Set<string>;
}

const TreeRow: React.FC<RowProps> = ({ node, depth, touched }) => {
  const currentFile = useStore((s) => s.currentFile);
  const setCurrentFile = useStore((s) => s.setCurrentFile);
  const [open, setOpen] = useState(true);

  const isActive = node.path === currentFile;
  const indent = 8 + depth * 14;

  if (node.isDir) {
    return (
      <div>
        <div
          onClick={() => setOpen((o) => !o)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            paddingLeft: indent,
            cursor: 'pointer',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            userSelect: 'none',
          }}
        >
          <span style={{ fontSize: '10px', width: '10px' }}>{open ? '▼' : '▶'}</span>
          <span>📁</span>
          <span>{node.name}</span>
        </div>
        {open && node.children.map((c) => (
          <TreeRow key={c.path} node={c} depth={depth + 1} touched={touched} />
        ))}
      </div>
    );
  }

  const isTouched = touched.has(node.path);
  return (
    <div
      onClick={() => setCurrentFile(node.path)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 8px',
        paddingLeft: indent + 14,
        cursor: 'pointer',
        fontSize: '13px',
        fontFamily: 'var(--font-mono)',
        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
        background: isActive ? 'var(--bg-hover)' : 'transparent',
        borderLeft: isActive ? '2px solid var(--accent-blue)' : '2px solid transparent',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.background = 'var(--bg-hover)';
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.background = 'transparent';
      }}
    >
      <span>{getFileIcon(node.name)}</span>
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{node.name}</span>
      {isTouched && (
        <span
          className="status-new"
          style={{ width: '6px', height: '6px', borderRadius: '50%', flexShrink: 0 }}
        />
      )}
    </div>
  );
};

/**
 * Hierarchical file tree with folder collapse and status dots for files
 * touched by the agents.
 */
export const FileTreePanel: React.FC = () => {
  const files = useStore((s) => s.files);
  const agentStatuses = useStore((s) => s.agentStatuses);

  const tree = useMemo(() => buildTree(files), [files]);

  // Files mentioned in any agent output are considered "touched".
  const touched = useMemo(() => {
    const set = new Set<string>();
    Object.values(agentStatuses).forEach((st) => {
      st.output?.files?.forEach((f) => set.add(f));
    });
    return set;
  }, [agentStatuses]);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: '10px 12px',
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          color: 'var(--text-secondary)',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        Explorer
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        {files.length === 0 ? (
          <div style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '13px' }}>
            No files yet
          </div>
        ) : (
          tree.children.map((c) => (
            <TreeRow key={c.path} node={c} depth={0} touched={touched} />
          ))
        )}
      </div>
    </div>
  );
};
