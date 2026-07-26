"""阶段8测试：LangGraph全流程串联"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import pytest


def test_workflow_import():
    """测试工作流模块能否正常导入"""
    from app.workflow import InvestmentWorkflow, run_investment_workflow
    print("✅ 工作流模块导入正常")


def test_workflow_build():
    """测试工作流图能否正常构建"""
    from app.workflow import InvestmentWorkflow
    wf = InvestmentWorkflow()
    assert wf.workflow is not None
    print("✅ 工作流图构建正常")


def test_workflow_run():
    """测试完整工作流运行"""
    from app.workflow import run_investment_workflow
    
    query = "我想投资上海浦东新区的商铺，帮我分析一下租金回报"
    result = asyncio.run(run_investment_workflow(query))
    
    print(f"\n=== 工作流运行结果 ===")
    print(f"状态: {result['status']}")
    print(f"迭代次数: {result['iterations']}")
    print(f"反思评分: {result['reflection_score']}")
    print(f"Agent结果数: {len(result['agent_results'])}")
    print(f"报告长度: {len(result['report'])} 字符")
    print(f"\n--- 报告内容 ---")
    report = result['report']
    if isinstance(report, str):
        print(report[:500])
    else:
        print(f"报告类型: {type(report)}")
        print(f"报告内容: {report}")
    
    assert result['status'] == 'success'
    assert len(result['report']) > 0
    assert len(result['agent_results']) > 0
    print("\n✅ 完整工作流运行正常")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
