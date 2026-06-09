# DevAgent Team — 多 Agent 协作编程系统

## 项目概述

一个模拟软件开发全流程的多 Agent 协作系统。用户输入自然语言需求，由 PM Agent、Architect Agent、Coder Agent、Reviewer Agent 四个专业角色协作完成从需求分析到代码交付的全过程。Reviewer 不通过时自动触发修改-审查循环，直到代码通过或达到最大迭代次数。

前端采用类似 GitHub Copilot Workspace（Codex）的 IDE 风格三栏布局，通过 WebSocket 实时展示各 Agent 的执行状态和产出物。

**目标**：作为 Agent AI 方向实习简历的核心项目，展示多 Agent 编排、状态机设计、LLM 编程应用、全栈开发能力。

---

## 核心设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| Agent 编排方式 | 手写状态机，不依赖 LangChain/LangGraph | 面试核心话题：展示对 Agent 编排原理的深度理解 |
| UI 风格 | React 三栏 Codex 风格 | 直观展示 Agent 协作过程，面试演示效果最佳 |
| 通信方式 | WebSocket + HTTP REST | WebSocket 实时推送状态，HTTP 读取文件内容 |
| LLM 支持 | Claude (默认) + GPT-4 (备用) | Claude 3.5/4 编程能力最强，支持降级 |
| 代码执行 | subprocess + 可选 Docker 沙箱 | 验证生成代码的可运行性，确保安全 |

---

## 系统架构

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer: React 前端 (Codex 风格三栏布局)       │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ 文件树    │ │ 代码编辑器    │ │ Agent 工作流面板      │ │
│  │ (左侧)   │ │ (中间)       │ │ (右侧)              │ │
│  └──────────┘ └──────────────┘ └──────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Communication Layer: WebSocket + HTTP REST              │
├─────────────────────────────────────────────────────────┤
│  Orchestrator Layer: 状态机 + Agent 调度器                │
│  (orchestrator/state_machine.py + scheduler.py)         │
├─────────────────────────────────────────────────────────┤
│  Agent Layer: 4 个专业 Agent                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ PM Agent │ │ Architect│ │  Coder   │ │ Reviewer │   │
│  │ (需求)   │ │ (架构)   │ │ (编码)   │ │ (审查)   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│  Infrastructure Layer:                                   │
│  LLM Client │ Message Bus │ State Store │ Code Runner   │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 文件 | 职责 |
|---|---|---|
| **Orchestrator** | `orchestrator/state_machine.py` | 维护全局状态机，决定下一步执行哪个 Agent |
| **Scheduler** | `orchestrator/scheduler.py` | Agent 执行调度，管理并发/串行执行 |
| **PM Agent** | `agents/pm_agent.py` | 将自然语言需求解析为结构化功能规格 |
| **Architect Agent** | `agents/architect_agent.py` | 根据功能规格设计系统架构、模块划分、接口定义 |
| **Coder Agent** | `agents/coder_agent.py` | 根据架构文档生成具体代码实现 |
| **Reviewer Agent** | `agents/reviewer_agent.py` | 审查代码质量、规范性、Bug，输出评审意见 |
| **LLM Client** | `llm/client.py` | 统一封装大模型调用，支持重试、流式、多 Provider |
| **Message Bus** | `core/message_bus.py` | Agent 间松耦合通信，产出物标准化传递 |
| **State Store** | `core/state_store.py` | 持久化每个阶段的中间产物，支持断点续跑 |
| **Code Runner** | `tools/code_runner.py` | 安全执行生成的代码，验证可运行性 |

---

## Agent 工作流（状态机）

```
┌─────────┐     ┌───────────┐     ┌────────────┐     ┌──────────┐
│  IDLE   │────▶│  PLANNING │────▶│  DESIGNING │────▶│  CODING  │
│ (等待)  │     │ (PM分析)  │     │ (架构设计) │     │ (编码)   │
└─────────┘     └───────────┘     └────────────┘     └────┬─────┘
                                                          │
                               ┌──────────────────────────┘
                               ▼
                          ┌───────────┐     ┌─────────┐
                     ┌────│ REVIEWING │────▶│  DONE   │
                     │No  │ (审查)    │ Yes │ (完成)  │
                     └────┴────┬──────┘     └─────────┘
                          (循环 ≤ 3 次)
```

### 状态转换规则

