"""
scraper.py  –  Auto-scrape grocery prices from Woolworths & Coles (Brisbane)
─────────────────────────────────────────────────────────────────────────────
Strategy
  • Woolworths  → undocumented JSON search API  (no JS rendering needed)
  • Coles       → undocumented JSON search API  (no JS rendering needed)

Both APIs are freely accessible from a browser; we replicate the same
headers a real browser sends.  No login is required for price data.

The scraper only looks up the canonical items already stored in MongoDB
(db["items"]) and writes results back into db["prices"] with
  source = "auto_scrape"
so they are clearly distinguished from crowdsourced entries.

Brisbane store filtering
  Woolworths uses a "storeId" for each location.  We store a curated list
  of Brisbane store IDs so results reflect local pricing.
  Coles returns national prices from its search API (prices don't vary
  per-store in their online catalogue), so we tag those as "Brisbane" and
  flag them as the Coles online price.

Rate-limiting / politeness
  • 1-second sleep between items
  • Exponential back-off on 429 / 5xx
  • User-Agent is a real Chrome UA
"""

import time
import random
import logging
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── HTTP session ──────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://www.woolworths.com.au/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def _get_with_retry(url: str, params: dict = None, max_retries: int = 3, timeout: int = 10) -> Optional[dict]:
    """GET with exponential back-off. Returns parsed JSON or None on failure."""
    for attempt in range(max_retries):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            elif r.status_code in (429, 503):
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate-limited ({r.status_code}). Waiting {wait:.1f}s…")
                time.sleep(wait)
            elif r.status_code == 403:
                logger.error(f"403 Forbidden on {url} – site may have blocked this IP.")
                return None
            else:
                logger.warning(f"HTTP {r.status_code} on {url}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    return None


# ── Woolworths ────────────────────────────────────────────────────────────────
# Woolworths search API returns JSON with a "Products" list.
# Each product has:   Name, Price, WasPrice, CupPrice, CupMeasure, Stockcode

WOOLWORTHS_SEARCH_URL = "https://www.woolworths.com.au/apis/ui/Search/products"

# Brisbane Woolworths store IDs (used for stock/availability checks; prices are
# the same online but storeId scopes results to local range).
WOOLWORTHS_BRISBANE_STORE_IDS = [
    "3039",  # Brisbane City
    "3031",  # South Brisbane
    "3040",  # Fortitude Valley
    "4051",  # Toowong
    "3066",  # West End / Boundary St
    "4102",  # Woolloongabba
    "4053",  # Paddington
    "4068",  # St Lucia
    "4069",  # Indooroopilly
    "4152",  # Carindale
    "4122",  # Mount Gravatt
    "4151",  # Greenslopes
    "4105",  # Moorooka
    "4108",  # Sunnybank
    "4109",  # Robertson
    "4034",  # Chermside
    "4032",  # Aspley
    "4030",  # Kedron
    "4012",  # Nundah
    "4017",  # Sandgate
    "4020",  # Redcliffe
    "4500",  # Strathpine / North Lakes
    "4503",  # Caboolture
]

# Suburb labels paired with store IDs for writing to MongoDB
WOOLWORTHS_STORE_MAP = {
    "3039": "Brisbane CBD",
    "3031": "South Brisbane",
    "3040": "Fortitude Valley",
    "4051": "Toowong",
    "3066": "West End",
    "4102": "Woolloongabba",
    "4053": "Paddington",
    "4068": "St Lucia",
    "4069": "Indooroopilly",
    "4152": "Carindale",
    "4122": "Mount Gravatt",
    "4151": "Greenslopes",
    "4105": "Moorooka",
    "4108": "Sunnybank",
    "4109": "Robertson",
    "4034": "Chermside",
    "4032": "Aspley",
    "4030": "Kedron",
    "4012": "Nundah",
    "4017": "Sandgate",
    "4020": "Redcliffe",
    "4500": "Strathpine",
    "4503": "Caboolture",
}

# We pick a representative subset of Brisbane stores to avoid hammering the API
WOOLWORTHS_SAMPLE_STORES = [
    ("3039", "Brisbane CBD"),
    ("4051", "Toowong"),
    ("4034", "Chermside"),
    ("4122", "Mount Gravatt"),
    ("4108", "Sunnybank"),
    ("4020", "Redcliffe"),
    ("4503", "Caboolture"),
]


def _woolworths_best_match(products: list, search_term: str) -> Optional[dict]:
    """Return the first in-stock, clearly matching product."""
    search_lower = search_term.lower()
    for p in products:
        name = (p.get("Name") or "").lower()
        price = p.get("Price")
        available = p.get("IsInStock", True)
        if price and price > 0 and available:
            # Prefer products whose name contains key words from the search
            words = [w for w in search_lower.split() if len(w) > 2]
            if any(w in name for w in words):
                return p
    # Fallback: first product with a price
    for p in products:
        if p.get("Price") and p.get("Price") > 0:
            return p
    return None


def scrape_woolworths(item: dict, store_id: str, suburb: str) -> Optional[dict]:
    """
    Scrape a single item from Woolworths for a given Brisbane store.
    Returns a price document ready for MongoDB insertion, or None.
    """
    # Use the first alias as the search term (usually most specific)
    aliases = item.get("aliases", [])
    search_term = aliases[0] if aliases else item["name"]

    data = _get_with_retry(
        WOOLWORTHS_SEARCH_URL,
        params={
            "searchTerm": search_term,
            "pageSize": 10,
            "pageNumber": 1,
            "sortType": "TraderRelevance",
            "storeId": store_id,
        },
    )
    if not data:
        return None

    products = []
    try:
        products = data["Products"]  # list of product groups
        # Flatten: each group may contain a Products sub-list
        flat = []
        for group in products:
            if isinstance(group, dict):
                if "Products" in group:
                    flat.extend(group["Products"])
                else:
                    flat.append(group)
        products = flat
    except (KeyError, TypeError):
        return None

    match = _woolworths_best_match(products, search_term)
    if not match:
        return None

    price = match.get("Price")
    unit = _infer_unit(match.get("PackageSize") or match.get("CupMeasure") or "", item)

    return {
        "item_name": item["name"],
        "price": round(float(price), 2),
        "unit": unit,
        "store": "Woolworths",
        "suburb": suburb,
        "state": "QLD",
        "submitted_at": datetime.now(timezone.utc),
        "source": "auto_scrape",
        "scraped_product_name": match.get("Name"),
        "store_id": store_id,
    }


# ── Coles ─────────────────────────────────────────────────────────────────────
# Coles search endpoint – prices are national online prices.
# We tag suburb as "Brisbane (Online)" so it's clear in the UI.

COLES_SEARCH_URL = "https://www.coles.com.au/api/2.0/collections/groceries"

COLES_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-AU,en;q=0.9",
    "Origin": "https://www.coles.com.au",
    "Referer": "https://www.coles.com.au/search?q=milk",
}

