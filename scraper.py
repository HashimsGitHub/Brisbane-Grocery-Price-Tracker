"""
scraper.py  –  Auto-scrape grocery prices from Woolworths & Coles (Brisbane)
─────────────────────────────────────────────────────────────────────────────
Both retailers expose JSON search APIs used by their own websites.
We replicate the same headers a real browser sends.

Error handling philosophy
  • Network/HTTP errors   → counted as "errors" (not silently skipped)
  • No matching product   → counted as "skipped"
  • Duplicate within 6h  → counted as "skipped"
  • Inserted successfully → counted as "inserted"
"""

import time
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# ── Sentinel to distinguish "failed" from "no match" ─────────────────────────
class ScrapeError(Exception):
    """Raised when a network/HTTP error occurs (not a missing product)."""
    pass


# ── HTTP helpers ──────────────────────────────────────────────────────────────

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-AU,en;q=0.9",
}


def _get_json(url: str, params: dict = None, extra_headers: dict = None,
              max_retries: int = 3, timeout: int = 12) -> dict:
    """
    GET → JSON with exponential back-off.
    Raises ScrapeError on HTTP errors or network failures.
    """
    headers = {**BROWSER_HEADERS, **(extra_headers or {})}
    session = requests.Session()
    session.headers.update(headers)

    for attempt in range(max_retries):
        try:
            r = session.get(url, params=params, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            if attempt == max_retries - 1:
                raise ScrapeError(f"Network error after {max_retries} attempts: {exc}") from exc
            time.sleep(2 ** attempt)
            continue

        if r.status_code == 200:
            try:
                return r.json()
            except ValueError as exc:
                raise ScrapeError(f"JSON decode error: {exc}") from exc

        elif r.status_code in (429, 503):
            wait = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Rate-limited ({r.status_code}) – waiting {wait:.1f}s")
            time.sleep(wait)

        elif r.status_code == 403:
            raise ScrapeError(
                f"403 Forbidden – the retailer's server blocked this request. "
                f"This usually means the hosting environment's IP is blocked. "
                f"Try running locally or adding a proxy."
            )
        else:
            raise ScrapeError(f"HTTP {r.status_code} from {url}")

    raise ScrapeError(f"Gave up after {max_retries} retries")


# ── Woolworths ────────────────────────────────────────────────────────────────

WOOLWORTHS_SEARCH_URL = "https://www.woolworths.com.au/apis/ui/Search/products"

WOOLWORTHS_SAMPLE_STORES = [
    ("3039", "Brisbane CBD"),
    ("4051", "Toowong"),
    ("4034", "Chermside"),
    ("4122", "Mount Gravatt"),
    ("4108", "Sunnybank"),
    ("4020", "Redcliffe"),
    ("4503", "Caboolture"),
]


def _woolworths_flatten_products(raw: dict) -> list:
    """
    Woolworths response structure (as of 2024–2025):
      { "Products": [ { "Products": [ {...product...}, ... ] }, ... ] }
    OR sometimes the inner list is at the top level.
    Return a flat list of individual product dicts.
    """
    products = []
    top = raw.get("Products") or raw.get("products") or []
    for group in top:
        if isinstance(group, dict):
            inner = group.get("Products") or group.get("products")
            if inner and isinstance(inner, list):
                products.extend(inner)
            elif group.get("Price") or group.get("price"):
                products.append(group)
    return products


def _woolworths_best_match(products: list, search_term: str) -> Optional[dict]:
    """Return the best-matching product that has a valid price."""
    words = [w.lower() for w in search_term.split() if len(w) > 2]

    # Pass 1 – must contain at least one keyword and have a price
    for p in products:
        name = (p.get("Name") or p.get("name") or "").lower()
        price = p.get("Price") or p.get("price")
        if price and float(price) > 0 and any(w in name for w in words):
            return p

    # Pass 2 – any product with a price
    for p in products:
        price = p.get("Price") or p.get("price")
        if price and float(price) > 0:
            return p

    return None


def scrape_woolworths(item: dict, store_id: str) -> Tuple[float, str, str]:
    """
    Returns (price, unit, product_name) or raises ScrapeError / returns None.
    """
    search_term = (item.get("aliases") or [item["name"]])[0]

    raw = _get_json(
        WOOLWORTHS_SEARCH_URL,
        params={
            "searchTerm": search_term,
            "pageSize": 12,
            "pageNumber": 1,
            "sortType": "TraderRelevance",
            "storeId": store_id,
        },
        extra_headers={"Referer": "https://www.woolworths.com.au/shop/search/products"},
    )

    products = _woolworths_flatten_products(raw)
    logger.debug(f"Woolworths '{search_term}' → {len(products)} products")

    match = _woolworths_best_match(products, search_term)
    if not match:
        return None

    price = float(match.get("Price") or match.get("price"))
    size_str = match.get("PackageSize") or match.get("packageSize") or match.get("CupMeasure") or ""
    unit = _infer_unit(size_str, item)
    product_name = match.get("Name") or match.get("name") or ""
    return price, unit, product_name


# ── Coles ─────────────────────────────────────────────────────────────────────

COLES_BRISBANE_STORES = [
    ("0587", "Brisbane CBD"),
    ("0579", "South Brisbane"),
    ("0581", "Toowong"),
    ("0642", "Chermside"),
    ("0632", "Mount Gravatt"),
    ("0628", "Indooroopilly"),
    ("0684", "Sunnybank"),
    ("0668", "Nundah"),
    ("0712", "Strathpine"),
    ("0731", "Caboolture"),
]

# Coles v2 search – used by their website
COLES_SEARCH_URL = "https://www.coles.com.au/api/2.0/collections/groceries"
# Alternate endpoint observed in network traffic
COLES_SEARCH_URL_V1 = "https://api.coles.com.au/search/v1/search"


def _coles_search_raw(search_term: str, store_id: str) -> list:
    """Try Coles v2 then v1 search endpoints. Returns list of result dicts."""
    headers_extra = {
        "Origin": "https://www.coles.com.au",
        "Referer": f"https://www.coles.com.au/search?q={requests.utils.quote(search_term)}",
    }

    # v2 endpoint
    try:
        raw = _get_json(
            COLES_SEARCH_URL,
            params={"q": search_term, "pageSize": 12, "page": 1, "storeId": store_id},
            extra_headers=headers_extra,
        )
        results = raw.get("results") or raw.get("catalogGroups") or []
        if results:
            return results
    except ScrapeError:
        pass  # fall through to v1

    # v1 endpoint
    raw = _get_json(
        COLES_SEARCH_URL_V1,
        params={"term": search_term, "storeId": store_id, "pageSize": 12},
        extra_headers=headers_extra,
    )
    return raw.get("results") or []


def _coles_best_match(results: list, search_term: str) -> Optional[dict]:
    words = [w.lower() for w in search_term.split() if len(w) > 2]

    def get_price(r):
        pricing = r.get("pricing") or r.get("price") or {}
        if isinstance(pricing, dict):
            return pricing.get("now") or pricing.get("current") or pricing.get("amount")
        return pricing if isinstance(pricing, (int, float)) else None

    # Pass 1 – keyword match + price
    for r in results:
        name = (r.get("name") or r.get("productName") or "").lower()
        price = get_price(r)
        if price and float(price) > 0 and any(w in name for w in words):
            return r

    # Pass 2 – any with price
    for r in results:
        price = get_price(r)
        if price and float(price) > 0:
            return r

    return None


def scrape_coles(item: dict, store_id: str) -> Optional[Tuple[float, str, str]]:
    search_term = (item.get("aliases") or [item["name"]])[0]
    results = _coles_search_raw(search_term, store_id)
    logger.debug(f"Coles '{search_term}' → {len(results)} results")

    match = _coles_best_match(results, search_term)
    if not match:
        return None

    pricing = match.get("pricing") or match.get("price") or {}
    if isinstance(pricing, dict):
        price = pricing.get("now") or pricing.get("current") or pricing.get("amount")
    else:
        price = pricing

    unit = _infer_unit(match.get("size") or match.get("packageSize") or "", item)
    product_name = match.get("name") or match.get("productName") or ""
    return float(price), unit, product_name


# ── Shared helpers ────────────────────────────────────────────────────────────

def _infer_unit(size_str: str, item: dict) -> str:
    s = (size_str or "").lower()
    if "kg" in s:
        return "kg"
    if "litre" in s or " l" in s or s.endswith("l"):
        return "L"
    if "ml" in s:
        return "100ml"
    return item.get("unit_default", "each")


def _make_doc(item: dict, price: float, unit: str, product_name: str,
              store: str, suburb: str, store_id: str) -> dict:
    return {
        "item_name": item["name"],
        "price": round(price, 2),
        "unit": unit,
        "store": store,
        "suburb": suburb,
        "state": "QLD",
        "submitted_at": datetime.utcnow(),   # naive UTC to match existing records
        "source": "auto_scrape",
        "scraped_product_name": product_name,
        "store_id": store_id,
    }


def _is_duplicate(db, doc: dict) -> bool:
    """True if same store+item was auto-scraped in the last 6 hours."""
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    return bool(db["prices"].find_one({
        "item_name": doc["item_name"],
        "store": doc["store"],
        "suburb": doc["suburb"],
        "source": "auto_scrape",
        "submitted_at": {"$gte": six_hours_ago},
    }))


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_scrape(db, progress_callback=None, stores: list = None) -> dict:
    """
    Scrape all canonical grocery items (excluding Fuel) from Woolworths & Coles
    for a representative set of Brisbane stores.

    Parameters
    ----------
    db               : pymongo database handle
    progress_callback: optional callable(current, total, message)
    stores           : list of {retailer, store_id, suburb}
                       defaults to WOOLWORTHS_SAMPLE_STORES + COLES_BRISBANE_STORES[:5]

    Returns
    -------
    dict: inserted, skipped, errors, error_messages, items_scraped
    """
    items = list(db["items"].find({"category": {"$ne": "Fuel"}}, {"_id": 0}))

    if stores is None:
        stores = (
            [{"retailer": "woolworths", "store_id": sid, "suburb": sub}
             for sid, sub in WOOLWORTHS_SAMPLE_STORES]
            + [{"retailer": "coles", "store_id": sid, "suburb": sub}
               for sid, sub in COLES_BRISBANE_STORES[:5]]
        )

    total = len(items) * len(stores)
    results = {"inserted": 0, "skipped": 0, "errors": 0,
               "error_messages": [], "items_scraped": []}
    step = 0

    for item in items:
        for store_info in stores:
            step += 1
            retailer  = store_info["retailer"]
            store_id  = store_info["store_id"]
            suburb    = store_info["suburb"]

            if progress_callback:
                progress_callback(
                    step, total,
                    f"[{retailer.title()}] {suburb} → {item['name']}"
                )

            try:
                if retailer == "woolworths":
                    result = scrape_woolworths(item, store_id)
                    store_label = "Woolworths"
                elif retailer == "coles":
                    result = scrape_coles(item, store_id)
                    store_label = "Coles"
                else:
                    results["skipped"] += 1
                    continue

            except ScrapeError as exc:
                msg = f"[{retailer.title()} {suburb}] {item['name']}: {exc}"
                logger.error(msg)
                results["errors"] += 1
                results["error_messages"].append(msg)
                # If we get a 403 on the first item, abort early – all will fail
                if "403" in str(exc) and step <= len(stores):
                    results["error_messages"].append(
                        "⚠️  Got 403 Forbidden early in the run. "
                        "The retailer is blocking requests from this server's IP. "
                        "This commonly happens on shared hosting (Streamlit Cloud). "
                        "See the README for workaround options."
                    )
                    return results
                continue

            except Exception as exc:
                msg = f"[{retailer.title()} {suburb}] {item['name']}: unexpected error: {exc}"
                logger.exception(msg)
                results["errors"] += 1
                results["error_messages"].append(msg)
                continue

            # No matching product found
            if result is None:
                results["skipped"] += 1
                continue

            price, unit, product_name = result
            doc = _make_doc(item, price, unit, product_name, store_label, suburb, store_id)

            if _is_duplicate(db, doc):
                results["skipped"] += 1
            else:
                db["prices"].insert_one(doc)
                results["inserted"] += 1
                results["items_scraped"].append(
                    f"{store_label} {suburb}: {item['name']} ${price:.2f}"
                )

            time.sleep(0.8 + random.uniform(0, 0.4))

    return results
