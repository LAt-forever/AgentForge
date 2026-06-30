# Agent平台

## 一句话定义

Agent 平台是一个支持**多 Agent 编排调度**、**Tool 动态调用**和**任务状态管理**的分布式执行框架，核心挑战在于 Agent 间协作、LLM 调用成本控制和长任务可靠性。

## 核心原理

### 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent 平台架构                                │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐     │
│  │  Client  │───→│  API Gateway │───→│   Orchestrator       │     │
│  │ (Web/CLI)│    │  (鉴权/限流)  │    │   (编排调度引擎)      │     │
│  └──────────┘    └──────────────┘    └──────────┬───────────┘     │
│                                                  │                  │
│                     ┌────────────────────────────┼────────────┐   │
│                     ↓                            ↓            ↓   │
│              ┌────────────┐              ┌──────────┐   ┌────────┐│
│              │  Agent     │              │  Tool    │   │ LLM   ││
│              │  Registry  │              │  Registry│   │Service││
│              │(Agent 发现)│              │(Tool 发现)│   │(模型调用)││
│              └─────┬──────┘              └────┬─────┘   └───┬────┘│
│                    │                          │             │      │
│         ┌────────┼────────┐          ┌──────┴──────┐     │      │
│         ↓        ↓        ↓          ↓             ↓     ↓      │
│      ┌────┐   ┌────┐   ┌────┐     ┌──────┐    ┌──────┐ ┌────┐ │
│      │A-1 │   │A-2 │   │A-3 │     │Search│    │Code  │ │GPT │ │
│      │订单│   │库存│   │客服│     │Engine│    │Exec  │ │Claude│ │
│      │Agent│   │Agent│   │Agent│     │      │    │      │ │    │ │
│      └────┘   └────┘   └────┘     └──────┘    └──────┘ └────┘ │
│                                                                     │
│  存储层：                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  MySQL   │  │  Redis   │  │  MongoDB │  │  Object  │            │
│  │(任务/会话)│  │(状态缓存)│  │(执行日志)│  │  Store   │            │
│  └──────────┘  └──────────┘  └──────────┘  │(文件/图片)│            │
│                                           └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. Orchestrator（编排调度引擎）

**职责**：接收用户请求，解析意图，调度 Agent 执行，管理任务状态。

```
编排模式：
┌─────────────────────────────────────────────────────────────┐
│  ① 串行编排（Sequential）                                    │
│     用户请求 → Agent-A → Agent-B → Agent-C → 结果           │
│     适用：有依赖关系的任务链                                  │
│                                                             │
│  ② 并行编排（Parallel）                                      │
│     用户请求 → [Agent-A, Agent-B, Agent-C] → 聚合 → 结果    │
│     适用：独立子任务同时执行                                  │
│                                                             │
│  ③ 条件编排（Conditional）                                   │
│     用户请求 → 判断 → Agent-A 或 Agent-B → 结果               │
│     适用：路由决策                                            │
│                                                             │
│  ④ 循环编排（Loop）                                          │
│     用户请求 → Agent-A → 检查条件 → 继续或结束               │
│     适用：迭代优化、多轮对话                                  │
│                                                             │
│  ⑤ 混合编排（DAG）                                           │
│     有向无环图，支持复杂依赖关系                              │
│     适用：工作流引擎                                          │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Agent 定义与注册

**Agent 元数据结构**：
```json
{
  "agent_id": "order-agent-v1",
  "name": "订单处理 Agent",
  "description": "处理用户订单查询、创建、取消等操作",
  "version": "1.0.0",
  "capabilities": ["query_order", "create_order", "cancel_order"],
  "tools": ["order_db_query", "inventory_check", "payment_api"],
  "llm_config": {
    "model": "gpt-4",
    "temperature": 0.2,
    "max_tokens": 2000
  },
  "system_prompt": "你是一个订单处理助手...",
  "max_execution_time": 30,
  "retry_policy": {
    "max_retries": 3,
    "backoff": "exponential"
  }
}
```

**Agent 注册中心**：
- 存储：etcd / Consul / MySQL
- 功能：Agent 发现、版本管理、健康检查、负载均衡
- 动态更新：Agent 配置变更无需重启平台

#### 3. Tool 注册与调用

**Tool 定义（OpenAI Function Calling 风格）**：
```json
{
  "type": "function",
  "function": {
    "name": "search_product",
    "description": "根据关键词搜索商品",
    "parameters": {
      "type": "object",
      "properties": {
        "keyword": {"type": "string", "description": "搜索关键词"},
        "category": {"type": "string", "enum": ["electronics", "clothing"]},
        "limit": {"type": "integer", "default": 10}
      },
      "required": ["keyword"]
    }
  }
}
```

**Tool 调用流程**：
```
1. LLM 生成 function_call 请求（模型决定调用哪个 Tool）
2. Orchestrator 解析调用意图
3. 根据 tool_name 查找 Tool Registry
4. 参数校验（JSON Schema 验证）
5. 执行 Tool（HTTP / RPC / 本地函数）
6. 将 Tool 结果返回给 LLM
7. LLM 生成最终回复
```

**Tool 执行安全**：
- 沙箱隔离：代码执行类 Tool 在 Docker 沙箱中运行
- 权限控制：每个 Tool 绑定 ACL，限制可访问资源
- 超时控制：Tool 执行设置超时（默认 30 秒）
- 熔断降级：Tool 失败率过高时自动熔断

#### 4. 执行引擎

**任务状态机**：
```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ PENDING │───→│ RUNNING │───→│WAITING  │───→│COMPLETED│    │ FAILED  │
│ (待执行) │    │ (执行中) │    │(等工具)  │───→│ (完成)  │───→│ (失败)  │
└─────────┘    └────┬────┘    └────┬────┘    └─────────┘    └────┬────┘
                    │              │                            │
                    └──────────────┘                            │
                    (LLM 生成中 / Tool 执行中)                   │
                                                                │
                    ┌───────────────────────────────────────────┘
                    ↓
              ┌─────────┐
              │ RETRYING│
              │ (重试中) │
              └─────────┘
