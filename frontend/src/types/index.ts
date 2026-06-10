export interface AgentStatus {
  agent: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  output?: {
    summary?: string;
    files?: string[];
    metadata?: Record<string, unknown>;
  };
  error?: string;
}

export interface WorkflowState {
  project_id: string;
  state: 'idle' | 'planning' | 'designing' | 'coding' | 'reviewing' | 'done';
  overall_progress: number;
  iteration_count: number;
}

export interface ReviewIssue {
  severity: 'error' | 'warning' | 'suggestion';
  file?: string;
  line?: number;
  message: string;
  suggestion?: string;
}

export interface Project {
  project_id: string;
  state: string;
  agent_statuses: Record<string, unknown>;
  iteration_count: number;
  outputs: Record<string, string>;
}

export interface TerminalLine {
  stream: 'stdout' | 'stderr' | 'agent';
  content: string;
}

export interface ProjectSummary {
  project_id: string;
  state: string;
  requirement: string;
  requirement_preview: string;
  iteration_count: number;
  created_at: string;
  updated_at: string;
}

export interface GitCommit {
  hash: string;
  message: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'agent_status' | 'workflow_state' | 'error' | 'terminal_output';
  project_id: string;
  [key: string]: unknown;
}
