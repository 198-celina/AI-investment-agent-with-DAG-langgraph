"""报告生成模块"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.utils.llm_client import get_llm


class ReportGenerator:
    """报告生成器 - 汇总所有Agent分析结果，生成标准化投顾报告"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.prompt = self._build_prompt()
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """构建报告生成Prompt"""
        template = """你是一个专业的金融投顾报告撰写专家。请基于以下分析结果，为用户生成一份标准化的投资顾问报告。

用户原始问题：{query}

各维度分析结果：
{analysis_results}

反思评估反馈：
{reflection_feedback}

请生成一份结构化的投资顾问报告，包含以下部分：

# 投资顾问报告

## 一、用户需求概述
（简要总结用户的核心诉求）

## 二、租金回报分析
（如有租金分析，汇总租金水平、回报率、空置率等）

## 三、竞品对比分析
（如有竞品分析，汇总主要竞品、优劣势对比等）

## 四、贷款政策分析
（如有贷款分析，汇总贷款方案、利率、首付等）

## 五、综合投资建议
（综合各维度分析，给出具体可操作的投资建议）

## 六、风险提示
（列出主要风险点和注意事项）

## 七、数据来源
（列出分析所依据的数据来源）

请确保报告：
1. 逻辑清晰，层次分明
2. 数据准确，引用具体
3. 建议具体，可操作性强
4. 语言专业但易懂
5. 格式规范，使用Markdown格式
"""
        return ChatPromptTemplate.from_template(template)
    
    async def generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成投顾报告
        
        Args:
            context: 执行上下文，包含 user_query、agent_results、reflection等
        
        Returns:
            报告结果字典
        """
        query = context.get("user_query", "")
        agent_results = context.get("agent_results", {})
        reflection_result = context.get("reflection_agent", {})
        
        # 汇总Agent分析结果
        analysis_parts = []
        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and "analysis" in result:
                agent_label = {
                    "rent_agent": "租金测算",
                    "competitor_agent": "竞品对比",
                    "loan_policy_agent": "贷款政策"
                }.get(agent_name, agent_name)
                analysis_parts.append(f"【{agent_label}分析】\n{result['analysis']}")
        
        analysis_text = "\n\n".join(analysis_parts)
        
        # 获取反思反馈
        reflection_feedback = ""
        if reflection_result and "evaluation" in reflection_result:
            eval_data = reflection_result["evaluation"]
            reflection_feedback = f"评分：{eval_data.get('score', 'N/A')}/10\n改进建议：{eval_data.get('feedback', '无')}"
        
        # LLM生成报告
        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "query": query,
            "analysis_results": analysis_text,
            "reflection_feedback": reflection_feedback
        })
        
        return {
            "agent_name": "report_generator",
            "report": response.content,
            "confidence": 0.9
        }


# 全局实例
_report_generator = None

def get_report_generator() -> ReportGenerator:
    """获取报告生成器单例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
