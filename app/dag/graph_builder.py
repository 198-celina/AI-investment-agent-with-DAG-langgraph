"""动态DAG图构建器"""
from typing import Dict, Any, Callable
from app.dag.scheduler import DAGScheduler


class GraphBuilder:
    """根据意图动态构建DAG图"""
    
    def __init__(self):
        self.scheduler = DAGScheduler()
    
    def build_from_intent(self, intent: Dict[str, bool], agent_handlers: Dict[str, Callable]):
        """根据意图识别结果构建DAG
        
        Args:
            intent: 意图识别结果，如 {"rent_analysis": True, "competitor_analysis": False, "loan_policy": True}
            agent_handlers: Agent处理函数字典，如 {"rent_analysis": handler_func, ...}
        
        Returns:
            配置好的DAGScheduler实例
        """
        self.scheduler.clear()
        
        # 添加起始节点（意图识别）
        self.scheduler.add_node("intent_classifier")
        
        # 根据意图添加对应的Agent节点
        active_agents = []
        
        if intent.get("rent_analysis"):
            self.scheduler.add_node("rent_agent", agent_handlers.get("rent_analysis"))
            active_agents.append("rent_agent")
        
        if intent.get("competitor_analysis"):
            self.scheduler.add_node("competitor_agent", agent_handlers.get("competitor_analysis"))
            active_agents.append("competitor_agent")
        
        if intent.get("loan_policy"):
            self.scheduler.add_node("loan_policy_agent", agent_handlers.get("loan_policy"))
            active_agents.append("loan_policy_agent")
        
        # 添加汇总节点
        self.scheduler.add_node("aggregator")
        
        # 添加反思节点
        self.scheduler.add_node("reflection")
        
        # 添加报告生成节点
        self.scheduler.add_node("report_generator")
        
        # 构建依赖关系
        # 1. 意图识别 -> 所有激活的Agent（并行）
        for agent in active_agents:
            self.scheduler.add_edge("intent_classifier", agent)
        
        # 2. 所有Agent -> 汇总节点
        for agent in active_agents:
            self.scheduler.add_edge(agent, "aggregator")
        
        # 3. 汇总 -> 反思 -> 报告生成（串行）
        self.scheduler.add_edge("aggregator", "reflection")
        self.scheduler.add_edge("reflection", "report_generator")
        
        return self.scheduler
    
    def get_execution_plan(self) -> Dict[str, Any]:
        """获取执行计划"""
        return self.scheduler.get_execution_plan()
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行DAG"""
        return await self.scheduler.execute(context)
