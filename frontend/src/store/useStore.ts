import { create } from 'zustand';
import type { AgentStatus, WorkflowState, Project } from '../types';

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

  setProject: (project: Project | null) => void;
  setProjectId: (id: string | null) => void;
  setAgentStatus: (status: AgentStatus) => void;
  setWorkflowState: (state: WorkflowState) => void;
  setFiles: (files: string[]) => void;
  setCurrentFile: (file: string | null) => void;
  setFileContent: (content: string) => void;
  setConnected: (connected: boolean) => void;
  setRunning: (running: boolean) => void;
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
};

export const useStore = create<AppState>((set) => ({
  ...initialState,

  setProject: (project) => set({ currentProject: project }),
  setProjectId: (id) => set({ projectId: id }),

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

  reset: () => set(initialState),
}));
