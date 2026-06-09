import { useStore } from '../store/useStore';
import { AgentCard } from './AgentCard';
import { ProgressBar } from './ProgressBar';

const AGENT_ORDER = ['pm', 'architect', 'coder', 'reviewer'];

export const AgentPanel: React.FC = () => {
  const agentStatuses = useStore((state) => state.agentStatuses);
  const workflowState = useStore((state) => state.workflowState);

  const orderedAgents = AGENT_ORDER.map((key) => agentStatuses[key]).filter(Boolean);

  return (
    <div style={{ padding: '12px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Section title */}
      <div
        style={{
          fontSize: '12px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          color: 'var(--text-muted)',
          marginBottom: '12px',
          paddingBottom: '8px',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        Agents
      </div>

      {/* Agent cards */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {orderedAgents.length === 0 && (
          <div
            style={{
              color: 'var(--text-muted)',
              fontSize: '13px',
              textAlign: 'center',
              padding: '24px 0',
            }}
          >
            No agent activity yet
          </div>
        )}
        {orderedAgents.map((status) => (
          <AgentCard key={status.agent} status={status} />
        ))}
      </div>

      {/* Iteration count */}
      {workflowState && workflowState.iteration_count > 0 && (
        <div
          style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            textAlign: 'center',
            padding: '8px 0',
            borderTop: '1px solid var(--border-color)',
          }}
        >
          Iteration {workflowState.iteration_count}
        </div>
      )}

      {/* Progress bar */}
      {workflowState && (
        <div style={{ borderTop: '1px solid var(--border-color)' }}>
          <ProgressBar progress={workflowState.overall_progress} />
        </div>
      )}
    </div>
  );
};
