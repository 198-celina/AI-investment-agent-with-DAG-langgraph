# State 与 Context 架构设计文档

## 一、核心概念

### 1.1 State（轻量内存状态）
**存储位置**：LangGraph 内存（进程内）  
**存储内容**：核心索引、session_id、request_id、路由标签、少量关键标记  
**特点**：
- 不存海量大文本、工具完整返回结果
- 仅保存决策所需的最小信息集
- 快速访问，无网络IO开销

### 1.2 Context（完整会话上下文）
**存储位置**：Redis 分布式缓存  
**存储内容**：完整对话历史、工具返回结果、中间Agent输出、RAG检索数据  
**特点**：
- 海量数据存储
- 分布式多实例共享
- 通过 JSONPath 按需精准读取

### 1.3 JSONPath 的作用
Agent 不会拉取全部上下文，而是通过 JSONPath 精准读取 Redis 中的指定字段，减少 IO 与内存占用。

---

## 二、基于测试案例的数据结构展示

**测试问题**：
> "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案"

---

## 三、State 数据结构（轻量内存状态）

```python
class InvestmentState:
    """投顾系统轻量状态"""
    
    # ========== 核心索引（轻量） ==========
    session_id: str = "sess_abc123xyz"
    request_id: str = "req_20260725_001"
    
    # ========== 路由标签（决策依据） ==========
    intent_tags: list[str] = [
        "rent_analysis",
        "competitor_analysis", 
        "loan_policy"
    ]
    route_decision: str = "parallel_3_agents"
    
    # ========== 关键标记（状态控制） ==========
    iteration_count: int = 1
    max_iterations: int = 3
    reflection_score: float = 7.5
    status: str = "running"  # pending/running/completed/failed
    
    # ========== DAG执行状态（轻量索引） ==========
    current_node: str = "agent_execution"
    completed_nodes: list[str] = [
        "intent_classification",
        "dag_planning",
        "rent_agent",
        "competitor_agent"
    ]
    failed_nodes: list[str] = []
    
    # ========== 完整上下文引用（指向Redis） ==========
    context_key: str = "context:sess_abc123xyz"
    checkpoint_key: str = "checkpoint:sess_abc123xyz:rent_agent"
    
    # ========== 最终报告引用（指向Redis） ==========
    report_key: str = "report:sess_abc123xyz"
```

**State 内存占用**：约 1-2 KB（仅索引和标记）

---

## 四、Context 数据结构（完整会话上下文，存储在 Redis）

**Redis Key**：`context:sess_abc123xyz`

