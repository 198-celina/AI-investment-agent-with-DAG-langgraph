"""贷款政策Agent"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.utils.llm_client import get_llm
from app.rag.knowledge_base import get_knowledge_base


class LoanPolicyAgent:
    """贷款政策Agent - 分析商业贷款政策"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.kb = get_knowledge_base()
        self.prompt = self._build_prompt()
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """构建贷款政策分析Prompt"""
        template = """你是一个专业的商业地产贷款政策分析师。请基于以下知识库数据，为用户提供贷款政策分析。

用户问题：{query}

相关贷款政策数据：
{context}

请提供以下分析：
1. 可选的银行贷款产品对比（利率、首付比例、期限）
2. 各银行的审批条件和要求
3. 贷款成本测算（如有具体投资金额）
4. 最优贷款方案推荐
5. 贷款风险提示

请用专业但易懂的语言回答，包含具体数据支撑。
"""
        return ChatPromptTemplate.from_template(template)
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行贷款政策分析
        
        Args:
            context: 执行上下文，包含 user_query 等
        
        Returns:
            分析结果字典
        """
        import asyncio
        query = context.get("user_query", "")
        
        # RAG检索贷款政策相关数据（FAISS不支持async，放到线程池执行）
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, lambda: self.kb.search(query, k=3, filter_type="loan"))
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # LLM分析
        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "query": query,
            "context": context_text
        })
        
        return {
            "agent_name": "loan_policy_agent",
            "analysis": response.content,
            "data": {
                "retrieved_docs": len(docs),
                "sources": [doc.metadata.get("id") for doc in docs]
            },
            "confidence": 0.85
        }


# 全局实例
_loan_policy_agent = None

def get_loan_policy_agent() -> LoanPolicyAgent:
    """获取贷款政策Agent单例"""
    global _loan_policy_agent
    if _loan_policy_agent is None:
        _loan_policy_agent = LoanPolicyAgent()
    return _loan_policy_agent
