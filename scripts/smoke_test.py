#!/usr/bin/env python3
"""
冒烟测试脚本
用于 CI/CD 流水线中的自动化接口验证
"""
import sys
import time
import argparse
import requests
from typing import Optional


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """等待服务就绪"""
    print(f"等待服务就绪: {url}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("✓ 服务已就绪")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    
    print("✗ 服务启动超时")
    return False


def test_health_check(url: str) -> bool:
    """测试健康检查接口"""
    print("\n[1/4] 测试健康检查接口...")
    try:
        response = requests.get(f"{url}/health", timeout=10)
        assert response.status_code == 200, f"状态码错误: {response.status_code}"
        data = response.json()
        assert data["status"] == "ok", f"状态异常: {data}"
        print("✓ 健康检查通过")
        return True
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False


def test_frontend_page(url: str) -> bool:
    """测试前端页面加载"""
    print("\n[2/4] 测试前端页面加载...")
    try:
        response = requests.get(f"{url}/", timeout=10)
        assert response.status_code == 200, f"状态码错误: {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "非 HTML 响应"
        assert "金融多Agent智能投顾系统" in response.text, "页面标题缺失"
        print("✓ 前端页面加载成功")
        return True
    except Exception as e:
        print(f"✗ 前端页面加载失败: {e}")
        return False


def test_invest_api(url: str) -> bool:
    """测试投顾分析接口（验证接口可响应，不要求完整分析结果）"""
    print("\n[3/4] 测试投顾分析接口...")
    try:
        response = requests.post(
            f"{url}/api/invest",
            json={"query": "我想投资商铺"},
            timeout=120
        )
        assert response.status_code == 200, f"状态码错误: {response.status_code}"
        data = response.json()
        assert "status" in data, "响应缺少 status 字段"
        assert "report" in data, "响应缺少 report 字段"
        # 注：没有向量库时 status 可能为 error，这是预期行为
        if data["status"] == "success":
            print(f"✓ 投顾分析接口通过 (报告长度: {len(data['report'])} 字符)")
        else:
            print(f"✓ 投顾分析接口可响应 (status={data['status']}, 无向量库时返回 error 属正常)")
        return True
    except Exception as e:
        print(f"✗ 投顾分析接口失败: {e}")
        return False


def test_sse_stream(url: str) -> bool:
    """测试 SSE 流式接口"""
    print("\n[4/4] 测试 SSE 流式接口...")
    try:
        response = requests.post(
            f"{url}/api/invest/stream",
            json={"query": "分析租金回报"},
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=120
        )
        assert response.status_code == 200, f"状态码错误: {response.status_code}"
        assert "text/event-stream" in response.headers.get("content-type", ""), "非 SSE 响应"
        
        event_count = 0
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                event_count += 1
        
        assert event_count > 0, "未收到任何事件"
        print(f"✓ SSE 流式接口通过 (收到 {event_count} 个事件)")
        return True
    except Exception as e:
        print(f"✗ SSE 流式接口失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="冒烟测试脚本")
    parser.add_argument("--url", required=True, help="服务地址，如 http://localhost:8000")
    parser.add_argument("--timeout", type=int, default=60, help="等待服务就绪超时时间（秒）")
    args = parser.parse_args()
    
    print("=" * 60)
    print("冒烟测试开始")
    print("=" * 60)
    
    # 等待服务就绪
    if not wait_for_service(args.url, args.timeout):
        sys.exit(1)
    
    # 执行测试
    results = []
    results.append(test_health_check(args.url))
    results.append(test_frontend_page(args.url))
    results.append(test_invest_api(args.url))
    results.append(test_sse_stream(args.url))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("冒烟测试结果")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