```json
{
  "user_query": "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案",
  "timestamp": "2026-07-25T10:30:00",
  "user_info": {
    "user_id": "user_12345",
    "risk_level": "moderate",
    "investment_experience": "5年"
  },
  
  "conversation_history": [
    {
      "role": "user",
      "content": "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案",
      "timestamp": "2026-07-25T10:30:00"
    },
    {
      "role": "assistant",
      "content": "好的，我来帮您分析浦东新区商铺投资的租金回报、周边竞品和贷款方案...",
      "timestamp": "2026-07-25T10:30:05"
    }
  ],
  
  "intent_result": {
    "rent_analysis": true,
    "competitor_analysis": true,
    "loan_policy": true,
    "topic": "投资浦东新区商铺，关注租金回报、周边竞品和贷款方案",
    "confidence": 0.95
  },
  
  "dag_plan": {
    "valid": true,
    "layers": [
      ["rent_agent", "competitor_agent", "loan_policy_agent"]
    ],
    "total_nodes": 3,
    "total_layers": 1,
    "execution_strategy": "parallel"
  },
  
  "agent_results": {
    "rent_agent": {
      "agent_name": "租金测算Agent",
      "status": "completed",
      "execution_time": 15.2,
      "rag_query": "上海浦东新区商铺租金回报率",
      "rag_results": [
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
      ],
      "analysis": "基于RAG检索结果，浦东新区商铺投资分析如下：\n\n1. **陆家嘴商圈**：\n   - 月租金范围：30,000-50,000元\n   - 平均租金单价：450元/㎡/月\n   - 年回报率：5.2%\n   - 空置率：8%\n   - 投资建议：核心地段，人流量大，适合高端零售餐饮\n\n2. **张江商圈**：\n   - 月租金范围：18,000-28,000元\n   - 平均租金单价：200元/㎡/月\n   - 年回报率：4.1%\n   - 空置率：12%\n   - 投资建议：科技园区周边，客群稳定，适合轻餐饮便利店",
      "confidence": 0.88
    },
    
    "competitor_agent": {
      "agent_name": "竞品对比Agent",
      "status": "completed",
      "execution_time": 12.5,
      "rag_query": "浦东新区商铺竞品项目分析",
      "rag_results": [
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
        },
        {
          "id": "comp_002",
          "area": "上海浦东新区",
          "business_district": "前滩",
          "project_name": "前滩太古里",
          "property_type": "开放式街区商铺",
          "avg_price": "95000元/㎡",
          "occupancy_rate": "88%",
          "advantages": "新兴商圈，规划先进，发展潜力大",
          "disadvantages": "商圈成熟度待提升，初期人流量有限",
          "description": "前滩太古里是浦东新兴商业地标，采用开放式街区设计，适合追求长期增值的投资者。"
        }
      ],
      "analysis": "浦东新区主要竞品项目对比：\n\n1. **正大广场（陆家嘴）**：\n   - 均价：120,000元/㎡\n   - 出租率：92%\n   - 优势：核心地段，品牌效应强，日均人流10万+\n   - 劣势：入场门槛高，租金成本大\n   - 适合：高端零售、餐饮品牌\n\n2. **前滩太古里（前滩）**：\n   - 均价：95,000元/㎡\n   - 出租率：88%\n   - 优势：新兴商圈，规划先进，发展潜力大\n   - 劣势：商圈成熟度待提升\n   - 适合：追求长期增值的投资者",
      "confidence": 0.85
    },
    
    "loan_policy_agent": {
      "agent_name": "贷款政策Agent",
      "status": "completed",
      "execution_time": 10.8,
      "rag_query": "上海商铺贷款政策 首付比例 利率",
      "rag_results": [
        {
          "id": "loan_001",
          "bank_name": "工商银行",
          "loan_type": "商业用房贷款",
          "interest_rate": "4.2%-4.8%",
          "down_payment_ratio": "50%",
          "max_loan_term": "10年",
          "approval_conditions": "需提供营业执照、近6个月流水、征信良好",
          "description": "工行商业用房贷款，首付50%起，利率4.2%起，最长10年，适合有稳定经营收入的投资者。"
        },
        {
          "id": "loan_002",
          "bank_name": "招商银行",
          "loan_type": "商铺按揭贷款",
          "interest_rate": "4.5%-5.0%",
          "down_payment_ratio": "50%",
          "max_loan_term": "10年",
          "approval_conditions": "需提供营业执照、经营证明、征信良好",
          "description": "招行商铺按揭贷款，首付50%起，利率4.5%起，审批较快，适合中小投资者。"
        }
      ],
      "analysis": "上海商铺贷款政策汇总：\n\n1. **工商银行（商业用房贷款）**：\n   - 利率：4.2%-4.8%\n   - 首付比例：50%\n   - 最长贷款期限：10年\n   - 审批条件：营业执照、近6个月流水、征信良好\n   - 特点：利率较低，适合有稳定经营收入的投资者\n\n2. **招商银行（商铺按揭贷款）**：\n   - 利率：4.5%-5.0%\n   - 首付比例：50%\n   - 最长贷款期限：10年\n   - 审批条件：营业执照、经营证明、征信良好\n   - 特点：审批较快，适合中小投资者\n\n**投资建议**：500万预算，首付250万，贷款250万，按4.5%利率、10年期计算，月供约25,900元。",
      "confidence": 0.90
    }
  },
  
  "reflection_result": {
    "evaluation": {
      "score": 7.5,
      "feedback": "报告覆盖了租金分析、竞品对比、贷款方案三个维度，内容较为完整。建议补充更多具体数据对比和风险评估。",
      "missing_dimensions": [],
      "suggestions": [
        "可以增加不同商圈的横向对比表格",
        "建议补充投资风险提示"
      ]
    },
    "iteration_count": 1,
    "timestamp": "2026-07-25T10:32:00"
  },
  
  "tool_results": {
    "faiss_search": {
      "rent_agent": [
        {"id": "rent_001", "score": 0.92},
        {"id": "rent_002", "score": 0.87}
      ],
      "competitor_agent": [
        {"id": "comp_001", "score": 0.89},
        {"id": "comp_002", "score": 0.85}
      ],
      "loan_policy_agent": [
        {"id": "loan_001", "score": 0.91},
        {"id": "loan_002", "score": 0.88}
      ]
    }
  },
  
  "final_report": "# 投资顾问报告\n\n## 一、用户需求概述\n您计划投资500万在上海浦东新区购买商铺，关注租金回报、周边竞品和贷款方案。\n\n## 二、租金分析\n### 2.1 陆家嘴商圈\n- 月租金范围：30,000-50,000元\n- 平均租金单价：450元/㎡/月\n- 年回报率：5.2%\n- 空置率：8%\n\n### 2.2 张江商圈\n- 月租金范围：18,000-28,000元\n- 平均租金单价：200元/㎡/月\n- 年回报率：4.1%\n- 空置率：12%\n\n## 三、竞品对比\n### 3.1 正大广场（陆家嘴）\n- 均价：120,000元/㎡\n- 出租率：92%\n- 优势：核心地段，品牌效应强\n\n### 3.2 前滩太古里（前滩）\n- 均价：95,000元/㎡\n- 出租率：88%\n- 优势：新兴商圈，发展潜力大\n\n## 四、贷款方案\n### 4.1 工商银行\n- 利率：4.2%-4.8%\n- 首付比例：50%\n- 最长贷款期限：10年\n\n### 4.2 招商银行\n- 利率：4.5%-5.0%\n- 首付比例：50%\n- 最长贷款期限：10年\n\n## 五、投资建议\n基于500万预算，建议首付250万，贷款250万，按4.5%利率、10年期计算，月供约25,900元。\n\n优先推荐陆家嘴商圈，回报率较高且空置率低。",
  
  "metadata": {
    "total_execution_time": 167.29,
    "total_tokens_used": 15680,
    "rag_retrievals": 6,
    "llm_calls": 8
  }
}
```

