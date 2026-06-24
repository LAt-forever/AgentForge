# 面试资料库 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `vibe-agent` 仓库根目录下搭建 `面试资料/` 学习资料库骨架，包含完整中文目录结构、元信息文档、编写规范，以及第一篇示例文档。

**Architecture:** 按知识领域组织为六大模块（计算机基础、后端核心、Agent 与 AI、系统设计、面试实战、资源），顶层由 `README.md` 和 `00-元信息/` 统一管控新增文档规范与路线图。

**Tech Stack:** Markdown，纯文档/目录结构，无需代码依赖。

---

## File Structure

### 要创建的目录

```
面试资料/
├── README.md
├── 00-元信息/
│   ├── 使用指南.md
│   ├── 文档编写规范.md
│   ├── 校招自检清单.md
│   └── 术语表.md
├── 01-计算机基础/
│   ├── 操作系统.md
│   ├── 计算机网络.md
│   ├── 数据库原理.md
│   ├── 数据结构.md
│   └── 算法.md
├── 02-后端核心/
│   ├── 编程语言/
│   │   ├── Go深入.md
│   │   └── Java深入.md
│   ├── 并发编程.md
│   ├── 存储/
│   │   ├── MySQL深入.md
│   │   ├── Redis深入.md
│   │   └── Elasticsearch基础.md
│   ├── 消息队列.md
│   ├── 微服务.md
│   ├── DevOps基础.md
│   └── 后端项目.md
├── 03-Agent与AI/
│   ├── 大模型基础.md
│   ├── Agent架构.md
│   ├── RAG系统.md
│   ├── 多Agent协作.md
│   ├── 评估与安全.md
│   ├── Agent项目.md
│   └── Agent面试八股.md
├── 04-系统设计/
│   ├── 设计原则.md
│   ├── 经典场景/
│   │   ├── 短链服务.md
│   │   ├── 限流器.md
│   │   ├── 即时通讯系统.md
│   │   └── Agent平台.md
│   ├── 技术选型与权衡.md
│   └── 面试答题框架.md
├── 05-面试实战/
│   ├── 后端八股100题.md
│   ├── 算法面试.md
│   ├── 项目介绍模板.md
│   ├── 系统设计面试.md
│   ├── 行为面试.md
│   └── 模拟面试记录.md
└── 06-资源/
    ├── 简历/
    │   ├── 模板.md
    │   └── 版本/
    │       ├── 后端通用.md
    │       └── Agent方向.md
    ├── 公司准备/
    │   ├── 字节跳动.md
    │   ├── 阿里巴巴.md
    │   └── 腾讯.md
    └── 链接收藏.md
```

### 资源子目录

- `面试资料/assets/`：图片统一存放处。
- `面试资料/snippets/`：代码片段统一存放处。

---

## Task 1: Create directory skeleton

**Files:**
- Create: all directories listed in File Structure plus `assets/` and `snippets/`

- [ ] **Step 1: Create the top-level `面试资料/` directory and all subdirectories**

Run:
```bash
mkdir -p "面试资料/00-元信息" \
  "面试资料/01-计算机基础" \
  "面试资料/02-后端核心/编程语言" \
  "面试资料/02-后端核心/存储" \
  "面试资料/03-Agent与AI" \
  "面试资料/04-系统设计/经典场景" \
  "面试资料/05-面试实战" \
  "面试资料/06-资源/简历/版本" \
  "面试资料/06-资源/公司准备" \
  "面试资料/assets" \
  "面试资料/snippets"
```

- [ ] **Step 2: Verify the directory tree**

Run:
```bash
find "面试资料" -type d | sort
```

Expected: all directories from File Structure are listed, plus `assets` and `snippets`.

- [ ] **Step 3: Commit**

```bash
git add "面试资料"
git commit -m "chore: create interview prep directory skeleton

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Create README.md with roadmap

**Files:**
- Create: `面试资料/README.md`

- [ ] **Step 1: Write README.md**

Create `面试资料/README.md` with the following content:

```markdown
# 后端设计 + Agent 岗面试学习资料

> 面向校招，主攻后端开发 / Agent（AI 应用）工程方向。

## 学习路线图

