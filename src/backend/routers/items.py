from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx
import asyncio
import difflib

from configs.config import SHOPIFY_STORES  # new

# Router for products
items_router = APIRouter(prefix="/products", tags=["products"])


async def _fetch_products_page(client: httpx.AsyncClient, shop: str, token: str, since_id: int | None):
    # Fetch one page of products (up to 250). Uses since_id pagination.
    url = f"https://{shop}/admin/api/2025-01/products.json"
    headers = {"X-Shopify-Access-Token": token, "Accept": "application/json"}
    params = {"limit": 250}
    if since_id:
        params["since_id"] = since_id

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            resp = await client.get(url, headers=headers, params=params, timeout=30.0)
            resp.raise_for_status()

            # If Shopify returns HTML (Cloudflare/admin verification page) we'll detect it and return helpful error
            content_type = resp.headers.get("content-type", "").lower()
            if "application/json" not in content_type:
                text_preview = (resp.text or "")[:1000]
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Unexpected non-JSON response from Shopify. This often indicates a Cloudflare or admin verification page "
                        "was returned instead of the API JSON (check that SHOPIFY_STORE is a shop domain like 'your-shop.myshopify.com' "
                        "and that SHOPIFY_ACCESS_TOKEN is a valid Admin API token). "
                        f"Response content-type: {content_type}. Response preview: {text_preview!s}"
                    ),
                )

            body = resp.json()
            return body.get("products", [])
        except httpx.HTTPStatusError as exc:
            # Non-2xx response from Shopify — surface the status and body
            # Try to show a short preview if body is not large
            preview = exc.response.text[:1000] if exc.response is not None else None
            raise HTTPException(status_code=exc.response.status_code if exc.response is not None else 502,
                                detail=f"Shopify returned HTTP {exc.response.status_code}. Response preview: {preview}")
        except httpx.RequestError as exc:
            # Network / DNS / connection issues — retry a few times then return 502
            if attempt < max_attempts:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                continue
            raise HTTPException(
                status_code=502, detail=f"Network error when connecting to Shopify: {str(exc)}"
            )
        except ValueError as exc:
            # JSON decoding error
            raise HTTPException(
                status_code=502, detail=f"Invalid JSON from Shopify: {str(exc)}"
            )


# New helper: resolve store name -> normalized shop domain and token (fallback to legacy env or first configured)
def _normalize_shop_domain(s: str) -> str:
    s = s.strip()
    if s.startswith("http://"):
        s = s[len("http://"):]
    elif s.startswith("https://"):
        s = s[len("https://"):]
    s = s.rstrip("/")
    if "." not in s:
        s = f"{s}.myshopify.com"
    return s


def _resolve_store(store_name: str | None) -> tuple[str, str]:
    """
    Return (shop_domain, token). Priority:
      1) explicit store_name matched to SHOPIFY_STORES keys (normalizes)
      2) if single-shop legacy env vars exist, use those
      3) first entry in SHOPIFY_STORES dict
    Raises HTTPException 400 if no store/token available.
    """
    # try explicit
    if store_name:
        candidate = _normalize_shop_domain(store_name)
        token = SHOPIFY_STORES.get(candidate)
        if token:
            return candidate, token
        # try raw provided value (some users may pass short key matching)
        token = SHOPIFY_STORES.get(store_name)
        if token:
            return _normalize_shop_domain(store_name), token
        raise HTTPException(
            status_code=400, detail=f"Store '{store_name}' not configured")

    # explicit not provided -> legacy env fallback
    single_shop = os.getenv("SHOPIFY_STORE", "").strip()
    single_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "").strip()
    if single_shop and single_token:
        return _normalize_shop_domain(single_shop), single_token

    # fallback to first configured store
    if SHOPIFY_STORES:
        # deterministic: take first item
        shop, token = next(iter(SHOPIFY_STORES.items()))
        return _normalize_shop_domain(shop), token

    raise HTTPException(
        status_code=500, detail="No Shopify stores configured (set SHOPIFY_STORES or legacy SHOPIFY_STORE/SHOPIFY_ACCESS_TOKEN)")


