"""Embedding向量化模块"""
from app.utils.llm_client import get_embeddings


def get_embedding_function():
    """获取Embedding函数"""
    return get_embeddings()
