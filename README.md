# DevAgent Team

Multi-Agent collaborative coding system. PM → Architect → Coder → Reviewer Agents cooperate to build software from natural language requirements.

## Demo

![DevAgent Demo](docs/demo.gif)

## Architecture

```
User Requirement
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PM Agent   │───▶│   Architect │───▶│    Coder    │───▶│  Reviewer   │
│  (Analyze)  │    │   (Design)  │    │  (Implement)│    │  (Review)   │
└─────────────┘    └─────────────┘    └──────┬──────┘    └──────┬──────┘
                                             │                   │
                                             │     Not Passed    │
                                             │◄──────────────────┘
                                             │    (max 3 loops)
                                             │
                                             ▼
                                        ┌─────────┐
                                        │  DONE   │
                                        └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API Key (or OpenAI API Key)

### Backend

```bash
cd backend
pip install -r ../requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, WebSocket |
| LLM | Claude 3.5 Sonnet / GPT-4o |
| Frontend | React 18, TypeScript, Vite |
| Editor | CodeMirror 6 |
| State | Zustand |
| Styling | CSS Variables (Codex-style dark theme) |

## Project Structure

```
devagent-team/
├── backend/           # Python FastAPI backend
│   ├── agents/        # 4 specialized Agents
│   ├── orchestrator/  # State machine + scheduler
│   ├── llm/           # LLM client + prompts
│   ├── core/          # Message bus + state store
│   └── tools/         # File manager + code runner
├── frontend/          # React TypeScript frontend
│   ├── components/    # UI components
│   ├── store/         # Zustand state
│   └── hooks/         # WebSocket hook
└── output/            # Agent-generated files
```

## Interview Topics

This project demonstrates:

- **Multi-Agent Orchestration**: Handwritten state machine for coordinating 4 AI Agents
- **LLM Application Design**: Structured prompts, output parsing, model fallback
- **Real-time Communication**: WebSocket for live Agent status streaming
- **Code Generation Pipeline**: From spec → architecture → code → review
- **Error Handling**: Retry with backoff, circuit breaker pattern, graceful degradation
- **Full-stack Development**: FastAPI + React with TypeScript

## License

MIT