**Context 内存占用**：约 50-100 KB（包含完整数据）

---

## 五、JSONPath 使用示例

### 5.1 Agent 按需读取字段

```python
# 租金分析Agent 只需要读取租金相关数据
rent_data = context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.agent_results.rent_agent"
)
# 返回: {"agent_name": "租金测算Agent", "analysis": "...", "rag_results": [...], ...}

# 只需要分析文本
analysis_text = context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.agent_results.rent_agent.analysis"
)
# 返回: "基于RAG检索结果，浦东新区商铺投资分析如下：..."

# 读取RAG检索的第一条结果
first_rag_result = context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.agent_results.rent_agent.rag_results[0]"
)
# 返回: {"id": "rent_001", "area": "上海浦东新区", ...}

# 读取用户原始问题
user_query = context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.user_query"
)
# 返回: "我想投资500万在上海浦东新区买商铺..."

# 读取最后一条对话
last_message = context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.conversation_history[-1]"
)
# 返回: {"role": "assistant", "content": "...", "timestamp": "..."}
```

### 5.2 不同 Agent 读取不同字段

```python
# 租金分析Agent：只读取租金相关数据
rent_agent_context = {
    "user_query": context_manager.get_by_jsonpath(session_id, "$.user_query"),
    "rag_results": context_manager.get_by_jsonpath(session_id, "$.agent_results.rent_agent.rag_results"),
    "previous_analysis": context_manager.get_by_jsonpath(session_id, "$.agent_results.rent_agent.analysis")
}

# 竞品分析Agent：只读取竞品相关数据
competitor_agent_context = {
    "user_query": context_manager.get_by_jsonpath(session_id, "$.user_query"),
    "rag_results": context_manager.get_by_jsonpath(session_id, "$.agent_results.competitor_agent.rag_results"),
    "previous_analysis": context_manager.get_by_jsonpath(session_id, "$.agent_results.competitor_agent.analysis")
}

# 贷款政策Agent：只读取贷款相关数据
loan_agent_context = {
    "user_query": context_manager.get_by_jsonpath(session_id, "$.user_query"),
    "rag_results": context_manager.get_by_jsonpath(session_id, "$.agent_results.loan_policy_agent.rag_results"),
    "previous_analysis": context_manager.get_by_jsonpath(session_id, "$.agent_results.loan_policy_agent.analysis")
}
```

