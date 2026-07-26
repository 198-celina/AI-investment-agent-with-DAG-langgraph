"""运行案例并捕获每个节点的输入输出"""
import asyncio
import json
import time
from app.workflow import run_investment_workflow


async def trace_workflow():
    """运行工作流并记录每个节点的输入输出"""
    query = "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案"
    
    print("=" * 80)
    print(f"【案例查询】{query}")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    # 运行工作流
    result = await run_investment_workflow(query)
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 80)
    print(f"【执行完成】总耗时: {elapsed:.2f}秒")
    print("=" * 80)
    print()
    
    # 输出结果摘要
    print("【结果摘要】")
    print(f"  - 状态: {result.get('status')}")
    print(f"  - 迭代次数: {result.get('iterations')}")
    print(f"  - 报告长度: {len(result.get('report', ''))} 字符")
    print(f"  - 激活Agent数: {len(result.get('agent_results', {}))}")
    print()
    
    # 输出每个Agent的结果
    print("【Agent执行结果】")
    for agent_name, agent_result in result.get('agent_results', {}).items():
        print(f"\n  [{agent_name}]")
        if 'analysis' in agent_result:
            analysis = agent_result['analysis']
            # 只显示前200字符
            print(f"    分析内容: {analysis[:200]}...")
        if 'error' in agent_result:
            print(f"    错误: {agent_result['error']}")
    
    print()
    print("=" * 80)
    print("【最终报告预览】")
    print("=" * 80)
    report = result.get('report', '')
    # 显示前500字符
    print(report[:500])
    print("...")
    print(f"\n（完整报告长度: {len(report)} 字符）")
    
    return result


if __name__ == "__main__":
    asyncio.run(trace_workflow())
