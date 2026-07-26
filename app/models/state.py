"""全局State定义 - LangGraph工作流状态（轻量内存状态）"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class InvestmentState(BaseModel):
    """投顾系统轻量状态（仅存核心索引，不存海量大文本）
    
    设计原则：
    - State 只保存核心索引、session_id、request_id、路由标签、少量关键标记
    - 完整对话、工具返回、中间Agent输出全部存入 Redis Context
    - Agent 通过 JSONPath 按需精准读取 Redis 字段，减少IO与内存占用
    """
    
    # 核心索引（轻量）
    session_id: str = Field(description="会话唯一标识，用于Redis统一读写")
    request_id: str = Field(description="请求唯一标识，用于追踪")
    
    # 路由标签（决策依据）
    intent_tags: list[str] = Field(default_factory=list, description="意图标签列表，如['rent_analysis', 'competitor_analysis']")
    route_decision: str = Field(default="", description="路由决策结果，如'parallel_3_agents'")
    
    # 关键标记（状态控制）
    iteration_count: int = Field(default=0, description="当前迭代次数")
    max_iterations: int = Field(default=3, description="最大迭代次数")
    reflection_score: float = Field(default=0.0, description="反思评分（用于判断是否迭代）")
    status: str = Field(default="pending", description="流程状态：pending/running/completed/failed")
    
    # DAG执行状态（轻量索引）
    current_node: str = Field(default="", description="当前执行节点ID")
    completed_nodes: list[str] = Field(default_factory=list, description="已完成节点列表")
    failed_nodes: list[str] = Field(default_factory=list, description="失败节点列表")
    
    # 完整上下文引用（指向Redis）
    context_key: str = Field(default="", description="Redis Context的key，格式：context:{session_id}")
    checkpoint_key: str = Field(default="", description="Redis Checkpoint的key，格式：checkpoint:{session_id}:{node_id}")
    
    # 最终报告引用（指向Redis）
    report_key: str = Field(default="", description="最终报告在Redis中的key")
