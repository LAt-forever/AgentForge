# 多 Agent 协作

## 一句话定义

多 Agent 协作（Multi-Agent Collaboration）是指多个具有不同角色、能力或视角的 AI Agent 通过通信、协商和任务分配，共同完成单个 Agent 难以独立解决的复杂任务的系统架构。

## 核心原理

当任务复杂度超出单个 Agent 的能力范围时，将任务分解给多个专业化 Agent 协作完成，类似于人类团队的分工合作。多 Agent 系统的核心挑战在于：如何设计 Agent 的角色、如何协调它们之间的通信、如何解决冲突和依赖关系。

### 1. Multi-Agent 架构

**常见架构模式：**

**A. 层级架构（Hierarchical）**

```
        [主管 Agent / 协调者]
              /        \
             /          \
    [子 Agent 1]    [子 Agent 2]    [子 Agent 3]
        |                 |                 |
    [工具/数据]       [工具/数据]       [工具/数据]
```

- 一个中央协调者（Orchestrator）负责整体规划和任务分配
- 子 Agent 负责执行具体子任务
- 适合有明确上下级关系的任务场景
- 代表：MetaGPT（模拟软件公司的组织架构）

**B. 对等架构（Peer-to-Peer / Flat）**

```
    [Agent A] <-----> [Agent B]
       ^       \   /       ^
       |        \ /        |
       |         X         |
       |        / \        |
       v       /   \       v
    [Agent C] <-----> [Agent D]
```

- 所有 Agent 地位平等，可以直接相互通信
- 适合需要多方协商、头脑风暴的场景
- 没有单点故障，但协调复杂度更高
- 代表：AutoGen 的群聊模式

**C. 流水线架构（Pipeline）**

```
[输入] --> [Agent 1: 提取] --> [Agent 2: 分析] --> [Agent 3: 生成] --> [输出]
```

- Agent 按固定顺序连接，每个 Agent 处理特定阶段
- 数据单向流动，结构清晰
- 适合有明确步骤顺序的任务（如内容生产流水线）
- 代表：LangChain 的 Sequential Chain

**D. 星型架构（Star）**

```
         [Agent A]
            |
            |
[Agent B]--[中心 Agent]--[Agent C]
            |
            |
         [Agent D]
```

- 中心 Agent 作为消息中转站，所有通信通过中心节点
- 便于集中监控和日志记录
- 中心节点是瓶颈和单点故障

### 2. 通信方式

多 Agent 系统中的通信是协作的基础，需要定义清晰的消息格式和协议。

**通信模式：**

- **直接通信（Direct Messaging）**：Agent A 直接向 Agent B 发送消息，点对点通信
- **广播（Broadcast）**：Agent 向所有其他 Agent 发送消息，适合通知类信息
- **发布-订阅（Pub-Sub）**：Agent 订阅特定主题，只接收感兴趣的消息
- **黑板系统（Blackboard）**：共享一个公共空间，Agent 可以读写信息，适合需要共享中间结果的场景

**消息格式设计：**

```json
{
  "from": "agent_id",
  "to": "agent_id_or_broadcast",
  "type": "request|response|notification|task_assign",
  "content": {
    "task_id": "uuid",
    "description": "任务描述",
    "deadline": "2024-06-01T00:00:00Z",
    "priority": "high|medium|low",
    "context": "相关上下文信息"
  },
  "timestamp": "2024-05-20T10:30:00Z"
}
```

**通信协议层：**

- **同步通信**：请求-响应模式，调用方等待结果返回。简单但阻塞
- **异步通信**：消息队列模式，发送方不等待，通过回调或事件获取结果。适合高并发场景
- **状态共享**：通过共享内存或数据库同步状态，减少消息传递开销

### 3. 协作模式

**A. 任务分解与分配（Task Decomposition & Assignment）**

```
[复杂任务]
    |
    v
[分解器 Agent] --> 分析任务依赖关系，生成子任务列表
    |
    v
[任务分配器] --> 根据 Agent 能力和负载分配子任务
    |
    v
[Agent 1 执行子任务 A] --[并行]--> [Agent 2 执行子任务 B]
    |                                     |
    v                                     v
[结果汇总] <------------------------------+
    |
    v
[整合 Agent 生成最终输出]
```

- 将复杂任务分解为可并行或串行的子任务
- 根据每个 Agent 的专长和当前负载进行智能分配
- 需要考虑子任务之间的依赖关系（DAG 调度）

**B. 辩论与投票（Debate & Voting）**

```
[问题/提案]
    |
    v
[Agent A: 提出观点]    [Agent B: 提出反对观点]    [Agent C: 提出补充观点]
    |                        |                         |
    +------------------------+-------------------------+
                             |
                             v
              [辩论/讨论轮次]
                             |
                             v
              [投票/共识 Agent 做出最终决策]
```

- 多个 Agent 从不同角度分析问题，提出不同观点
- 通过辩论揭示问题的多个维度
- 最后通过投票或共识机制做出决策
- 适合需要多角度分析、避免单一视角偏见的问题
- 代表工作：ChatEval（多 Agent 辩论评估）

