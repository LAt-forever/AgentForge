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

export type WorkflowProfileName = 'default' | 'static_web';

export interface ArtifactIssue {
  severity: string;
  code?: string;
  file?: string;
  line?: number;
  message: string;
  repairable?: boolean;
}

export interface ArtifactStatus {
  type: string;
  status:
    | 'unknown'
    | 'not_web_artifact'
    | 'validating'
    | 'ready'
    | 'missing_entry'
    | 'invalid_refs'
    | 'syntax_error'
    | 'unsafe_path'
    | 'error';
  preview_url: string;
  issues: ArtifactIssue[];
}

export interface WorkflowState {
  project_id: string;
  state: 'idle' | 'planning' | 'designing' | 'coding' | 'reviewing' | 'done';
  overall_progress: number;
  iteration_count: number;
  workflow_profile?: WorkflowProfileName;
  artifact_status?: ArtifactStatus;
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
  workflow_profile: WorkflowProfileName;
  artifact_status: ArtifactStatus;
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
  workflow_profile?: WorkflowProfileName;
  artifact_status?: ArtifactStatus;
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

export interface AppSettings {
  default_model: string;
  fallback_model: string;
  max_review_iterations: number;
  code_execution_timeout: number;
  default_language: string;
  use_docker_sandbox: boolean;
  anthropic_api_key: string;
  openai_api_key: string;
  deepseek_api_key: string;
  glm_api_key: string;
}

export type ModelsByProvider = Record<string, string[]>;
