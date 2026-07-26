"""LangGraph 工作流编排"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from app.agents.intent_classifier import IntentClassifier
from app.dag.scheduler import DAGScheduler
from app.agents.rent_agent import RentAgent
from app.agents.competitor_agent import CompetitorAgent
from app.agents.loan_policy_agent import LoanPolicyAgent
from app.agents.reflection import ReflectionAgent
from app.report.generator import ReportGenerator


class InvestmentState(BaseModel):
    """投资分析状态"""
    query: str
    intent_result: Dict[str, bool] = {}
    dag_plan: Dict[str, Any] = {}
    agent_results: Dict[str, Any] = {}
    reflection_result: Dict[str, Any] = {}
    final_report: str = ""
    iteration_count: int = 0
    max_iterations: int = 3
    
    class Config:
        arbitrary_types_allowed = True


class InvestmentWorkflow:
    """投资分析工作流编排器"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.dag_scheduler = DAGScheduler()
        self.rent_agent = RentAgent()
        self.competitor_agent = CompetitorAgent()
        self.loan_policy_agent = LoanPolicyAgent()
        self.reflection_agent = ReflectionAgent()
        self.report_generator = ReportGenerator()
        
        # 构建工作流图
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        
        # 创建状态图
        workflow = StateGraph(InvestmentState)
        
        # 添加节点
        workflow.add_node("intent_classification", self._intent_classification_node)
        workflow.add_node("dag_planning", self._dag_planning_node)
        workflow.add_node("agent_execution", self._agent_execution_node)
        workflow.add_node("reflection", self._reflection_node)
        workflow.add_node("report_generation", self._report_generation_node)
        
        # 设置入口
        workflow.set_entry_point("intent_classification")
        
        # 添加边
        workflow.add_edge("intent_classification", "dag_planning")
        workflow.add_edge("dag_planning", "agent_execution")
        workflow.add_edge("agent_execution", "reflection")
        
        # 添加条件边：反思后决定是否迭代
        workflow.add_conditional_edges(
            "reflection",
            self._should_iterate,
            {
                "iterate": "agent_execution",  # 需要迭代，重新执行 Agent
                "complete": "report_generation"  # 完成，生成报告
            }
        )
        
        workflow.add_edge("report_generation", END)
        
        # 编译工作流
        return workflow.compile()
    
    async def _intent_classification_node(self, state: InvestmentState) -> Dict[str, Any]:
        """意图识别节点"""
        print(f"[工作流] 执行意图识别: {state.query}")
        intent_result = self.intent_classifier.classify(state.query)
        print(f"[工作流] 意图识别结果: {intent_result}")
        return {"intent_result": intent_result}
    
    async def _dag_planning_node(self, state: InvestmentState) -> Dict[str, Any]:
        """DAG 规划节点"""
        print("[工作流] 规划 DAG 执行计划")
        intent_result = state.intent_result
        
        # 根据意图构建 DAG
        self.dag_scheduler.clear()
        
        # 添加 Agent 节点
        if intent_result.get("rent_analysis"):
            self.dag_scheduler.add_node("rent_agent")
        if intent_result.get("competitor_analysis"):
            self.dag_scheduler.add_node("competitor_agent")
        if intent_result.get("loan_policy"):
            self.dag_scheduler.add_node("loan_policy_agent")
        
        # 获取执行计划
        dag_plan = self.dag_scheduler.get_execution_plan()
        print(f"[工作流] DAG 执行计划: {dag_plan}")
        
        return {"dag_plan": dag_plan}
    
    async def _agent_execution_node(self, state: InvestmentState) -> Dict[str, Any]:
        """Agent 执行节点"""
        print(f"[工作流] 执行 Agent（第 {state.iteration_count + 1} 轮）")
        intent_result = state.intent_result
        query = state.query
        context = {"user_query": query}
        
        agent_results = {}
        
        # 根据意图执行对应的 Agent
        if intent_result.get("rent_analysis"):
            print("[工作流] 执行租金分析 Agent")
            agent_results["rent_agent"] = await self.rent_agent.analyze(context)
        
        if intent_result.get("competitor_analysis"):
            print("[工作流] 执行竞品分析 Agent")
            agent_results["competitor_agent"] = await self.competitor_agent.analyze(context)
        
        if intent_result.get("loan_policy"):
            print("[工作流] 执行贷款政策 Agent")
            agent_results["loan_policy_agent"] = await self.loan_policy_agent.analyze(context)
        
        print(f"[工作流] Agent 执行完成，结果数量: {len(agent_results)}")
        
        return {
            "agent_results": agent_results,
            "iteration_count": state.iteration_count + 1
        }
    
    async def _reflection_node(self, state: InvestmentState) -> Dict[str, Any]:
        """反思节点"""
        print("[工作流] 执行反思评估")
        
        # 准备反思输入
        reflection_input = {
            "user_query": state.query,
            "agent_results": state.agent_results,
            "iteration_count": state.iteration_count
        }
        
        reflection_result = await self.reflection_agent.evaluate(reflection_input)
        score = reflection_result.get("evaluation", {}).get("score", 0)
        print(f"[工作流] 反思结果: 评分 {score}/10")
        
        return {"reflection_result": reflection_result}
    
    def _should_iterate(self, state: InvestmentState) -> str:
        """判断是否需要迭代"""
        reflection_result = state.reflection_result
        score = reflection_result.get("evaluation", {}).get("score", 0)
        iteration_count = state.iteration_count
        
        print(f"[工作流] 判断是否迭代: 评分={score}, 迭代次数={iteration_count}/{state.max_iterations}")
        
        # 如果评分低于 7 分且未达到最大迭代次数，则继续迭代
        if score < 7 and iteration_count < state.max_iterations:
            print("[工作流] 决定: 继续迭代")
            return "iterate"
        else:
            print("[工作流] 决定: 完成分析")
            return "complete"
    
    async def _report_generation_node(self, state: InvestmentState) -> Dict[str, Any]:
        """报告生成节点"""
        print("[工作流] 生成最终报告")
        
        # 准备报告生成输入
        report_input = {
            "query": state.query,
            "agent_results": state.agent_results,
            "reflection_result": state.reflection_result
        }
        
        report_result = await self.report_generator.generate(report_input)
        final_report = report_result.get("report", "")
        print(f"[工作流] 报告生成完成，长度: {len(final_report)} 字符")
        
        return {"final_report": final_report}
    
    async def run(self, query: str) -> Dict[str, Any]:
        """运行完整工作流"""
        print(f"\n{'='*60}")
        print(f"[工作流] 开始处理查询: {query}")
        print(f"{'='*60}\n")
        
        # 初始化状态
        initial_state = InvestmentState(query=query)
        
        # 执行工作流
        final_state = await self.workflow.ainvoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"[工作流] 分析完成")
        print(f"{'='*60}\n")
        
        return {
            "status": "success",
            "report": final_state.get("final_report", ""),
            "agent_results": final_state.get("agent_results", {}),
            "iterations": final_state.get("iteration_count", 0),
            "reflection_score": final_state.get("reflection_result", {}).get("evaluation", {}).get("score", 0)
        }


