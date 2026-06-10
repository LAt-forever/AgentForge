import { useEffect, useState } from 'react';
import type { GitCommit } from '../types';

interface DiffViewerProps {
  projectId: string;
}

function lineColor(line: string): string {
  if (line.startsWith('+') && !line.startsWith('+++')) return '#2ea043';
  if (line.startsWith('-') && !line.startsWith('---')) return '#f85149';
  if (line.startsWith('@@')) return '#58a6ff';
  return '#8b949e';
}

export function DiffViewer({ projectId }: DiffViewerProps) {
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [diff, setDiff] = useState<string>('');

  useEffect(() => {
    if (!projectId) return;
    fetch(`/api/projects/${projectId}/git/log`)
      .then((r) => (r.ok ? r.json() : { commits: [] }))
      .then((d) => setCommits(d.commits ?? []))
      .catch(() => setCommits([]));
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !selected) return;
    fetch(`/api/projects/${projectId}/git/diff/${selected}`)
      .then((r) => (r.ok ? r.json() : { diff: '' }))
      .then((d) => setDiff(d.diff ?? ''))
      .catch(() => setDiff(''));
  }, [projectId, selected]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontSize: 12 }}>
      <select
        value={selected ?? ''}
        onChange={(e) => setSelected(e.target.value || null)}
        style={{ margin: 8, background: '#2d2d2d', color: '#ddd', border: '1px solid #444' }}
      >
        <option value="">Select a commit…</option>
        {commits.map((c) => (
          <option key={c.hash} value={c.hash}>
            {c.message}
          </option>
        ))}
      </select>
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          fontFamily: 'monospace',
          background: '#0d1117',
          padding: 8,
          whiteSpace: 'pre-wrap',
        }}
      >
        {diff ? (
          diff.split('\n').map((line, i) => (
            <div key={i} style={{ color: lineColor(line) }}>
              {line || ' '}
            </div>
          ))
        ) : (
          <span style={{ color: '#666' }}>No diff selected.</span>
        )}
      </div>
    </div>
  );
}