| 阶段 | 周期 | 目标 | 对应目录 |
|---|---|---|---|
| 1. 夯实基础 | 第 1-3 周 | 操作系统、网络、数据库、数据结构、算法 | `01-计算机基础/` |
| 2. 后端深入 | 第 4-6 周 | 语言、并发、存储、消息队列、微服务 | `02-后端核心/` |
| 3. Agent 与 AI | 第 7-8 周 | 大模型、Agent 架构、RAG、项目 | `03-Agent与AI/` |
| 4. 系统设计 | 第 9-10 周 | 设计原则、经典场景、答题框架 | `04-系统设计/` |
| 5. 面试实战 | 第 11-12 周 | 八股、算法、项目、行为面、模拟面 | `05-面试实战/` |
| 6. 求职准备 | 持续 | 简历、公司准备、链接收藏 | `06-资源/` |

## 每日使用建议

1. 先读 `00-元信息/使用指南.md`，确认当天学习范围。
2. 学习时按“是什么 → 为什么 → 怎么做 → 面试怎么说”四层整理笔记。
3. 新增文档前先查看 `00-元信息/文档编写规范.md`。

## 目录速览

- `00-元信息/`：使用指南、编写规范、自检清单、术语表。
- `01-计算机基础/`：操作系统、计算机网络、数据库原理、数据结构、算法。
- `02-后端核心/`：编程语言、并发编程、存储、消息队列、微服务、DevOps、后端项目。
- `03-Agent与AI/`：大模型基础、Agent 架构、RAG、多 Agent、评估安全、Agent 项目、八股。
- `04-系统设计/`：设计原则、经典场景、技术选型、答题框架。
- `05-面试实战/`：后端八股、算法面试、项目介绍、系统设计面试、行为面试、模拟记录。
- `06-资源/`：简历模板、公司准备、链接收藏。
```

- [ ] **Step 2: Verify the file exists**

Run:
```bash
ls -la "面试资料/README.md"
```

Expected: file exists.

- [ ] **Step 3: Commit**

```bash
git add "面试资料/README.md"
git commit -m "docs: add interview prep README with roadmap

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Create meta documents

**Files:**
- Create: `面试资料/00-元信息/使用指南.md`
- Create: `面试资料/00-元信息/文档编写规范.md`
- Create: `面试资料/00-元信息/校招自检清单.md`
- Create: `面试资料/00-元信息/术语表.md`

- [ ] **Step 1: Write 使用指南.md**

Create `面试资料/00-元信息/使用指南.md`:

```markdown
# 使用指南

## 这套资料适合谁

- 目标岗位：后端开发 / Agent（AI 应用）工程 / 平台工程。
- 背景：计算机相关专业应届生，或有一定编程基础想转后端/Agent 方向的同学。

## 推荐学习节奏

- **工作日**：每天 1 个知识点（30-60 分钟阅读 + 整理笔记）。
- **周末**：做 2-3 道算法题 + 复盘一周内容 + 更新项目讲稿。
- **考前 2 周**：重点看 `05-面试实战/` 和 `06-资源/公司准备/`。

## 怎么用

1. 按 `README.md` 的路线图顺序推进。
2. 每学完一篇，在文档末尾用自己的话写 3 条“面试回答要点”。
3. 遇到不会或容易混淆的概念，补充到 `术语表.md`。
```

- [ ] **Step 2: Write 文档编写规范.md**

Create `面试资料/00-元信息/文档编写规范.md`:

```markdown
# 文档编写规范

## 新增文档放哪

| 新增内容 | 放置位置 |
|---|---|
| 新增一个知识点 | 按主题放入 `01-计算机基础/`、`02-后端核心/` 或 `03-Agent与AI/` 的对应子目录 |
| 新增一个可讲项目 | `02-后端核心/后端项目.md` 或 `03-Agent与AI/Agent项目.md` 中新增一节 |
| 新增一道系统设计题 | `04-系统设计/经典场景/` 下新建 `<场景名>.md` |
| 新增一类面试题型 | `05-面试实战/` 下新建文档，或在已有文档末尾追加 |
| 新增一家公司准备 | `06-资源/公司准备/` 下新建 `<公司名>.md` |
| 新增简历版本 | `06-资源/简历/版本/` 下新建 `<岗位方向>.md` |
| 新增术语 | `00-元信息/术语表.md` 中追加 |

## 文档模板

每篇新文档建议遵循以下模板：

```markdown
# 标题

