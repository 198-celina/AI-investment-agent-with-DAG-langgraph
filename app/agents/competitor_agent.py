"""竞品对比Agent"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.utils.llm_client import get_llm
from app.rag.knowledge_base import get_knowledge_base


class CompetitorAgent:
    """竞品对比Agent - 分析商圈竞品项目"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.kb = get_knowledge_base()
        self.prompt = self._build_prompt()
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """构建竞品分析Prompt"""
        template = """你是一个专业的商业地产竞品分析师。请基于以下知识库数据，为用户提供竞品对比分析。

用户问题：{query}

相关竞品数据：
{context}

请提供以下分析：
1. 目标商圈的主要竞品项目列表
2. 各竞品的定位、价格、入住率对比
3. 各竞品的优劣势分析
4. 市场竞争格局评估
5. 投资建议（差异化定位策略）

请用专业但易懂的语言回答，包含具体数据支撑。
"""
        return ChatPromptTemplate.from_template(template)
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行竞品分析
        
        Args:
            context: 执行上下文，包含 user_query 等
        
        Returns:
            分析结果字典
        """
        import asyncio
        query = context.get("user_query", "")
        
        # RAG检索竞品相关数据（FAISS不支持async，放到线程池执行）
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, lambda: self.kb.search(query, k=3, filter_type="competitor"))
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # LLM分析
        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "query": query,
            "context": context_text
        })
        
        return {
            "agent_name": "competitor_agent",
            "analysis": response.content,
            "data": {
                "retrieved_docs": len(docs),
                "sources": [doc.metadata.get("id") for doc in docs]
            },
            "confidence": 0.85
        }


# 全局实例
_competitor_agent = None

def get_competitor_agent() -> CompetitorAgent:
    """获取竞品Agent单例"""
    global _competitor_agent
    if _competitor_agent is None:
        _competitor_agent = CompetitorAgent()
    return _competitor_agent