@items_router.get("/", summary="Retrieve all products from the configured Shopify stores")
async def list_products():
    """
    Retrieve products from all configured Shopify stores (SHOPIFY_STORES).
    Each returned product object will include a 'store' key with the shop domain.
    """
    shops = SHOPIFY_STORES.copy()
    # fallback to legacy single-store env if no SHOPIFY_STORES provided
    if not shops:
        single_shop = os.getenv("SHOPIFY_STORE", "").strip()
        single_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "").strip()
        if single_shop and single_token:
            shops[_normalize_shop_domain(single_shop)] = single_token

    if not shops:
        raise HTTPException(
            status_code=500, detail="No Shopify stores configured")

    products = []
    async with httpx.AsyncClient() as client:
        for shop, token in shops.items():
            shop = _normalize_shop_domain(shop)
            since_id = None
            while True:
                page = await _fetch_products_page(client, shop, token, since_id)
                if not page:
                    break
                # annotate each product with origin store
                for p in page:
                    try:
                        p["store"] = shop
                    except Exception:
                        # if product is not a dict for some reason, wrap it
                        p = {"product": p, "store": shop}
                    products.append(p)
                # use last product id for next page
                last_id = page[-1].get("id")
                if not last_id:
                    break
                since_id = last_id
                if len(page) < 250:
                    break

    return products


# New: request body model for adding items (store optional)
class AddItemsRequest(BaseModel):
    item_name: str
    quantity: int
    # optional store identifier (domain or short name)
    store: str | None = None


async def _find_product_by_name(client: httpx.AsyncClient, shop: str, token: str, name: str):
    """
    Page through products and return the first product whose title matches (case-insensitive substring or exact).
    """
    since_id = None
    name_lower = name.strip().lower()
    while True:
        page = await _fetch_products_page(client, shop, token, since_id)
        if not page:
            return None
        for p in page:
            title = (p.get("title") or "").lower()
            if title == name_lower or name_lower in title:
                return p
        last_id = page[-1].get("id")
        if not last_id or len(page) < 250:
            break
        since_id = last_id
    return None


async def _collect_product_titles(client: httpx.AsyncClient, shop: str, token: str, limit: int = 20):
    titles = []
    since_id = None
    while len(titles) < limit:
        page = await _fetch_products_page(client, shop, token, since_id)
        if not page:
            break
        for p in page:
            titles.append(p.get("title", ""))
            if len(titles) >= limit:
                break
        last_id = page[-1].get("id")
        if not last_id or len(page) < 250:
            break
        since_id = last_id
    return titles


async def _get_first_location_id(client: httpx.AsyncClient, shop: str, token: str) -> int | None:
    url = f"https://{shop}/admin/api/2025-01/locations.json"
    headers = {"X-Shopify-Access-Token": token, "Accept": "application/json"}
    resp = await client.get(url, headers=headers, timeout=30.0)
    resp.raise_for_status()
    body = resp.json()
    locations = body.get("locations", [])
    if not locations:
        return None
    return locations[0].get("id")


async def _adjust_inventory(client: httpx.AsyncClient, shop: str, token: str, inventory_item_id: int, location_id: int, adjustment: int):
    """
    Adjust inventory for given inventory_item_id at location_id by available_adjustment (can be positive or negative).
    Uses inventory_levels/adjust.json
    """
    url = f"https://{shop}/admin/api/2025-01/inventory_levels/adjust.json"
    headers = {"X-Shopify-Access-Token": token,
               "Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available_adjustment": adjustment
    }

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as exc:
            if attempt < max_attempts:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                continue
            raise HTTPException(
                status_code=502, detail=f"Network error when adjusting inventory: {exc}")
        except httpx.HTTPStatusError as exc:
            # surface Shopify error with short preview
            preview = exc.response.text[:1000] if exc.response is not None else None
            status = exc.response.status_code if exc.response is not None else 502
            raise HTTPException(
                status_code=status, detail=f"Shopify error adjusting inventory: {preview}")


async def _get_inventory_level(client: httpx.AsyncClient, shop: str, token: str, inventory_item_id: int, location_id: int) -> int | None:
    """
    Return available inventory for inventory_item_id at location_id, or None if not found.
    """
    url = f"https://{shop}/admin/api/2025-01/inventory_levels.json"
    headers = {"X-Shopify-Access-Token": token, "Accept": "application/json"}
    params = {"inventory_item_ids": inventory_item_id,
              "location_ids": location_id}

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            resp = await client.get(url, headers=headers, params=params, timeout=30.0)
            resp.raise_for_status()
            body = resp.json()
            levels = body.get("inventory_levels", []) or []
            if not levels:
                return None
            return levels[0].get("available")
        except httpx.RequestError as exc:
            if attempt < max_attempts:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                continue
            raise HTTPException(
                status_code=502, detail=f"Network error when fetching inventory level: {exc}")
        except httpx.HTTPStatusError as exc:
            preview = exc.response.text[:1000] if exc.response is not None else None
            status = exc.response.status_code if exc.response is not None else 502
            raise HTTPException(
                status_code=status, detail=f"Shopify error fetching inventory level: {preview}")
        except ValueError as exc:
            raise HTTPException(
                status_code=502, detail=f"Invalid JSON from Shopify when fetching inventory level: {exc}")


