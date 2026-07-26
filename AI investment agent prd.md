# 金融多Agent智能投顾系统 - 需求与架构设计文档

## 一、项目概述

### 1.1 项目定位
面向高净值理财用户的金融多Agent智能投顾系统，通过自然语言交互，自动生成标准化投资方案报告。

### 1.2 技术决策（已确认）
| 决策项 | 选择 |
|--------|------|
| 开发范围 | 先做Python层（AI核心流程） |
| 大模型 | 硅基流动（SiliconFlow）API |
| 知识库数据 | 示例数据搭建，后续替换 |
| 意图识别 | 通用模型 + Prompt工程 |

---

## 二、技术架构

### 2.1 技术栈
| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web框架 | FastAPI | 高性能异步API |
| 工作流引擎 | LangGraph | DAG + 条件循环 + 反思迭代 |
| Agent框架 | LangChain | Agent编排、工具调用 |
| 向量数据库 | FAISS | 轻量级本地向量库 |
| Embedding | 硅基流动 BAAI/bge-large-zh-v1.5 | 中文向量化 |
| LLM | 硅基流动 Qwen/Qwen2.5-7B-Instruct | 主力推理模型 |
| 序列化 | Pydantic | 数据校验、State定义 |
| 分布式缓存 | Redis | Context存储、Checkpoint快照、分布式共享 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI 入口层                         │
│              POST /api/invest  (用户提问)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              意图识别模块 (IntentClassifier)               │
│   通用LLM + Few-shot Prompt → 输出结构化需求标签           │
│   输出: {rent_analysis: bool, competitor_analysis: bool,  │
│          loan_policy: bool, topic: str}                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│            主调度Agent (OrchestratorAgent)                 │
│   根据意图标签 → 动态构建DAG图                              │
│   决定激活哪些子Agent、依赖关系、并行/串行策略               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              DAG调度引擎 (DAGScheduler)                    │
│   拓扑排序 → 分层执行 → 并行/串行调度                      │
│   循环依赖检测 → 全局State状态管控                          │
└──────┬───────────────┬───────────────┬──────────────────┘
       │               │               │
       ▼               ▼               ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│ 租金测算    │ │ 竞品对比    │ │ 贷款政策    │
│ Agent      │ │ Agent      │ │ Agent      │
│            │ │            │ │            │
│ RAG检索    │ │ RAG检索    │ │ RAG检索    │
│ + LLM分析  │ │ + LLM分析  │ │ + LLM分析  │
└─────┬──────┘ └─────┬──────┘ └─────┬──────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│              反思迭代模块 (ReflectionNode)                 │
│   LLM评估报告质量 → 评分 + 缺失维度识别                    │
│   不满意 → 条件回退 → 重新调度（LangGraph循环）             │
│   满意 → 进入报告生成                                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              报告生成模块 (ReportGenerator)                │
│   汇总所有Agent输出 → 标准化投顾报告                        │
│   输出: 结构化JSON + 可读Markdown                          │
└──────────────────────────────────────────────────────────┘
```

### 2.3 LangGraph 工作流状态图

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                         ▼
                ┌────────────────┐
                │  意图识别节点   │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │ 主调度决策节点  │
                └────────┬───────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        ┌──────────┐┌──────────┐┌──────────┐
        │租金测算   ││竞品对比   ││贷款政策   │
        │(可并行)   ││(可并行)   ││(可并行)   │
        └────┬─────┘└────┬─────┘└────┬─────┘
             │           │           │
             └───────────┼───────────┘
                         │
                         ▼
                ┌────────────────┐
                │   汇总评估节点  │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │  反思判断节点   │──── 不满意 ────┐
                └────────┬───────┘                │
                         │                        │
                    满意  │                        │
                         │                        │
                         ▼                        │
                ┌────────────────┐                │
                │   报告生成节点  │                │
                └────────┬───────┘                │
                         │                        │
                         ▼                        │
                    ┌──────────┐                  │
                    │   END    │                  │
                    └──────────┘                  │
                                                  │
                          ◄───────────────────────┘
                          (回退到调度决策节点，重新分析)
```

---

## 三、项目目录结构

