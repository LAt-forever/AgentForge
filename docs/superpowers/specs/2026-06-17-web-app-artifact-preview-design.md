# Web App Artifact Preview v1 Design

## Overview

This spec defines the first optimization pass for DevAgent Team after the Codex-style desktop UI work. The goal is to make the project stronger as an interview and product demo by supporting a polished "Web App" generation path for small frontend tools.

The target experience is:

1. The user asks for a small web tool, such as a pomodoro timer, BMI calculator, color palette picker, or simple interactive widget.
2. The system recognizes the request as a static web app task.
3. The agent workflow feels like a Web App workflow in the UI.
4. The Coder is guided to produce browser-ready files, preferably `index.html`, `style.css`, and `script.js`.
5. The backend validates the generated artifact enough to catch missing entry points, broken local references, unsafe paths, and basic JavaScript syntax issues.
6. The Completed view exposes a reliable `Preview App` action that opens the generated app in a new browser tab.

This is intentionally v1. It should be stable, easy to explain, and compatible with the existing event-driven orchestrator. Browser automation, screenshots, React/Vite app generation, and extra agents remain future extensions.

## Goals

- Add a first-class Web App Mode experience without duplicating the full orchestrator.
- Improve static frontend artifact generation quality.
- Add a backend preview endpoint for generated static web apps.
- Add lightweight web artifact validation that can feed repair feedback back into the Coder.
- Show clear UI state for preview-ready and preview-unavailable projects.
- Preserve existing Python/CLI workflows.
- Keep implementation incremental and testable.

## Non-Goals

- No separate `WebOrchestrator` in v1.
- No separate `WebPMAgent`, `WebArchitectAgent`, `WebCoderAgent`, or `WebReviewerAgent` classes in v1.
- No required Playwright/browser automation in v1.
- No automatic npm install or full Vite project execution in v1.
- No deployment or public sharing in v1.
- No iframe-only preview experience in v1.

## Chosen Approach

Use a `WorkflowProfile` abstraction rather than a completely parallel workflow.

From the user's perspective, `static_web` is a distinct Web App Mode. From the implementation perspective, it reuses the existing event bus, plugin registry, state store, websocket messages, and PM -> Architect -> Coder -> Reviewer sequence.

The first profile set is:

```text
default
static_web
```

The `static_web` profile changes the workflow personality and validation rules:

- PM writes a web product brief.
- Architect designs a static frontend file structure.
- Coder produces browser-ready HTML/CSS/JS.
- Reviewer evaluates as a static web app.
- A WebArtifactValidator runs after code generation.
- Completed UI shows preview status and a Preview App action.

This gives the product a real Web App Mode while avoiding early duplication of orchestration logic.

## Workflow Profile Model

Add a small profile object, conceptually:

```python
class WorkflowProfile:
    name: str
    display_name: str
    agent_labels: dict[str, str]
    prompt_context: str
    validators: list[str]
    preview_enabled: bool
```

For v1 this does not need to become a large framework. It can be a compact module or dataclass used by the orchestrator and agents.

### Profile Selection

The system should support two profile selection paths:

1. Explicit selection from request payload or future UI.
2. Heuristic fallback based on the requirement text.

The first implementation can use a deterministic heuristic:

- `static_web` when the requirement includes web-app terms such as `web`, `page`, `html`, `css`, `javascript`, `frontend`, `browser`, `timer`, `calculator`, `palette`, `dashboard`, `form`, or equivalent Chinese terms such as `网页`, `页面`, `前端`, `浏览器`, `计时器`, `计算器`, `调色板`, `表单`.
- `default` otherwise.

This heuristic is intentionally conservative and can later be replaced by a PM classification step or explicit UI selector.

### State Persistence

Each project state should persist:

```json
{
  "workflow_profile": "static_web",
  "artifact_status": {
    "type": "static_web",
    "status": "ready",
    "preview_url": "/api/projects/{project_id}/preview/",
    "issues": []
  }
}
```

