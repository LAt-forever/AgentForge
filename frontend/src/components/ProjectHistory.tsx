import { useStore } from '../store/useStore';

interface ProjectHistoryProps {
  onSelect: (projectId: string) => void;
}

export function ProjectHistory({ onSelect }: ProjectHistoryProps) {
  const projectList = useStore((state) => state.projectList);
  const activeId = useStore((state) => state.projectId);

  return (
    <div style={{ borderBottom: '1px solid #333', maxHeight: 200, overflow: 'auto' }}>
      <div
        style={{
          padding: '6px 10px',
          fontSize: 11,
          color: '#888',
          textTransform: 'uppercase',
        }}
      >
        Projects
      </div>
      {projectList.length === 0 ? (
        <div style={{ padding: '6px 10px', fontSize: 12, color: '#666' }}>No projects yet.</div>
      ) : (
        projectList.map((p) => (
          <div
            key={p.project_id}
            onClick={() => onSelect(p.project_id)}
            style={{
              padding: '6px 10px',
              cursor: 'pointer',
              fontSize: 12,
              background: p.project_id === activeId ? '#2d2d2d' : 'transparent',
              color: '#ddd',
            }}
          >
            <div
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {p.requirement_preview || p.project_id}
            </div>
            <div style={{ fontSize: 10, color: '#777' }}>{p.state}</div>
          </div>
        ))
      )}
    </div>
  );
}
