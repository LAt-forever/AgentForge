import React from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { oneDark } from '@codemirror/theme-one-dark';
import { useStore } from '../store/useStore';

function getLanguageExtension(filename: string | null) {
  if (!filename) return [];
  if (filename.endsWith('.py')) return [python()];
  if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx') || filename.endsWith('.jsx')) {
    return [javascript({ jsx: filename.endsWith('.jsx') || filename.endsWith('.tsx'), typescript: filename.endsWith('.ts') || filename.endsWith('.tsx') })];
  }
  return [];
}

export const CodeEditor: React.FC = () => {
  const currentFile = useStore((state) => state.currentFile);
  const fileContent = useStore((state) => state.fileContent);

  if (!currentFile) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: 'var(--text-muted)',
          fontSize: '14px',
        }}
      >
        Select a file to view its contents
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 12px',
          height: '36px',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: '4px 12px',
            fontSize: '13px',
            fontFamily: 'var(--font-mono)',
            background: 'var(--bg-primary)',
            borderTop: '2px solid var(--accent-blue)',
            borderRadius: '0 0 4px 4px',
            color: 'var(--text-primary)',
          }}
        >
          {currentFile}
        </div>
      </div>

      {/* CodeMirror */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <CodeMirror
          value={fileContent}
          theme={oneDark}
          editable={false}
          height="100%"
          extensions={getLanguageExtension(currentFile)}
          basicSetup={{
            lineNumbers: true,
            highlightActiveLineGutter: true,
            highlightActiveLine: true,
            foldGutter: false,
          }}
        />
      </div>
    </div>
  );
};
