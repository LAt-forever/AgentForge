# Stitch Prompt: DevAgent Desktop UI — Codex-Style Terminal Interface

> **Target**: Figma Stitch AI  
> **Style Reference**: OpenAI Codex Desktop (codex-cli) — terminal-first, developer-tool aesthetic  
> **Product**: DevAgent Team — Multi-Agent collaborative coding system (PM → Architect → Coder → Reviewer)

---

## 1. Product Overview

DevAgent Desktop is an AI-powered coding companion where users describe what they want to build in natural language, and a team of specialized AI agents collaborates to produce production-ready code. The UI should feel like a **modern terminal-based IDE** — dark, code-centric, information-dense, with the raw power of a command-line interface but the polish of a native desktop app.

The core interaction paradigm:
1. User types a project requirement in a terminal-style input
2. Agents execute in sequence: **PM** (plan) → **Architect** (design) → **Coder** (code) → **Reviewer** (review)
3. Real-time file changes, terminal output, and agent status stream in as it happens
4. User can inspect, edit, and iterate

---

## 2. Design System — Visual Language

### Color Palette (Dark Theme Primary)
Use a sophisticated dark terminal palette with semantic color coding:

| Token | Hex | Usage |
|-------|-----|-------|
| `bg-primary` | `#0D0D0D` | Main background — deep black, not pure black |
| `bg-secondary` | `#141414` | Panel backgrounds, sidebar |
| `bg-tertiary` | `#1E1E1E` | Elevated surfaces, cards, input fields |
| `bg-hover` | `#262626` | Hover states |
| `border-subtle` | `#2A2A2A` | Divider lines, borders |
| `border-active` | `#3A3A3A` | Active/selected borders |
| `text-primary` | `#E8E8E8` | Headings, primary text |
| `text-secondary` | `#8A8A8A` | Labels, descriptions, timestamps |
| `text-muted` | `#5A5A5A` | Disabled, placeholders |
| `accent-green` | `#4ADE80` | Success, running status, positive actions |
| `accent-yellow` | `#FBBF24` | Warnings, thinking states, attention |
| `accent-red` | `#F87171` | Errors, failed states, destructive actions |
| `accent-blue` | `#60A5FA` | Links, active agents, primary actions |
| `accent-purple` | `#A78BFA` | PM agent identity |
| `accent-cyan` | `#22D3EE` | Architect agent identity |
| `accent-orange` | `#FB923C` | Coder agent identity |
| `accent-pink` | `#F472B6` | Reviewer agent identity |

### Typography
- **Primary font**: `JetBrains Mono` or `SF Mono` — monospace for everything terminal-related
- **UI font**: `Inter` or `SF Pro` — for labels, buttons, panel headers (sans-serif)
- **Font sizes**:
  - Terminal text: `13px`, line-height `1.6`
  - Panel headers: `11px`, uppercase, letter-spacing `0.05em`, weight `600`
  - Code editor: `14px`, line-height `1.5`
  - Status badges: `11px`

### Spacing & Shape
- **Border radius**: `4px` for buttons/inputs, `0px` for panels (sharp edges for tool feel)
- **Panel gaps**: `1px` borders only, no visible gaps between panels
- **Padding**: `12px` standard, `8px` compact in dense areas
- **Scrollbars**: Custom thin scrollbar, `4px` width, `bg-tertiary` track, `border-active` thumb

---

## 3. Layout Architecture — 4 Viewports to Design

Design the following **4 viewport states** as separate screens/frames:

### Viewport 1: Empty State — "Ready to Build"
The app has just launched. No project is active.

**Layout**: Full-screen terminal aesthetic
- **Top Bar** (40px height): Minimal — left side shows `🤖 devagent` logo in `accent-blue`, right side shows connection status dot (green = connected) and a `⚙` settings icon
- **Main Area**: Centered vertically and horizontally
  - Large terminal prompt symbol `>` in `accent-green`, `48px` size
  - Below it: placeholder text in `text-muted`: "Describe what you want to build..."
  - Below that: hint text in `text-secondary` at `12px`: "Press Enter to submit · The agent team will plan, architect, code, and review"
- **Bottom Bar** (32px height): Left shows current model (e.g., `claude-sonnet-4-6`), right shows keyboard shortcuts hint `⌘K settings · ⌘N new project`
- **Left Sidebar** (collapsed state, 40px wide): Just icons vertically — 📁 files, 📜 history, ⚙ settings

