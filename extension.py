from rich.console import Console
from config import AppConfig, ApiKeyConfig, PromptConfig
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from algo.search import initialize_case_retrieval_system

db = SQLAlchemy()

console = Console()

# ===== 配置参数 =====
EMBEDDING_FILE = "E:\Desktop\LawAI\LawAI-algoend\搜索\案例搜索\case_embeddings.npy"
METADATA_FILE = "E:\Desktop\LawAI\LawAI-algoend\搜索\案例搜索\案例库数据全（清洗后）.json"
MODEL_NAME = "E:\\Desktop\\LawAI\\LawAI-algoend\\multilingual-e5-large-instruct"
model, embeddings, metadata = initialize_case_retrieval_system(EMBEDDING_FILE, METADATA_FILE, MODEL_NAME)

qwen_client = OpenAI(
    api_key=ApiKeyConfig.QWEN_API_KEY,
    base_url=ApiKeyConfig.QWEN_BASE_URL
)

zhipu_client = OpenAI(
    api_key=ApiKeyConfig.ZHIPU_API_KEY,
    base_url=ApiKeyConfig.ZHIPU_BASE_URL 
)