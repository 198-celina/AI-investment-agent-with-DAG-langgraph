"""DAG调度引擎测试"""
import pytest
from app.dag.scheduler import DAGScheduler


def test_single_node_execution():
    """测试单节点执行"""
    scheduler = DAGScheduler()
    scheduler.add_node("rent_agent")
    
    plan = scheduler.get_execution_plan()
    
    assert plan["valid"] is True
    assert plan["total_nodes"] == 1
    assert plan["total_layers"] == 1
    assert len(plan["layers"]) == 1
    assert "rent_agent" in plan["layers"][0]
    print("✓ 单节点执行测试通过")


def test_multi_node_parallel():
    """测试多节点并行执行"""
    scheduler = DAGScheduler()
    scheduler.add_node("rent_agent")
    scheduler.add_node("competitor_agent")
    scheduler.add_node("loan_policy_agent")
    
    plan = scheduler.get_execution_plan()
    
    assert plan["valid"] is True
    assert plan["total_nodes"] == 3
    assert plan["total_layers"] == 1
    assert len(plan["layers"]) == 1
    # 所有Agent应该在同一层（并行执行）
    assert len(plan["layers"][0]) == 3
    assert "rent_agent" in plan["layers"][0]
    assert "competitor_agent" in plan["layers"][0]
    assert "loan_policy_agent" in plan["layers"][0]
    print("✓ 多节点并行执行测试通过")


def test_dependency_ordering():
    """测试依赖排序"""
    scheduler = DAGScheduler()
    scheduler.add_node("node_a")
    scheduler.add_node("node_b")
    scheduler.add_node("node_c")
    
    # 添加依赖关系：A -> B -> C
    scheduler.add_edge("node_a", "node_b")
    scheduler.add_edge("node_b", "node_c")
    
    plan = scheduler.get_execution_plan()
    
    assert plan["valid"] is True
    assert plan["total_nodes"] == 3
    assert plan["total_layers"] == 3
    # 应该按拓扑顺序分3层
    assert plan["layers"][0] == ["node_a"]
    assert plan["layers"][1] == ["node_b"]
    assert plan["layers"][2] == ["node_c"]
    print("✓ 依赖排序测试通过")


def test_cycle_detection():
    """测试循环依赖检测"""
    scheduler = DAGScheduler()
    scheduler.add_node("node_a")
    scheduler.add_node("node_b")
    scheduler.add_node("node_c")
    
    # 构造循环依赖：A -> B -> C -> A
    scheduler.add_edge("node_a", "node_b")
    scheduler.add_edge("node_b", "node_c")
    scheduler.add_edge("node_c", "node_a")
    
    plan = scheduler.get_execution_plan()
    
    # 应该检测到循环依赖
    assert plan["valid"] is False
    assert "error" in plan
    print("✓ 循环依赖检测测试通过")


def test_complex_dag():
    """测试复杂DAG结构"""
    scheduler = DAGScheduler()
    scheduler.add_node("intent")
    scheduler.add_node("rent")
    scheduler.add_node("competitor")
    scheduler.add_node("loan")
    scheduler.add_node("report")
    
    # 意图识别 -> 3个Agent并行 -> 报告生成
    scheduler.add_edge("intent", "rent")
    scheduler.add_edge("intent", "competitor")
    scheduler.add_edge("intent", "loan")
    scheduler.add_edge("rent", "report")
    scheduler.add_edge("competitor", "report")
    scheduler.add_edge("loan", "report")
    
    plan = scheduler.get_execution_plan()
    
    assert plan["valid"] is True
    assert plan["total_nodes"] == 5
    assert plan["total_layers"] == 3
    # 第1层：意图识别
    assert plan["layers"][0] == ["intent"]
    # 第2层：3个Agent并行
    assert len(plan["layers"][1]) == 3
    # 第3层：报告生成
    assert plan["layers"][2] == ["report"]
    print("✓ 复杂DAG结构测试通过")


def test_empty_dag():
    """测试空DAG"""
    scheduler = DAGScheduler()
    
    plan = scheduler.get_execution_plan()
    
    assert plan["valid"] is True
    assert plan["total_nodes"] == 0
    assert plan["total_layers"] == 0
    assert len(plan["layers"]) == 0
    print("✓ 空DAG测试通过")


def test_clear_nodes():
    """测试清空节点"""
    scheduler = DAGScheduler()
    scheduler.add_node("node_a")
    scheduler.add_node("node_b")
    
    plan1 = scheduler.get_execution_plan()
    assert plan1["total_nodes"] == 2
    
    # 清空节点
    scheduler.clear()
    
    plan2 = scheduler.get_execution_plan()
    assert plan2["total_nodes"] == 0
    print("✓ 清空节点测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
