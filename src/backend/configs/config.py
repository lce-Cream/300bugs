import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class AppConfig(BaseModel):
    log_level: str = os.getenv('APP_LOG_LEVEL', 'INFO')


class AzureOpenAIConfig(BaseModel):
    api_key: str = os.getenv('AZURE_OPENAI_API_KEY', '')
    endpoint: str = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    deployment_name: str = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4.1-turbo')
    api_version: str = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')


class MCPConfig(BaseModel):
    url: str = os.getenv('MCP_B8N_URL')


class N8NConfig(BaseModel):
    url: str = os.getenv('N8N_URL')

APP_CONFIG = AppConfig()
AZURE_OPENAI_CONFIG = AzureOpenAIConfig()
MCP_CONFIG = MCPConfig()
N8N_CONFIG = N8NConfig()