```
investment_agent(DAG)/
├── app/
│   ├── __init__.py                # 应用初始化
│   ├── main.py                    # FastAPI入口 + 前端静态文件服务
│   ├── config.py                  # 配置管理（API Key等）
│   ├── workflow.py                # LangGraph工作流编排 + SSE事件流
│   │
│   ├── frontend/                  # 前端可视化界面
│   │   └── index.html             # 单页应用（HTML+CSS+JS）
│   │       - 输入区域：用户提问
│   │       - Thinking展示区：实时思考过程
│   │       - 流转链路可视化：工作流节点状态
│   │       - 报告展示区：Markdown渲染投顾报告
│   │
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── state.py               # 全局State定义（LangGraph State）
│   │   └── schemas.py             # 请求/响应Schema
│   │
│   ├── dag/                       # DAG调度引擎
│   │   ├── __init__.py
│   │   ├── scheduler.py           # 拓扑排序、依赖检测、调度执行
│   │   └── graph_builder.py       # 根据意图动态构建DAG图
│   │
│   ├── agents/                    # Agent模块
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # 主调度Agent
│   │   ├── intent_classifier.py   # 意图识别Agent
│   │   ├── rent_agent.py          # 租金测算子Agent
│   │   ├── competitor_agent.py    # 竞品对比子Agent
│   │   ├── loan_policy_agent.py   # 贷款政策子Agent
│   │   └── reflection.py          # 反思迭代Agent
│   │
│   ├── rag/                       # RAG知识库
│   │   ├── __init__.py
│   │   ├── knowledge_base.py      # 知识库管理（加载、检索）
│   │   └── embeddings.py          # Embedding向量化
│   │
│   ├── report/                    # 报告生成
│   │   ├── __init__.py
│   │   └── generator.py           # 报告汇总生成
│   │
│   └── utils/                     # 工具
│       ├── __init__.py
│       └── llm_client.py          # 硅基流动LLM客户端
│
├── data/                          # 示例知识库数据
│   ├── rent_data.json             # 租金数据示例
│   ├── competitor_data.json       # 竞品数据示例
│   └── loan_policy_data.json      # 贷款政策数据示例
│
├── scripts/                       # 脚本工具
│   ├── __init__.py
│   └── build_vectorstore.py       # 向量库构建脚本
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── test_intent.py             # 意图识别测试
│   ├── test_dag.py                # DAG调度测试
│   ├── test_agents.py             # 各Agent测试
│   ├── test_rag.py                # RAG检索测试
│   ├── test_reflection_report.py  # 反思+报告生成测试
│   ├── test_workflow.py           # 工作流集成测试
│   ├── test_e2e.py                # 端到端全流程测试
│   ├── test_frontend_e2e.py       # 前端端到端测试
│   ├── test_performance.py        # 性能测试
│   ├── test_exception.py          # 异常处理测试
│   ├── test_data_validation.py    # 数据验证测试
│   ├── test_stage1_skeleton.py    # 阶段1骨架测试
│   └── test_data/                 # 测试数据
│       ├── __init__.py
│       ├── intent_test_cases.json # 意图识别测试用例
│       └── retrieval_test_cases.json # 检索测试用例
│
├── vectorstore/                   # 向量库（自动生成）
│   └── faiss_index/
│       ├── index.faiss            # FAISS索引文件
│       └── index.pkl              # 元数据
│
├── .env                           # 环境变量（API Key）
├── AI investment agent prd.md     # 需求与架构设计文档
├── TEST_CHECKLIST.md              # 测试清单
├── CASE_STUDY.md                  # 案例分析文档
├── requirements.txt               # 依赖
└── image.png                      # 架构图
```

---

## 四、核心模块详细设计

### 4.1 State + Context 双层状态架构

#### 4.1.1 设计原则

| 层级 | 存储位置 | 存储内容 | 内存占用 |
|------|----------|----------|----------|
| State（轻量内存状态） | LangGraph 内存 | 核心索引、session_id、路由标签、关键标记 | 1-2 KB |
| Context（完整会话上下文） | Redis 分布式缓存 | 完整对话、工具返回、Agent输出、RAG数据 | 50-100 KB |

#### 4.1.2 State（轻量内存状态）

只保存核心索引、session_id、request_id、路由标签、少量关键标记，不存海量大文本、工具完整返回结果。

```python
class InvestmentState(BaseModel):
    """投顾系统轻量状态（仅存核心索引）"""
    
    # 核心索引（轻量）
    session_id: str                    # 会话唯一标识，用于Redis统一读写
    request_id: str                    # 请求唯一标识，用于追踪
    
    # 路由标签（决策依据）
    intent_tags: list[str]             # 意图标签，如['rent_analysis', 'competitor_analysis']
    route_decision: str                # 路由决策，如'parallel_3_agents'
    
    # 关键标记（状态控制）
    iteration_count: int = 0           # 当前迭代次数
    max_iterations: int = 3            # 最大迭代次数
    reflection_score: float = 0.0      # 反思评分（判断是否迭代）
    status: str = "pending"            # 流程状态
    
    # DAG执行状态（轻量索引）
    current_node: str = ""             # 当前执行节点ID
    completed_nodes: list[str] = []    # 已完成节点列表
    failed_nodes: list[str] = []       # 失败节点列表
    
    # 完整上下文引用（指向Redis）
    context_key: str = ""              # Redis Context的key
    checkpoint_key: str = ""           # Redis Checkpoint的key
    report_key: str = ""               # 最终报告在Redis中的key
```

#### 4.1.3 Context（完整会话上下文，存储在 Redis）

完整对话、工具返回、中间Agent输出全部存入 Redis，所有 Agent 通过 session_id 统一读写同一份上下文。

