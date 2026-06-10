import { create } from 'zustand';
import type { AgentStatus, WorkflowState, Project, TerminalLine, ProjectSummary } from '../types';

interface AppState {
  currentProject: Project | null;
  projectId: string | null;
  agentStatuses: Record<string, AgentStatus>;
  workflowState: WorkflowState | null;
  files: string[];
  currentFile: string | null;
  fileContent: string;
  isConnected: boolean;
  isRunning: boolean;
  terminalLines: TerminalLine[];
  projectList: ProjectSummary[];

  setProject: (project: Project | null) => void;
  setProjectId: (id: string | null) => void;
  setAgentStatus: (status: AgentStatus) => void;
  setWorkflowState: (state: WorkflowState) => void;
  setFiles: (files: string[]) => void;
  setCurrentFile: (file: string | null) => void;
  setFileContent: (content: string) => void;
  setConnected: (connected: boolean) => void;
  setRunning: (running: boolean) => void;
  appendTerminalLine: (line: TerminalLine) => void;
  clearTerminal: () => void;
  setProjectList: (projects: ProjectSummary[]) => void;
  reset: () => void;
}

const initialState = {
  currentProject: null,
  projectId: null,
  agentStatuses: {},
  workflowState: null,
  files: [],
  currentFile: null,
  fileContent: '',
  isConnected: false,
  isRunning: false,
  terminalLines: [],
  projectList: [],
};

export const useStore = create<AppState>((set) => ({
  ...initialState,

  setProject: (project) => set({ currentProject: project }),
  setProjectId: (id) => {
    set({ projectId: id });
    if (id) {
      localStorage.setItem('devagent-project-id', id);
    } else {
      localStorage.removeItem('devagent-project-id');
    }
  },

  setAgentStatus: (status) =>
    set((state) => ({
      agentStatuses: {
        ...state.agentStatuses,
        [status.agent]: status,
      },
    })),

  setWorkflowState: (workflowState) => set({ workflowState }),

  setFiles: (files) => set({ files }),
  setCurrentFile: (currentFile) => set({ currentFile }),
  setFileContent: (fileContent) => set({ fileContent }),

  setConnected: (isConnected) => set({ isConnected }),
  setRunning: (isRunning) => set({ isRunning }),

  appendTerminalLine: (line) =>
    set((state) => ({ terminalLines: [...state.terminalLines, line].slice(-1000) })),
  clearTerminal: () => set({ terminalLines: [] }),
  setProjectList: (projects) => set({ projectList: projects }),

  reset: () => {
    localStorage.removeItem('devagent-project-id');
    set({ ...initialState });
  },
}));

// Helper to get saved project ID on app load
export function getSavedProjectId(): string | null {
  return localStorage.getItem('devagent-project-id');
}
