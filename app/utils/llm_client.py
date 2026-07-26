"""LLM客户端工具"""
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.config import settings


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """获取LLM实例"""
    return ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.siliconflow_api_key,
        openai_api_base=settings.siliconflow_base_url,
        temperature=temperature,
    )


def get_embeddings() -> OpenAIEmbeddings:
    """获取Embedding实例"""
    # 绕过代理，避免tiktoken下载编码文件时SSL错误
    os.environ['NO_PROXY'] = 'openaipublic.blob.core.windows.net'
    os.environ['no_proxy'] = 'openaipublic.blob.core.windows.net'
    
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.siliconflow_api_key,
        openai_api_base=settings.siliconflow_base_url,
        check_embedding_ctx_length=False,  # 禁用tiktoken长度检查
    )