**Redis Key 格式**：`context:{session_id}`

**Context 数据结构示例**（基于测试问题："我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案"）：

```json
{
  "user_query": "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案",
  "timestamp": "2026-07-25T10:30:00",
  "conversation_history": [
    {"role": "user", "content": "我想投资500万...", "timestamp": "..."},
    {"role": "assistant", "content": "好的，我来帮您分析...", "timestamp": "..."}
  ],
  "intent_result": {
    "rent_analysis": true,
    "competitor_analysis": true,
    "loan_policy": true,
    "topic": "投资浦东新区商铺",
    "confidence": 0.95
  },
  "agent_results": {
    "rent_agent": {
      "agent_name": "租金测算Agent",
      "status": "completed",
      "execution_time": 15.2,
      "rag_results": [...],
      "analysis": "基于RAG检索结果...",
      "confidence": 0.88
    },
    "competitor_agent": {...},
    "loan_policy_agent": {...}
  },
  "reflection_result": {
    "evaluation": {"score": 7.5, "feedback": "..."},
    "iteration_count": 1
  },
  "final_report": "# 投资顾问报告\n\n...",
  "tool_results": {"faiss_search": {...}},
  "metadata": {"total_execution_time": 167.29, "total_tokens_used": 15680}
}
```

#### 4.1.4 JSONPath 按需读取

Agent 不会拉取全部上下文，通过 JSONPath 精准读取 Redis 中的指定字段，减少 IO 与内存占用。

```python
# 租金分析Agent 只读取租金相关数据
rent_data = context_manager.get_by_jsonpath(
    session_id="sess_abc123",
    jsonpath="$.agent_results.rent_agent"
)

# 只需要分析文本
analysis_text = context_manager.get_by_jsonpath(
    session_id="sess_abc123",
    jsonpath="$.agent_results.rent_agent.analysis"
)

# 读取RAG检索的第一条结果
first_rag = context_manager.get_by_jsonpath(
    session_id="sess_abc123",
    jsonpath="$.agent_results.rent_agent.rag_results[0]"
)
```

#### 4.1.5 Checkpoint 快照机制

DAG 每个节点执行完成后，自动把当前完整上下文快照存入 Redis，故障可回滚。

```python
# 节点执行完成后自动保存快照
context_manager.save_checkpoint(
    session_id="sess_abc123",
    node_id="rent_agent",
    context=current_context
)

# 故障时回滚到上一个节点状态
checkpoint = context_manager.load_checkpoint(
    session_id="sess_abc123",
    node_id="rent_agent"
)
```

#### 4.1.6 分布式多实例数据共享

所有 Agent（Supervisor 主 Agent + 3-4 个子 Agent）通过 session_id 作为唯一 key，统一读写同一份 Redis 上下文，实现分布式多实例数据共享。

```python
# Agent 1（运行在实例 A）
agent_a.session_id = "sess_abc123"
agent_a.context_manager.get_by_jsonpath(session_id, "$.user_query")

# Agent 2（运行在实例 B）
agent_b.session_id = "sess_abc123"  # 同一个 session_id
# 可以读取到 Agent 1 写入的结果
```

#### 4.1.7 性能对比

| 指标 | 传统方案（全量加载） | State + Context 方案 |
|------|---------------------|---------------------|
| 内存占用 | 100-200 KB/请求 | 1-2 KB/请求（State） |
| 网络IO | 每次加载全部上下文 | 按需读取指定字段 |
| 并发能力 | 受限于单机内存 | 分布式共享，无上限 |
| 故障恢复 | 无法恢复 | Checkpoint 快照，可回滚 |
| 多实例支持 | 需要额外同步机制 | 天然支持（Redis 共享） |

### 4.2 DAG调度引擎

核心能力：
- **拓扑排序**：根据Agent依赖关系，计算执行顺序
- **循环依赖检测**：Kahn算法检测环，抛出异常
- **并行调度**：无依赖Agent使用asyncio.gather并行执行
- **状态管控**：全局State记录每个节点执行状态

### 4.3 意图识别

使用通用LLM + Few-shot Prompt，输出结构化标签：
```json
{
    "rent_analysis": true,
    "competitor_analysis": true,
    "loan_policy": false,
    "topic": "投资浦东新区商铺，关注租金回报和周边竞品"
}
```

### 4.4 子Agent设计（统一接口）

每个子Agent遵循统一接口：
- 输入：用户问题 + 上下文
- RAG检索：从知识库检索相关数据
- LLM分析：基于检索数据生成分析结果
- 输出：结构化JSON（统一Schema）

### 4.5 反思迭代

- LLM评估报告完整性（维度覆盖、数据充分性、逻辑性）
- 评分 0-10，低于阈值（如7分）触发迭代
- 回退到调度节点，补充缺失维度重新分析
- 最大迭代3次，防止死循环

### 4.6 硅基流动API配置