| 当前状态 | 触发条件 | 下一个状态 | 说明 |
|---|---|---|---|
| `IDLE` | 用户提交需求 | `PLANNING` | 初始化项目，触发 PM Agent |
| `PLANNING` | PM Agent 完成 | `DESIGNING` | PM 输出功能规格，触发 Architect |
| `DESIGNING` | Architect 完成 | `CODING` | Architect 输出架构设计，触发 Coder |
| `CODING` | Coder 完成 | `REVIEWING` | Coder 输出代码文件，触发 Reviewer |
| `REVIEWING` | Reviewer 通过 | `DONE` | 代码审查通过，流程结束 |
| `REVIEWING` | Reviewer 不通过（< 3次）| `CODING` | Coder 根据审查意见修改代码 |
| `REVIEWING` | Reviewer 不通过（≥ 3次）| `DONE` | 取最后一次代码，标记"部分通过" |

---

## 数据流

### 1. 用户提交需求

```
用户(前端) ──HTTP POST /api/projects──▶ FastAPI ──▶ Orchestrator
                                            │
                                            ▼
                                    初始化 State Store
                                    状态: IDLE → PLANNING
                                    触发 PM Agent
```

### 2. Agent 执行与状态推送

```
Orchestrator ──▶ Agent 执行 ──▶ 产出物写入文件系统
     │                              │
     │                              ▼
     │                        State Store 更新
     │                              │
     ▼                              ▼
WebSocket 推送 ◄────────────────── 状态变更
     │
     ▼
React 前端实时更新 Agent 状态面板
```

### 3. 前端读取文件内容

```
React ──HTTP GET /api/projects/{id}/files/{path}──▶ FastAPI ──▶ 文件系统
                                                           │
                                                           ▼
                                                    返回文件内容
                                                           │
                                                           ▼
                                                    CodeMirror 展示代码
```

### WebSocket 消息协议

```typescript
// Agent 状态更新
interface AgentStatusMessage {
  type: "agent_status";
  project_id: string;
  agent: "pm" | "architect" | "coder" | "reviewer";
  status: "idle" | "running" | "completed" | "failed";
  progress: number;  // 0-100
  output?: {
    files_created?: string[];
    summary?: string;
    review_issues?: ReviewIssue[];
  };
  timestamp: string;
}

// 全局状态更新
interface WorkflowStateMessage {
  type: "workflow_state";
  project_id: string;
  state: "idle" | "planning" | "designing" | "coding" | "reviewing" | "done";
  overall_progress: number;
  iteration_count: number;  // 审查循环次数
}

interface ReviewIssue {
  severity: "error" | "warning" | "suggestion";
  file?: string;
  line?: number;
  message: string;
  suggestion?: string;
}
```

---

## UI 设计

### 布局：Codex 风格三栏 IDE

```
┌─────────────────────────────────────────────────────────────────────┐
│  [🤖 DevAgent]  项目: todo-app                      [运行] [⚙️]   │
├──────────┬──────────────────────────────┬───────────────────────────┤
│          │                              │  🤖 Agent Workspace       │
│  📁 文件树 │                              │  ───────────────────────  │
│          │   (CodeMirror 代码编辑器)      │                           │
│  src/    │                              │  ▶ PM Agent               │
│   main.py│   def hello():               │    ✓ 需求分析完成          │
│   ...    │     pass                     │    输出: spec.md          │
│          │                              │                           │
│          │                              │  ▶ Architect Agent        │
│          │                              │    ✓ 架构设计完成          │
│          │                              │    输出: architecture.md  │
│          │                              │                           │
│          │                              │  ▶ Coder Agent            │
│          │                              │    🔄 正在生成代码...       │
│          │                              │    进度: 75%              │
│          │                              │                           │
│          │                              │  📋 整体进度 [██████░░░░]  │
└──────────┴──────────────────────────────┴───────────────────────────┘
```

### 组件列表

| 组件 | 文件 | 功能 |
|---|---|---|
| **Layout** | `components/Layout.tsx` | 三栏布局骨架，响应式调整 |
| **FileTree** | `components/FileTree.tsx` | 左侧文件树，支持点击打开文件 |
| **CodeEditor** | `components/CodeEditor.tsx` | 中间代码编辑区，CodeMirror 6 |
| **AgentPanel** | `components/AgentPanel.tsx` | 右侧 Agent 工作流总览 |
| **AgentCard** | `components/AgentCard.tsx` | 单个 Agent 状态卡片（idle/running/completed/failed） |
| **ProgressBar** | `components/ProgressBar.tsx` | 整体任务进度 |
| **ChatInput** | `components/ChatInput.tsx` | 底部需求输入框 |
| **ReviewReport** | `components/ReviewReport.tsx` | 审查报告展示（问题列表 + 建议） |