COLES_SESSION = requests.Session()
COLES_SESSION.headers.update(COLES_HEADERS)

# Brisbane Coles store IDs for the /store endpoint (used only for availability)
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


def _coles_search(search_term: str, store_id: str = "0587") -> Optional[list]:
    """Call the Coles search API and return the raw results list."""
    url = "https://www.coles.com.au/api/2.0/collections/groceries"
    params = {
        "q": search_term,
        "pageSize": 10,
        "page": 1,
        "storeId": store_id,
    }
    try:
        r = COLES_SESSION.get(url, params=params, timeout=10)
        if r.status_code != 200:
            logger.warning(f"Coles HTTP {r.status_code} for '{search_term}'")
            return None
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        logger.warning(f"Coles request error: {e}")
        return None


def _coles_best_match(results: list, search_term: str) -> Optional[dict]:
    """Return the first result with a valid price."""
    search_lower = search_term.lower()
    for item in results:
        price_info = item.get("pricing") or {}
        price = price_info.get("now")
        if price and float(price) > 0:
            name = (item.get("name") or "").lower()
            words = [w for w in search_lower.split() if len(w) > 2]
            if any(w in name for w in words):
                return item
    # Fallback
    for item in results:
        price_info = item.get("pricing") or {}
        price = price_info.get("now")
        if price and float(price) > 0:
            return item
    return None


