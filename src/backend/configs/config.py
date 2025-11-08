import os
import ast
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel
import json
import re

load_dotenv()


class AppConfig(BaseModel):
    log_level: str = os.getenv('APP_LOG_LEVEL', 'INFO')


class AzureOpenAIConfig(BaseModel):
    api_key: str = os.getenv('AZURE_OPENAI_API_KEY', '')
    endpoint: str = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    deployment_name: str = os.getenv(
        'AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4.1-nano')
    api_version: str = os.getenv(
        'AZURE_OPENAI_API_VERSION', '2024-12-01-preview')


class MCPConfig(BaseModel):
    url: str = os.getenv('MCP_B8N_URL', '')


class N8NConfig(BaseModel):
    url: List[str] = ast.literal_eval(os.getenv('N8N_URL', '[]'))


class ShopifyStoresConfig(BaseModel):
    # maps shop domain -> admin access token
    stores: dict[str, str] = {}


def _load_shopify_stores() -> ShopifyStoresConfig:
    raw = os.getenv("SHOPIFY_STORES", "").strip()
    stores: dict[str, str] = {}

    if raw:
        # Prefer JSON map: {"shop.myshopify.com": "shpat_xxx", ...}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                stores.update({k: v for k, v in parsed.items()
                              if isinstance(k, str) and isinstance(v, str)})
        except Exception:
            # Fallback simple formats: "shop:token,shop2:token2" or "shop=token,shop2=token2"
            for pair in re.split(r'\s*,\s*', raw):
                if not pair:
                    continue
                if ':' in pair:
                    k, v = pair.split(':', 1)
                elif '=' in pair:
                    k, v = pair.split('=', 1)
                else:
                    continue
                stores[k.strip()] = v.strip()

    # Legacy single-store env compatibility
    single_shop = os.getenv("SHOPIFY_STORE", "").strip()
    single_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "").strip()
    if single_shop and single_token:
        # normalize domain (strip protocol/trailing slash) similar to existing logic
        s = single_shop
        if s.startswith("http://"):
            s = s[len("http://"):]
        elif s.startswith("https://"):
            s = s[len("https://"):]
        s = s.rstrip("/")
        if "." not in s:
            s = f"{s}.myshopify.com"
        stores.setdefault(s, single_token)

    return ShopifyStoresConfig(stores=stores)


SHOPIFY_STORES_CONFIG = _load_shopify_stores()
# plain dict for easy use elsewhere
SHOPIFY_STORES = SHOPIFY_STORES_CONFIG.stores

APP_CONFIG = AppConfig()
AZURE_OPENAI_CONFIG = AzureOpenAIConfig()
MCP_CONFIG = MCPConfig()
N8N_CONFIG = N8NConfig()
