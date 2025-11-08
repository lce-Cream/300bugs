from typing import List

import requests

from configs.config import N8N_CONFIG
from schemas.shopify import ShopifySchema


def get_shopify_data() -> List[ShopifySchema]:
    response = requests.post(N8N_CONFIG.url)
    response.raise_for_status()
    data = response.json()
    return [ShopifySchema(**product) for product in data]
