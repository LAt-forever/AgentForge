import { useCallback, useEffect, useRef } from 'react';
import { Layout } from './components/Layout';
import { FileTree } from './components/FileTree';
import { CodeEditor } from './components/CodeEditor';
import { AgentPanel } from './components/AgentPanel';
import { ChatInput } from './components/ChatInput';
import { useStore } from './store/useStore';
import { useWebSocket } from './hooks/useWebSocket';

export default function App() {
  const { connect } = useWebSocket();

  const projectId = useStore((state) => state.projectId);
  const currentFile = useStore((state) => state.currentFile);
  const setFileContent = useStore((state) => state.setFileContent);
  const setFiles = useStore((state) => state.setFiles);
  const setProjectId = useStore((state) => state.setProjectId);
  const setProject = useStore((state) => state.setProject);
  const setRunning = useStore((state) => state.setRunning);
  const reset = useStore((state) => state.reset);

  const filePollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Handle submit: create project and start workflow
  const handleSubmit = useCallback(
    async (requirement: string) => {
      reset();
      setRunning(true);

      try {
        const res = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ requirement }),
        });

        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = (await res.json()) as {
          project_id: string;
          state: string;
          agent_statuses: Record<string, unknown>;
          iteration_count: number;
          outputs: Record<string, string>;
        };

        setProjectId(data.project_id);
        setProject({
          project_id: data.project_id,
          state: data.state,
          agent_statuses: data.agent_statuses,
          iteration_count: data.iteration_count,
          outputs: data.outputs,
        });

        // Connect WebSocket after project is created
        // Need a small delay to ensure projectId is set in the ref
        setTimeout(() => {
          connect();
        }, 0);
      } catch (err) {
        console.error('Failed to create project:', err);
        setRunning(false);
      }
    },
    [reset, setRunning, setProjectId, setProject, connect]
  );

  // Effect: fetch file content when currentFile changes
  useEffect(() => {
    if (!projectId || !currentFile) return;

    fetch(`/api/projects/${projectId}/files/${currentFile}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.text();
      })
      .then((content) => {
        setFileContent(content);
      })
      .catch((err) => {
        console.error('Failed to fetch file content:', err);
        setFileContent('');
      });
  }, [projectId, currentFile, setFileContent]);

  // Effect: poll file list every 2s when projectId exists
  useEffect(() => {
    if (!projectId) {
      if (filePollRef.current) {
        clearInterval(filePollRef.current);
        filePollRef.current = null;
      }
      return;
    }

    const pollFiles = async () => {
      try {
        const res = await fetch(`/api/projects/${projectId}/files`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const files = (await res.json()) as string[];
        setFiles(files);
      } catch (err) {
        console.error('Failed to poll files:', err);
      }
    };

    // Poll immediately
    pollFiles();

    // Then every 2 seconds
    filePollRef.current = setInterval(pollFiles, 2000);

    return () => {
      if (filePollRef.current) {
        clearInterval(filePollRef.current);
        filePollRef.current = null;
      }
    };
  }, [projectId, setFiles]);

  // Sidebar content: FileTree + ChatInput
  const sidebar = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <FileTree />
      </div>
      <ChatInput onSubmit={handleSubmit} />
    </div>
  );

  return (
    <Layout
      sidebar={sidebar}
      editor={<CodeEditor />}
      agentPanel={<AgentPanel />}
    />
  );
}
