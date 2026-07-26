"""性能测试"""
import pytest
import asyncio
import time
from app.workflow import run_investment_workflow


@pytest.mark.asyncio
async def test_intent_recognition_performance():
    """测试意图识别性能"""
    from app.agents.intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    query = "我想投资商铺，帮我分析租金回报、竞品和贷款"
    
    start = time.time()
    result = classifier.classify(query)
    elapsed = time.time() - start
    
    print(f"意图识别耗时: {elapsed:.2f}秒")
    assert elapsed < 5, f"意图识别超时: {elapsed}秒"
    assert result["rent_analysis"] is True


@pytest.mark.asyncio
async def test_single_agent_performance():
    """测试单Agent执行性能"""
    from app.agents.rent_agent import RentAgent
    
    agent = RentAgent()
    context = {"user_query": "我想投资浦东新区的商铺，帮我分析租金回报"}
    
    start = time.time()
    result = await agent.analyze(context)
    elapsed = time.time() - start
    
    print(f"单Agent执行耗时: {elapsed:.2f}秒")
    assert elapsed < 60, f"单Agent执行超时: {elapsed}秒"
    assert "analysis" in result


@pytest.mark.asyncio
async def test_multi_agent_performance():
    """测试多Agent并行执行性能"""
    from app.agents.rent_agent import RentAgent
    from app.agents.competitor_agent import CompetitorAgent
    from app.agents.loan_policy_agent import LoanPolicyAgent
    
    rent_agent = RentAgent()
    competitor_agent = CompetitorAgent()
    loan_agent = LoanPolicyAgent()
    
    context = {"user_query": "我想投资500万买商铺，分析租金、竞品和贷款"}
    
    start = time.time()
    
    # 并行执行3个Agent
    results = await asyncio.gather(
        rent_agent.analyze(context),
        competitor_agent.analyze(context),
        loan_agent.analyze(context)
    )
    
    elapsed = time.time() - start
    
    print(f"多Agent并行执行耗时: {elapsed:.2f}秒")
    assert elapsed < 120, f"多Agent执行超时: {elapsed}秒"
    assert len(results) == 3


@pytest.mark.asyncio
async def test_workflow_performance():
    """测试完整工作流性能"""
    query = "我想投资商铺，帮我分析租金回报、竞品和贷款"
    
    start = time.time()
    result = await run_investment_workflow(query)
    elapsed = time.time() - start
    
    print(f"完整工作流耗时: {elapsed:.2f}秒")
    # 工作流包含意图识别、Agent执行、反思、报告生成，允许较长时间
    assert elapsed < 180, f"工作流执行超时: {elapsed}秒"
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_api_response_performance():
    """测试API响应性能"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    start = time.time()
    response = client.post("/api/invest", json={"query": "我想投资商铺"})
    elapsed = time.time() - start
    
    print(f"API响应时间: {elapsed:.2f}秒")
    # API响应包含完整工作流，允许较长时间
    assert elapsed < 300, f"API响应超时: {elapsed}秒"
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_requests():
    """测试并发请求性能"""
    from fastapi.testclient import TestClient
    from app.main import app
    import concurrent.futures
    
    client = TestClient(app)
    
    def make_request(i):
        """发送单个请求"""
        start = time.time()
        response = client.post("/api/invest", json={"query": f"我想投资商铺{i}"})
        elapsed = time.time() - start
        return response.status_code, elapsed
    
    # 测试5个并发请求
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    total_elapsed = time.time() - start
    
    # 验证所有请求成功
    status_codes = [r[0] for r in results]
    response_times = [r[1] for r in results]
    
    print(f"并发测试: 5个请求，总耗时 {total_elapsed:.2f}秒")
    print(f"平均响应时间: {sum(response_times)/len(response_times):.2f}秒")
    print(f"最慢响应时间: {max(response_times):.2f}秒")
    
    assert all(code == 200 for code in status_codes), f"部分请求失败: {status_codes}"
    assert total_elapsed < 600, f"并发测试超时: {total_elapsed}秒"


def test_deployment_verification():
    """测试部署验证"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # 1. 健康检查接口
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✓ 健康检查接口正常")
    
    # 2. 投顾分析接口
    response = client.post("/api/invest", json={"query": "我想投资商铺"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["report"]) > 50
    assert data["iterations"] >= 1
    print("✓ 投顾分析接口正常")
    
    # 3. 验证返回数据结构
    assert "report" in data
    assert "iterations" in data
    assert "agent_results" in data
    print("✓ 返回数据结构完整")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