Allowed `artifact_status.status` values:

- `unknown`
- `not_web_artifact`
- `validating`
- `ready`
- `missing_entry`
- `invalid_refs`
- `syntax_error`
- `unsafe_path`
- `error`

## Backend Design

### Orchestrator Integration

The existing `EventDrivenOrchestrator` remains the central workflow engine.

When a workflow starts:

1. Resolve `workflow_profile`.
2. Store it in `AgentContext` and `StateStore`.
3. Include it in websocket workflow state messages.
4. Pass profile context to agents through the existing `AgentContext`.

After Coder completes:

1. Persist files as it does today.
2. Run existing syntax validation for known code files.
3. If `workflow_profile == "static_web"`, run `WebArtifactValidator`.
4. If validation finds repairable issues and iterations remain, set `context.review_feedback` and publish `ITERATION_STARTED`.
5. If validation passes, persist `artifact_status.ready` and continue to Reviewer.

This keeps validator feedback in the same repair loop as syntax and review feedback.

### Agent Prompt Behavior

The agents can remain the same classes in v1, but prompts should receive profile-specific instructions.

For `static_web`:

- PM should produce a product brief oriented around user interactions, visible states, and edge cases.
- Architect should define static frontend files and data flow.
- Coder should prefer:
  - `index.html`
  - `style.css`
  - `script.js`
- Coder may produce a single-file `index.html` with inline CSS/JS when appropriate, but the prompt should clearly prefer the three-file structure.
- Coder should avoid external runtime dependencies and CDN dependencies in v1.
- Reviewer should evaluate browser usability, DOM interactions, event handling, accessible labels, empty/error states, and whether local references resolve.

### WebArtifactValidator

Add a focused validator for static web artifacts.

Responsibilities:

- Confirm `index.html` exists.
- Confirm project files are inside the project directory.
- Parse or scan `index.html` for local stylesheet and script references.
- Confirm referenced local CSS/JS files exist.
- Reject path traversal and absolute filesystem references.
- Validate JavaScript syntax when possible:
  - Use Docker/Node `node --check` when sandbox is enabled and available.
  - Fall back to structural checks when Node is unavailable.
- Produce structured issues for UI and repair feedback.

Issue shape:

```json
{
  "severity": "error",
  "code": "missing_entry",
  "file": "index.html",
  "message": "Static web app requires an index.html entry point.",
  "repairable": true
}
```

Repairable issues should become Coder feedback. Non-web projects should not be penalized by this validator.

### Preview API

Add static preview endpoints:

```text
GET /api/projects/{project_id}/preview/
GET /api/projects/{project_id}/preview/{path:path}
```

Behavior:

- `/preview/` serves the project's `index.html`.
- `/preview/{path}` serves safe local static assets under the project directory.
- The endpoint must prevent path traversal.
- The endpoint must only serve files from the selected project.
- Missing files return a clear error response.
- MIME types should be set for HTML, CSS, JavaScript, JSON, SVG, PNG, JPG, JPEG, GIF, WebP, and plain text.

Security constraints:

- No access outside `output/{project_id}`.
- No hidden dotfiles.
- No `.git` directory access.
- No Python source execution.
- No directory listing.

## Frontend Design

### Mode Signal

The UI should show the active workflow profile when available.

For `static_web`, display:

```text
Mode: Web App
```

Agent display labels can be profile-aware:

- PM: Product Brief
- Architect: Web Structure
- Coder: Frontend Build
- Reviewer: Web Review

This is a product-facing label change only. The backend plugin names can remain `pm`, `architect`, `coder`, and `reviewer`.

### Preview Actions

Add a `Preview App` action in Completed view when `artifact_status.status == "ready"` and `preview_url` exists.

The action opens the preview URL in a new tab for v1. This is the primary preview mechanism because it is stable and avoids iframe sizing/security complications.

Also add a lightweight preview entry near file/editor views:

- If `index.html` is selected, show `Preview`.
- If project artifact status is ready, show `Preview App`.
- If preview is unavailable, show a disabled action with a concise reason.

### Completed View Copy

Completed view success copy should depend on profile.

For `static_web`:

```text
Preview ready
Static web app validated
```

For default:

```text
Workflow complete
Review finished
```

### Problems and Logs

Validator issues should appear in the Problems tab alongside Reviewer issues.

Examples:

- `index.html not found`
- `index.html references missing script.js`
- `script.js has a syntax error`
- `Preview unavailable because this project is not a web app`

Terminal output should include short lifecycle messages:

- `Detected workflow profile: Web App`
- `Validating static web artifact`
- `Preview ready: /api/projects/{project_id}/preview/`
- `Preview unavailable: missing index.html`

## Error Handling

### Repairable Errors

These should feed back into the Coder when iterations remain:

- Missing `index.html`
- Missing referenced local CSS/JS
- JavaScript syntax error
- Unsafe local reference
- Empty generated app files

### Non-Blocking States

If a project uses the `default` profile, lack of preview is not an error.

If a `static_web` project produces a valid single-file `index.html`, it should pass even if no `style.css` or `script.js` exists.

### Preview Endpoint Errors

Preview endpoint errors must be clear:

- `404`: project or file not found
- `403`: unsafe path or disallowed file
- `409`: project is not preview-ready

The browser should not show a blank page for expected validation failures.

## Testing Strategy

### Backend Unit Tests

Profile tests:

- Web tool requirement selects `static_web`.
- CLI/script requirement remains `default`.
- Explicit profile override wins over heuristic.

Validator tests:

- Three-file static app passes.
- Single-file `index.html` passes.
- Missing `index.html` fails with `missing_entry`.
- Missing referenced CSS/JS fails with `invalid_refs`.
- Path traversal is rejected.
- JavaScript syntax error is reported when JS validation is available.

Preview endpoint tests:

- `/preview/` returns `index.html`.
- `/preview/style.css` returns CSS with correct content type.
- Missing file returns a clear error.
- Path traversal is blocked.
- `.git` files are blocked.

Workflow tests:

- FakeLLM generates a static web app and reaches `DONE`.
- State includes `workflow_profile == "static_web"`.
- State includes `artifact_status.status == "ready"`.
- State includes a usable `preview_url`.
- FakeLLM missing `index.html` triggers repair feedback and iteration.

### Frontend Verification

- TypeScript build passes.
- Types include workflow profile and artifact status.
- Completed view shows Preview App for ready web artifacts.
- Completed view does not show false preview success for default projects.
- Problems tab displays validator issues.

### Manual Demo Acceptance

Primary demo:

1. Start backend and frontend.
2. Submit: `做一个番茄钟网页工具`.
3. UI shows `Mode: Web App`.
4. Generated files include `index.html`, preferably `style.css` and `script.js`.
5. Completed view shows `Preview ready`.
6. Click `Preview App`.
7. New tab opens an interactive static web app.

Fallback demo:

1. Submit: `做一个颜色调色板网页`.
2. Validate that a single-file `index.html` is acceptable if generated.
3. Preview still opens successfully.

Regression demo:

1. Submit a normal Python CLI request.
2. Confirm the default workflow remains available.
3. Confirm no false Web App preview failure is shown.

## Future Extensions

- Playwright-based preview smoke tests.
- Console error capture.
- Screenshot capture in Completed view.
- In-app iframe preview panel.
- React/Vite profile.
- DesignerAgent for visual planning.
- BrowserTesterAgent for interactive QA.
- Deploy/share endpoint.

## Implementation Boundaries

This spec should be implemented as a focused v1:

- Add the smallest useful workflow profile abstraction.
- Add static web prompt/context changes.
- Add validator and preview endpoint.
- Add UI preview/status affordances.
- Add tests around the new behavior.

Avoid broad refactors of the existing agent architecture, frontend layout, or state store beyond what this feature needs.