@items_router.post("/add", summary="Add quantity to a product by name")
async def add_items(body: AddItemsRequest):
    # resolve store -> shop domain and token
    shop, token = _resolve_store(body.store)
    if body.quantity == 0:
        raise HTTPException(
            status_code=400, detail="Quantity must be non-zero")

    async with httpx.AsyncClient() as client:
        product = await _find_product_by_name(client, shop, token, body.item_name)
        if not product:
            available = await _collect_product_titles(client, shop, token, limit=30)
            suggestions = difflib.get_close_matches(
                body.item_name, available, n=5, cutoff=0.5)
            samples = available if available else ["(no products found)"]
            detail = {
                "message": f"Product '{body.item_name}' not found in store '{shop}'.",
                "suggestions": suggestions,
                "available_sample": samples[:20]
            }
            raise HTTPException(status_code=404, detail=detail)

        variants = product.get("variants") or []
        if not variants:
            raise HTTPException(
                status_code=400, detail="Product has no variants to adjust inventory for")

        variant = variants[0]
        inventory_item_id = variant.get("inventory_item_id")
        if not inventory_item_id:
            raise HTTPException(
                status_code=400, detail="Variant has no inventory_item_id")

        location_id = await _get_first_location_id(client, shop, token)
        if not location_id:
            raise HTTPException(
                status_code=400, detail="No Shopify locations found to adjust inventory")

        result = await _adjust_inventory(client, shop, token, inventory_item_id, location_id, body.quantity)

    return {
        "store": shop,
        "product_id": product.get("id"),
        "product_title": product.get("title"),
        "variant_id": variant.get("id"),
        "inventory_item_id": inventory_item_id,
        "location_id": location_id,
        "adjusted_by": body.quantity,
        "shopify_response": result
    }


@items_router.delete("/delete", summary="Delete quantity from a product by name")
async def delete_items(body: AddItemsRequest):
    # resolve store -> shop domain and token
    shop, token = _resolve_store(body.store)
    if body.quantity <= 0:
        raise HTTPException(
            status_code=400, detail="Quantity must be a positive integer")

    async with httpx.AsyncClient() as client:
        product = await _find_product_by_name(client, shop, token, body.item_name)
        if not product:
            available = await _collect_product_titles(client, shop, token, limit=30)
            suggestions = difflib.get_close_matches(
                body.item_name, available, n=5, cutoff=0.5)
            samples = available if available else ["(no products found)"]
            detail = {
                "message": f"Product '{body.item_name}' not found in store '{shop}'.",
                "suggestions": suggestions,
                "available_sample": samples[:20]
            }
            raise HTTPException(status_code=404, detail=detail)

        variants = product.get("variants") or []
        if not variants:
            raise HTTPException(
                status_code=400, detail="Product has no variants to adjust inventory for")

        variant = variants[0]
        inventory_item_id = variant.get("inventory_item_id")
        if not inventory_item_id:
            raise HTTPException(
                status_code=400, detail="Variant has no inventory_item_id")

        location_id = await _get_first_location_id(client, shop, token)
        if not location_id:
            raise HTTPException(
                status_code=400, detail="No Shopify locations found to adjust inventory")

        current_available = await _get_inventory_level(client, shop, token, inventory_item_id, location_id)
        if current_available is None:
            raise HTTPException(
                status_code=400, detail="Could not determine current inventory for this variant")

        if current_available - body.quantity < 0:
            raise HTTPException(status_code=400, detail={
                "message": "Cannot delete requested quantity; would result in negative stock",
                "requested_delete": body.quantity,
                "current_available": current_available,
                "store": shop
            })

        result = await _adjust_inventory(client, shop, token, inventory_item_id, location_id, -body.quantity)

    return {
        "store": shop,
        "product_id": product.get("id"),
        "product_title": product.get("title"),
        "variant_id": variant.get("id"),
        "inventory_item_id": inventory_item_id,
        "location_id": location_id,
        "deleted_by": body.quantity,
        "previous_available": current_available,
        "shopify_response": result
    }
