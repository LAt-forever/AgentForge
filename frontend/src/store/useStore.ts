import { create } from 'zustand';
import type { AgentStatus, WorkflowState, Project, TerminalLine, ProjectSummary } from '../types';

export type ActiveView = 'empty' | 'orchestrator' | 'completed' | 'diff';
export type ActiveTab = 'explorer' | 'orchestrator' | 'logs';
export type Theme = 'light' | 'dark';
export type LogTab = 'terminal' | 'problems';

export interface Problem {
  severity: string;
  file: string;
  line?: number;
  message: string;
}

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
  isSettingsOpen: boolean;

  // UI view state
  activeView: ActiveView;
  activeTab: ActiveTab;
  theme: Theme;
  activeLogTab: LogTab;
  selectedDiffFile: string | null;
  problems: Problem[];

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
  setSettingsOpen: (open: boolean) => void;

  setActiveView: (view: ActiveView) => void;
  setActiveTab: (tab: ActiveTab) => void;
  setTheme: (theme: Theme) => void;
  setActiveLogTab: (tab: LogTab) => void;
  setSelectedDiffFile: (file: string | null) => void;
  setProblems: (problems: Problem[]) => void;
  clearProblems: () => void;

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
  isSettingsOpen: false,

  activeView: 'empty' as ActiveView,
  activeTab: 'orchestrator' as ActiveTab,
  theme: 'light' as Theme,
  activeLogTab: 'terminal' as LogTab,
  selectedDiffFile: null,
  problems: [],
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

  setWorkflowState: (workflowState) =>
    set((state) => ({
      workflowState,
      currentProject:
        state.currentProject?.project_id === workflowState.project_id
          ? {
              ...state.currentProject,
              state: workflowState.state,
              iteration_count: workflowState.iteration_count,
              workflow_profile:
                workflowState.workflow_profile ?? state.currentProject.workflow_profile,
              artifact_status:
                workflowState.artifact_status ?? state.currentProject.artifact_status,
            }
          : state.currentProject,
    })),

  setFiles: (files) => set({ files }),
  setCurrentFile: (currentFile) => set({ currentFile }),
  setFileContent: (fileContent) => set({ fileContent }),

  setConnected: (isConnected) => set({ isConnected }),
  setRunning: (isRunning) => set({ isRunning }),

  appendTerminalLine: (line) =>
    set((state) => ({ terminalLines: [...state.terminalLines, line].slice(-1000) })),
  clearTerminal: () => set({ terminalLines: [] }),
  setProjectList: (projects) => set({ projectList: projects }),
  setSettingsOpen: (isSettingsOpen) => set({ isSettingsOpen }),

  setActiveView: (activeView) => set({ activeView }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setTheme: (theme) => set({ theme }),
  setActiveLogTab: (activeLogTab) => set({ activeLogTab }),
  setSelectedDiffFile: (selectedDiffFile) => set({ selectedDiffFile }),
  setProblems: (problems) => set({ problems }),
  clearProblems: () => set({ problems: [] }),

  reset: () => {
    localStorage.removeItem('devagent-project-id');
    set({ ...initialState });
  },
}));

// Helper to get saved project ID on app load
export function getSavedProjectId(): string | null {
  return localStorage.getItem('devagent-project-id');
}
