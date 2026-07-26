"""租金测算Agent"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.utils.llm_client import get_llm
from app.rag.knowledge_base import get_knowledge_base


class RentAgent:
    """租金测算Agent - 分析租金回报率、空置率等"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.kb = get_knowledge_base()
        self.prompt = self._build_prompt()
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """构建租金分析Prompt"""
        template = """你是一个专业的商业地产租金测算分析师。请基于以下知识库数据，为用户提供租金测算分析。

用户问题：{query}

相关租金数据：
{context}

请提供以下分析：
1. 目标区域/商圈的租金水平（月租金范围、每平米租金）
2. 投资回报率分析
3. 空置率风险评估
4. 适合的业态建议
5. 租金收益测算（如有具体投资金额）

请用专业但易懂的语言回答，包含具体数据支撑。
"""
        return ChatPromptTemplate.from_template(template)
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行租金分析
        
        Args:
            context: 执行上下文，包含 user_query 等
        
        Returns:
            分析结果字典
        """
        import asyncio
        query = context.get("user_query", "")
        
        # RAG检索租金相关数据（FAISS不支持async，放到线程池执行）
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, lambda: self.kb.search(query, k=3, filter_type="rent"))
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # LLM分析
        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "query": query,
            "context": context_text
        })
        
        return {
            "agent_name": "rent_agent",
            "analysis": response.content,
            "data": {
                "retrieved_docs": len(docs),
                "sources": [doc.metadata.get("id") for doc in docs]
            },
            "confidence": 0.85
        }


# 全局实例
_rent_agent = None

def get_rent_agent() -> RentAgent:
    """获取租金Agent单例"""
    global _rent_agent
    if _rent_agent is None:
        _rent_agent = RentAgent()
    return _rent_agent
