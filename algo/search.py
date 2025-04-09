import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ===== 初始化函数 =====
def initialize_case_retrieval_system(embedding_file, metadata_file, model_name):
    """
    初始化案例检索系统，加载预计算数据和模型。
    
    参数:
        embedding_file (str): 预计算的案例嵌入向量文件路径。
        metadata_file (str): 案例库元数据文件路径。
        model_name (str): 使用的模型名称或路径。
    
    返回:
        tuple: (model, embeddings, metadata)
    """
    print("正在加载案例数据库...")
    embeddings = np.load(embedding_file)
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # 初始化模型
    model = SentenceTransformer(model_name, device="cpu")  # 使用CPU推理
    print("案例检索系统初始化完成。")
    return model, embeddings, metadata

# ===== 文本预处理函数 =====
def preprocess_text(text):
    """
    预处理文本，与生成embedding时相同的预处理。
    
    参数:
        text (str): 输入文本。
    
    返回:
        str: 预处理后的文本。
    """
    return text.replace("\n", " ").replace("  ", " ").strip()

# ===== 相似案例检索函数 =====
def find_similar_cases(model, embeddings, metadata, query, top_k):
    """
    检索与查询文本最相似的案例。
    
    参数:
        model (SentenceTransformer): 用于生成文本嵌入的模型。
        embeddings (numpy.ndarray): 预计算的案例嵌入向量。
        metadata (list): 案例库元数据。
        query (str): 查询文本。
        top_k (int): 返回的最相似案例数量。
    
    返回:
        list: [(案例索引, 相似度分数)]
    """
    # 预处理查询文本
    processed_query = preprocess_text(query)
    
    # 生成查询embedding
    query_embedding = model.encode(
        processed_query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # 计算相似度
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    # 获取Top K结果
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    return [(i, similarities[i]) for i in top_indices]

# ===== 搜索函数 =====
def search(query, model, embeddings, metadata, top_k):
    """
    执行案例搜索并展示结果。
    
    参数:
        query (str): 查询文本。
        model (SentenceTransformer): 用于生成文本嵌入的模型。
        embeddings (numpy.ndarray): 预计算的案例嵌入向量。
        metadata (list): 案例库元数据。
        top_k (int): 返回的最相似案例数量。
    
    返回:
        None
    """
    # 执行检索
    results = find_similar_cases(model, embeddings, metadata, query, top_k)
    
    # 展示结果
    print(f"\n找到 {len(results)} 个相似案例：")
    for rank, (idx, score) in enumerate(results, 1):
        case_info = metadata[idx]
        print(f"\n▌ 相似度排名 {rank} （相似度：{score:.4f}）")
        print(f"案例标题：{case_info['案例']}")
        print(f"核心关键词：{', '.join(case_info['关键词'])}")
        print(f"裁判要旨：{case_info['基本案情']}")
