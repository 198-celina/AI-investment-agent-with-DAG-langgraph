"""配置管理模块"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 硅基流动API配置
    siliconflow_api_key: str = Field(alias="SILICONFLOW_API_KEY")
    siliconflow_base_url: str = Field(default="https://api.siliconflow.cn/v1", alias="SILICONFLOW_BASE_URL")
    
    # 模型配置
    llm_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", alias="LLM_MODEL")
    embedding_model: str = Field(default="BAAI/bge-large-zh-v1.5", alias="EMBEDDING_MODEL")
    
    # 服务配置
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # 向量库配置
    vectorstore_path: str = Field(default="./vectorstore/faiss_index", alias="VECTORSTORE_PATH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
