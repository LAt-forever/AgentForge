import { useCallback, useEffect, useRef } from 'react';
import { Layout } from './components/Layout';
import { EmptyState } from './components/EmptyState';
import { OrchestratorView } from './components/OrchestratorView';
import { CompletedView } from './components/CompletedView';
import { DiffView } from './components/DiffView';
import { useStore, getSavedProjectId } from './store/useStore';
import { useWebSocket } from './hooks/useWebSocket';
import type { ArtifactIssue, ArtifactStatus, WorkflowProfileName } from './types';

const DEFAULT_ARTIFACT_STATUS: ArtifactStatus = {
  type: 'none',
  status: 'unknown',
  preview_url: '',
  issues: [],
};

const ARTIFACT_STATUSES: ReadonlySet<ArtifactStatus['status']> = new Set([
  'unknown',
  'not_web_artifact',
  'validating',
  'ready',
  'missing_entry',
  'invalid_refs',
  'syntax_error',
  'unsafe_path',
  'error',
]);

function normalizeArtifactIssue(raw: unknown): ArtifactIssue {
  const value = raw as Partial<ArtifactIssue> | undefined;
  return {
    severity: value?.severity ?? 'error',
    code: value?.code,
    file: value?.file,
    line: typeof value?.line === 'number' ? value.line : undefined,
    message: value?.message ?? '',
    repairable: value?.repairable,
  };
}

function normalizeArtifactStatus(raw: unknown): ArtifactStatus {
  const value = raw as Partial<ArtifactStatus> | undefined;
  const status = value?.status;

  return {
    type: value?.type ?? DEFAULT_ARTIFACT_STATUS.type,
    status: ARTIFACT_STATUSES.has(status as ArtifactStatus['status'])
      ? (status as ArtifactStatus['status'])
      : DEFAULT_ARTIFACT_STATUS.status,
    preview_url: typeof value?.preview_url === 'string' ? value.preview_url : '',
    issues: Array.isArray(value?.issues) ? value.issues.map(normalizeArtifactIssue) : [],
  };
}

function normalizeWorkflowProfile(raw: unknown): WorkflowProfileName {
  return raw === 'static_web' ? 'static_web' : 'default';
}