### Viewport 2: Running State — "Agents at Work"
The user has submitted a request: *"Build a Python CLI that greets the user by name"*. Agents are executing.

**Layout**: 3-column IDE layout

```
+----------------------------------------------------------+
| [🤖 devagent]          Project: cli-greeter    [●] [⚙]  |  <- Top Bar (40px)
+----------+------------------------------------+----------+
|          |                                    |          |
| Sidebar  |    Terminal / Main Workspace       |  Agent   |
| (240px)  |    (flexible, primary)             |  Panel   |
|          |                                    | (280px)  |
| 📁 Files |                                    |          |
| 📜 Hist  |    > Build a Python CLI...         |  ┌────┐  |
|          |                                    |  │ PM │  |
| cli-     |    ✻ Thinking...                   |  │ ✅ │  |
| greeter/ |    ┌────────────────────────┐      |  └────┘  |
|   ├ src/ |    │ Plan: Create a CLI...  │      |  ┌────┐  |
|   │ ├ __ │    │ 1. Parse arguments     │      |  │Arch│  |
|   │ ├ gr │    │ 2. Greeting logic      │      |  │ 🔄 │  |
|   │ └ te │    │ 3. Entry point         │      |  └────┘  |
|   ├ pypr │    └────────────────────────┘      |  ┌────┐  |
|   └ READ │                                    |  │Code│  |
|          |    ○ Creating src/__init__.py      |  │ ⏳ │  |
|          |    ○ Creating src/greeter.py       |  └────┘  |
|          |    ○ Modifying pyproject.toml      |  ┌────┐  |
|          |                                    |  │Rev │  |
|          |    ── Running: python -m pytest    |  │ ⏳ │  |
|          |    passed: 3/3                     |  └────┘  |
|          |                                    |          |
+----------+------------------------------------+----------+
|          |  Terminal Output (180px, collapsible)         |
|          |  > pip install -e .                           |
|          |  > python -m pytest                           |
|          |  =====================                        |
|          |  3 passed in 0.02s                            |
+----------+-----------------------------------------------+
```

**Detailed Panel Descriptions**:

#### Left Sidebar (240px)
- **Header** (32px): `FILES` label in uppercase, `text-secondary`, with a small `+` button for new file
- **File Tree**: Hierarchical tree view
  - Directories: `📁 src/` in `text-secondary`, chevron `▶` for collapsed, `▼` for expanded
  - Files: `📄 greeter.py` in `text-primary`
  - **Status indicators**: New files get a green dot `●` in `accent-green`, modified files get a yellow dot `●` in `accent-yellow`, deleted get red
  - Active/selected file: background `bg-hover`, left border `2px solid accent-blue`
  - Hover: background `bg-hover`
- **Bottom section**: Project selector dropdown showing current project name

#### Main Workspace (Center, flexible)
This is the **terminal-style interaction area** — the heart of the UI.

- **User Input Block**:
  - Prompt symbol `>` in `accent-green`, `16px`
  - User text in `text-primary`, `14px`
  - Timestamp in `text-muted`, `11px`, right-aligned on the same line

- **Agent Response Blocks**: Each agent response is a distinct block separated by a thin `border-subtle` horizontal rule
  - **Thinking block** (collapsible):
    - Header: `✻ Thinking...` in `accent-yellow`, with a spinner `⠋` (unicode braille pattern)
    - Content area: `bg-tertiary` background, `12px` padding, `border-radius: 4px`
    - Text in `text-secondary`, `13px`
    - Collapse/expand chevron on the right
  - **Plan block** (from PM agent):
    - Header: `📋 Plan` in `accent-purple`, with agent badge `PM`
    - Numbered list in `text-primary`
    - Each item has a checkbox `☐` that animates to `☑` when that step starts
  - **File operation block**:
    - Header shows operation type: `+ Create` (green), `~ Modify` (yellow), `- Delete` (red)
    - File path in monospace
    - For modifications: inline diff view — removed lines have red background `rgba(248,113,113,0.15)` with `-` prefix, added lines have green background `rgba(74,222,128,0.15)` with `+` prefix
  - **Command execution block**:
    - Header: `$ command` in `text-secondary`
    - Output area: `bg-primary` background, `1px solid border-subtle` border, `8px` padding
    - Stdout in `text-primary`, stderr in `accent-red`
    - Exit code indicator: green check `✓` or red cross `✗` with exit code number