```

**长任务处理**：
- 问题：LLM 调用可能耗时 10-30 秒，HTTP 连接不能一直挂起
- 方案：异步执行 + 回调/轮询
```
客户端提交任务 → 返回 task_id
                    ↓
              客户端轮询 / WebSocket 推送
                    ↓
              任务完成 → 返回结果
```

### 存储设计

**会话表（Session）**：
```sql
CREATE TABLE session (
    session_id VARCHAR(64) PRIMARY KEY,  -- UUID
    user_id BIGINT NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    status ENUM('active', 'closed', 'expired'),
    context JSON,                         -- 会话上下文（变量、记忆）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    expires_at TIMESTAMP,                  -- 会话过期时间
    INDEX idx_user (user_id, updated_at)
);
```

**任务表（Task）**：
```sql
CREATE TABLE task (
    task_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    parent_task_id VARCHAR(64),           -- 支持子任务
    agent_id VARCHAR(64) NOT NULL,
    status ENUM('pending', 'running', 'waiting', 'completed', 'failed', 'cancelled'),
    input TEXT,                           -- 任务输入
    output TEXT,                          -- 任务输出
    tool_calls JSON,                      -- 工具调用记录
    error TEXT,                           -- 错误信息
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_session (session_id, created_at)
);
```

**消息历史（Message History）**：
- 存储：MongoDB（Schema 灵活，适合对话消息）
- 结构：每条消息包含 role（system/user/assistant/tool）、content、timestamp
- 截断策略：超出 token 限制时，保留最近 N 轮 + 关键摘要

### LLM 调用优化

| 优化手段 | 原理 | 效果 |
|----------|------|------|
| 请求合并 | 将多个独立请求批量发送 | 减少 RTT |
| 流式响应 | SSE 逐字返回 | 降低首字延迟 |
| 缓存层 | 相同 prompt 缓存结果 | 减少 30-50% 调用 |
| 模型路由 | 简单任务用小模型（GPT-3.5），复杂任务用大模型（GPT-4） | 降低成本 70% |
| 超时降级 | LLM 超时后返回兜底回复 | 保证可用性 |

**成本估算**：
- GPT-4：$0.03/1K tokens（输入）+ $0.06/1K tokens（输出）
- 单次对话平均 2000 tokens → $0.09/次
- 日活 10 万，人均 10 次对话 → 100 万次/天 → $90,000/天
- 优化后（缓存+模型路由）：降低 60% → $36,000/天

## 为什么这样设计 / 优缺点

| 设计点 | 优点 | 缺点 | 权衡 |
|--------|------|------|------|
| 编排引擎 | 灵活支持多种执行模式 | 复杂工作流调试困难 | 先支持串行+并行，再扩展 DAG |
| Tool Registry | 动态发现，热更新 | 需要统一接口规范 | 基于 OpenAPI / Function Calling 标准 |
| 异步执行 | 支持长任务，不阻塞客户端 | 状态管理复杂 | 长任务必选，短任务可同步 |
| 多模型路由 | 大幅降低成本 | 需要评估模型能力边界 | 简单任务用 GPT-3.5，复杂用 GPT-4 |
| 会话上下文 | 支持多轮对话 | 上下文过长影响性能 | 自动摘要 + 关键信息提取 |

## 实际应用 / 项目经验

**电商客服 Agent 示例**：
```
用户："我想查一下昨天买的手机到哪了"

Orchestrator 解析意图 → 路由到"订单 Agent"