## 一句话定义
<!-- 面试时能直接说的 1-2 句话 -->

## 核心原理
<!-- 概念、流程、关键组件 -->

## 为什么这样设计 / 优缺点
<!-- 面试常问的 trade-off -->

## 实际应用 / 项目经验
<!-- 结合自己做过的项目 -->

## 高频面试题
<!-- 3-5 道题 + 回答要点 -->

## 延伸链接
<!-- 论文、博客、源码 -->
```

## 命名与附件规则

- **文件/文件夹**：中文标题，不加序号（目录顺序由 README 维护）。
- **图片**：统一放 `assets/` 子目录，命名 `<文档名>-<序号>.png`。
- **代码片段**：统一放 `snippets/<文档名>/` 下。
- **链接收藏**：`06-资源/链接收藏.md` 按主题分组。
```

- [ ] **Step 3: Write 校招自检清单.md**

Create `面试资料/00-元信息/校招自检清单.md`:

```markdown
# 校招自检清单

## 简历

- [ ] 简历控制在 1 页（最多 2 页）。
- [ ] 项目经历使用 STAR 法则描述。
- [ ] 技术关键词与目标岗位 JD 对齐。
- [ ] 没有错别字和格式错乱。

## 技术准备

- [ ] 操作系统、网络、数据库基础能口头讲清楚核心概念。
- [ ] 至少一门主语言有深入理解（Go/Java/Python）。
- [ ] 有 1-2 个能讲 10 分钟以上的项目。
- [ ] 常见系统设计题能画出架构图并解释 trade-off。
- [ ] Agent 方向问题能讲清楚 RAG / ReAct / Tool Use 的基本流程。

## 面试状态

- [ ] 自我介绍控制在 1-2 分钟。
- [ ] 准备了 3 个“你还有什么想问我的”问题。
- [ ] 行为面问题有具体例子支撑。
```

- [ ] **Step 4: Write 术语表.md**

Create `面试资料/00-元信息/术语表.md`:

```markdown
# 术语表

## 后端

- **QPS**：Queries Per Second，每秒查询数。
- **TPS**：Transactions Per Second，每秒事务数。
- **RT**：Response Time，响应时间。
- **CAP 定理**：一致性、可用性、分区容错性三者不可兼得。
- **BASE**：Basically Available, Soft state, Eventually consistent。

## Agent / AI

- **LLM**：Large Language Model，大语言模型。
- **RAG**：Retrieval-Augmented Generation，检索增强生成。
- **ReAct**：Reasoning + Acting，一种让 LLM 交替思考与行动的 Agent 范式。
- **Tool Use**：LLM 调用外部工具（API、函数、数据库等）完成任务。
```

- [ ] **Step 5: Verify all meta files exist**

Run:
```bash
ls -la "面试资料/00-元信息/"
```

Expected: four `.md` files listed.

- [ ] **Step 6: Commit**

```bash
git add "面试资料/00-元信息/"
git commit -m "docs: add meta documents for interview prep

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Create placeholder topic documents

**Files:**
- Create: all leaf `.md` files in `01-计算机基础/`, `02-后端核心/`, `03-Agent与AI/`, `04-系统设计/`, `05-面试实战/`, `06-资源/`

- [ ] **Step 1: Create placeholder topic files**

Run the following script from the repo root:

```bash
cd "面试资料"

# 01-计算机基础
for f in 操作系统 计算机网络 数据库原理 数据结构 算法; do
  echo "# $f" > "01-计算机基础/$f.md"
done

# 02-后端核心
for f in 并发编程 消息队列 微服务 DevOps基础 后端项目; do
  echo "# $f" > "02-后端核心/$f.md"
done
echo "# Go深入" > "02-后端核心/编程语言/Go深入.md"
echo "# Java深入" > "02-后端核心/编程语言/Java深入.md"
for f in MySQL深入 Redis深入 Elasticsearch基础; do
  echo "# $f" > "02-后端核心/存储/$f.md"
done

# 03-Agent与AI
for f in 大模型基础 Agent架构 RAG系统 多Agent协作 评估与安全 Agent项目 Agent面试八股; do
  echo "# $f" > "03-Agent与AI/$f.md"
done

# 04-系统设计
for f in 设计原则 技术选型与权衡 面试答题框架; do
  echo "# $f" > "04-系统设计/$f.md"