- **Input Area** (fixed at bottom of main workspace):
  - Container: `bg-secondary`, `border-top: 1px solid border-subtle`
  - Textarea: full width, `bg-tertiary`, `border: 1px solid border-subtle`, `border-radius: 4px`
  - Placeholder: "Ask a follow-up or type a new requirement..."
  - Send button: `accent-green` background, `>` icon, `32px` square
  - Status row above input: shows `🟢 Connected · 4 agents active` or similar

#### Right Agent Panel (280px)
- **Header** (32px): `AGENTS` label uppercase
- **Agent Timeline**: Vertical stack of agent cards, connected by a vertical line `1px solid border-subtle`

Each agent card:
```
┌─────────────────────────────┐
│ 🤖 PM        [PLANNING]     │  <- Agent icon + name + status badge
│ ─────────────────────────   │  <- Separator
│ ✅ Requirement analyzed     │  <- Progress items
│ ✅ Functional spec written  │
│ ⏳ Edge cases identified    │
│                             │
│ ▼ Output (click to expand)  │  <- Expandable output preview
│   Create a CLI tool with... │
└─────────────────────────────┘
```

- **Card styling**:
  - Background: `bg-secondary`
  - Border: `1px solid border-subtle`, left border `3px solid` with agent's accent color
  - Padding: `12px`
  - Margin bottom: `8px`
  - Status badges:
    - `WAITING` — `bg-tertiary`, `text-muted`, pill shape
    - `RUNNING` — `bg` with `accent-blue` at 15% opacity, `accent-blue` text, with animated pulse dot `●`
    - `COMPLETED` — `bg` with `accent-green` at 15% opacity, `accent-green` text, checkmark `✓`
    - `ERROR` — `bg` with `accent-red` at 15% opacity, `accent-red` text, cross `✗`

- **Agent identity colors**:
  - PM: `accent-purple`
  - Architect: `accent-cyan`
  - Coder: `accent-orange`
  - Reviewer: `accent-pink`

- **Iteration indicator**: When review fails and loops back, show a circular badge with `↻ Iteration 2/5` in `accent-yellow`

#### Bottom Terminal Panel (180px, collapsible)
- **Header** (28px): `TERMINAL` label + clear button + collapse button `▾`
- **Content**: Scrollable log output
  - Timestamps in `text-muted` at `11px`: `[10:23:45]`
  - Log levels: `INFO` in `accent-blue`, `WARN` in `accent-yellow`, `ERROR` in `accent-red`
  - Message in `text-secondary`
  - Auto-scrolls to bottom as new logs arrive

### Viewport 3: Completed State — "Project Ready"
All agents have finished. Code is generated and reviewed.

**Changes from Viewport 2**:
- All agent cards show `COMPLETED` status with green checkmarks
- File tree shows all files with their final state (no dots = unchanged from last)
- Main workspace shows a summary block:
  - `✓ All checks passed` banner in `accent-green` with `bg` at 10% opacity
  - Summary: "Generated 5 files, 247 lines of code. All tests passing."
  - Action buttons: `Open in Editor` · `Run Tests` · `Export Project`
- Input area now accepts follow-up requests: "Add error handling" or "Refactor into a class"
- Bottom terminal shows final test results

### Viewport 4: Review / Diff State — "Inspecting Changes"
User has clicked on a modified file to see the diff.

**Layout**: Main workspace switches to diff view
- **Diff header**: File path + `+12 -3` stats in green/red
- **Side-by-side diff** (preferred) or unified diff:
  - Left: original code (dimmed, `text-muted`)
  - Right: new code (full brightness, `text-primary`)
  - Line numbers in `text-muted`
  - Added lines: left border `2px solid accent-green`, background `rgba(74,222,128,0.08)`
  - Removed lines: left border `2px solid accent-red`, background `rgba(248,113,113,0.08)`
  - Modified lines: left border `2px solid accent-yellow`
- **Action bar** at bottom: `Accept Changes` (green) · `Reject` (red) · `Edit Manually` (blue)

---

## 4. Micro-interactions & Animations

### Typing Indicator
When an agent is "thinking" or generating:
- Show a 3-dot bouncing animation in `accent-yellow`: `● ● ●` where each dot fades in/out in sequence
- Position: inline after the agent's name or at the start of a new block

