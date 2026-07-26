"""异常处理测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_empty_query():
    """测试空查询"""
    client = TestClient(app)
    response = client.post("/api/invest", json={"query": ""})
    
    print(f"空查询响应: {response.status_code}")
    # 应该返回400错误或正常处理
    assert response.status_code in [400, 422, 200]


def test_special_characters():
    """测试特殊字符输入"""
    client = TestClient(app)
    query = "<script>alert('xss')</script>"
    response = client.post("/api/invest", json={"query": query})
    
    print(f"特殊字符响应: {response.status_code}")
    # 应该正常处理，不应有XSS
    assert response.status_code == 200
    data = response.json()
    assert "<script>" not in data.get("report", "")


def test_very_long_query():
    """测试超长查询"""
    client = TestClient(app)
    query = "我想投资商铺" * 1000  # 10000字符
    response = client.post("/api/invest", json={"query": query})
    
    print(f"超长查询响应: {response.status_code}, 报告长度: {len(response.json().get('report', ''))}")
    # 应该正常处理或返回413
    assert response.status_code in [200, 413]


def test_invalid_json():
    """测试无效JSON"""
    client = TestClient(app)
    # 发送无效JSON
    response = client.post(
        "/api/invest",
        content='{"query": invalid}',
        headers={"Content-Type": "application/json"}
    )
    
    print(f"无效JSON响应: {response.status_code}")
    # 应该返回400或422
    assert response.status_code in [400, 422]


def test_missing_query_field():
    """测试缺少query字段"""
    client = TestClient(app)
    response = client.post("/api/invest", json={})
    
    print(f"缺少字段响应: {response.status_code}")
    # 应该返回422
    assert response.status_code == 422


def test_health_check():
    """测试健康检查接口"""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print(f"健康检查: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
