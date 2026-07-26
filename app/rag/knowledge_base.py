"""知识库管理模块"""
from pathlib import Path
from langchain_community.vectorstores import FAISS
from app.config import settings
from app.rag.embeddings import get_embedding_function


class KnowledgeBase:
    """知识库管理类"""
    
    def __init__(self):
        self.vectorstore = None
        self._load_vectorstore()
    
    def _load_vectorstore(self):
        """加载向量库"""
        vectorstore_path = Path(settings.vectorstore_path)
        if not vectorstore_path.exists():
            raise FileNotFoundError(
                f"向量库不存在: {vectorstore_path}\n"
                "请先运行: python scripts/build_vectorstore.py"
            )
        
        embeddings = get_embedding_function()
        self.vectorstore = FAISS.load_local(
            str(vectorstore_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
    
    def search(self, query: str, k: int = 3, filter_type: str = None) -> list:
        """检索知识库
        
        Args:
            query: 查询语句
            k: 返回结果数量
            filter_type: 过滤类型（rent/competitor/loan）
        
        Returns:
            检索到的文档列表
        """
        if filter_type:
            # 使用元数据过滤
            filter_dict = {"type": filter_type}
            docs = self.vectorstore.similarity_search(
                query, 
                k=k,
                filter=filter_dict
            )
        else:
            docs = self.vectorstore.similarity_search(query, k=k)
        
        return docs
    
    def search_with_scores(self, query: str, k: int = 3) -> list:
        """带相似度分数的检索"""
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        return docs_and_scores


# 全局知识库实例（延迟加载）
_kb_instance = None

def get_knowledge_base() -> KnowledgeBase:
    """获取知识库单例"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