**C. 评审与迭代（Review & Iterate）**

```
[Agent A: 生成初稿]
    |
    v
[Agent B: 评审/批评] --> [提出修改意见]
    |
    v
[Agent A: 修改完善] --> [生成修订版]
    |
    v
[Agent B: 再次评审] --> ... 循环直到满意
    |
    v
[输出最终版本]
```

- 一个 Agent 生成内容，另一个 Agent 评审
- 评审 Agent 扮演"批评者"角色，指出问题和改进方向
- 生成 Agent 根据反馈修改，形成迭代改进循环
- 类似软件开发中的 Code Review 流程
- 代表工作：Self-Refine、Multi-Agent Debate

**D. 专家咨询（Expert Consultation）**

```
[通用 Agent 接到任务]
    |
    v
[判断是否需要专家] --[否]--> [自行处理]
    |--[是]
    v
[识别所需专家类型]
    |
    v
[咨询专家 Agent 1]    [咨询专家 Agent 2]
    |                       |
    v                       v
[整合专家建议] <------------+
    |
    v
[生成最终回答]
```

- 通用 Agent 识别任务的专长需求
- 向对应的专家 Agent 咨询
- 整合多个专家的意见生成最终输出
- 适合需要跨领域知识的复杂问题

### 4. 调度与冲突解决

**调度策略：**

- **静态调度**：任务分解后，预先确定每个子任务的执行 Agent 和顺序
- **动态调度**：根据 Agent 的实时状态（负载、可用性）动态分配任务
- **工作窃取（Work Stealing）**：空闲 Agent 从忙碌 Agent 的任务队列中"窃取"任务
- **负载均衡**：监控各 Agent 的负载，将新任务分配给最空闲的 Agent

**冲突类型与解决：**

| 冲突类型 | 描述 | 解决方法 |
|----------|------|----------|
| 资源冲突 | 多个 Agent 争用同一资源 | 锁机制、资源预留、优先级调度 |
| 结果冲突 | 不同 Agent 对同一问题给出矛盾答案 | 投票机制、置信度加权、人工仲裁 |
| 目标冲突 | Agent 的子目标相互矛盾 | 上层协调者重新分配目标、协商妥协 |
| 信息冲突 | Agent 基于不同信息源得出不同结论 | 信息融合、多源验证、时效性优先 |
| 依赖冲突 | 子任务 A 依赖子任务 B，但 B 失败 | 重试机制、替代方案、回退策略 |

**共识机制：**

- **多数投票（Majority Voting）**：取超过半数的意见
- **加权投票（Weighted Voting）**：根据 Agent 的专长或历史准确率赋予不同权重
- **Borda 计数**：对每个选项排序，综合排名最高的胜出
- **协商一致（Consensus）**：Agent 通过讨论逐步达成一致，直到没有反对意见

## 为什么这样设计 / 优缺点

**多 Agent 相比单 Agent 的优势：**

- **专业化**：每个 Agent 可以专注于特定领域或任务，深度优于广度
- **并行化**：多个 Agent 可以并行处理独立子任务，提升效率
- **鲁棒性**：单个 Agent 失败不会导致整个系统崩溃，其他 Agent 可以接管
- **可扩展性**：新增 Agent 即可扩展系统能力，无需修改现有 Agent
- **多样性**：不同 Agent 提供不同视角，减少单一模型的偏见和盲点
- **可解释性**：每个 Agent 的决策过程相对独立，便于调试和审计

**多 Agent 的劣势：**

- **协调复杂度**：Agent 之间的通信、同步、冲突解决增加了系统复杂度
- **通信开销**：Agent 间频繁通信带来延迟和成本（每个消息可能都需要 LLM 调用）
- **一致性问题**：多个 Agent 可能基于不同信息做出矛盾决策
- **调试困难**：错误可能在 Agent 间传播，定位问题根源更困难
- **设计挑战**：需要合理划分 Agent 角色和职责边界，设计不当会导致效率低下

**适用场景判断：**

- 适合多 Agent：任务可明确分解、需要多领域知识、对鲁棒性要求高、需要并行处理
- 适合单 Agent：任务简单直接、对延迟敏感、成本敏感、不需要多视角

## 实际应用 / 项目经验

**典型应用场景：**

- **软件开发团队模拟**：Product Manager Agent -> Architect Agent -> Engineer Agent -> QA Agent -> Reviewer Agent，模拟完整软件开发生命周期（MetaGPT）
- **内容创作团队**：Research Agent -> Writer Agent -> Editor Agent -> Fact-checker Agent，协作完成文章
- **投资分析团队**：Data Collector Agent -> Analyst Agent -> Risk Assessor Agent -> Strategist Agent，协作生成投资建议
- **医疗诊断团队**：Symptom Analyzer Agent -> Medical Knowledge Agent -> Diagnosis Agent -> Treatment Advisor Agent（辅助，非替代医生）
- **客服升级系统**：L1 Agent 处理常见问题 -> L2 Agent 处理复杂问题 -> L3 Expert Agent 处理专业问题 -> Human Agent 兜底