- Base URL: `https://api.siliconflow.cn/v1`
- LLM模型: `Qwen/Qwen2.5-7B-Instruct`
- Embedding模型: `BAAI/bge-large-zh-v1.5`
- 兼容OpenAI SDK格式

---

## 五、接口规范

### 5.1 投顾分析接口

```
POST /api/invest
Request:
{
    "query": "我想投资上海浦东新区的商铺，预算500万，帮我分析一下租金回报和周边竞品"
}

Response:
{
    "status": "success",
    "report": "...(Markdown格式投顾报告)...",
    "agent_results": {
        "rent_analysis": {...},
        "competitor_analysis": {...}
    },
    "iterations": 1
}
```

### 5.2 健康检查

```
GET /health
Response: {"status": "ok"}
```

---

## 六、向量库选型说明

### 6.1 为什么选FAISS而不是Milvus

| 对比项 | FAISS | Milvus |
|--------|-------|--------|
| 部署方式 | pip安装，本地运行 | 需要独立部署服务（Docker/集群） |
| 上手难度 | 极低，几行代码 | 需要配置服务、端口、连接 |
| 适合规模 | 百万级以下向量 | 十亿级大规模向量 |
| 本项目情况 | 示例数据量小，几百条 | 杀鸡用牛刀 |

**结论**：本项目是示例数据 + 开发验证阶段，FAISS完全够用，无需额外部署服务。后续数据量大了可平滑迁移到Milvus。

---

## 七、知识库数据设计（样本数据 + 测试数据）

### 7.1 数据整体流程

```
原始样本数据（JSON）
    ↓ 数据预处理脚本（split_documents）
文档片段（chunks）
    ↓ Embedding向量化（硅基流动 bge-large-zh-v1.5）
向量数据
    ↓ 存入FAISS
向量索引（本地持久化）
    ↓ 检索测试
验证检索效果
```

### 7.2 原始样本数据设计

#### 7.2.1 租金数据（data/rent_data.json）
每条数据包含完整语义，适合切分为检索片段：

```json
[
  {
    "id": "rent_001",
    "area": "上海浦东新区",
    "location": "陆家嘴",
    "property_type": "商铺",
    "size_sqm": 80,
    "monthly_rent_range": "30000-50000元",
    "avg_rent_per_sqm": "450元/㎡/月",
    "annual_return_rate": "5.2%",
    "vacancy_rate": "8%",
    "description": "陆家嘴核心商圈商铺，人流量大，适合餐饮零售，年回报率约5.2%，空置率较低。"
  },
  {
    "id": "rent_002",
    "area": "上海浦东新区",
    "location": "张江",
    "property_type": "商铺",
    "size_sqm": 120,
    "monthly_rent_range": "18000-28000元",
    "avg_rent_per_sqm": "200元/㎡/月",
    "annual_return_rate": "4.1%",
    "vacancy_rate": "12%",
    "description": "张江科技园周边商铺，客群以白领为主，适合轻餐饮便利店，回报率稳定。"
  }
]
```

#### 7.2.2 竞品数据（data/competitor_data.json）

```json
[
  {
    "id": "comp_001",
    "area": "上海浦东新区",
    "business_district": "陆家嘴",
    "project_name": "正大广场",
    "property_type": "购物中心商铺",
    "avg_price": "120000元/㎡",
    "occupancy_rate": "92%",
    "advantages": "核心地段，品牌效应强，人流量日均10万+",
    "disadvantages": "入场门槛高，租金成本大",
    "description": "正大广场是陆家嘴标杆商业项目，入驻品牌超200个，适合高端零售餐饮投资。"
  }
]
```

#### 7.2.3 贷款政策数据（data/loan_policy_data.json）

```json
[
  {
    "id": "loan_001",
    "bank_name": "工商银行",
    "loan_type": "商业用房贷款",
    "interest_rate": "4.2%-4.8%",
    "down_payment_ratio": "50%",
    "max_loan_term": "10年",
    "approval_conditions": "需提供营业执照、近6个月流水、征信良好",
    "description": "工行商业用房贷款，首付50%起，利率4.2%起，最长10年，适合有稳定经营收入的投资者。"
  }
]
```

### 7.3 数据预处理与向量化流程

**脚本位置**：`scripts/build_vectorstore.py`

**处理步骤**：
1. 加载 `data/` 下所有JSON文件
2. 将每条记录转换为文本片段（包含description + 关键字段）
3. 调用硅基流动 Embedding API（`BAAI/bge-large-zh-v1.5`）向量化
4. 构建FAISS索引
5. 持久化到 `vectorstore/faiss_index/`

**输出产物**：
- `vectorstore/faiss_index/index.faiss` — FAISS索引文件
- `vectorstore/faiss_index/index.json` — 元数据（id、文本、来源）

### 7.4 测试数据设计

#### 7.4.1 检索测试用例（tests/test_data/retrieval_test_cases.json）

用于验证RAG检索准确性，每个用例包含：查询语句、期望命中的数据ID、期望内容关键词。

