"""反思Agent和报告生成Agent测试"""
import pytest
import asyncio
from app.agents.reflection import ReflectionAgent
from app.report.generator import ReportGenerator


@pytest.mark.asyncio
async def test_reflection_agent_high_quality():
    """测试反思Agent评估高质量报告"""
    agent = ReflectionAgent()
    context = {
        "user_query": "我想投资上海浦东新区的商铺",
        "agent_results": {
            "rent_agent": {
                "analysis": "浦东新区商铺租金回报率分析：平均租金约5-8元/㎡/天，投资回报率约4-6%，空置率约10-15%。陆家嘴商圈租金较高，回报率稳定；金桥商圈租金适中，增长潜力大。"
            }
        },
        "iteration_count": 1
    }
    
    result = await agent.evaluate(context)
    
    assert "evaluation" in result
    assert "score" in result["evaluation"]
    assert "feedback" in result["evaluation"]
    assert result["evaluation"]["score"] >= 7  # 高质量报告应该得高分
    print(f"✓ 反思Agent高质量评估通过，评分: {result['evaluation']['score']}/10")


@pytest.mark.asyncio
async def test_reflection_agent_low_quality():
    """测试反思Agent评估低质量报告"""
    agent = ReflectionAgent()
    context = {
        "user_query": "我想投资商铺",
        "agent_results": {
            "rent_agent": {
                "analysis": "租金分析完成"  # 过于简单
            }
        },
        "iteration_count": 1
    }
    
    result = await agent.evaluate(context)
    
    assert "evaluation" in result
    assert "score" in result["evaluation"]
    assert "feedback" in result["evaluation"]
    print(f"✓ 反思Agent低质量评估通过，评分: {result['evaluation']['score']}/10")


@pytest.mark.asyncio
async def test_reflection_iteration_limit():
    """测试反思Agent迭代次数限制"""
    agent = ReflectionAgent()
    context = {
        "user_query": "我想投资商铺",
        "agent_results": {
            "rent_agent": {"analysis": "简单分析"}
        },
        "iteration_count": 3  # 达到最大迭代次数
    }
    
    result = await agent.evaluate(context)
    
    assert "evaluation" in result
    # 达到最大迭代次数时，即使质量不高也应该返回较高评分
    assert result["evaluation"]["score"] >= 7
    print(f"✓ 反思Agent迭代限制测试通过，评分: {result['evaluation']['score']}/10")


@pytest.mark.asyncio
async def test_report_generator_single_agent():
    """测试报告生成器单Agent场景"""
    generator = ReportGenerator()
    context = {
        "query": "我想投资浦东新区的商铺，帮我分析租金回报",
        "agent_results": {
            "rent_agent": {
                "analysis": "浦东新区商铺租金回报率分析：平均租金约5-8元/㎡/天，投资回报率约4-6%。"
            }
        },
        "reflection_result": {
            "evaluation": {
                "score": 8,
                "feedback": "报告质量良好"
            }
        }
    }
    
    result = await generator.generate(context)
    
    assert "report" in result
    assert len(result["report"]) > 100
    assert "租金" in result["report"] or "回报" in result["report"]
    print(f"✓ 报告生成器单Agent测试通过，报告长度: {len(result['report'])} 字符")


@pytest.mark.asyncio
async def test_report_generator_multi_agent():
    """测试报告生成器多Agent场景"""
    generator = ReportGenerator()
    context = {
        "query": "投资500万买商铺，分析租金、竞品和贷款",
        "agent_results": {
            "rent_agent": {
                "analysis": "租金回报率分析：平均回报率约4-6%。"
            },
            "competitor_agent": {
                "analysis": "竞品分析：周边3公里内有5个竞品项目。"
            },
            "loan_policy_agent": {
                "analysis": "贷款政策：首付50%，利率4.5-5.5%。"
            }
        },
        "reflection_result": {
            "evaluation": {
                "score": 8,
                "feedback": "多维度分析报告质量良好"
            }
        }
    }
    
    result = await generator.generate(context)
    
    assert "report" in result
    assert len(result["report"]) > 200
    assert "租金" in result["report"] or "回报" in result["report"]
    assert "竞品" in result["report"]
    assert "贷款" in result["report"]
    print(f"✓ 报告生成器多Agent测试通过，报告长度: {len(result['report'])} 字符")


@pytest.mark.asyncio
async def test_report_generator_format():
    """测试报告生成器格式"""
    generator = ReportGenerator()
    context = {
        "query": "分析租金回报",
        "agent_results": {
            "rent_agent": {"analysis": "租金分析内容"}
        },
        "reflection_result": {
            "evaluation": {"score": 8, "feedback": "良好"}
        }
    }
    
    result = await generator.generate(context)
    
    assert "report" in result
    report = result["report"]
    # 检查Markdown格式
    assert "#" in report or "**" in report  # 应该有标题或加粗
    print(f"✓ 报告生成器格式测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