**面试可谈的技术点：**

- 设计过多 Agent 系统的角色划分和通信协议
- 实现过任务分解器，将复杂任务分解为 DAG 形式的子任务图
- 处理过 Agent 间的冲突，设计过投票或协商机制
- 使用过 AutoGen、MetaGPT、CrewAI 等多 Agent 框架
- 优化过 Agent 间通信效率，减少不必要的 LLM 调用
- 设计过 Agent 的负载均衡和故障转移机制

## 高频面试题

**Q1: 什么时候需要使用多 Agent 系统，而不是单个 Agent？**

- 任务复杂度超出单个 Agent 的上下文处理能力或专长范围
- 任务涉及多个领域知识，需要不同专家协作
- 任务可以分解为多个可并行的子任务，需要提升效率
- 对系统鲁棒性要求高，不能因单点故障而完全失效
- 需要多角度分析以避免单一模型的偏见
- 反例：简单问答、单轮对话、对延迟极度敏感的场景，单 Agent 更合适

**Q2: 多 Agent 系统中如何设计角色划分？**

- 按职能划分：规划者、执行者、评审者、协调者（类似人类团队）
- 按领域划分：不同 Agent 掌握不同领域的知识和工具
- 按任务阶段划分：每个阶段有专门的 Agent 负责
- 设计原则：
  - 每个 Agent 有明确的职责边界，避免重叠或遗漏
  - Agent 之间能力互补，覆盖任务所需的所有技能
  - 尽量减少 Agent 间的依赖，增加可并行度
  - 参考人类组织的最佳实践（如软件公司的角色设置）

**Q3: 如何处理 Agent 之间的冲突？**

- 结果冲突：投票机制（多数决、加权投票）、引入仲裁 Agent、置信度排序
- 资源冲突：锁机制、优先级队列、资源预留和超时释放
- 目标冲突：上层协调者重新规划、子目标协商、引入共同优化目标
- 信息冲突：多源交叉验证、时效性优先、来源权威性排序
- 通用策略：设置冲突解决规则（如"数据 Agent 的结果优先于推理 Agent"）

**Q4: 多 Agent 系统的通信开销如何优化？**

- 减少通信频率：批量处理消息，而非每条信息都发送
- 压缩消息内容：只传递必要信息，使用摘要代替全文
- 共享状态代替消息传递：使用共享数据库或缓存，Agent 按需读取
- 异步通信：使用消息队列，避免阻塞等待
- 本地决策：Agent 能在本地决策的尽量不外发请求
- 缓存机制：缓存常见查询的响应，避免重复计算

**Q5: 如何保证多 Agent 系统的整体一致性？**

- 共享上下文：所有 Agent 基于统一的上下文工作，避免信息不一致
- 中心协调者：由上层 Agent 统一规划和协调，确保目标一致
- 状态同步机制：关键状态变更时通知所有相关 Agent
- 检查点（Checkpoint）：在关键节点验证中间结果的一致性
- 回滚机制：发现不一致时，能够回退到上一个一致状态重新执行
- 最终一致性：允许短暂不一致，通过后续同步达到最终一致

**Q6: 介绍一个你熟悉的多 Agent 框架（如 AutoGen、MetaGPT、CrewAI）**

- **AutoGen（Microsoft）**：
  - 支持 Conversable Agent，Agent 之间通过对话协作
  - 支持群聊模式（GroupChat）和嵌套对话
  - 提供 UserProxyAgent（代表人类用户）和 AssistantAgent（执行任务的 AI）
  - 可以集成代码执行、工具调用、LLM 推理
  - 特点：灵活、可编程性强，适合研究和小规模应用

- **MetaGPT**：
  - 模拟软件公司的组织架构（产品经理、架构师、工程师、QA）
  - 每个角色有标准化的输出文档（PRD、设计文档、代码）
  - 通过共享文档（类似黑板系统）进行协作
  - 特点：结构化、流程化，适合软件开发类任务

- **CrewAI**：
  - 基于角色的多 Agent 框架，定义 Agent、Task、Crew
  - 支持顺序、并行、层级等执行流程
  - 与 LangChain 生态集成良好
  - 特点：简洁易用，适合快速原型开发

## 延伸链接

- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155) — AutoGen 论文
- [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework](https://arxiv.org/abs/2308.00352) — MetaGPT 论文
- [Multi-Agent Debate Supervises Language Models](https://arxiv.org/abs/2305.14256) — 多 Agent 辩论
- [Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924) — ChatDev 论文
- [CrewAI 官方文档](https://docs.crewai.com/) — CrewAI 框架
- [AutoGen 官方文档](https://microsoft.github.io/autogen/) — AutoGen 框架
- [MetaGPT GitHub](https://github.com/geekan/MetaGPT) — MetaGPT 开源项目
- [Multi-Agent Reinforcement Learning: A Survey](https://arxiv.org/abs/2312.10997) — 多 Agent 强化学习综述
