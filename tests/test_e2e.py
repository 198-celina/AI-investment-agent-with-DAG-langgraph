"""端到端集成测试"""
import pytest
import asyncio
from app.workflow import run_investment_workflow


@pytest.mark.asyncio
async def test_rent_only_scenario():
    """测试场景1：只查询租金"""
    query = "我想投资上海浦东新区的商铺，帮我分析一下租金回报"
    result = await run_investment_workflow(query)
    
    assert result["status"] == "success"
    assert len(result["report"]) > 100
    assert result["iterations"] >= 1
    assert result["reflection_score"] >= 7
    assert "rent_agent" in result["agent_results"]
    print(f"✓ 租金场景通过，报告长度: {len(result['report'])} 字符")


@pytest.mark.asyncio
async def test_competitor_only_scenario():
    """测试场景2：只查询竞品"""
    query = "帮我分析一下前滩商圈的竞品情况"
    result = await run_investment_workflow(query)
    
    assert result["status"] == "success"
    assert len(result["report"]) > 100
    assert "competitor_agent" in result["agent_results"]
    print(f"✓ 竞品场景通过，报告长度: {len(result['report'])} 字符")


@pytest.mark.asyncio
async def test_loan_only_scenario():
    """测试场景3：只查询贷款"""
    query = "招商银行商铺贷款利率是多少"
    result = await run_investment_workflow(query)
    
    assert result["status"] == "success"
    assert len(result["report"]) > 100
    assert "loan_policy_agent" in result["agent_results"]
    print(f"✓ 贷款场景通过，报告长度: {len(result['report'])} 字符")


@pytest.mark.asyncio
async def test_multi_agent_scenario():
    """测试场景4：多Agent并行（租金+竞品+贷款）"""
    query = "我想投资500万在上海浦东新区买商铺，帮我分析租金回报、周边竞品和贷款方案"
    result = await run_investment_workflow(query)
    
    assert result["status"] == "success"
    assert len(result["report"]) > 200
    assert result["iterations"] >= 1
    # 应该激活多个Agent
    assert len(result["agent_results"]) >= 2
    print(f"✓ 多Agent场景通过，激活Agent数: {len(result['agent_results'])}")


@pytest.mark.asyncio
async def test_api_endpoint():
    """测试场景5：FastAPI接口"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # 测试健康检查
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    # 测试投顾接口
    response = client.post("/api/invest", json={
        "query": "我想投资商铺，帮我看看租金回报"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["report"]) > 0
    print(f"✓ API接口测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
