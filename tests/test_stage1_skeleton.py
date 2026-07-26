"""阶段1测试：项目骨架 + 配置 + LLM连通"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.config import settings


def test_config_load():
    """测试配置加载"""
    assert settings.siliconflow_api_key == "sk-parugppfathywsonjavnfqfkyydrsxekawheegvffygzxmss"
    assert settings.siliconflow_base_url == "https://api.siliconflow.cn/v1"
    assert settings.llm_model == "Qwen/Qwen2.5-7B-Instruct"
    assert settings.embedding_model == "BAAI/bge-large-zh-v1.5"
    print("✅ 配置加载正常")


def test_llm_connectivity():
    """测试LLM连通性"""
    from app.utils.llm_client import get_llm
    llm = get_llm(temperature=0.1)
    response = llm.invoke("你好，请用一句话介绍自己")
    assert response.content is not None
    assert len(response.content) > 0
    print(f"✅ LLM连通正常，回复: {response.content}")


def test_embedding_connectivity():
    """测试Embedding连通性"""
    from app.utils.llm_client import get_embeddings
    embeddings = get_embeddings()
    result = embeddings.embed_query("测试向量化")
    assert result is not None
    assert len(result) > 0
    print(f"✅ Embedding连通正常，向量维度: {len(result)}")


def test_fastapi_app():
    """测试FastAPI应用"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # 健康检查
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✅ 健康检查接口正常")
    
    # 投顾接口
    response = client.post("/api/invest", json={"query": "我想投资商铺"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["report"]) > 50  # 报告长度>50字符即可
    print("✅ 投顾接口正常")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
