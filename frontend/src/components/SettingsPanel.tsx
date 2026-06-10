import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import type { AppSettings, ModelsByProvider } from '../types';

const PROVIDERS = ['anthropic', 'openai', 'deepseek', 'glm'] as const;

const KEY_FIELD: Record<string, keyof AppSettings> = {
  anthropic: 'anthropic_api_key',
  openai: 'openai_api_key',
  deepseek: 'deepseek_api_key',
  glm: 'glm_api_key',
};

export function SettingsPanel() {
  const isOpen = useStore((s) => s.isSettingsOpen);
  const setOpen = useStore((s) => s.setSettingsOpen);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [models, setModels] = useState<ModelsByProvider>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    fetch('/api/settings')
      .then((r) => (r.ok ? r.json() : { settings: null }))
      .then((d) => setSettings(d.settings))
      .catch(() => setSettings(null));
    fetch('/api/settings/models')
      .then((r) => (r.ok ? r.json() : { models: {} }))
      .then((d) => setModels(d.models ?? {}))
      .catch(() => setModels({}));
  }, [isOpen]);

  if (!isOpen) return null;

  const update = (patch: Partial<AppSettings>) =>
    setSettings((prev) => (prev ? { ...prev, ...patch } : prev));

  const save = () => {
    if (!settings) return;
    setSaving(true);
    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings }),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setSettings(d.settings);
        setOpen(false);
      })
      .finally(() => setSaving(false));
  };

  const allModels = PROVIDERS.flatMap((p) => models[p] ?? []);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 360,
        height: '100vh',
        background: 'var(--bg-secondary)',
        borderLeft: '1px solid var(--border-color)',
        padding: 16,
        overflow: 'auto',
        zIndex: 1000,
        color: 'var(--text-primary)',
        fontSize: 13,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <strong>Settings</strong>
        <button onClick={() => setOpen(false)} style={{ cursor: 'pointer' }}>✕</button>
      </div>

      {!settings ? (
        <div style={{ color: 'var(--text-muted)' }}>Loading…</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <label>Default model
            <select
              value={settings.default_model}
              onChange={(e) => update({ default_model: e.target.value })}
              style={{ width: '100%' }}
            >
              {allModels.length === 0 && <option>{settings.default_model}</option>}
              {allModels.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>

          {PROVIDERS.map((p) => (
            <label key={p}>{p} API key
              <input
                type="password"
                value={settings[KEY_FIELD[p]] as string}
                placeholder="(unchanged)"
                onChange={(e) =>
                  update({ [KEY_FIELD[p]]: e.target.value } as Partial<AppSettings>)
                }
                style={{ width: '100%' }}
              />
            </label>
          ))}

          <label>Target language
            <select
              value={settings.default_language}
              onChange={(e) => update({ default_language: e.target.value })}
              style={{ width: '100%' }}
            >
              <option value="python">Python</option>
              <option value="typescript">TypeScript</option>
            </select>
          </label>

          <label>Max review iterations
            <input
              type="number"
              min={1}
              max={10}
              value={settings.max_review_iterations}
              onChange={(e) => update({ max_review_iterations: Number(e.target.value) })}
              style={{ width: '100%' }}
            />
          </label>

          <label>Code execution timeout (s)
            <input
              type="number"
              min={1}
              value={settings.code_execution_timeout}
              onChange={(e) => update({ code_execution_timeout: Number(e.target.value) })}
              style={{ width: '100%' }}
            />
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={settings.use_docker_sandbox}
              onChange={(e) => update({ use_docker_sandbox: e.target.checked })}
            />
            Use Docker sandbox
          </label>

          <button onClick={save} disabled={saving} style={{ marginTop: 12, cursor: 'pointer' }}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      )}
    </div>
  );
}