```json
[
  {
    "query": "陆家嘴商铺租金多少",
    "expected_ids": ["rent_001"],
    "expected_keywords": ["陆家嘴", "租金", "回报率"]
  },
  {
    "query": "工商银行商业贷款政策",
    "expected_ids": ["loan_001"],
    "expected_keywords": ["工商银行", "首付", "利率"]
  },
  {
    "query": "正大广场竞品分析",
    "expected_ids": ["comp_001"],
    "expected_keywords": ["正大广场", "陆家嘴", "入驻"]
  }
]
```

#### 7.4.2 意图识别测试用例（tests/test_data/intent_test_cases.json）

```json
[
  {
    "query": "我想投资浦东新区的商铺，帮我看看租金回报",
    "expected_intent": {
      "rent_analysis": true,
      "competitor_analysis": false,
      "loan_policy": false
    }
  },
  {
    "query": "对比一下陆家嘴和张江的商铺投资价值",
    "expected_intent": {
      "rent_analysis": true,
      "competitor_analysis": true,
      "loan_policy": false
    }
  },
  {
    "query": "买商铺可以贷款吗？首付多少？",
    "expected_intent": {
      "rent_analysis": false,
      "competitor_analysis": false,
      "loan_policy": true
    }
  }
]
```

#### 7.4.3 端到端测试用例（tests/test_data/e2e_test_cases.json）

```json
[
  {
    "query": "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案",
    "expected_agents": ["rent_analysis", "competitor_analysis", "loan_policy"],
    "expected_report_sections": ["租金分析", "竞品对比", "贷款方案", "投资建议"]
  }
]
```

### 7.5 数据文件清单

| 文件路径 | 用途 | 数量 |
|----------|------|------|
| `data/rent_data.json` | 租金样本数据 | 10-15条 |
| `data/competitor_data.json` | 竞品样本数据 | 10-15条 |
| `data/loan_policy_data.json` | 贷款政策样本数据 | 8-10条 |
| `scripts/build_vectorstore.py` | 向量化入库脚本 | 1个 |
| `vectorstore/faiss_index/` | FAISS索引持久化目录 | 自动生成 |
| `tests/test_data/retrieval_test_cases.json` | 检索测试用例 | 6-8个 |
| `tests/test_data/intent_test_cases.json` | 意图识别测试用例 | 5-6个 |
| `tests/test_data/e2e_test_cases.json` | 端到端测试用例 | 3-4个 |

---

## 八、开发顺序（逐步闭环）

| 阶段 | 模块 | 验证目标 |
|------|------|----------|
| 1 | 项目骨架 + 配置 | FastAPI启动、LLM连通 |
| 2 | RAG知识库 | 数据加载、向量检索可用 |
| 3 | 意图识别 | 输入自然语言，输出结构化标签 |
| 4 | DAG调度引擎 | 拓扑排序、并行调度、循环检测 |
| 5 | 三个子Agent | 各自独立运行、RAG检索+LLM分析 |
| 6 | 反思迭代 | 评估报告质量、触发回退 |
| 7 | 报告生成 | 汇总输出标准化报告 |
| 8 | LangGraph全流程 | 端到端完整流程跑通 |
| 9 | 集成测试 | 多场景测试、异常处理 |
| 10 | 前端可视化界面 | 输入、Thinking、流转链路、报告展示 |

---

## 九、前端可视化方案

### 9.1 技术选型

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 框架 | React + TypeScript | 生态成熟，类型安全 |
| UI库 | Ant Design | 组件丰富，适合后台系统 |
| 可视化 | React Flow | 流程图可视化，展示工作流节点 |
| HTTP | Axios | 调用FastAPI接口 |
| 样式 | CSS Modules | 局部样式隔离 |

### 9.2 功能模块

#### 9.2.1 输入区域
- 文本输入框，支持多行输入
- 提交按钮，触发分析请求
- 示例查询快捷按钮

#### 9.2.2 Thinking展示区
实时展示每个节点的执行状态：
```
💭 思考过程
├─ 意图识别中... (0.88s)
│  ✓ 识别到：租金分析、竞品分析、贷款政策
├─ 规划执行计划... (0.01s)
│  ✓ DAG规划完成，3个Agent并行执行
├─ Agent执行中... (99.04s)
│  ✓ 租金分析Agent完成
│  ✓ 竞品分析Agent完成
│  ✓ 贷款政策Agent完成
├─ 反思评估中... (5s)
│  ✓ 评分：7/10，质量达标
└─ 生成报告中... (3s)
   ✓ 报告生成完成
```

#### 9.2.3 可视化流转链路
使用React Flow展示工作流节点状态：
- 节点颜色变化：灰色(等待) → 蓝色(执行中) → 绿色(完成)
- 连线动画：表示数据流转方向
- 节点点击：查看该节点的输入输出详情