---

## 六、Checkpoint 快照机制

### 6.1 每个 DAG 节点执行完成后自动保存快照

```python
# 租金分析Agent 执行完成后
context_manager.save_checkpoint(
    session_id="sess_abc123xyz",
    node_id="rent_agent",
    context=current_context  # 当前完整上下文
)

# 竞品分析Agent 执行完成后
context_manager.save_checkpoint(
    session_id="sess_abc123xyz",
    node_id="competitor_agent",
    context=current_context
)

# 贷款政策Agent 执行完成后
context_manager.save_checkpoint(
    session_id="sess_abc123xyz",
    node_id="loan_policy_agent",
    context=current_context
)
```

### 6.2 故障回滚

```python
# 如果反思评估失败，可以回滚到上一个节点的状态
checkpoint = context_manager.load_checkpoint(
    session_id="sess_abc123xyz",
    node_id="loan_policy_agent"  # 回滚到贷款分析完成时的状态
)

if checkpoint:
    # 恢复上下文
    context_manager.save_context(session_id, checkpoint)
    print("已回滚到贷款分析完成时的状态")
```

---

## 七、分布式多实例数据共享

### 7.1 所有 Agent 通过 session_id 统一读写

```python
# Agent 1（运行在实例 A）
agent_a = RentAgent()
agent_a.session_id = "sess_abc123xyz"
agent_a.context_manager = get_context_manager()

# 读取用户问题
user_query = agent_a.context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.user_query"
)

# 执行分析
result = agent_a.analyze({"user_query": user_query})

# 将结果写回 Context
agent_a.context_manager.set_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.agent_results.rent_agent",
    value=result
)

# Agent 2（运行在实例 B）
agent_b = CompetitorAgent()
agent_b.session_id = "sess_abc123xyz"  # 同一个 session_id
agent_b.context_manager = get_context_manager()

# 可以读取到 Agent 1 写入的结果
rent_result = agent_b.context_manager.get_by_jsonpath(
    session_id="sess_abc123xyz",
    jsonpath="$.agent_results.rent_agent"
)
# 返回: Agent 1 写入的租金分析结果
```

---

## 八、性能对比

| 指标 | 传统方案（全量加载） | State + Context 方案 |
|------|---------------------|---------------------|
| 内存占用 | 100-200 KB/请求 | 1-2 KB/请求（State） |
| 网络IO | 每次加载全部上下文 | 按需读取指定字段 |
| 并发能力 | 受限于单机内存 | 分布式共享，无上限 |
| 故障恢复 | 无法恢复 | Checkpoint 快照，可回滚 |
| 多实例支持 | 需要额外同步机制 | 天然支持（Redis 共享） |

---

## 九、总结

### State（轻量内存状态）
- **存储内容**：session_id、request_id、intent_tags、iteration_count、status 等核心索引
- **内存占用**：1-2 KB
- **访问速度**：纳秒级（内存访问）

### Context（完整会话上下文）
- **存储位置**：Redis
- **存储内容**：完整对话、工具返回、Agent输出、RAG数据
- **内存占用**：50-100 KB
- **访问方式**：通过 JSONPath 按需读取

### JSONPath 的作用
- Agent 不拉取全部上下文
- 精准读取指定字段，减少 IO 与内存占用
- 示例：`$.agent_results.rent_agent.analysis`

### Checkpoint 快照
- DAG 每个节点执行完成后自动保存
- 故障时可回滚到上一个节点状态
- 格式：`checkpoint:{session_id}:{node_id}`

### 分布式支持
- 所有 Agent 通过 session_id 统一读写 Redis
- 支持多实例部署，数据天然共享
- 无需额外同步机制
