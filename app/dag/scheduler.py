"""DAG调度引擎 - 拓扑排序与并行调度"""
from typing import Dict, List, Set, Callable, Any
from collections import defaultdict, deque
import asyncio


class DAGScheduler:
    """DAG调度器"""
    
    def __init__(self):
        self.graph = defaultdict(list)  # 邻接表
        self.in_degree = defaultdict(int)  # 入度表
        self.nodes = set()  # 所有节点
        self.node_handlers = {}  # 节点处理函数映射
    
    def add_node(self, node_id: str, handler: Callable = None):
        """添加节点
        
        Args:
            node_id: 节点ID
            handler: 节点处理函数
        """
        self.nodes.add(node_id)
        if handler:
            self.node_handlers[node_id] = handler
        # 初始化入度
        if node_id not in self.in_degree:
            self.in_degree[node_id] = 0
    
    def add_edge(self, from_node: str, to_node: str):
        """添加有向边（依赖关系）
        
        Args:
            from_node: 起始节点
            to_node: 目标节点（依赖from_node）
        """
        if from_node not in self.nodes:
            self.add_node(from_node)
        if to_node not in self.nodes:
            self.add_node(to_node)
        
        self.graph[from_node].append(to_node)
        self.in_degree[to_node] += 1
    
    def detect_cycle(self) -> bool:
        """检测是否存在循环依赖
        
        Returns:
            True表示存在循环，False表示无循环
        """
        # 使用Kahn算法检测环
        temp_in_degree = dict(self.in_degree)
        queue = deque([node for node in self.nodes if temp_in_degree[node] == 0])
        visited_count = 0
        
        while queue:
            node = queue.popleft()
            visited_count += 1
            
            for neighbor in self.graph[node]:
                temp_in_degree[neighbor] -= 1
                if temp_in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 如果访问的节点数小于总节点数，说明存在环
        return visited_count < len(self.nodes)
    
    def topological_sort(self) -> List[List[str]]:
        """拓扑排序，返回分层执行计划
        
        Returns:
            分层列表，每层包含可并行执行的节点
        
        Raises:
            ValueError: 如果存在循环依赖
        """
        if self.detect_cycle():
            raise ValueError("检测到循环依赖，无法执行拓扑排序")
        
        temp_in_degree = dict(self.in_degree)
        queue = deque([node for node in self.nodes if temp_in_degree[node] == 0])
        
        layers = []
        while queue:
            # 当前层的所有节点可以并行执行
            current_layer = list(queue)
            layers.append(current_layer)
            
            next_queue = deque()
            for node in current_layer:
                for neighbor in self.graph[node]:
                    temp_in_degree[neighbor] -= 1
                    if temp_in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            
            queue = next_queue
        
        return layers
    
    def get_execution_plan(self) -> Dict[str, Any]:
        """获取执行计划
        
        Returns:
            执行计划字典
        """
        try:
            layers = self.topological_sort()
            return {
                "valid": True,
                "layers": layers,
                "total_nodes": len(self.nodes),
                "total_layers": len(layers)
            }
        except ValueError as e:
            return {
                "valid": False,
                "error": str(e),
                "total_nodes": len(self.nodes)
            }
    
    async def execute_node(self, node_id: str, context: Dict[str, Any]) -> Any:
        """执行单个节点
        
        Args:
            node_id: 节点ID
            context: 执行上下文
        
        Returns:
            节点执行结果
        """
        if node_id not in self.node_handlers:
            raise ValueError(f"节点 {node_id} 没有注册处理函数")
        
        handler = self.node_handlers[node_id]
        if asyncio.iscoroutinefunction(handler):
            return await handler(context)
        else:
            return handler(context)
    
    async def execute_layer(self, layer: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行一层节点
        
        Args:
            layer: 节点列表
            context: 执行上下文
        
        Returns:
            各节点执行结果
        """
        tasks = [self.execute_node(node_id, context) for node_id in layer]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        layer_results = {}
        for node_id, result in zip(layer, results):
            if isinstance(result, Exception):
                layer_results[node_id] = {"error": str(result)}
            else:
                layer_results[node_id] = result
        
        return layer_results
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行整个DAG
        
        Args:
            context: 执行上下文
        
        Returns:
            所有节点执行结果
        """
        execution_plan = self.get_execution_plan()
        if not execution_plan["valid"]:
            raise ValueError(f"DAG执行失败: {execution_plan['error']}")
        
        all_results = {}
        for layer in execution_plan["layers"]:
            print(f"执行层: {layer}")
            layer_results = await self.execute_layer(layer, context)
            all_results.update(layer_results)
            # 将当前层结果加入上下文，供下一层使用
            context.update(layer_results)
        
        return all_results
    
    def clear(self):
        """清空DAG"""
        self.graph.clear()
        self.in_degree.clear()
        self.nodes.clear()
        self.node_handlers.clear()


# 全局调度器实例
_scheduler = None

def get_scheduler() -> DAGScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DAGScheduler()
    return _scheduler
