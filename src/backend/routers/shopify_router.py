from typing import List

from fastapi import APIRouter, HTTPException

from configs.logger import LOGGER
from schemas.shopify import ShopifySchema
from services.shopify_service import get_shopify_data

shopify_router = APIRouter()


@shopify_router.get(
    "/all",
    summary="Get all products from Shopify.",
    description="Get all products from Shopify.",
    response_model=List[ShopifySchema]
)
async def get_all_products_from_shopify() -> List[ShopifySchema]:
    """
    Get all products from Shopify.

    Returns:
        List[ShopifySchema]: All products data from Shopify.
    """
    LOGGER.debug("Fetching all products from Shopify")
    try:
        return get_shopify_data()
    except Exception as e:
        LOGGER.error(f"Error fetching products from Shopify: {e}")
        raise HTTPException(status_code=404, detail=f"Products not found: {e}")