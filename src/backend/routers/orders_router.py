from typing import Any

from fastapi import APIRouter, HTTPException

from configs.logger import LOGGER
from schemas.cosmos import CosmosQuerySchema
from services.cosmos_db_service import query_orders_container

orders_router = APIRouter()


@orders_router.post(
    "/query",
    summary="Execute a query to get orders."
)
async def get_orders_by_query(query: CosmosQuerySchema) -> Any:
    LOGGER.debug("Fetching all suppliers information")
    try:
        print(query.query)
        return await query_orders_container(query.query)
    except Exception as e:
        LOGGER.error("Error fetching suppliers information: {e}")
        raise HTTPException(status_code=404, detail="Orders information not found")
