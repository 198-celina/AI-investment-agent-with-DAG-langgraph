"""反思迭代Agent"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.utils.llm_client import get_llm


class ReflectionAgent:
    """反思迭代Agent - 评估分析质量并提供改进建议"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.prompt = self._build_prompt()
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """构建反思评估Prompt"""
        template = """你是一个投资分析报告的质量评估专家。请评估以下分析报告的质量。

用户原始问题：{query}

分析报告内容：
{analysis}

请从以下维度评估报告质量（1-10分）：
1. 完整性：是否覆盖了用户关心的所有维度
2. 准确性：数据引用是否准确，分析是否合理
3. 实用性：建议是否具体可操作
4. 逻辑性：分析逻辑是否清晰

请输出JSON格式：
{{
    "score": 评分（1-10的整数）,
    "completeness": 完整性评分（1-10）,
    "accuracy": 准确性评分（1-10）,
    "practicality": 实用性评分（1-10）,
    "logic": 逻辑性评分（1-10）,
    "feedback": "改进建议",
    "missing_aspects": ["缺失的维度1", "缺失的维度2"]
}}
"""
        return ChatPromptTemplate.from_template(template)
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行反思评估
        
        Args:
            context: 执行上下文，包含 user_query 和 agent_results
        
        Returns:
            评估结果字典
        """
        query = context.get("user_query", "")
        agent_results = context.get("agent_results", {})
        
        # 汇总所有Agent的分析结果
        analysis_parts = []
        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and "analysis" in result:
                analysis_parts.append(f"【{agent_name}分析】\n{result['analysis']}")
        
        analysis_text = "\n\n".join(analysis_parts)
        
        # LLM评估
        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "query": query,
            "analysis": analysis_text
        })
        
        # 解析JSON响应
        import json
        try:
            evaluation = json.loads(response.content)
        except json.JSONDecodeError:
            # 如果解析失败，返回默认值
            evaluation = {
                "score": 7,
                "completeness": 7,
                "accuracy": 7,
                "practicality": 7,
                "logic": 7,
                "feedback": "报告质量一般，建议补充更多数据支撑",
                "missing_aspects": []
            }
        
        # 判断是否需要重新执行（分数低于7分或迭代次数小于3次）
        current_iteration = context.get("iteration_count", 0)
        needs_retry = evaluation["score"] < 7 and current_iteration < 3
        
        return {
            "agent_name": "reflection_agent",
            "evaluation": evaluation,
            "needs_retry": needs_retry,
            "iteration_count": current_iteration + 1,
            "confidence": 0.9
        }


# 全局实例
_reflection_agent = None

def get_reflection_agent() -> ReflectionAgent:
    """获取反思Agent单例"""
    global _reflection_agent
    if _reflection_agent is None:
        _reflection_agent = ReflectionAgent()
    return _reflection_agent
