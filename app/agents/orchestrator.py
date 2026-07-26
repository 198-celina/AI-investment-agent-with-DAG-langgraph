"""主调度Agent - 使用LangGraph编排完整工作流"""
import asyncio
from typing import Dict, Any, TypedDict, Literal
from langgraph.graph import StateGraph, END, START
from app.agents.intent_classifier import get_intent_classifier
from app.agents.rent_agent import get_rent_agent
from app.agents.competitor_agent import get_competitor_agent
from app.agents.loan_policy_agent import get_loan_policy_agent
from app.agents.reflection import get_reflection_agent
from app.report.generator import get_report_generator


class InvestmentState(TypedDict):
    """投资分析状态"""
    user_query: str
    intent_result: Dict[str, bool]
    agent_results: Dict[str, Any]
    reflection_result: Dict[str, Any]
    iteration_count: int
    final_report: str


class OrchestratorAgent:
    """主调度Agent - 编排整个投资分析流程"""
    
    def __init__(self):
        self.intent_classifier = get_intent_classifier()
        self.rent_agent = get_rent_agent()
        self.competitor_agent = get_competitor_agent()
        self.loan_policy_agent = get_loan_policy_agent()
        self.reflection_agent = get_reflection_agent()
        self.report_generator = get_report_generator()
        
        # 构建LangGraph工作流
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """构建LangGraph工作流图"""
        
        # 创建状态图
        workflow = StateGraph(InvestmentState)
        
        # 添加节点
        workflow.add_node("intent_classifier", self._intent_classifier_node)
        workflow.add_node("execute_agents", self._execute_agents_node)
        workflow.add_node("reflection", self._reflection_node)
        workflow.add_node("report_generator", self._report_generator_node)
        
        # 添加边
        workflow.add_edge(START, "intent_classifier")
        workflow.add_edge("intent_classifier", "execute_agents")
        workflow.add_edge("execute_agents", "reflection")
        
        # 添加条件边：反思后决定是否重新执行
        workflow.add_conditional_edges(
            "reflection",
            self._should_retry,
            {
                "retry": "execute_agents",  # 不满意，重新执行
                "complete": "report_generator"  # 满意，生成报告
            }
        )
        
        workflow.add_edge("report_generator", END)
        
        # 编译工作流
        return workflow.compile()
    
    async def _intent_classifier_node(self, state: InvestmentState) -> Dict[str, Any]:
        """意图识别节点"""
        print("🔍 执行意图识别...")
        query = state["user_query"]
        intent_result = self.intent_classifier.classify(query)
        print(f"   意图识别结果: {intent_result}")
        return {"intent_result": intent_result}
    
    async def _execute_agents_node(self, state: InvestmentState) -> Dict[str, Any]:
        """执行子Agent节点（并行执行）"""
        intent_result = state["intent_result"]
        query = state["user_query"]
        iteration_count = state.get("iteration_count", 0)
        
        print(f"🤖 执行子Agent（第{iteration_count + 1}轮）...")
        
        # 准备上下文
        context = {"user_query": query}
        
        # 根据意图并行执行对应的Agent
        tasks = []
        agent_names = []
        
        if intent_result.get("rent_analysis"):
            tasks.append(self.rent_agent.analyze(context))
            agent_names.append("rent_agent")
        
        if intent_result.get("competitor_analysis"):
            tasks.append(self.competitor_agent.analyze(context))
            agent_names.append("competitor_agent")
        
        if intent_result.get("loan_policy"):
            tasks.append(self.loan_policy_agent.analyze(context))
            agent_names.append("loan_policy_agent")
        
        # 并行执行
        results = await asyncio.gather(*tasks)
        
        # 汇总结果
        agent_results = {}
        for agent_name, result in zip(agent_names, results):
            agent_results[agent_name] = result
            print(f"   ✓ {agent_name} 完成")
        
        return {
            "agent_results": agent_results,
            "iteration_count": iteration_count + 1
        }
    
    async def _reflection_node(self, state: InvestmentState) -> Dict[str, Any]:
        """反思评估节点"""
        print("🤔 执行反思评估...")
        query = state["user_query"]
        agent_results = state["agent_results"]
        iteration_count = state.get("iteration_count", 0)
        
        context = {
            "user_query": query,
            "agent_results": agent_results,
            "iteration_count": iteration_count
        }
        
        reflection_result = await self.reflection_agent.evaluate(context)
        score = reflection_result["evaluation"]["score"]
        print(f"   反思评分: {score}/10")
        
        return {"reflection_result": reflection_result}
    
    def _should_retry(self, state: InvestmentState) -> Literal["retry", "complete"]:
        """判断是否需要重新执行"""
        reflection_result = state.get("reflection_result", {})
        iteration_count = state.get("iteration_count", 0)
        
        # 最多迭代3次
        if iteration_count >= 3:
            print("   ⚠️  达到最大迭代次数，继续生成报告")
            return "complete"
        
        # 评分低于7分，重新执行
        evaluation = reflection_result.get("evaluation", {})
        score = evaluation.get("score", 10)
        
        if score < 7:
            print(f"   🔄 评分{score}分 < 7分，重新执行Agent")
            return "retry"
        
        print(f"   ✓ 评分{score}分 >= 7分，继续生成报告")
        return "complete"
    
    async def _report_generator_node(self, state: InvestmentState) -> Dict[str, Any]:
        """报告生成节点"""
        print("📝 生成投顾报告...")
        query = state["user_query"]
        agent_results = state["agent_results"]
        reflection_result = state.get("reflection_result", {})
        
        context = {
            "user_query": query,
            "agent_results": agent_results,
            "reflection_result": reflection_result
        }
        
        report_result = await self.report_generator.generate(context)
        final_report = report_result["report"]
        print(f"   ✓ 报告生成完成（{len(final_report)}字符）")
        
        return {"final_report": final_report}
    
    async def analyze(self, query: str) -> Dict[str, Any]:
        """执行完整的投资分析流程
        
        Args:
            query: 用户问题
        
        Returns:
            分析结果字典
        """
        # 初始化状态
        initial_state = {
            "user_query": query,
            "intent_result": {},
            "agent_results": {},
            "reflection_result": {},
            "iteration_count": 0,
            "final_report": ""
        }
        
        # 执行工作流
        final_state = await self.workflow.ainvoke(initial_state)
        
        return {
            "status": "success",
            "report": final_state["final_report"],
            "agent_results": final_state["agent_results"],
            "iterations": final_state["iteration_count"],
            "reflection_score": final_state["reflection_result"].get("evaluation", {}).get("score", 0)
        }


# 全局实例
_orchestrator = None

def get_orchestrator() -> OrchestratorAgent:
    """获取主调度Agent单例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