#### 9.2.4 结果展示区
- Markdown渲染投顾报告
- 支持复制、导出PDF
- 折叠/展开各章节

### 9.3 后端接口改造

当前后端是同步返回，需改造为**SSE（Server-Sent Events）流式输出**：

```python
@app.get("/api/invest/stream")
async def invest_stream(query: str):
    async def event_generator():
        # 1. 发送意图识别结果
        yield {"event": "intent", "data": {...}}
        # 2. 发送DAG规划结果
        yield {"event": "dag_plan", "data": {...}}
        # 3. 发送Agent执行进度
        yield {"event": "agent_progress", "data": {...}}
        # 4. 发送反思结果
        yield {"event": "reflection", "data": {...}}
        # 5. 发送最终报告
        yield {"event": "report", "data": {...}}

    return EventSourceResponse(event_generator())
```

### 9.4 页面布局

```
┌─────────────────────────────────────────────────────────┐
│  金融多Agent智能投顾系统                                    │
├────────────────────┬────────────────────────────────────┤
│                    │                                    │
│   输入区域          │   可视化流转链路（React Flow）        │
│   ┌────────────┐  │   ┌──────────┐  ┌──────────┐       │
│   │ 请输入...   │  │   │ 意图识别  │→│ DAG规划  │       │
│   └────────────┘  │   └──────────┘  └──────────┘       │
│   [提交分析]       │        ↓                            │
│                    │   ┌──────────┐  ┌──────────┐       │
│   Thinking展示区   │   │ Agent执行 │→│ 反思评估  │       │
│   ├─ 意图识别 ✓   │   └──────────┘  └──────────┘       │
│   ├─ DAG规划 ✓    │        ↓                            │
│   ├─ Agent执行 ✓  │   ┌──────────┐                      │
│   ├─ 反思评估 ✓   │   │ 报告生成  │                      │
│   └─ 报告生成 ✓   │   └──────────┘                      │
│                    │                                    │
├────────────────────┴────────────────────────────────────┤
│  结果展示区（Markdown渲染）                                 │
│  # 投资顾问报告                                          │
│  ## 一、用户需求概述                                       │
│  ...                                                    │
└─────────────────────────────────────────────────────────┘
```

### 9.5 测试要点

| 测试项 | 目标 | 验证方法 |
|--------|------|----------|
| 页面加载时间 | <2秒 | 浏览器DevTools |
| 流式输出延迟 | <500ms | 网络面板 |
| 流程图渲染 | 流畅无卡顿 | 手动测试 |
| 浏览器兼容 | Chrome/Firefox/Safari | 多浏览器测试 |
| 移动端适配 | 响应式布局 | 浏览器缩放测试 |

---

## 十、CI/CD 自动化交付流程

### 10.1 流程概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD 自动化交付流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 代码提交 Git                                                 │
│     ↓                                                           │
│  2. 触发流水线 (GitHub Actions)                                  │
│     ↓                                                           │
│  3. 单元测试自动执行                                              │
│     - RAG 检索测试                                               │
│     - Agent 调度单元测试                                         │
│     - 意图识别测试                                               │
│     ↓                                                           │
│  4. 构建 Docker 镜像                                             │
│     - 多阶段构建 (减小体积)                                       │
│     - 镜像漏洞扫描 (Trivy)                                       │
│     ↓                                                           │
│  5. 推送私有镜像仓库                                              │
│     - GitHub Container Registry (ghcr.io)                       │
│     ↓                                                           │
│  6. K8s 滚动更新                                                 │
│     - 不中断线上用户                                              │
│     - 自动健康检查                                               │
│     ↓                                                           │
│  7. 自动化冒烟测试                                                │
│     - 健康检查接口                                               │
│     - 前端页面加载                                               │
│     - 投顾分析接口                                               │
│     - SSE 流式接口                                               │
│     ↓                                                           │
│  8. 失败自动回滚                                                  │
│     - 冒烟测试失败 → 自动回滚到上一版本                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 技术选型

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| CI/CD 平台 | GitHub Actions | 与代码仓库深度集成 |
| 容器化 | Docker | 标准化交付，环境一致性 |
| 镜像仓库 | GitHub Container Registry (ghcr.io) | 私有镜像托管 |
| 漏洞扫描 | Trivy | 开源容器安全扫描工具 |
| 容器编排 | Kubernetes (K8s) | 生产级容器编排 |
| 滚动更新 | K8s Rolling Update | 零停机部署 |
| 冒烟测试 | Python + requests | 自动化接口验证 |

### 10.3 流水线配置

#### 10.3.1 GitHub Actions 工作流

**文件位置**: `.github/workflows/ci-cd.yml`

**触发条件**:
- `push` 到 `main` 或 `develop` 分支
- `pull_request` 到 `main` 分支

**Job 1: 单元测试**
```yaml
- 安装 Python 3.11
- 安装依赖
- 运行 RAG 检索测试
- 运行 Agent 调度测试
- 运行意图识别测试
```

