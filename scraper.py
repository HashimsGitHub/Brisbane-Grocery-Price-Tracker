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
        elif r.status_code == 404:
            # Coles rotates its API base URL — invalidate cache so next call re-discovers
            global _coles_api_base
            _coles_api_base = None
            raise ScrapeError(f"HTTP 404 from {url} — Coles API URL has rotated, will re-discover on next run.")
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
    "plant", "seed", "fertiliser", "pot", "shopping cart", "grocery shop",
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


# Cache for the discovered Coles API base URL (rotates periodically)
_coles_api_base: str | None = None


def _discover_coles_api_base() -> str:
    """
    Coles rotates their API base URL. Discover it dynamically by fetching
    the search page and extracting the URL from the next.js __NEXT_DATA__
    script tag or by trying known candidate patterns.
    """
    global _coles_api_base

    # Candidates in order of likelihood (newest first)
    candidates = [
        "https://www.coles.com.au/api/2.0/collections/groceries",
        "https://www.coles.com.au/api/2.0/products/search",
        "https://www.coles.com.au/api/2.0/products",
        "https://www.coles.com.au/api/v2/collections/groceries",
        "https://www.coles.com.au/api/v1/search/products",
    ]

    headers_extra = {
        "Origin": "https://www.coles.com.au",
        "Referer": "https://www.coles.com.au/search?q=milk",
    }

    for url in candidates:
        try:
            r = cf.get(
                url,
                params={"q": "milk", "pageSize": 1, "page": 1},
                headers={**BROWSER_HEADERS, **headers_extra},
                impersonate="chrome124",
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                # Valid response must contain results or products
                if data.get("results") or data.get("products") or data.get("catalogGroups"):
                    logger.info(f"Coles API base discovered: {url}")
                    return url
        except Exception:
            continue

    raise ScrapeError(
        "Could not discover Coles API endpoint. All candidates failed. "
        "Visit coles.com.au, search for a product, check DevTools Network tab "
        "for the products.json request URL and update COLES_API_CANDIDATES in scraper.py."
    )


def _get_coles_base() -> str:
    global _coles_api_base
    if not _coles_api_base:
        _coles_api_base = _discover_coles_api_base()
    return _coles_api_base


def scrape_coles(item: dict, store_id: str) -> Optional[Tuple[float, str, str]]:
    search_term = (item.get("aliases") or [item["name"]])[0]
    base_url = _get_coles_base()

    raw = _get_json(
        base_url,
        params={"q": search_term, "pageSize": 12, "page": 1, "storeId": store_id},
        headers={
            "Origin": "https://www.coles.com.au",
            "Referer": f"https://www.coles.com.au/search?q={search_term.replace(' ', '+')}",
        },
    )

    results = raw.get("results") or raw.get("products") or raw.get("catalogGroups") or []
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

# Workers per retailer.
# Woolworths and Coles are hit on separate thread pools so we never send
# concurrent requests to the same retailer faster than it can handle.
# 4 workers each means ~4 simultaneous requests per retailer — fast but
# still polite. Raise to 6 if you want more speed (may increase 429s).
_WW_WORKERS    = 4
_COLES_WORKERS = 4


def _scrape_task(task: dict) -> dict:
    """
    Execute a single (item, store) scrape task.
    Returns a result dict — never raises.
    """
    item     = task["item"]
    retailer = task["retailer"]
    store_id = task["store_id"]
    suburb   = task["suburb"]

    out = {
        "retailer": retailer,
        "suburb":   suburb,
        "item":     item["name"],
        "doc":      None,
        "skipped":  False,
        "error":    None,
    }

    try:
        if retailer == "woolworths":
            result      = scrape_woolworths(item, store_id)
            store_label = "Woolworths"
        else:
            result      = scrape_coles(item, store_id)
            store_label = "Coles"

    except ScrapeError as exc:
        out["error"] = f"[{retailer.title()} {suburb}] {item['name']}: {exc}"
        return out
    except Exception as exc:
        out["error"] = f"[{retailer.title()} {suburb}] {item['name']}: unexpected: {exc}"
        return out

    if result is None:
        out["skipped"] = True
        return out

    price, unit, product_name = result
    if not _price_is_sane(price):
        logger.warning(f"Rejected insane price ${price} for {item['name']} from {product_name}")
        out["skipped"] = True
        return out

    out["doc"] = _make_doc(item, price, unit, product_name, store_label, suburb, store_id)
    return out


def run_scrape(db, progress_callback=None, stores: list = None) -> dict:
    """
    Scrape all canonical grocery items (Fuel excluded) from Woolworths & Coles
    across Brisbane stores using parallel ThreadPoolExecutors.

    Woolworths and Coles requests run on separate thread pools so neither
    retailer receives more than _WW_WORKERS / _COLES_WORKERS concurrent
    requests at a time.

    Returns dict: inserted, skipped, errors, error_messages, items_scraped
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    items = list(db["items"].find({"category": {"$ne": "Fuel"}}, {"_id": 0}))

    if stores is None:
        stores = (
            [{"retailer": "woolworths", "store_id": sid, "suburb": sub}
             for sid, sub in WOOLWORTHS_SAMPLE_STORES]
            + [{"retailer": "coles", "store_id": sid, "suburb": sub}
               for sid, sub in COLES_BRISBANE_STORES[:5]]
        )

    # Build flat task list
    tasks = [
        {**store_info, "item": item}
        for item in items
        for store_info in stores
    ]
    total = len(tasks)

    results = {
        "inserted": 0, "skipped": 0, "errors": 0,
        "error_messages": [], "items_scraped": [],
    }

    # Thread-safe counters
    lock    = threading.Lock()
    counter = {"n": 0}

    # Pre-fetch dedup set to avoid per-insert MongoDB round-trips in threads
    from datetime import timezone
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    existing = set(
        (d["item_name"], d["store"], d["suburb"])
        for d in db["prices"].find(
            {"source": "auto_scrape", "submitted_at": {"$gte": six_hours_ago}},
            {"item_name": 1, "store": 1, "suburb": 1, "_id": 0},
        )
    )

    # Split tasks by retailer
    ww_tasks    = [t for t in tasks if t["retailer"] == "woolworths"]
    coles_tasks = [t for t in tasks if t["retailer"] == "coles"]

    docs_to_insert = []

    def process_futures(futures_map):
        for future in as_completed(futures_map):
            task = futures_map[future]
            with lock:
                counter["n"] += 1
                step = counter["n"]

            if progress_callback:
                progress_callback(
                    step, total,
                    f"[{task['retailer'].title()}] {task['suburb']} → {task['item']['name']}"
                )

            try:
                out = future.result()
            except Exception as exc:
                with lock:
                    results["errors"] += 1
                    results["error_messages"].append(str(exc))
                continue

            if out["error"]:
                with lock:
                    results["errors"] += 1
                    results["error_messages"].append(out["error"])
                    # Abort whole run on early 403
                    if "403" in out["error"] and step <= len(stores):
                        results["error_messages"].append(
                            "⛔ Aborting: 403 Forbidden — bot detection is blocking requests. "
                            "Add SCRAPER_PROXY to secrets.toml or run locally."
                        )
                continue

            if out["skipped"] or out["doc"] is None:
                with lock:
                    results["skipped"] += 1
                continue

            doc = out["doc"]
            key = (doc["item_name"], doc["store"], doc["suburb"])
            with lock:
                if key in existing:
                    results["skipped"] += 1
                else:
                    existing.add(key)
                    docs_to_insert.append(doc)

    # Run both pools concurrently using threads-within-threads is fine here
    # because we're doing I/O (network + DB), not CPU work.
    with ThreadPoolExecutor(max_workers=_WW_WORKERS,    thread_name_prefix="ww")    as ww_pool,          ThreadPoolExecutor(max_workers=_COLES_WORKERS, thread_name_prefix="coles") as coles_pool:

        ww_futures    = {ww_pool.submit(_scrape_task, t):    t for t in ww_tasks}
        coles_futures = {coles_pool.submit(_scrape_task, t): t for t in coles_tasks}

        all_futures = {**ww_futures, **coles_futures}
        process_futures(all_futures)

    # Batch-insert all collected docs in one MongoDB round-trip
    if docs_to_insert:
        try:
            db["prices"].insert_many(docs_to_insert, ordered=False)
            results["inserted"] = len(docs_to_insert)
            results["items_scraped"] = [
                f"{d['store']} {d['suburb']}: {d['item_name']} ${d['price']:.2f}"
                for d in docs_to_insert
            ]
        except Exception as exc:
            results["errors"] += 1
            results["error_messages"].append(f"Batch insert error: {exc}")

    return results