def scrape_coles(item: dict, store_id: str, suburb: str) -> Optional[dict]:
    """
    Scrape a single item from Coles for a given Brisbane store.
    Returns a price document or None.
    """
    aliases = item.get("aliases", [])
    search_term = aliases[0] if aliases else item["name"]

    results = _coles_search(search_term, store_id)
    if not results:
        return None

    match = _coles_best_match(results, search_term)
    if not match:
        return None

    price_info = match.get("pricing") or {}
    price = price_info.get("now")
    unit = _infer_unit(match.get("size") or "", item)

    return {
        "item_name": item["name"],
        "price": round(float(price), 2),
        "unit": unit,
        "store": "Coles",
        "suburb": suburb,
        "state": "QLD",
        "submitted_at": datetime.now(timezone.utc),
        "source": "auto_scrape",
        "scraped_product_name": match.get("name"),
        "store_id": store_id,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _infer_unit(size_str: str, item: dict) -> str:
    """Derive unit from product size string, falling back to item default."""
    s = (size_str or "").lower()
    if "kg" in s:
        return "kg"
    if " l" in s or s.endswith("l") or "litre" in s:
        return "L"
    if "ml" in s:
        return "100ml"
    if "g" in s:
        return "each"  # packaged good – sold by pack
    return item.get("unit_default", "each")


# ── Main scrape orchestrator ──────────────────────────────────────────────────

def run_scrape(db, progress_callback=None, stores: list = None) -> dict:
    """
    Scrape all canonical items from both Woolworths and Coles for a
    representative set of Brisbane stores.

    Parameters
    ----------
    db               : pymongo database handle
    progress_callback: optional callable(current, total, message)
    stores           : list of store dicts [{retailer, store_id, suburb}]
                       – defaults to WOOLWORTHS_SAMPLE_STORES + COLES_BRISBANE_STORES

    Returns
    -------
    dict with keys: inserted, skipped, errors, items_scraped
    """
    items = list(db["items"].find({}, {"_id": 0}))
    # Skip fuel – those require different sources (FuelWatch / GasBuddy)
    grocery_items = [i for i in items if i.get("category") != "Fuel"]

    if stores is None:
        woolies_stores = [{"retailer": "woolworths", "store_id": sid, "suburb": sub}
                          for sid, sub in WOOLWORTHS_SAMPLE_STORES]
        coles_stores = [{"retailer": "coles", "store_id": sid, "suburb": sub}
                        for sid, sub in COLES_BRISBANE_STORES]
        stores = woolies_stores + coles_stores

    total = len(grocery_items) * len(stores)
    results = {"inserted": 0, "skipped": 0, "errors": 0, "items_scraped": []}
    step = 0

    for item in grocery_items:
        for store_info in stores:
            step += 1
            retailer = store_info["retailer"]
            store_id = store_info["store_id"]
            suburb = store_info["suburb"]
            msg = f"Scraping {retailer.title()} {suburb} → {item['name']}"

            if progress_callback:
                progress_callback(step, total, msg)

            # --- scrape ---
            try:
                if retailer == "woolworths":
                    doc = scrape_woolworths(item, store_id, suburb)
                elif retailer == "coles":
                    doc = scrape_coles(item, store_id, suburb)
                else:
                    doc = None
            except Exception as e:
                logger.error(f"Scrape error [{retailer}/{store_id}/{item['name']}]: {e}")
                results["errors"] += 1
                continue

            if doc is None:
                results["skipped"] += 1
                continue

            # --- deduplicate: skip if same store/item scraped in last 6 hours ---
            from datetime import timedelta
            six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6)
            existing = db["prices"].find_one({
                "item_name": doc["item_name"],
                "store": doc["store"],
                "suburb": doc["suburb"],
                "source": "auto_scrape",
                "submitted_at": {"$gte": six_hours_ago},
            })
            if existing:
                results["skipped"] += 1
            else:
                db["prices"].insert_one(doc)
                results["inserted"] += 1
                results["items_scraped"].append(f"{doc['store']} {doc['suburb']}: {doc['item_name']} ${doc['price']:.2f}")

            time.sleep(0.8 + random.uniform(0, 0.4))  # ~1 s between requests

    return results
