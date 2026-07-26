"""意图识别模块测试"""
import pytest
import json
from pathlib import Path
from app.agents.intent_classifier import get_intent_classifier


def test_intent_classifier_basic():
    """测试意图识别器基本功能"""
    classifier = get_intent_classifier()
    
    query = "我想投资商铺，帮我看看租金回报"
    result = classifier.classify(query)
    
    print(f"查询: {query}")
    print(f"识别结果: {result}")
    
    assert "rent_analysis" in result
    assert "competitor_analysis" in result
    assert "loan_policy" in result
    assert result["rent_analysis"] is True


def test_intent_classifier_all_cases():
    """测试所有意图识别用例"""
    classifier = get_intent_classifier()
    
    # 加载测试用例
    test_file = Path(__file__).parent / "test_data" / "intent_test_cases.json"
    with open(test_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    
    print("\n=== 意图识别测试 ===")
    passed = 0
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected = case["expected_intent"]
        
        result = classifier.classify(query)
        
        # 检查是否匹配
        match = (
            result.get("rent_analysis") == expected["rent_analysis"] and
            result.get("competitor_analysis") == expected["competitor_analysis"] and
            result.get("loan_policy") == expected["loan_policy"]
        )
        
        if match:
            print(f"[{i}] ✅ {query}")
            passed += 1
        else:
            print(f"[{i}] ❌ {query}")
            print(f"   期望: {expected}")
            print(f"   实际: {result}")
    
    print(f"\n通过率: {passed}/{len(test_cases)}")
    assert passed >= len(test_cases) * 0.8, f"意图识别准确率过低: {passed}/{len(test_cases)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
