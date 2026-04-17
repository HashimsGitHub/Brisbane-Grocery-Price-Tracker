import streamlit as st
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, GEOSPHERE


@st.cache_resource
def get_db():
    uri = st.secrets["MONGO_URI"]
    client = MongoClient(uri)
    db = client["price_tracker"]
    _ensure_indexes(db)
    _seed_items(db)
    return db


def _ensure_indexes(db):
    prices = db["prices"]

    # Drop old 6-month TTL index if it exists, recreate with 3-year expiry
    # so historical seed data (2024) is never auto-deleted
    try:
        prices.drop_index("ttl_6months")
    except Exception:
        pass
    prices.create_index(
        [("submitted_at", ASCENDING)],
        expireAfterSeconds=60 * 60 * 24 * 365 * 10,
        name="ttl_6months",
    )

    prices.create_index([("item_name", TEXT)], name="text_item")
    prices.create_index(
        [("item_name", ASCENDING), ("submitted_at", DESCENDING)],
        name="item_time",
    )
    prices.create_index(
        [("suburb", ASCENDING), ("item_name", ASCENDING)],
        name="suburb_item",
    )
    prices.create_index([("location", GEOSPHERE)], name="geo")

    items = db["items"]
    items.create_index([("name", ASCENDING)], unique=True, name="item_name_unique")
    items.create_index([("aliases", ASCENDING)], name="aliases")

    suburbs = db["suburbs"]
    suburbs.create_index(
        [("name", ASCENDING), ("state", ASCENDING)],
        unique=True,
        name="suburb_state_unique",
    )


def _seed_items(db):
    """Insert canonical item list if collection is empty."""
    if db["items"].count_documents({}) > 0:
        return

    seed = [
        {"name": "Full Cream Milk 2L",  "category": "Dairy",   "aliases": ["milk", "full cream milk", "2l milk"],          "unit_default": "each"},
        {"name": "White Bread Loaf",     "category": "Bakery",  "aliases": ["bread", "white bread", "toast bread"],         "unit_default": "each"},
        {"name": "Free Range Eggs 12pk", "category": "Dairy",   "aliases": ["eggs", "12 eggs", "dozen eggs"],               "unit_default": "each"},
        {"name": "Chicken Breast",       "category": "Meat",    "aliases": ["chicken", "chicken breast", "chicken fillet"], "unit_default": "kg"},
        {"name": "Beef Mince 500g",      "category": "Meat",    "aliases": ["mince", "beef mince", "ground beef"],          "unit_default": "each"},
        {"name": "Cheddar Cheese 500g",  "category": "Dairy",   "aliases": ["cheese", "cheddar", "tasty cheese"],           "unit_default": "each"},
        {"name": "Butter 500g",          "category": "Dairy",   "aliases": ["butter"],                                      "unit_default": "each"},
        {"name": "White Rice 1kg",       "category": "Pantry",  "aliases": ["rice", "white rice", "jasmine rice"],          "unit_default": "each"},
        {"name": "Pasta 500g",           "category": "Pantry",  "aliases": ["pasta", "spaghetti", "penne"],                 "unit_default": "each"},
        {"name": "Tinned Tomatoes 400g", "category": "Pantry",  "aliases": ["tinned tomatoes", "canned tomatoes"],          "unit_default": "each"},
        {"name": "Olive Oil 750ml",      "category": "Pantry",  "aliases": ["olive oil", "oil"],                            "unit_default": "each"},
        {"name": "Bananas",              "category": "Produce", "aliases": ["banana", "bananas"],                           "unit_default": "kg"},
        {"name": "Tomatoes",             "category": "Produce", "aliases": ["tomato", "tomatoes"],                          "unit_default": "kg"},
        {"name": "Potatoes 2kg",         "category": "Produce", "aliases": ["potatoes", "spuds"],                           "unit_default": "each"},
        {"name": "Carrots 1kg",          "category": "Produce", "aliases": ["carrots", "carrot"],                           "unit_default": "each"},
        {"name": "Orange Juice 2L",      "category": "Drinks",  "aliases": ["oj", "orange juice"],                         "unit_default": "each"},
        {"name": "Coca-Cola 1.25L",      "category": "Drinks",  "aliases": ["coke", "coca cola", "cola"],                  "unit_default": "each"},
        {"name": "Unleaded Petrol",      "category": "Fuel",    "aliases": ["petrol", "91 unleaded", "unleaded"],           "unit_default": "L"},
        {"name": "Premium Petrol",       "category": "Fuel",    "aliases": ["premium", "98", "e10"],                        "unit_default": "L"},
        {"name": "Diesel",               "category": "Fuel",    "aliases": ["diesel"],                                      "unit_default": "L"},
    ]
    db["items"].insert_many(seed)