done
for f in 短链服务 限流器 即时通讯系统 Agent平台; do
  echo "# $f" > "04-系统设计/经典场景/$f.md"
done

# 05-面试实战
for f in 后端八股100题 算法面试 项目介绍模板 系统设计面试 行为面试 模拟面试记录; do
  echo "# $f" > "05-面试实战/$f.md"
done

# 06-资源
for f in 模板; do
  echo "# $f" > "06-资源/简历/$f.md"
done
for f in 后端通用 Agent方向; do
  echo "# $f" > "06-资源/简历/版本/$f.md"
done
for f in 字节跳动 阿里巴巴 腾讯; do
  echo "# $f" > "06-资源/公司准备/$f.md"
done
echo "# 链接收藏" > "06-资源/链接收藏.md"
```

- [ ] **Step 2: Verify the file count**

Run from repo root:
```bash
find "面试资料" -name "*.md" -type f | wc -l
```

Expected: 38 (1 README + 4 meta + 33 topic files).

- [ ] **Step 3: Commit**

```bash
git add "面试资料"
git commit -m "docs: add placeholder topic documents for interview prep

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Write the first example document

**Files:**
- Create: `面试资料/01-计算机基础/操作系统.md` (overwrite the placeholder)

- [ ] **Step 1: Replace the placeholder with a full example**

Write the following content to `面试资料/01-计算机基础/操作系统.md`:

```markdown
# 操作系统

## 一句话定义

操作系统是管理计算机硬件与软件资源、为应用程序提供统一接口的系统软件。

## 核心原理

### 进程与线程

- **进程**：资源分配的基本单位，拥有独立的地址空间。
- **线程**：CPU 调度的基本单位，共享进程的资源。
- **协程**：用户态轻量级线程，由程序自己调度，切换开销小。

### 内存管理

- **虚拟内存**：让每个进程认为自己拥有完整地址空间，通过页表映射到物理内存。
- **页表 / 页缺中断**：访问不在物理内存中的页时触发缺页中断，由 OS 加载数据。
- **TLB**：页表的高速缓存，加速虚拟地址到物理地址的转换。

### IO 模型

- **阻塞 IO**：调用一直等待数据就绪。
- **非阻塞 IO**：立即返回，需要轮询。
- **IO 多路复用**：select/poll/epoll，一个线程管理多个连接。
- **异步 IO**：内核完成 IO 后通知应用。

## 为什么这样设计 / 优缺点

- 进程隔离提高稳定性，但上下文切换开销大。
- 线程共享内存，通信成本低，但需要同步机制避免数据竞争。
- 虚拟内存提高了内存利用率，但增加了地址转换开销。

## 实际应用 / 项目经验

- 在高并发服务中使用线程池 + IO 多路复用（如 Go 的 netpoll、Java NIO）。
- 使用协程（Go goroutine）降低高并发场景下的切换成本。

## 高频面试题

1. **进程和线程的区别？**
   - 进程是资源单位，线程是调度单位；线程共享进程地址空间。
2. **什么是虚拟内存？**
   - 通过页表将虚拟地址映射到物理地址，实现内存隔离和超过物理内存的寻址。
3. **select、poll、epoll 的区别？**
   - select/poll 需要遍历所有 fd；epoll 基于事件通知，适合高并发连接。
4. **进程间通信方式有哪些？**
   - 管道、消息队列、共享内存、信号量、套接字。

## 延伸链接

- 《操作系统导论》（Operating Systems: Three Easy Pieces）
- Linux epoll 源码分析
```

- [ ] **Step 2: Verify the example content**

Run:
```bash
head -n 20 "面试资料/01-计算机基础/操作系统.md"
```

Expected: starts with `# 操作系统` and includes `## 一句话定义`.

- [ ] **Step 3: Commit**

```bash
git add "面试资料/01-计算机基础/操作系统.md"
git commit -m "docs: add operating systems example document

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage**: 目录结构、每篇讲什么、新增文档规范、命名规则均已对应到 Task 1-5。
- **Placeholder scan**: 无 TBD/TODO；所有文档内容已给出完整示例。
- **Type consistency**: 文件路径与 `docs/superpowers/specs/2026-06-24-interview-prep-design.md` 中的目录结构一致。
