"""Redis Context 管理器 - 完整会话上下文管理（海量数据）"""
import json
from typing import Any, Optional
from redis import Redis
from app.config import settings


class ContextManager:
    """Redis Context 管理器
    
    职责：
    - 存储完整对话历史、工具返回、中间Agent输出
    - 支持 JSONPath 精准读取指定字段
    - 支持 Checkpoint 快照（DAG节点执行完成后自动保存）
    - 所有 Agent 通过 session_id 统一读写同一份上下文
    """
    
    def __init__(self):
        """初始化 Redis 连接"""
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def get_context_key(self, session_id: str) -> str:
        """获取 Context 的 Redis key"""
        return f"context:{session_id}"
    
    def get_checkpoint_key(self, session_id: str, node_id: str) -> str:
        """获取 Checkpoint 的 Redis key"""
        return f"checkpoint:{session_id}:{node_id}"
    
    def save_context(self, session_id: str, data: dict[str, Any]) -> None:
        """保存完整上下文到 Redis
        
        Args:
            session_id: 会话ID
            data: 完整上下文数据
        """
        key = self.get_context_key(session_id)
        self.redis_client.set(key, json.dumps(data, ensure_ascii=False))
    
    def load_context(self, session_id: str) -> dict[str, Any]:
        """从 Redis 加载完整上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            完整上下文数据
        """
        key = self.get_context_key(session_id)
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return {}
    
    def update_context(self, session_id: str, updates: dict[str, Any]) -> None:
        """更新上下文的部分字段
        
        Args:
            session_id: 会话ID
            updates: 需要更新的字段
        """
        context = self.load_context(session_id)
        context.update(updates)
        self.save_context(session_id, context)
    
    def save_checkpoint(self, session_id: str, node_id: str, context: dict[str, Any]) -> None:
        """保存 Checkpoint 快照
        
        Args:
            session_id: 会话ID
            node_id: 节点ID
            context: 当前完整上下文
        """
        key = self.get_checkpoint_key(session_id, node_id)
        self.redis_client.set(key, json.dumps(context, ensure_ascii=False))
    
    def load_checkpoint(self, session_id: str, node_id: str) -> Optional[dict[str, Any]]:
        """加载 Checkpoint 快照（用于故障回滚）
        
        Args:
            session_id: 会话ID
            node_id: 节点ID
            
        Returns:
            Checkpoint 数据，不存在则返回 None
        """
        key = self.get_checkpoint_key(session_id, node_id)
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def delete_context(self, session_id: str) -> None:
        """删除会话上下文（清理）"""
        key = self.get_context_key(session_id)
        self.redis_client.delete(key)
    
    def exists(self, session_id: str) -> bool:
        """检查会话上下文是否存在"""
        key = self.get_context_key(session_id)
        return self.redis_client.exists(key) > 0


# 全局 ContextManager 实例
_context_manager = None


def get_context_manager() -> ContextManager:
    """获取 ContextManager 单例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
