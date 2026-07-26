"""前端端到端测试"""
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from app.main import app


def test_frontend_page_loads():
    """测试前端页面能否正常加载"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "金融多Agent智能投顾系统" in response.text
    assert "text/html" in response.headers["content-type"]


def test_sse_stream_endpoint():
    """测试SSE流式接口"""
    client = TestClient(app)
    
    # 发送请求
    response = client.post(
        "/api/invest/stream",
        json={"query": "我想投资商铺"},
        headers={"Accept": "text/event-stream"}
    )
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    # 解析SSE事件
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            events.append(data)
    
    # 验证事件序列
    event_types = [e["type"] for e in events]
    
    # 必须包含这些关键事件
    assert "intent_start" in event_types
    assert "intent_complete" in event_types
    assert "dag_start" in event_types
    assert "dag_complete" in event_types
    assert "agents_start" in event_types
    assert "agents_complete" in event_types
    assert "reflection_start" in event_types
    assert "reflection_complete" in event_types
    assert "report_start" in event_types
    assert "report_complete" in event_types
    assert "complete" in event_types
    
    # 验证最终事件包含报告
    final_event = events[-1]
    assert final_event["type"] == "complete"
    assert "report" in final_event["data"]
    assert len(final_event["data"]["report"]) > 0
    
    print(f"✓ SSE流式测试通过，共收到 {len(events)} 个事件")
    print(f"  事件序列: {' → '.join(event_types)}")


def test_sse_event_data_structure():
    """测试SSE事件数据结构"""
    client = TestClient(app)
    
    response = client.post(
        "/api/invest/stream",
        json={"query": "分析租金回报"},
        headers={"Accept": "text/event-stream"}
    )
    
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            events.append(data)
    
    # 验证每个事件都有 type 和 data 字段
    for event in events:
        assert "type" in event
        assert "data" in event
    
    # 验证意图识别事件包含结果
    intent_complete = next(e for e in events if e["type"] == "intent_complete")
    assert "result" in intent_complete["data"]
    assert "elapsed" in intent_complete["data"]
    
    # 验证DAG规划事件包含计划
    dag_complete = next(e for e in events if e["type"] == "dag_complete")
    assert "plan" in dag_complete["data"]
    assert "valid" in dag_complete["data"]["plan"]
    
    # 验证Agent执行事件
    agents_complete = next(e for e in events if e["type"] == "agents_complete")
    assert "count" in agents_complete["data"]
    assert "elapsed" in agents_complete["data"]
    
    # 验证反思评估事件
    reflection_complete = next(e for e in events if e["type"] == "reflection_complete")
    assert "score" in reflection_complete["data"]
    assert "elapsed" in reflection_complete["data"]
    
    # 验证报告生成事件
    report_complete = next(e for e in events if e["type"] == "report_complete")
    assert "length" in report_complete["data"]
    assert "elapsed" in report_complete["data"]
    
    print("✓ SSE事件数据结构验证通过")


def test_cors_headers():
    """测试CORS跨域配置"""
    client = TestClient(app)
    
    response = client.options(
        "/api/invest/stream",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        }
    )
    
    # 验证CORS头
    assert "access-control-allow-origin" in response.headers
    # FastAPI CORS中间件在allow_credentials=True时返回具体Origin而非*
    assert response.headers["access-control-allow-origin"] in ("*", "http://localhost:3000")
    
    print("✓ CORS跨域配置验证通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