### 主题设计

采用深色主题，参考 Codex / VS Code 风格：

```css
:root {
  --bg-primary: #0d1117;      /* 主背景 */
  --bg-secondary: #161b22;    /* 侧边栏背景 */
  --bg-tertiary: #21262d;     /* 卡片/输入框背景 */
  --border-color: #30363d;    /* 边框 */
  --text-primary: #c9d1d9;    /* 主文字 */
  --text-secondary: #8b949e;  /* 次要文字 */
  --accent-blue: #58a6ff;     /* 强调色（运行中） */
  --accent-green: #238636;    /* 成功 */
  --accent-yellow: #d29922;   /* 警告 */
  --accent-red: #da3633;      /* 错误 */
}
```

---

## 技术选型

### 后端

| 技术 | 版本 | 用途 |
|---|---|---|
| Python | 3.11+ | 主语言 |
| FastAPI | 0.110+ | Web 框架 + WebSocket |
| anthropic | 最新 | Claude API 调用 |
| openai | 最新 | GPT-4 备用 |
| pydantic | 2.x | 数据验证 |
| pytest | 最新 | 单元/集成测试 |
| python-multipart | 最新 | 文件上传 |

### 前端

| 技术 | 版本 | 用途 |
|---|---|---|
| React | 18.3+ | UI 框架 |
| TypeScript | 5.4+ | 类型安全 |
| Vite | 5.x | 构建工具 |
| Zustand | 4.x | 状态管理 |
| CodeMirror 6 | 最新 | 代码编辑器 |
| CSS Variables | - | 主题系统 |

---

## 项目结构

```
devagent-team/
├── README.md
├── requirements.txt
├── pyproject.toml
│
├── backend/
│   ├── main.py
│   ├── config.py
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── state_machine.py
│   │   ├── scheduler.py
│   │   └── websocket_manager.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── pm_agent.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   └── reviewer_agent.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── models.py
│   │   └── prompts/
│   │       ├── pm_prompt.txt
│   │       ├── architect_prompt.txt
│   │       ├── coder_prompt.txt
│   │       └── reviewer_prompt.txt
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── code_runner.py
│   │   ├── file_manager.py
│   │   └── git_utils.py
│   │
│   └── core/
│       ├── __init__.py
│       ├── message_bus.py
│       └── state_store.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── store/
│   │   │   └── useStore.ts
│   │   │
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── FileTree.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── AgentPanel.tsx
│   │   │   ├── AgentCard.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ReviewReport.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   └── useAgentStatus.ts
│   │   │
│   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   └── styles/
│   │       └── theme.css
│   │
│   └── public/
│
└── output/
    └── .gitkeep
```

---

## Agent 详细设计

### BaseAgent（抽象基类）

所有 Agent 继承自 `BaseAgent`，统一接口：

```python
class BaseAgent(ABC):
    def __init__(self, name: str, llm_client: LLMClient):
        self.name = name
        self.llm = llm_client

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentOutput:
        """执行 Agent 任务，返回产出物"""
        pass

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """统一 LLM 调用，内置重试"""
        pass
```

### PM Agent

**输入**：用户自然语言需求描述  
**输出**：`spec.md` — 结构化功能规格说明书

**Prompt 设计要点**：
- 要求输出 Markdown 格式，包含：功能概述、用户故事、功能列表、非功能需求、约束条件
- 如果需求有歧义，标记出来而不是猜测
- 输出必须是结构化的，方便下游 Agent 消费

### Architect Agent

**输入**：`spec.md`（PM Agent 产出）  
**输出**：`architecture.md` — 架构设计文档

**Prompt 设计要点**：
- 要求输出：模块划分、每个模块的职责、模块间接口定义、数据流图（文本描述）、技术选型建议
- 为 Coder Agent 提供足够详细的实现指导

### Coder Agent

**输入**：`architecture.md` + `spec.md` + 审查意见（如果有）  
**输出**：源代码文件（多文件）

**Prompt 设计要点**：
- 一次生成完整的项目代码，多文件输出
- 每个文件标注文件路径
- 代码必须有适当的注释和错误处理
- 如果是修改模式（有审查意见），只修改被指出的问题

### Reviewer Agent

**输入**：所有源代码文件 + `spec.md` + `architecture.md`  
**输出**：`review.md` — 审查报告（结构化 JSON + 可读文本）

