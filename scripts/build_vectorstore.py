"""向量化入库脚本：将样本数据转换为向量并存入FAISS"""
import sys
import os
# 解决OpenMP库冲突问题
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from app.utils.llm_client import get_embeddings
from app.config import settings


def load_data():
    """加载所有样本数据"""
    data_dir = Path(__file__).parent.parent / "data"
    all_docs = []
    
    # 加载租金数据
    with open(data_dir / "rent_data.json", "r", encoding="utf-8") as f:
        rent_data = json.load(f)
        for item in rent_data:
            text = f"{item['description']} 区域：{item['area']}，位置：{item['location']}，类型：{item['property_type']}，月租金：{item['monthly_rent_range']}，回报率：{item['annual_return_rate']}，空置率：{item['vacancy_rate']}"
            all_docs.append(Document(
                page_content=text,
                metadata={"id": item["id"], "type": "rent", **item}
            ))
    
    # 加载竞品数据
    with open(data_dir / "competitor_data.json", "r", encoding="utf-8") as f:
        comp_data = json.load(f)
        for item in comp_data:
            text = f"{item['description']} 商圈：{item['business_district']}，项目：{item['project_name']}，类型：{item['property_type']}，均价：{item['avg_price']}，入住率：{item['occupancy_rate']}，优势：{item['advantages']}，劣势：{item['disadvantages']}"
            all_docs.append(Document(
                page_content=text,
                metadata={"id": item["id"], "type": "competitor", **item}
            ))
    
    # 加载贷款政策数据
    with open(data_dir / "loan_policy_data.json", "r", encoding="utf-8") as f:
        loan_data = json.load(f)
        for item in loan_data:
            text = f"{item['description']} 银行：{item['bank_name']}，类型：{item['loan_type']}，利率：{item['interest_rate']}，首付：{item['down_payment_ratio']}，期限：{item['max_loan_term']}，条件：{item['approval_conditions']}"
            all_docs.append(Document(
                page_content=text,
                metadata={"id": item["id"], "type": "loan", **item}
            ))
    
    print(f"加载了 {len(all_docs)} 条文档")
    return all_docs


def build_vectorstore(docs):
    """构建向量库"""
    print("开始向量化...")
    embeddings = get_embeddings()
    
    # 创建FAISS向量库
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    # 持久化保存
    output_path = Path(settings.vectorstore_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    vectorstore.save_local(str(output_path))
    print(f"向量库已保存到: {output_path}")
    
    return vectorstore


def test_retrieval(vectorstore):
    """测试检索效果"""
    test_queries = [
        "陆家嘴商铺租金多少",
        "工商银行商业贷款政策",
        "正大广场竞品分析",
        "张江科技园商铺投资",
    ]
    
    print("\n=== 检索测试 ===")
    for query in test_queries:
        print(f"\n查询: {query}")
        docs = vectorstore.similarity_search(query, k=2)
        for i, doc in enumerate(docs, 1):
            print(f"  [{i}] {doc.metadata['id']} - {doc.page_content[:80]}...")


if __name__ == "__main__":
    docs = load_data()
    vectorstore = build_vectorstore(docs)
    test_retrieval(vectorstore)
    print("\n✅ 向量库构建完成")
