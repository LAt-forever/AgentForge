# DevAgent Team

Multi-Agent collaborative coding system. PM → Architect → Coder → Reviewer Agents cooperate to build software from natural language requirements.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Architecture

4 specialized Agents orchestrated by a state machine:
- **PM Agent**: Parses requirements into structured specs
- **Architect Agent**: Designs system architecture and module interfaces
- **Coder Agent**: Generates implementation code
- **Reviewer Agent**: Reviews code quality and suggests fixes

## Tech Stack

- Backend: Python, FastAPI, Claude/GPT-4 API
- Frontend: React, TypeScript, Vite, CodeMirror 6
- Communication: WebSocket + REST API