### File Creation Animation
When a new file is created:
1. File tree item slides in from left with `translateX(-10px)` → `translateX(0)`, duration `200ms`, ease-out
2. Green dot `●` scales from `0` → `1` with a subtle bounce

### Progress Transitions
Agent status changes:
- `WAITING` → `RUNNING`: Card left border color transitions over `300ms`
- `RUNNING` → `COMPLETED`: Status badge background smoothly transitions, checkmark draws in (SVG stroke animation)
- Card expands when clicked to show full output, with `height` transition `300ms` ease

### Terminal Output Stream
New log lines appear:
- Fade in + slide up: `opacity: 0 → 1`, `translateY(4px) → translateY(0)`, `150ms`
- Auto-scroll follows the new content smoothly

### Input Focus
When user clicks the input textarea:
- Border transitions to `accent-blue` with `box-shadow: 0 0 0 2px rgba(96,165,250,0.2)`
- Prompt symbol `>` glows brighter

---

## 5. Component Specifications

### Component: TerminalBlock
- Container: full width, `border-bottom: 1px solid border-subtle`, `padding: 12px 16px`
- Types: `user-input`, `agent-thinking`, `agent-plan`, `file-create`, `file-modify`, `file-delete`, `command-run`, `summary`
- Each type has distinct left border color and icon

### Component: AgentCard
- Width: 100% of panel
- Collapsed height: `~60px` (header + 1 line preview)
- Expanded height: auto (up to `300px` max, then scroll)
- Click to expand/collapse

### Component: FileTreeItem
- Height: `28px`
- Indent per level: `16px`
- Icon: folder `📁` or file `📄` in `text-secondary`
- Status dot: `6px` circle, positioned `8px` from right edge

### Component: StatusBadge
- Height: `20px`
- Padding: `0 8px`
- Border-radius: `10px` (pill)
- Font: `11px`, weight `600`, uppercase

---

## 6. Responsive Behavior

At viewports narrower than `1200px`:
- Right Agent Panel collapses to a **floating status bar** at the top (showing only current agent + progress)
- Clicking the status bar expands a drawer overlay

At viewports narrower than `900px`:
- Left sidebar collapses to icon-only mode (`40px` wide)
- Bottom terminal fully collapses (accessible via toggle button)

---

## 7. Special States

### Error State
When an agent fails:
- Agent card turns red-left-border
- Error message displayed in the card with `accent-red` background at 10% opacity
- Main workspace shows error block with stack trace in monospace
- `Retry` button appears in the agent card

### Connection Lost
- Top bar status dot turns red and pulses
- A toast/notification appears at top center: "Connection lost. Reconnecting..."
- Input area disabled with overlay

### Loading / Skeleton
On initial app load:
- Sidebar shows 5 skeleton lines (shimmering gray bars)
- Main workspace shows centered loading spinner (rotating braille pattern)
- Agent panel shows 4 placeholder cards

---

## 8. Assets & Icons

Use simple unicode symbols and minimal iconography:
- `>` — User prompt
- `✻` — Thinking/AI activity
- `📁` / `📄` — File system
- `✓` / `✗` — Success / Error
- `●` — Status dots
- `▶` / `▼` — Expand/collapse
- `↻` — Iteration/refresh
- `⚙` — Settings
- `🤖` — App logo

Avoid heavy icon sets. The aesthetic is **terminal-minimal**.

---

## Summary for Stitch

Create a **dark-themed, terminal-inspired desktop application UI** for an AI multi-agent coding tool. The design should feel like a hybrid of a modern code editor (VS Code) and a terminal emulator (iTerm2), with:

1. **3-column layout**: File sidebar | Terminal workspace | Agent status panel
2. **Terminal-style interaction**: User types at a `>` prompt, AI responds in structured blocks
3. **Real-time agent tracking**: Visual timeline showing 4 agents (PM→Architect→Coder→Reviewer) with color-coded status
4. **Inline file operations**: File creation/modification shown inline with diff highlighting
5. **Information-dense but clean**: Every pixel serves a purpose, no wasted space, but not cluttered
6. **Dark palette**: Deep blacks, subtle grays, semantic accent colors (green/yellow/red/blue/purple/cyan/orange/pink)
7. **Monospace-first**: JetBrains Mono for all code and terminal text

Design all 4 viewports (Empty, Running, Completed, Diff) as separate frames in Figma, using consistent spacing and the design system above.
