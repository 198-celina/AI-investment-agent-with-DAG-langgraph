"""阶段2测试：RAG知识库"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import json
from pathlib import Path
from app.rag.knowledge_base import get_knowledge_base


def test_knowledge_base_load():
    """测试知识库加载"""
    kb = get_knowledge_base()
    assert kb is not None
    assert kb.vectorstore is not None
    print("✅ 知识库加载成功")


def test_retrieval_accuracy():
    """测试检索准确性"""
    kb = get_knowledge_base()
    
    # 加载测试用例
    test_file = Path(__file__).parent / "test_data" / "retrieval_test_cases.json"
    with open(test_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    
    print("\n=== 检索准确性测试 ===")
    passed = 0
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected_ids = case["expected_ids"]
        expected_keywords = case["expected_keywords"]
        
        # 执行检索
        docs = kb.search(query, k=3)
        retrieved_ids = [doc.metadata["id"] for doc in docs]
        retrieved_text = " ".join([doc.page_content for doc in docs])
        
        # 检查是否包含期望ID
        id_match = any(eid in retrieved_ids for eid in expected_ids)
        
        # 检查是否包含期望关键词
        keyword_match = all(kw in retrieved_text for kw in expected_keywords)
        
        if id_match and keyword_match:
            print(f"[{i}] ✅ {query}")
            passed += 1
        else:
            print(f"[{i}] ❌ {query}")
            print(f"   期望ID: {expected_ids}, 实际: {retrieved_ids}")
            print(f"   关键词匹配: {keyword_match}")
    
    print(f"\n通过率: {passed}/{len(test_cases)}")
    assert passed >= len(test_cases) * 0.8, f"检索准确率过低: {passed}/{len(test_cases)}"


def test_filter_by_type():
    """测试按类型过滤检索"""
    kb = get_knowledge_base()
    
    # 测试租金类型过滤
    docs = kb.search("商铺租金", k=3, filter_type="rent")
    assert len(docs) > 0
    assert all(doc.metadata["type"] == "rent" for doc in docs)
    print("✅ 租金类型过滤正常")
    
    # 测试竞品类型过滤
    docs = kb.search("购物中心", k=3, filter_type="competitor")
    assert len(docs) > 0
    assert all(doc.metadata["type"] == "competitor" for doc in docs)
    print("✅ 竞品类型过滤正常")
    
    # 测试贷款类型过滤
    docs = kb.search("贷款利率", k=3, filter_type="loan")
    assert len(docs) > 0
    assert all(doc.metadata["type"] == "loan" for doc in docs)
    print("✅ 贷款类型过滤正常")


def test_search_with_scores():
    """测试带分数的检索"""
    kb = get_knowledge_base()
    
    results = kb.search_with_scores("陆家嘴商铺", k=3)
    assert len(results) > 0
    
    print("\n=== 带分数检索测试 ===")
    for doc, score in results:
        print(f"ID: {doc.metadata['id']}, 相似度分数: {score:.4f}")
        assert score >= 0, "相似度分数应非负"
    
    print("✅ 带分数检索正常")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
