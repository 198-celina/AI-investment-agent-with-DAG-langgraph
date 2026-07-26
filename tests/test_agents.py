"""子Agent测试"""
import pytest
import asyncio
from app.agents.rent_agent import RentAgent
from app.agents.competitor_agent import CompetitorAgent
from app.agents.loan_policy_agent import LoanPolicyAgent


@pytest.mark.asyncio
async def test_rent_agent():
    """测试租金测算Agent"""
    agent = RentAgent()
    context = {
        "user_query": "我想投资上海浦东新区的商铺，帮我分析一下租金回报",
        "intent_result": {"rent_analysis": True}
    }
    
    result = await agent.analyze(context)
    
    assert "analysis" in result
    assert len(result["analysis"]) > 100
    assert "租金" in result["analysis"] or "回报" in result["analysis"]
    print(f"✓ 租金Agent测试通过，分析长度: {len(result['analysis'])} 字符")


@pytest.mark.asyncio
async def test_competitor_agent():
    """测试竞品分析Agent"""
    agent = CompetitorAgent()
    context = {
        "user_query": "帮我分析一下前滩商圈的竞品情况",
        "intent_result": {"competitor_analysis": True}
    }
    
    result = await agent.analyze(context)
    
    assert "analysis" in result
    assert len(result["analysis"]) > 100
    assert "竞品" in result["analysis"] or "商圈" in result["analysis"]
    print(f"✓ 竞品Agent测试通过，分析长度: {len(result['analysis'])} 字符")


@pytest.mark.asyncio
async def test_loan_policy_agent():
    """测试贷款政策Agent"""
    agent = LoanPolicyAgent()
    context = {
        "user_query": "招商银行商铺贷款利率是多少",
        "intent_result": {"loan_policy": True}
    }
    
    result = await agent.analyze(context)
    
    assert "analysis" in result
    assert len(result["analysis"]) > 100
    assert "贷款" in result["analysis"] or "利率" in result["analysis"]
    print(f"✓ 贷款Agent测试通过，分析长度: {len(result['analysis'])} 字符")


@pytest.mark.asyncio
async def test_rent_agent_with_context():
    """测试租金Agent带上下文"""
    agent = RentAgent()
    context = {
        "user_query": "投资500万买商铺，分析租金回报",
        "intent_result": {"rent_analysis": True},
        "investment_amount": 5000000,
        "location": "浦东新区"
    }
    
    result = await agent.analyze(context)
    
    assert "analysis" in result
    assert len(result["analysis"]) > 100
    print(f"✓ 租金Agent带上下文测试通过")


@pytest.mark.asyncio
async def test_competitor_agent_with_context():
    """测试竞品Agent带上下文"""
    agent = CompetitorAgent()
    context = {
        "user_query": "对比前滩和金桥的商铺",
        "intent_result": {"competitor_analysis": True},
        "locations": ["前滩", "金桥"]
    }
    
    result = await agent.analyze(context)
    
    assert "analysis" in result
    assert len(result["analysis"]) > 100
    print(f"✓ 竞品Agent带上下文测试通过")


@pytest.mark.asyncio
async def test_loan_agent_with_context():
    """测试贷款Agent带上下文"""
    agent = LoanPolicyAgent()
    context = {
        "user_query": "投资500万买商铺，贷款方案",
        "intent_result": {"loan_policy": True},
        "investment_amount": 5000000
    }
    
    result = await agent.analyze(context)
    
    assert "analysis" in result
    assert len(result["analysis"]) > 100
    print(f"✓ 贷款Agent带上下文测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