订单 Agent 执行：
1. 提取实体：商品=手机，时间=昨天
2. 调用 Tool：search_order(user_id, keyword="手机", date="yesterday")
3. Tool 返回：订单 #12345，状态=已发货，物流=顺丰
4. 调用 Tool：query_logistics(order_id=12345)
5. Tool 返回：当前位置=上海转运中心，预计明天送达
6. LLM 生成回复："您的订单 #12345（iPhone 15）已发货，
   目前在上海转运中心，预计明天送达。"
```

**多 Agent 协作示例（旅游规划）**：
```
用户："帮我规划一个 5 天日本游"

Orchestrator 分解任务：
├─ 航班 Agent：查询机票 → 推荐东京往返航班
├─ 酒店 Agent：查询住宿 → 推荐新宿区域酒店
├─ 景点 Agent：推荐行程 → 生成每日路线
├─ 签证 Agent：检查护照 → 提醒签证要求
└─ 汇总 Agent：整合结果 → 生成完整行程单

并行执行 → 聚合结果 → 返回用户
```

**安全与沙箱设计**：
```
代码执行 Tool：
用户请求 → 代码生成 → 沙箱执行（Docker）
              ↓
         限制：CPU 1核、内存 256MB、网络隔离、超时 30s
              ↓
         执行结果 → 返回 LLM → 生成回复
```

## 高频面试题

**Q1: Agent 和传统的 Rule-based 聊天机器人有什么区别？**
> Rule-based：基于关键词匹配和固定规则，无法处理未知输入，维护成本高。Agent：基于 LLM 理解意图，可动态调用 Tool 获取实时信息，具备推理和规划能力。本质区别：**从"匹配模式"到"理解+行动"**。Agent 更适合开放域、需要实时数据、多步骤推理的场景。

**Q2: 怎么防止 LLM 调用 Tool 时出现循环调用？**
> 三层防护：① **最大步数限制**：单轮对话最多 10 次 Tool 调用；② **调用去重**：记录已调用 Tool + 参数，相同调用直接返回缓存；③ **意图检测**：若连续多次调用相同 Tool 且无进展，强制终止并返回提示。④ **人工介入**：复杂任务拆分为多轮，每轮人工确认后再继续。

**Q3: 多个 Agent 之间怎么共享上下文？**
> 两种模式：① **共享会话上下文**：所有 Agent 读写同一个 Session 的 context 字段，类似全局变量；② **消息传递**：Agent-A 的输出作为 Agent-B 的输入，类似管道。推荐混合模式：公共信息（用户信息、环境配置）放共享上下文，Agent 专属信息通过消息传递，避免耦合。

**Q4: LLM 调用超时或失败怎么处理？**
> 三级降级：① **重试**：指数退避重试 3 次；② **降级模型**：GPT-4 超时 → 降级到 GPT-3.5 或本地模型；③ **兜底回复**：返回预设模板（"服务繁忙，请稍后重试"）；④ **异步处理**：非实时场景入队列，后台处理完成后通知用户。同时监控 LLM 延迟 P99，超过阈值告警。

**Q5: 怎么评估 Agent 的效果？**
> 三个维度：① **任务完成率**：用户请求是否被正确理解和执行；② **用户满意度**：对话轮数、是否转人工、用户评分；③ **成本效率**：单次对话的 token 消耗、模型调用次数。具体指标：准确率（意图识别）、召回率（Tool 调用）、F1（综合）、平均对话轮数、LLM 成本/会话。

**Q6: 长会话的上下文窗口超限怎么办？**
> ① **滑动窗口**：保留最近 N 轮对话，丢弃早期消息；② **关键信息提取**：用 LLM 将历史对话摘要为关键事实，替代原始消息；③ **分层记忆**：短期记忆（当前会话）、长期记忆（用户画像）、工作记忆（当前任务变量）；④ **RAG 增强**：将历史消息存入向量数据库，需要时检索相关片段注入上下文。

**Q7: 如何保证 Tool 调用的安全性？**
> ① **权限最小化**：每个 Tool 绑定 OAuth Scope，只能访问授权资源；② **参数校验**：JSON Schema 严格校验，防止 SQL 注入和 XSS；③ **沙箱执行**：代码类 Tool 在隔离容器运行；④ **审计日志**：所有 Tool 调用记录操作人、参数、结果，支持追溯；⑤ **人工审批**：敏感操作（转账、删除）需人工确认。

## 延伸链接

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [LangChain 框架](https://python.langchain.com/)
- [AutoGen - 多 Agent 对话](https://microsoft.github.io/autogen/)
- [ReAct 论文 - 推理+行动](https://arxiv.org/abs/2210.03629)
- [LLM Agent 综述](https://lilianweng.github.io/posts/2023-06-23-llm-agent/)