**Job 2: 构建与扫描**
```yaml
- 构建 Docker 镜像 (多阶段构建)
- Trivy 漏洞扫描 (CRITICAL + HIGH)
- 推送到 ghcr.io
- 镜像标签: 分支名 + commit SHA
```

**Job 3: 部署到 K8s**
```yaml
- 应用 K8s 配置 (Deployment + Service)
- 滚动更新 (maxSurge=1, maxUnavailable=0)
- 等待部署完成 (超时 300s)
- 执行冒烟测试
- 失败自动回滚
```

### 10.4 Docker 镜像构建

#### 10.4.1 多阶段构建

**文件位置**: `Dockerfile`

**构建阶段**:
1. **Builder 阶段**: 安装编译依赖，构建 Python 虚拟环境
2. **Runtime 阶段**: 仅复制运行时必需文件，减小镜像体积

**镜像特性**:
- 基础镜像: `python:3.11-slim` (约 120MB)
- 非 root 用户运行 (安全性)
- 内置健康检查 (HEALTHCHECK)
- 排除大文件 (vectorstore/, tests/)

**构建命令**:
```bash
docker build -t investment-agent:latest .
```

#### 10.4.2 镜像漏洞扫描

**工具**: Trivy (Aqua Security)

**扫描策略**:
- 扫描操作系统漏洞 (os)
- 扫描语言特定漏洞 (library)
- 仅报告 CRITICAL 和 HIGH 级别
- 忽略未修复漏洞 (ignore-unfixed)

**扫描命令**:
```bash
trivy image --severity CRITICAL,HIGH investment-agent:latest
```

### 10.5 Kubernetes 部署

#### 10.5.1 Deployment 配置

**文件位置**: `k8s/deployment.yaml`

**关键配置**:
- **副本数**: 3 (高可用)
- **滚动更新策略**:
  - `maxSurge: 1` (最多多 1 个 Pod)
  - `maxUnavailable: 0` (不允许不可用)
- **资源限制**:
  - 请求: 512Mi 内存, 500m CPU
  - 限制: 1Gi 内存, 1000m CPU
- **健康检查**:
  - Liveness Probe: `/health` (每 10s)
  - Readiness Probe: `/health` (每 5s)

#### 10.5.2 Service 配置

**文件位置**: `k8s/service.yaml`

**服务类型**: LoadBalancer (暴露到外部)

**端口映射**: 8000 → 8000

#### 10.5.3 密钥管理

**Secret**: `siliconflow-secret`
- 存储 SiliconFlow API Key
- 通过环境变量注入到 Pod

### 10.6 冒烟测试

#### 10.6.1 测试脚本

**文件位置**: `scripts/smoke_test.py`

**测试项**:
1. **健康检查**: `GET /health` → 200 OK
2. **前端页面**: `GET /` → 200, 包含标题
3. **投顾分析**: `POST /api/invest` → 成功返回报告
4. **SSE 流式**: `POST /api/invest/stream` → 事件流正常

**执行命令**:
```bash
python scripts/smoke_test.py --url http://<service-ip>:8000
```

#### 10.6.2 失败回滚

**触发条件**: 冒烟测试失败

**回滚命令**:
```bash
kubectl rollout undo deployment/investment-agent -n investment-agent
```

**回滚验证**:
```bash
kubectl rollout status deployment/investment-agent -n investment-agent
```

### 10.7 环境变量与密钥

#### 10.7.1 GitHub Secrets

需要在 GitHub 仓库设置中配置:

| Secret 名称 | 说明 |
|-------------|------|
| `SILICONFLOW_API_KEY` | SiliconFlow API 密钥 |
| `K8S_KUBECONFIG` | Kubernetes 集群配置文件 |
| `K8S_CONTEXT` | Kubernetes 上下文名称 |

#### 10.7.2 K8s Secrets

**创建命令**:
```bash
kubectl create secret generic siliconflow-secret \
  --from-literal=api-key=<YOUR_API_KEY> \
  -n investment-agent
```

### 10.8 部署流程示例

#### 10.8.1 开发者提交流程

```bash
# 1. 开发完成，提交代码
git add .
git commit -m "feat: 添加新功能"
git push origin develop

# 2. GitHub Actions 自动触发
#    - 运行单元测试
#    - 构建 Docker 镜像
#    - 漏洞扫描
#    - 推送到 ghcr.io

# 3. 合并到 main 分支
git checkout main
git merge develop
git push origin main

# 4. GitHub Actions 自动部署
#    - K8s 滚动更新
#    - 冒烟测试
#    - 失败自动回滚
```

#### 10.8.2 手动部署流程

