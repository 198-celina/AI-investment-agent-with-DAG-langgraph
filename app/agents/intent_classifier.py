"""意图识别模块"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.utils.llm_client import get_llm


class IntentClassifier:
    """意图识别器"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.1)
        self.prompt = self._build_prompt()
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """构建意图识别Prompt"""
        template = """分析用户投资咨询问题，判断需要哪些分析维度。

维度定义：
- rent_analysis: 租金、回报率、空置率相关
- competitor_analysis: 竞品、商圈对比、项目对比相关  
- loan_policy: 贷款、首付、利率、银行相关

输出格式：{{"rent_analysis": true/false, "competitor_analysis": true/false, "loan_policy": true/false}}

用户问题：{query}

只输出JSON："""
        return ChatPromptTemplate.from_template(template)
    
    def classify(self, query: str) -> Dict[str, Any]:
        """识别用户意图
        
        Args:
            query: 用户问题
        
        Returns:
            意图识别结果字典
        """
        chain = self.prompt | self.llm
        response = chain.invoke({"query": query})
        
        # 解析JSON响应
        import json
        import re
        
        content = response.content.strip()
        
        # 尝试从markdown代码块中提取JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # 尝试直接解析
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # 尝试修复常见的JSON格式问题
            try:
                # 修复：双冒号 :: 改为单冒号 :
                fixed_content = re.sub(r'::', ':', content)
                # 修复：在 true/false 后面如果没有逗号，添加逗号
                fixed_content = re.sub(r'(true|false)\s*(?=\s*")', r'\1, ', fixed_content)
                # 修复：去除多余冒号如 ":true" 前面的冒号
                fixed_content = re.sub(r'":\s*(true|false)', r'": \1', fixed_content)
                result = json.loads(fixed_content)
                return result
            except json.JSONDecodeError:
                # 最后尝试：用正则表达式直接提取键值对
                try:
                    result = {
                        "rent_analysis": bool(re.search(r'"rent_analysis":\s*:?\s*true', content, re.IGNORECASE)),
                        "competitor_analysis": bool(re.search(r'"competitor_analysis":\s*:?\s*true', content, re.IGNORECASE)),
                        "loan_policy": bool(re.search(r'"loan_policy":\s*:?\s*true', content, re.IGNORECASE))
                    }
                    return result
                except Exception:
                    # 如果仍然失败，返回默认值
                    return {
                        "rent_analysis": False,
                        "competitor_analysis": False,
                        "loan_policy": False
                    }


# 全局实例
_intent_classifier = None

def get_intent_classifier() -> IntentClassifier:
    """获取意图识别器单例"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