**审查维度**：
1. 功能完整性：是否实现了 spec 中所有功能
2. 代码质量：可读性、命名规范、注释
3. Bug 检查：明显的逻辑错误、边界条件
4. 架构遵循：是否符合 architecture.md 的设计

**输出格式**：
```json
{
  "passed": false,
  "issues": [
    {
      "severity": "error",
      "file": "main.py",
      "line": 15,
      "message": "变量未定义",
      "suggestion": "在使用前初始化变量"
    }
  ],
  "summary": "存在 1 个错误需要修复"
}
```

---

## 错误处理策略

| 错误场景 | 处理策略 | 降级方案 |
|---|---|---|
| **LLM API 调用失败** | 指数退避重试，最多 3 次 | 切换到备用模型（Claude → GPT-4） |
| **LLM 输出格式错误** | JSON Schema 约束，解析失败要求重试 | 3 次失败后标记 Agent 为 failed |
| **代码语法错误** | `python -m py_compile` 自动检查 | Coder Agent 自动修复或重试生成 |
| **审查循环不收敛** | 最大迭代 3 次 | 取最后一次代码，标记"部分通过" |
| **WebSocket 断开** | 前端自动重连（指数退避） | 后端状态持久化，支持断点续跑 |
| **代码执行超时** | 30 秒超时自动终止 | 标记该代码为"未通过运行测试" |
| **代码执行危险操作** | Docker 沙箱隔离（可选） | 默认限制文件系统访问范围 |

---

## 测试策略

### 单元测试

| 测试目标 | 工具 | 覆盖点 |
|---|---|---|
| State Machine | pytest | 所有状态转换路径 |
| 每个 Agent | pytest + mock LLM | Agent 输入输出逻辑 |
| LLM Client | pytest + mock | 重试逻辑、降级逻辑 |
| Code Runner | pytest | 语法检查、超时处理 |

### 集成测试

| 测试目标 | 方法 | 验证点 |
|---|---|---|
| 完整工作流 | pytest + mock LLM | 从需求输入到代码输出的端到端流程 |
| WebSocket 通信 | 手动 + 自动化 | 状态推送、前端接收 |

### 演示用例

准备 3 个不同复杂度的需求用于面试演示：

1. **简单** — "写一个命令行 Todo List 应用，支持添加、列出、删除任务，数据用 JSON 文件存储"
2. **中等** — "写一个 Python 网页爬虫，爬取 Hacker News 首页标题和链接，保存为 JSON 文件"
3. **较复杂** — "写一个 REST API 服务，实现用户注册和登录，使用 SQLite 存储数据，FastAPI 框架，包含密码哈希和 JWT 验证"

---

## 面试话题地图

这个项目可以展开的面试话题：

### Agent 编排
- 为什么选择状态机而不是 DAG？
- 审查循环如何设计？最大迭代次数怎么定？
- Agent 间通信协议是怎么设计的？
- 未来如何支持并行 Agent 执行？

### LLM 应用
- 每个 Agent 的 Prompt 怎么设计？如何确保输出可被下游消费？
- 模型选择策略？Claude vs GPT-4 的编程能力对比？
- Token 管理：长上下文怎么处理（architecture + code）？
- 输出格式约束：JSON Schema、Few-shot prompting

### 工程实践
- 如何确保生成代码的可运行性？
- 错误处理：重试、降级、超时、沙箱
- 状态持久化：如何实现断点续跑？
- WebSocket 实时通信的设计

### 系统思考
- 如果 Reviewer 和 Coder 陷入无限循环怎么办？
- 如何让 Reviewer 的审查标准一致？
- 代码生成质量如何评估？
- 多文件项目如何管理上下文窗口？

---

## 排期估算（约 2 周）

| 阶段 | 天数 | 内容 |
|---|---|---|
| Day 1-2 | 2 | 项目骨架搭建：目录结构、配置、LLM Client |
| Day 3-4 | 2 | Core 基础设施：Message Bus、State Store、File Manager |
| Day 5-6 | 2 | Agent 实现：BaseAgent + 4 个 Agent + Prompts |
| Day 7-8 | 2 | Orchestrator：状态机、Scheduler、WebSocket Manager |
| Day 9-10 | 2 | 后端集成：FastAPI 路由、完整工作流联调 |
| Day 11-12 | 2 | 前端骨架：React 布局、CodeMirror、主题 |
| Day 13-14 | 2 | 前端功能：WebSocket 连接、Agent 面板、文件树 |
| Day 15 | 1 | 联调、测试、修复、录制演示 GIF |

**加班节奏**：如果每天加 3-4 小时，约 **8-10 天**可以完成。
