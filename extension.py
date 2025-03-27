from rich.console import Console
from config import AppConfig, ApiKeyConfig, PromptConfig
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

console = Console()

qwen_client = OpenAI(
    api_key=ApiKeyConfig.QWEN_API_KEY,
    base_url=ApiKeyConfig.QWEN_BASE_URL
)

zhipu_client = OpenAI(
    api_key=ApiKeyConfig.ZHIPU_API_KEY,
    base_url=ApiKeyConfig.ZHIPU_BASE_URL 
)