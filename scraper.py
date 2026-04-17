"""
scraper.py  –  Auto-scrape grocery prices from Woolworths & Coles (Brisbane)
─────────────────────────────────────────────────────────────────────────────
Uses curl_cffi to impersonate a real Chrome browser TLS fingerprint.
This bypasses the bot-detection (Cloudflare/Akamai) that blocks the standard
Python `requests` library on shared cloud hosts like Streamlit Community Cloud.

Install: pip install curl-cffi
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from curl_cffi import requests as cf

logger = logging.getLogger(__name__)


class ScrapeError(Exception):
    """Network / HTTP failure (distinct from 'product not found')."""
    pass


# ── Shared HTTP helper ────────────────────────────────────────────────────────

def _get_json(url: str, params: dict = None, headers: dict = None,
              max_retries: int = 3, timeout: int = 15) -> dict:
    """
    GET → JSON using curl_cffi Chrome124 TLS impersonation.
    Raises ScrapeError on failure.
    """
    base_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    if headers:
        base_headers.update(headers)

    for attempt in range(max_retries):
        try:
            r = cf.get(
                url,
                params=params,
                headers=base_headers,
                impersonate="chrome124",   # <-- full Chrome TLS fingerprint
                timeout=timeout,
            )
        except Exception as exc:
            if attempt == max_retries - 1:
                raise ScrapeError(f"Network error: {exc}") from exc
            time.sleep(2 ** attempt)
            continue

        if r.status_code == 200:
            try:
                return r.json()
            except ValueError as exc:
                raise ScrapeError(f"JSON parse error: {exc}") from exc

        elif r.status_code in (429, 503):
            wait = (2 ** attempt) + random.uniform(0.5, 1.5)
            logger.warning(f"Rate-limited ({r.status_code}), retrying in {wait:.1f}s")
            time.sleep(wait)

        elif r.status_code == 403:
            raise ScrapeError(
                f"403 Forbidden from {url}. "
                "Bot detection is still blocking requests. "
                "Add SCRAPER_PROXY to .streamlit/secrets.toml or run locally."
            )
        else:
            raise ScrapeError(f"HTTP {r.status_code} from {url}")

    raise ScrapeError(f"Gave up after {max_retries} retries on {url}")


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


def _woolworths_flatten(raw: dict) -> list:
    """Flatten the nested Products > Products structure."""
    out = []
    for group in (raw.get("Products") or []):
        if isinstance(group, dict):
            inner = group.get("Products") or group.get("products")
            if inner:
                out.extend(inner)
            elif group.get("Price") or group.get("price"):
                out.append(group)
    return out


# Words that indicate a result is NOT a grocery product.
_BLOCKLIST = {
    "bag", "bags", "carry", "foldable", "reusable", "trolley", "basket",
    "toy", "melissa", "doug", "game", "gift", "book", "magazine", "dvd",
    "utensil", "container", "storage", "cleaning cloth", "sponge", "brush",
    "mop", "broom", "bin", "candle", "diffuser", "detergent", "laundry",
    "nappy", "diaper", "shampoo", "conditioner", "bodywash", "soap",
    "toothpaste", "razor", "deodorant", "sunscreen", "cosmetic", "makeup",
    "vitamin", "supplement", "protein powder", "medicine", "tablet",
    "capsule", "bandage", "first aid", "pet food", "dog food", "cat food",
    "plant", "seed", "fertiliser", "pot", "shopping cart",
}


def _is_blocked(name: str) -> bool:
    name_lower = name.lower()
    return any(term in name_lower for term in _BLOCKLIST)


def _match_score(name: str, search_term: str) -> int:
    """Count how many search keywords appear in the product name."""
    name_lower = name.lower()
    keywords = [w.lower() for w in search_term.split()
                if len(w) > 2 and w.lower() not in {"per", "the", "and", "for"}]
    return sum(1 for kw in keywords if kw in name_lower)


def _best_match(products: list, search_term: str,
                name_key: str = "Name", price_key: str = "Price") -> Optional[dict]:
    """
    Return the best matching product with strict validation:
    - Must score >= 1 (at least one keyword in product name)
    - Must NOT match the blocklist
    - NO fallback to unrelated products — returns None if nothing qualifies
    """
    scored = []
    for p in products:
        name  = (p.get(name_key) or p.get(name_key.lower()) or "").strip()
        price = p.get(price_key) or p.get(price_key.lower())
        if not name or not price or float(price) <= 0:
            continue
        if _is_blocked(name):
            logger.debug(f"Blocked irrelevant result: '{name}'")
            continue
        score = _match_score(name, search_term)
        if score > 0:
            scored.append((score, p))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def scrape_woolworths(item: dict, store_id: str) -> Optional[Tuple[float, str, str]]:
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
        headers={
            "Referer": "https://www.woolworths.com.au/shop/search/products",
            "Origin": "https://www.woolworths.com.au",
        },
    )

    products = _woolworths_flatten(raw)
    logger.debug(f"Woolworths '{search_term}' store {store_id} → {len(products)} products")

    match = _best_match(products, search_term, name_key="Name", price_key="Price")
    if not match:
        return None

    price = float(match.get("Price") or match.get("price"))
    size  = match.get("PackageSize") or match.get("CupMeasure") or ""
    return price, _infer_unit(size, item), (match.get("Name") or "")


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


def scrape_coles(item: dict, store_id: str) -> Optional[Tuple[float, str, str]]:
    search_term = (item.get("aliases") or [item["name"]])[0]

    raw = _get_json(
        "https://www.coles.com.au/api/2.0/collections/groceries",
        params={"q": search_term, "pageSize": 12, "page": 1, "storeId": store_id},
        headers={
            "Origin": "https://www.coles.com.au",
            "Referer": f"https://www.coles.com.au/search?q={search_term.replace(' ', '+')}",
        },
    )

    results = raw.get("results") or raw.get("catalogGroups") or []
    logger.debug(f"Coles '{search_term}' store {store_id} → {len(results)} results")

    def get_price(r):
        p = r.get("pricing") or {}
        if isinstance(p, dict):
            return p.get("now") or p.get("current") or p.get("amount")
        return p if isinstance(p, (int, float)) else None

    # Build a flat list with normalised price key for _best_match
    flat = []
    for r in results:
        price = get_price(r)
        if price:
            flat.append({
                "_name": r.get("name") or r.get("productName") or "",
                "_price": float(price),
                "_size": r.get("size") or r.get("packageSize") or "",
            })

    # Use the same strict matching — build normalised dicts for _best_match
    normalised = [{"Name": p["_name"], "Price": p["_price"], "_size": p["_size"]} for p in flat]
    match = _best_match(normalised, search_term, name_key="Name", price_key="Price")
    if not match:
        return None

    return match["Price"], _infer_unit(match.get("_size", ""), item), match["Name"]


# ── Helpers ───────────────────────────────────────────────────────────────────

# Plausible price range for any grocery item ($0.50 – $150)
_MIN_PRICE = 0.50
_MAX_PRICE = 150.00


def _price_is_sane(price: float) -> bool:
    return _MIN_PRICE <= price <= _MAX_PRICE


def _infer_unit(size_str: str, item: dict) -> str:
    s = (size_str or "").lower()
    if "kg"    in s: return "kg"
    if "litre" in s or " l" in s or s.endswith("l"): return "L"
    if "ml"    in s: return "100ml"
    return item.get("unit_default", "each")


def _make_doc(item, price, unit, product_name, store, suburb, store_id):
    return {
        "item_name":            item["name"],
        "price":                round(price, 2),
        "unit":                 unit,
        "store":                store,
        "suburb":               suburb,
        "state":                "QLD",
        "submitted_at":         datetime.utcnow(),
        "source":               "auto_scrape",
        "scraped_product_name": product_name,
        "store_id":             store_id,
    }


def _is_duplicate(db, doc: dict) -> bool:
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    return bool(db["prices"].find_one({
        "item_name":    doc["item_name"],
        "store":        doc["store"],
        "suburb":       doc["suburb"],
        "source":       "auto_scrape",
        "submitted_at": {"$gte": six_hours_ago},
    }))


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_scrape(db, progress_callback=None, stores: list = None) -> dict:
    """
    Scrape all canonical grocery items (Fuel excluded) from Woolworths & Coles
    across Brisbane stores.

    Returns dict: inserted, skipped, errors, error_messages, items_scraped
    """
    items = list(db["items"].find({"category": {"$ne": "Fuel"}}, {"_id": 0}))

    if stores is None:
        stores = (
            [{"retailer": "woolworths", "store_id": sid, "suburb": sub}
             for sid, sub in WOOLWORTHS_SAMPLE_STORES]
            + [{"retailer": "coles", "store_id": sid, "suburb": sub}
               for sid, sub in COLES_BRISBANE_STORES[:5]]
        )

    total   = len(items) * len(stores)
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
                progress_callback(step, total,
                    f"[{retailer.title()}] {suburb} → {item['name']}")

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
                # Abort early if we hit a persistent 403 on the first store
                if "403" in str(exc) and step <= len(stores):
                    results["error_messages"].append(
                        "⛔ Aborting: repeated 403s indicate bot-detection is blocking "
                        "requests from this server. curl_cffi Chrome impersonation was "
                        "not sufficient. Add SCRAPER_PROXY to secrets.toml or run locally."
                    )
                    return results
                continue

            except Exception as exc:
                msg = f"[{retailer.title()} {suburb}] {item['name']}: unexpected: {exc}"
                logger.exception(msg)
                results["errors"] += 1
                results["error_messages"].append(msg)
                continue

            if result is None:
                results["skipped"] += 1
                continue

            price, unit, product_name = result

            # Reject implausible prices
            if not _price_is_sane(price):
                logger.warning(f"Rejected insane price ${price} for {item['name']} from {product_name}")
                results["skipped"] += 1
                continue

            doc = _make_doc(item, price, unit, product_name, store_label, suburb, store_id)

            if _is_duplicate(db, doc):
                results["skipped"] += 1
            else:
                db["prices"].insert_one(doc)
                results["inserted"] += 1
                results["items_scraped"].append(
                    f"{store_label} {suburb}: {item['name']} ${price:.2f}"
                )

            time.sleep(0.6 + random.uniform(0, 0.4))

    return results