# 全局工作流实例
workflow_instance = InvestmentWorkflow()


async def run_investment_workflow(query: str) -> Dict[str, Any]:
    """运行投资分析工作流的便捷函数"""
    return await workflow_instance.run(query)


class InvestmentWorkflowWithEvents:
    """支持事件回调的投资分析工作流"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.dag_scheduler = DAGScheduler()
        self.rent_agent = RentAgent()
        self.competitor_agent = CompetitorAgent()
        self.loan_policy_agent = LoanPolicyAgent()
        self.reflection_agent = ReflectionAgent()
        self.report_generator = ReportGenerator()
    
    async def run_with_events(self, query: str):
        """运行工作流并发送事件（生成器模式）"""
        import time
        
        # 1. 意图识别
        yield {"type": "intent_start", "data": {"query": query}}
        start_time = time.time()
        intent_result = self.intent_classifier.classify(query)
        elapsed = time.time() - start_time
        yield {
            "type": "intent_complete", 
            "data": {
                "result": intent_result,
                "elapsed": round(elapsed, 2)
            }
        }
        
        # 2. DAG规划
        yield {"type": "dag_start", "data": {}}
        start_time = time.time()
        self.dag_scheduler.clear()
        if intent_result.get("rent_analysis"):
            self.dag_scheduler.add_node("rent_agent")
        if intent_result.get("competitor_analysis"):
            self.dag_scheduler.add_node("competitor_agent")
        if intent_result.get("loan_policy"):
            self.dag_scheduler.add_node("loan_policy_agent")
        dag_plan = self.dag_scheduler.get_execution_plan()
        elapsed = time.time() - start_time
        yield {
            "type": "dag_complete",
            "data": {
                "plan": dag_plan,
                "elapsed": round(elapsed, 2)
            }
        }
        
        # 3. Agent执行
        yield {"type": "agents_start", "data": {"count": dag_plan.get("total_nodes", 0)}}
        start_time = time.time()
        context = {"user_query": query}
        agent_results = {}
        
        if intent_result.get("rent_analysis"):
            yield {"type": "agent_start", "data": {"agent": "rent_agent"}}
            agent_results["rent_agent"] = await self.rent_agent.analyze(context)
            yield {"type": "agent_complete", "data": {"agent": "rent_agent"}}
        
        if intent_result.get("competitor_analysis"):
            yield {"type": "agent_start", "data": {"agent": "competitor_agent"}}
            agent_results["competitor_agent"] = await self.competitor_agent.analyze(context)
            yield {"type": "agent_complete", "data": {"agent": "competitor_agent"}}
        
        if intent_result.get("loan_policy"):
            yield {"type": "agent_start", "data": {"agent": "loan_policy_agent"}}
            agent_results["loan_policy_agent"] = await self.loan_policy_agent.analyze(context)
            yield {"type": "agent_complete", "data": {"agent": "loan_policy_agent"}}
        
        elapsed = time.time() - start_time
        yield {
            "type": "agents_complete",
            "data": {
                "count": len(agent_results),
                "elapsed": round(elapsed, 2)
            }
        }
        
        # 4. 反思评估
        yield {"type": "reflection_start", "data": {}}
        start_time = time.time()
        reflection_input = {
            "user_query": query,
            "agent_results": agent_results,
            "iteration_count": 1
        }
        reflection_result = await self.reflection_agent.evaluate(reflection_input)
        score = reflection_result.get("evaluation", {}).get("score", 0)
        elapsed = time.time() - start_time
        yield {
            "type": "reflection_complete",
            "data": {
                "score": score,
                "elapsed": round(elapsed, 2)
            }
        }
        
        # 5. 报告生成
        yield {"type": "report_start", "data": {}}
        start_time = time.time()
        report_input = {
            "query": query,
            "agent_results": agent_results,
            "reflection_result": reflection_result
        }
        report_result = await self.report_generator.generate(report_input)
        final_report = report_result.get("report", "")
        elapsed = time.time() - start_time
        yield {
            "type": "report_complete",
            "data": {
                "length": len(final_report),
                "elapsed": round(elapsed, 2)
            }
        }
        
        # 6. 完成
        yield {
            "type": "complete",
            "data": {
                "status": "success",
                "report": final_report,
                "agent_results": agent_results,
                "iterations": 1,
                "reflection_score": score
            }
        }


# 全局事件工作流实例
workflow_events_instance = InvestmentWorkflowWithEvents()


async def run_investment_workflow_with_events(query: str):
    """运行投资分析工作流并返回事件生成器"""
    async for event in workflow_events_instance.run_with_events(query):
        yield event
