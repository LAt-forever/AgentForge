import React from 'react';
import { useStore } from '../store/useStore';
import type { ReviewIssue } from '../types';

const severityColors: Record<string, { color: string; bg: string }> = {
  error: { color: 'var(--accent-red)', bg: 'rgba(218, 54, 51, 0.15)' },
  warning: { color: 'var(--accent-yellow)', bg: 'rgba(210, 153, 34, 0.15)' },
  suggestion: { color: 'var(--accent-blue)', bg: 'rgba(88, 166, 255, 0.15)' },
};

export const ReviewReport: React.FC = () => {
  const currentProject = useStore((state) => state.currentProject);

  if (!currentProject || !currentProject.outputs.review) {
    return null;
  }

  let issues: ReviewIssue[] = [];
  try {
    const parsed = JSON.parse(currentProject.outputs.review);
    if (Array.isArray(parsed.issues)) {
      issues = parsed.issues;
    }
  } catch {
    return null;
  }

  if (issues.length === 0) {
    return (
      <div
        style={{
          padding: '16px',
          borderRadius: '8px',
          background: 'rgba(35, 134, 54, 0.1)',
          border: '1px solid var(--accent-green)',
          color: 'var(--accent-green)',
          fontSize: '14px',
          fontWeight: 600,
          textAlign: 'center',
        }}
      >
        All checks passed!
      </div>
    );
  }

  return (
    <div>
      {/* Title */}
      <div
        style={{
          fontSize: '13px',
          fontWeight: 700,
          color: 'var(--text-primary)',
          marginBottom: '12px',
          paddingBottom: '8px',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        Review Report ({issues.length} {issues.length === 1 ? 'issue' : 'issues'})
      </div>

      {/* Issue list */}
      {issues.map((issue, index) => {
        const style = severityColors[issue.severity] || severityColors.suggestion;
        return (
          <div
            key={index}
            style={{
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              background: 'var(--bg-secondary)',
              padding: '12px',
              marginBottom: '8px',
            }}
          >
            {/* Header: severity badge + file/line */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px',
              }}
            >
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  color: style.color,
                  background: style.bg,
                }}
              >
                {issue.severity}
              </span>
              {issue.file && (
                <span
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {issue.file}
                  {issue.line !== undefined && `:${issue.line}`}
                </span>
              )}
            </div>

            {/* Message */}
            <div
              style={{
                fontSize: '13px',
                color: 'var(--text-primary)',
                lineHeight: 1.5,
                marginBottom: issue.suggestion ? '8px' : '0',
              }}
            >
              {issue.message}
            </div>

            {/* Suggestion */}
            {issue.suggestion && (
              <div
                style={{
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-tertiary)',
                  padding: '8px',
                  borderRadius: '4px',
                  borderLeft: `3px solid ${style.color}`,
                  lineHeight: 1.4,
                }}
              >
                {issue.suggestion}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
