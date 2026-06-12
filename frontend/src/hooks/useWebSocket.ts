import { useRef, useCallback, useEffect } from 'react';
import { useStore } from '../store/useStore';
import type { WebSocketMessage } from '../types';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const projectIdRef = useRef<string | null>(null);

  const setConnected = useStore((state) => state.setConnected);
  const setAgentStatus = useStore((state) => state.setAgentStatus);
  const setWorkflowState = useStore((state) => state.setWorkflowState);
  const setRunning = useStore((state) => state.setRunning);
  const appendTerminalLine = useStore((state) => state.appendTerminalLine);
  const setProblems = useStore((state) => state.setProblems);
  const projectId = useStore((state) => state.projectId);

  // Keep ref in sync with store
  useEffect(() => {
    projectIdRef.current = projectId;
  }, [projectId]);

  const connect = useCallback(() => {
    const id = projectIdRef.current;
    if (!id) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`ws://localhost:8000/ws/${id}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;

        if (message.type === 'agent_status') {
          setAgentStatus({
            agent: message.agent as string,
            status: message.status as 'idle' | 'running' | 'completed' | 'failed',
            progress: 0,
            output: message.output as Record<string, unknown> | undefined,
            error: message.error as string | undefined,
          });
          // A fresh reviewer run invalidates the previous problem list.
          if (message.agent === 'reviewer' && message.status === 'running') {
            setProblems([]);
          }
        } else if (message.type === 'workflow_state') {
          setWorkflowState({
            project_id: message.project_id as string,
            state: message.state as 'idle' | 'planning' | 'designing' | 'coding' | 'reviewing' | 'done',
            overall_progress: message.overall_progress as number,
            iteration_count: message.iteration_count as number,
          });
          if ((message.state as string) === 'done') {
            setRunning(false);
          }
        } else if (message.type === 'error') {
          console.error('WebSocket error message:', message);
          setRunning(false);
        } else if (message.type === 'terminal_output') {
          appendTerminalLine({
            stream: message.stream as 'stdout' | 'stderr' | 'agent',
            content: message.content as string,
          });
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;

      // Reconnect after 3 seconds
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      reconnectTimeoutRef.current = setTimeout(() => {
        if (projectIdRef.current) {
          connect();
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [setConnected, setAgentStatus, setWorkflowState, setRunning, appendTerminalLine, setProblems]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { connect };
}
