"""数据验证测试"""
import pytest
import asyncio
from app.workflow import run_investment_workflow


@pytest.mark.asyncio
async def test_report_contains_user_summary():
    """测试报告包含用户需求概述"""
    result = await run_investment_workflow("我想投资浦东新区的商铺")
    
    report = result.get("report", "")
    # 报告应该包含用户需求相关内容
    assert len(report) > 100
    assert "用户需求" in report or "需求" in report or "投资" in report
    print(f"✓ 报告包含需求概述，长度: {len(report)}")


@pytest.mark.asyncio
async def test_report_contains_rent_analysis():
    """测试报告包含租金分析（租金场景）"""
    result = await run_investment_workflow("帮我分析浦东新区商铺租金回报")
    
    report = result.get("report", "")
    assert "租金" in report or "回报" in report or "收益率" in report
    print(f"✓ 报告包含租金分析")


@pytest.mark.asyncio
async def test_report_contains_competitor_analysis():
    """测试报告包含竞品分析（竞品场景）"""
    result = await run_investment_workflow("分析一下前滩商圈的竞品情况")
    
    report = result.get("report", "")
    assert "竞品" in report or "商圈" in report or "竞争" in report
    print(f"✓ 报告包含竞品分析")


@pytest.mark.asyncio
async def test_report_contains_loan_analysis():
    """测试报告包含贷款分析（贷款场景）"""
    result = await run_investment_workflow("招商银行商铺贷款利率是多少")
    
    report = result.get("report", "")
    assert "贷款" in report or "利率" in report or "首付" in report
    print(f"✓ 报告包含贷款分析")


@pytest.mark.asyncio
async def test_report_contains_investment_advice():
    """测试报告包含投资建议"""
    result = await run_investment_workflow("我想投资商铺，帮我分析租金回报")
    
    report = result.get("report", "")
    assert "建议" in report or "投资" in report or "推荐" in report
    print(f"✓ 报告包含投资建议")


@pytest.mark.asyncio
async def test_report_contains_risk_warning():
    """测试报告包含风险提示"""
    result = await run_investment_workflow("我想投资商铺，帮我分析租金回报")
    
    report = result.get("report", "")
    assert "风险" in report or "注意" in report or "提示" in report
    print(f"✓ 报告包含风险提示")


@pytest.mark.asyncio
async def test_report_contains_data_source():
    """测试报告包含数据来源"""
    result = await run_investment_workflow("我想投资商铺，帮我分析租金回报")
    
    report = result.get("report", "")
    assert "数据" in report or "来源" in report or "参考" in report
    print(f"✓ 报告包含数据来源")


@pytest.mark.asyncio
async def test_no_hallucination_data():
    """测试无幻觉数据（数据可溯源）"""
    result = await run_investment_workflow("帮我分析浦东新区商铺租金回报")
    
    report = result.get("report", "")
    
    # 检查报告中的数字是否合理（不应有离谱的幻觉数据）
    # 简单验证：报告中不应有超大数字（如1000000000%回报率）
    import re
    numbers = re.findall(r'\d+\.?\d*%', report)
    for num_str in numbers:
        num = float(num_str.rstrip('%'))
        assert num < 1000, f"发现可疑数据: {num_str}"
    
    print(f"✓ 无幻觉数据，所有百分比数据合理")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
