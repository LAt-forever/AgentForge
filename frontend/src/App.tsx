import { useCallback, useEffect, useRef } from 'react';
import { Layout } from './components/Layout';
import { FileTree } from './components/FileTree';
import { CodeEditor } from './components/CodeEditor';
import { AgentPanel } from './components/AgentPanel';
import { ChatInput } from './components/ChatInput';
import { TerminalPanel } from './components/TerminalPanel';
import { ProjectHistory } from './components/ProjectHistory';
import { useStore, getSavedProjectId } from './store/useStore';
import { useWebSocket } from './hooks/useWebSocket';

export default function App() {
  const { connect } = useWebSocket();

  const projectId = useStore((state) => state.projectId);

  // Restore project from localStorage on mount
  useEffect(() => {
    const savedId = getSavedProjectId();
    if (savedId && !projectId) {
      setProjectId(savedId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const currentFile = useStore((state) => state.currentFile);
  const setFileContent = useStore((state) => state.setFileContent);
  const setFiles = useStore((state) => state.setFiles);
  const setProjectId = useStore((state) => state.setProjectId);
  const setProject = useStore((state) => state.setProject);
  const setRunning = useStore((state) => state.setRunning);
  const setProjectList = useStore((state) => state.setProjectList);
  const clearTerminal = useStore((state) => state.clearTerminal);
  const reset = useStore((state) => state.reset);

  const filePollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Handle submit: create project and start workflow
  const handleSubmit = useCallback(
    async (requirement: string) => {
      console.log('[App] handleSubmit called with:', requirement);
      reset();
      setRunning(true);

      try {
        console.log('[App] fetching /api/projects...');
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

  // Effect: fetch project list on mount and when active project changes
  useEffect(() => {
    fetch('/api/projects')
      .then((res) => (res.ok ? res.json() : { projects: [] }))
      .then((data) => setProjectList(data.projects ?? []))
      .catch((err) => console.error('Failed to fetch project list:', err));
  }, [projectId, setProjectList]);

  // Handle switching to a different project from the history list
  const handleSelectProject = useCallback(
    (id: string) => {
      if (id === projectId) return;
      clearTerminal();
      setProjectId(id);
      setTimeout(() => connect(), 0);
      fetch(`/api/projects/${id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setProject({
              project_id: data.project_id,
              state: data.state,
              agent_statuses: data.agent_statuses || {},
              iteration_count: data.iteration_count || 0,
              outputs: data.outputs || {},
            });
            setRunning(data.state !== 'done');
          }
        })
        .catch((err) => console.error('Failed to load project:', err));
    },
    [projectId, clearTerminal, setProjectId, connect, setProject, setRunning]
  );

  // Effect: fetch file content when currentFile changes
  useEffect(() => {
    if (!projectId || !currentFile) return;
    fetch(`/api/projects/${projectId}/files/${currentFile}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json() as Promise<{ content: string }>;
      })
      .then((data) => {
        setFileContent(data.content);
      })
      .catch((err) => {
        console.error('Failed to fetch file content:', err);
        setFileContent('');
      });
  }, [projectId, currentFile, setFileContent]);

  // Effect: on mount, if projectId exists (from localStorage restore), reconnect and fetch files
  useEffect(() => {
    if (!projectId) return;

    // Reconnect WebSocket
    setTimeout(() => {
      connect();
    }, 100);

    // Fetch project status
    fetch(`/api/projects/${projectId}`)
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data) => {
        if (data) {
          setProject({
            project_id: data.project_id,
            state: data.state,
            agent_statuses: data.agent_statuses || {},
            iteration_count: data.iteration_count || 0,
            outputs: data.outputs || {},
          });
          if (data.state === 'done') {
            setRunning(false);
          }
        }
      })
      .catch((err) => {
        console.error('Failed to fetch project status:', err);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only on mount

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
        const data = await res.json() as { files: string[] };
        setFiles(data.files);
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
      <ProjectHistory onSelect={handleSelectProject} />
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
      terminal={<TerminalPanel />}
    />
  );
}
