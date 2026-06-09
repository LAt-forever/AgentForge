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
          const status = message.status as Parameters<typeof setAgentStatus>[0];
          if (status) {
            setAgentStatus(status);
          }
        } else if (message.type === 'workflow_state') {
          const state = message.state as Parameters<typeof setWorkflowState>[0];
          if (state) {
            setWorkflowState(state);
            if (state.state === 'done') {
              setRunning(false);
            }
          }
        } else if (message.type === 'error') {
          console.error('WebSocket error message:', message);
          setRunning(false);
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
  }, [setConnected, setAgentStatus, setWorkflowState, setRunning]);

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