export default function App() {
  const { connect } = useWebSocket();

  const projectId = useStore((state) => state.projectId);
  const currentFile = useStore((state) => state.currentFile);
  const isRunning = useStore((state) => state.isRunning);
  const workflowState = useStore((state) => state.workflowState);
  const activeView = useStore((state) => state.activeView);
  const currentProject = useStore((state) => state.currentProject);
  const setProblems = useStore((state) => state.setProblems);
  const setAgentStatus = useStore((state) => state.setAgentStatus);

  const setFileContent = useStore((state) => state.setFileContent);
  const setFiles = useStore((state) => state.setFiles);
  const setProjectId = useStore((state) => state.setProjectId);
  const setProject = useStore((state) => state.setProject);
  const setRunning = useStore((state) => state.setRunning);
  const setProjectList = useStore((state) => state.setProjectList);
  const clearTerminal = useStore((state) => state.clearTerminal);
  const setActiveView = useStore((state) => state.setActiveView);
  const setTheme = useStore((state) => state.setTheme);
  const reset = useStore((state) => state.reset);

  const filePollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const hydrateAgentStatuses = useCallback(
    (statuses: Record<string, unknown>) => {
      Object.entries(statuses).forEach(([agent, raw]) => {
        const st = raw as {
          status?: string;
          output?: Record<string, unknown>;
          error?: string;
        };
        setAgentStatus({
          agent,
          status: (st.status as 'idle' | 'running' | 'completed' | 'failed') ?? 'idle',
          progress: 0,
          output: st.output,
          error: st.error,
        });
      });
    },
    [setAgentStatus]
  );

  // Restore project from localStorage on mount
  useEffect(() => {
    const savedId = getSavedProjectId();
    if (savedId && !projectId) {
      setProjectId(savedId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ----- View + theme auto-switching -----
  useEffect(() => {
    if (!projectId) {
      setActiveView('empty');
      return;
    }
    if (activeView === 'diff') return; // diff is user-driven; don't override
    if (!isRunning && workflowState?.state === 'done') {
      setActiveView('completed');
    } else {
      setActiveView('orchestrator');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, isRunning, workflowState?.state]);

  useEffect(() => {
    setTheme(activeView === 'empty' ? 'light' : 'dark');
  }, [activeView, setTheme]);

  // Merge reviewer output and artifact validation issues into the problems list.
  useEffect(() => {
    const nextProblems: Array<{
      severity: string;
      file: string;
      line?: number;
      message: string;
    }> = [];

    const raw = currentProject?.outputs?.reviewer;
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as {
          issues?: Array<{ severity: string; file?: string; line?: number; message: string }>;
        };
        if (Array.isArray(parsed.issues)) {
          nextProblems.push(
            ...parsed.issues.map((it) => ({
              severity: it.severity ?? 'warning',
              file: it.file ?? '',
              line: it.line,
              message: it.message,
            }))
          );
        }
      } catch {
        // Reviewer output not valid JSON — ignore.
      }
    }

    nextProblems.push(
      ...(currentProject?.artifact_status?.issues ?? []).map((issue) => ({
        severity: issue.severity ?? 'error',
        file: issue.file ?? '',
        line: issue.line,
        message: issue.message,
      }))
    );

    setProblems(nextProblems);
  }, [currentProject?.outputs?.reviewer, currentProject?.artifact_status, setProblems]);

  // Handle submit: create project and start workflow
  const handleSubmit = useCallback(
    async (requirement: string) => {
      reset();
      setRunning(true);
      setActiveView('orchestrator');

      try {
        const res = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ requirement }),
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const data = (await res.json()) as {
          project_id: string;
          state: string;
        };

        setProjectId(data.project_id);
        setProject({
          project_id: data.project_id,
          state: data.state,
          agent_statuses: {},
          iteration_count: 0,
          outputs: {},
          workflow_profile: 'default',
          artifact_status: normalizeArtifactStatus(undefined),
        });
        setTimeout(() => connect(), 0);
      } catch (err) {
        console.error('Failed to create project:', err);
        setRunning(false);
      }
    },
    [reset, setRunning, setActiveView, setProjectId, setProject, connect]
  );

  // Handle follow-up: continue iterating on the current project
  const handleFollowUp = useCallback(
    async (message: string) => {
      if (!projectId) return;
      setRunning(true);
      setActiveView('orchestrator');
      try {
        const res = await fetch(`/api/projects/${projectId}/follow_up`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        setTimeout(() => connect(), 0);
      } catch (err) {
        console.error('Failed to send follow-up:', err);
        setRunning(false);
      }
    },
    [projectId, setRunning, setActiveView, connect]
  );

  // Fetch project list on mount and when active project changes
  useEffect(() => {
    fetch('/api/projects')
      .then((res) => (res.ok ? res.json() : { projects: [] }))
      .then((data) => setProjectList(data.projects ?? []))
      .catch((err) => console.error('Failed to fetch project list:', err));
  }, [projectId, setProjectList]);

  // Fetch file content when currentFile changes
  useEffect(() => {
    if (!projectId || !currentFile) return;
    fetch(`/api/projects/${projectId}/files/${currentFile}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json() as Promise<{ content: string }>;
      })
      .then((data) => setFileContent(data.content))
      .catch((err) => {
        console.error('Failed to fetch file content:', err);
        setFileContent('');
      });
  }, [projectId, currentFile, setFileContent]);

  // On mount with restored projectId: reconnect and fetch status
  useEffect(() => {
    if (!projectId) return;
    setTimeout(() => connect(), 100);
    fetch(`/api/projects/${projectId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          const artifactStatus = normalizeArtifactStatus(data.artifact_status);
          setProject({
            project_id: data.project_id,
            state: data.state,
            agent_statuses: data.agent_statuses || {},
            iteration_count: data.iteration_count || 0,
            outputs: data.outputs || {},
            workflow_profile: normalizeWorkflowProfile(data.workflow_profile),
            artifact_status: artifactStatus,
          });
          if (data.state === 'done') setRunning(false);
          else setRunning(true);
          hydrateAgentStatuses(data.agent_statuses || {});
        }
      })
      .catch((err) => console.error('Failed to fetch project status:', err));
  }, [projectId, connect, setProject, setRunning, hydrateAgentStatuses]);

  // Poll file list every 2s when projectId exists
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
        const data = (await res.json()) as { files: string[] };
        setFiles(data.files);
      } catch (err) {
        console.error('Failed to poll files:', err);
      }
    };
    pollFiles();
    filePollRef.current = setInterval(pollFiles, 2000);
    return () => {
      if (filePollRef.current) {
        clearInterval(filePollRef.current);
        filePollRef.current = null;
      }
    };
  }, [projectId, setFiles]);

  // Switching to a different project from history
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
            const artifactStatus = normalizeArtifactStatus(data.artifact_status);
            setProject({
              project_id: data.project_id,
              state: data.state,
              agent_statuses: data.agent_statuses || {},
              iteration_count: data.iteration_count || 0,
              outputs: data.outputs || {},
              workflow_profile: normalizeWorkflowProfile(data.workflow_profile),
              artifact_status: artifactStatus,
            });
            setRunning(data.state !== 'done');
            hydrateAgentStatuses(data.agent_statuses || {});
          }
        })
        .catch((err) => console.error('Failed to load project:', err));
    },
    [projectId, clearTerminal, setProjectId, connect, setProject, setRunning, hydrateAgentStatuses]
  );

  return (
    <Layout>
      {activeView === 'empty' && <EmptyState onSubmit={handleSubmit} />}
      {activeView === 'orchestrator' && (
        <OrchestratorView onFollowUp={handleFollowUp} onSelectProject={handleSelectProject} />
      )}
      {activeView === 'completed' && <CompletedView onFollowUp={handleFollowUp} />}
      {activeView === 'diff' && <DiffView />}
    </Layout>
  );
}