```bash
# 1. 构建镜像
docker build -t investment-agent:v1.0.0 .

# 2. 推送到镜像仓库
docker tag investment-agent:v1.0.0 ghcr.io/<username>/investment-agent:v1.0.0
docker push ghcr.io/<username>/investment-agent:v1.0.0

# 3. 更新 K8s 部署
kubectl set image deployment/investment-agent \
  investment-agent=ghcr.io/<username>/investment-agent:v1.0.0 \
  -n investment-agent

# 4. 查看部署状态
kubectl rollout status deployment/investment-agent -n investment-agent

# 5. 执行冒烟测试
python scripts/smoke_test.py --url http://<service-ip>:8000
```

### 10.9 监控与日志

#### 10.9.1 健康检查

**端点**: `/health`

**响应**:
```json
{
  "status": "ok"
}
```

**检查频率**: 每 10 秒 (K8s Liveness Probe)

#### 10.9.2 日志查看

```bash
# 查看 Pod 日志
kubectl logs -l app=investment-agent -n investment-agent -f

# 查看特定 Pod 日志
kubectl logs <pod-name> -n investment-agent -f
```

### 10.10 回滚策略

#### 10.10.1 自动回滚

**触发条件**:
- 冒烟测试失败
- 健康检查失败
- Pod 启动失败

**回滚命令**:
```bash
kubectl rollout undo deployment/investment-agent -n investment-agent
```

#### 10.10.2 手动回滚

```bash
# 查看部署历史
kubectl rollout history deployment/investment-agent -n investment-agent

# 回滚到指定版本
kubectl rollout undo deployment/investment-agent \
  --to-revision=2 \
  -n investment-agent
```

### 10.11 性能优化

#### 10.11.1 镜像优化

- **多阶段构建**: 减小最终镜像体积 (约 200MB)
- **排除大文件**: vectorstore/ 不打包进镜像
- **缓存依赖**: 利用 Docker 层缓存

#### 10.11.2 部署优化

- **滚动更新**: 零停机部署
- **资源限制**: 防止资源争抢
- **健康检查**: 快速发现故障 Pod

#### 10.11.3 扩展性

- **水平扩展**: 增加副本数
  ```bash
  kubectl scale deployment/investment-agent --replicas=5 -n investment-agent
  ```
- **自动扩缩容**: 配置 HPA (Horizontal Pod Autoscaler)

### 10.12 安全最佳实践

#### 10.12.1 镜像安全

- **非 root 用户**: 使用 `appuser` 运行应用
- **最小权限**: 仅安装运行时必需依赖
- **漏洞扫描**: 每次构建自动扫描

#### 10.12.2 密钥管理

- **Secrets**: 敏感信息不硬编码
- **环境变量**: 通过 K8s Secrets 注入
- **RBAC**: 限制 K8s 访问权限

#### 10.12.3 网络安全

- **NetworkPolicy**: 限制 Pod 间通信
- **Ingress**: 配置 HTTPS/TLS
- **防火墙**: 限制外部访问

### 10.13 CI/CD 测试要点

| 测试项 | 验证方法 | 预期结果 |
|--------|----------|----------|
| 单元测试 | pytest | 所有测试通过 |
| 镜像构建 | docker build | 构建成功 |
| 漏洞扫描 | trivy | 无 CRITICAL/HIGH 漏洞 |
| 镜像推送 | docker push | 推送到 ghcr.io |
| K8s 部署 | kubectl apply | Deployment 就绪 |
| 滚动更新 | kubectl rollout | 零停机更新 |
| 冒烟测试 | smoke_test.py | 所有接口正常 |
| 回滚机制 | kubectl rollout undo | 成功回滚 |

### 10.14 故障排查

#### 10.14.1 常见问题

**问题 1: Pod 启动失败**
```bash
# 查看 Pod 状态
kubectl get pods -n investment-agent

# 查看 Pod 详情
kubectl describe pod <pod-name> -n investment-agent

# 查看日志
kubectl logs <pod-name> -n investment-agent
```

**问题 2: 镜像拉取失败**
```bash
# 检查镜像拉取密钥
kubectl get secret ghcr-secret -n investment-agent

# 重新创建密钥
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n investment-agent
```

**问题 3: 健康检查失败**
```bash
# 检查服务是否启动
kubectl exec -it <pod-name> -n investment-agent -- curl http://localhost:8000/health

# 检查端口映射
kubectl get service investment-agent -n investment-agent
```

### 10.15 总结

**CI/CD 流程价值**:
- ✅ **自动化**: 代码提交 → 测试 → 构建 → 部署全自动
- ✅ **安全性**: 镜像漏洞扫描，密钥管理
- ✅ **可靠性**: 滚动更新，自动回滚
- ✅ **可观测性**: 健康检查，日志查看
- ✅ **可扩展**: 水平扩展，自动扩缩容

**关键文件清单**:
- `.github/workflows/ci-cd.yml` - GitHub Actions 工作流
- `Dockerfile` - Docker 镜像构建
- `.dockerignore` - Docker 构建排除
- `k8s/deployment.yaml` - K8s Deployment 配置
- `k8s/service.yaml` - K8s Service 配置
- `scripts/smoke_test.py` - 冒烟测试脚本
