"""请求/响应Schema定义"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class InvestRequest(BaseModel):
    """投顾分析请求"""
    query: str = Field(..., description="用户投资咨询问题", min_length=1)


class AgentResult(BaseModel):
    """子Agent输出结果"""
    agent_name: str
    analysis: str
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class InvestResponse(BaseModel):
    """投顾分析响应"""
    status: str = "success"
    report: str = ""
    agent_results: dict[str, Any] = Field(default_factory=dict)
    iterations: int = 0
    reflection_score: float = 0.0


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
