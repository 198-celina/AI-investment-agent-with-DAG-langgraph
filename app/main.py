"""FastAPI入口"""
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import InvestRequest, InvestResponse, HealthResponse
from app.workflow import run_investment_workflow, run_investment_workflow_with_events
import os

app = FastAPI(title="金融多Agent智能投顾系统", version="1.0.0")

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 前端目录
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(status="ok")


@app.get("/")
async def serve_frontend():
    """提供前端页面"""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.post("/api/invest")
async def invest_analysis(request: InvestRequest):
    """投顾分析接口（同步版本，保留兼容性）"""
    try:
        result = await run_investment_workflow(request.query)
        
        return InvestResponse(
            status=result.get("status", "success"),
            report=result.get("report", ""),
            agent_results=result.get("agent_results", {}),
            iterations=result.get("iterations", 0),
            reflection_score=result.get("reflection_score", 0.0),
        )
    except Exception as e:
        return InvestResponse(
            status="error",
            report=f"分析过程中发生错误：{str(e)}",
            agent_results={},
            iterations=0,
            reflection_score=0.0,
        )


@app.post("/api/invest/stream")
async def invest_stream(request: InvestRequest):
    """投顾分析接口（SSE流式版本）"""
    async def event_generator():
        try:
            async for event in run_investment_workflow_with_events(request.query):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "data": {"message": str(e)}
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
