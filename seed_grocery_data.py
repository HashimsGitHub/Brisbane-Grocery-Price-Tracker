"""
Seed MongoDB with 2024 grocery price data extracted from Expense_Tracker_2024.xlsx.
Usage:
    pip install pandas openpyxl pymongo dnspython
    MONGO_URI="your-uri" python seed_grocery_data.py
Or place your MONGO_URI in .streamlit/secrets.toml and run:
    python seed_grocery_data.py --from-secrets
"""

import os
import sys
import argparse
from datetime import datetime
import pandas as pd
from pymongo import MongoClient

# ── Category map: normalise raw Excel item names → app categories ─────────────
CATEGORY_MAP = {
    # Food / Bakery
    'Bread': 'Bakery', 'Amin Bhai Roti': 'Bakery', 'Bread Crumb': 'Bakery',
    'Baking powder': 'Pantry', 'Baking Paper': 'Pantry',
    # Dairy
    'Milk 1l': 'Dairy', 'Milk 2L': 'Dairy', 'Milk 3l': 'Dairy',
    'Eggs 18': 'Dairy', 'Eggs 12': 'Dairy', 'Eggs liquid': 'Dairy',
    'Butter': 'Dairy', 'Cheese': 'Dairy',
    # Poultry & Meat
    'Chicken Maryland': 'Meat', 'Chicken Drumsticks': 'Meat',
    'Chicken Curry pcs': 'Meat', 'Chicken Whole': 'Meat',
    'Chicken Breast': 'Meat', 'Chicken Seekh': 'Meat',
    'Chicken Qorma': 'Meat', 'Qeema': 'Meat',
    'Mutton': 'Meat', 'Beef': 'Meat', 'Mince': 'Meat',
    # Produce
    'Bananas': 'Produce', 'Apple': 'Produce', 'Tomatoes': 'Produce',
    'Carrots': 'Produce', 'Potatoes': 'Produce', 'Capsicum': 'Produce',
    'Cabbage': 'Produce', 'Cauliflower': 'Produce', 'Celery Stick': 'Produce',
    'Spinach': 'Produce', 'Ginger': 'Produce', 'Garlic': 'Produce',
    'Onion': 'Produce', 'Lemon': 'Produce', 'Black lemon': 'Produce',
    # Pantry
    'Rice 5kg': 'Pantry', 'Rice 10kg': 'Pantry',
    'Aata 5kg': 'Pantry', 'Barlley Flour': 'Pantry',
    'Olive Oil': 'Pantry', 'Almond Oil': 'Pantry', 'Castor Oil': 'Pantry',
    'Almond Raw': 'Pantry', 'Coconut': 'Pantry',
    'Baked beans': 'Pantry', 'Additive': 'Pantry',
    # Drinks
    'Water': 'Drinks', 'Apple Juice': 'Drinks', 'Orange Juice': 'Drinks',
    'BBQ Flavor Snacks ALDI': 'Snacks',
    # Toiletries
    'Toiler Cleaner': 'Toiletries', 'Handsoap': 'Toiletries',
    'Shampoo': 'Toiletries', 'Conditioner': 'Toiletries',
    'Bodywash': 'Toiletries', 'Veet': 'Toiletries',
    'Toilet Wipes': 'Toiletries', 'Razor Blades': 'Toiletries',
    'Extra pad': 'Toiletries', 'Nivea Moisture': 'Toiletries',
    'Electric Toothbrish': 'Toiletries',
    'Smiles Herbal Toothpaste': 'Toiletries', 'Smiles Toothpaste': 'Toiletries',
    'Air Freshner': 'Cleaning', 'Cotton Buds 200pc': 'Toiletries',
    'Disinfectant': 'Cleaning', 'Vasiline': 'Toiletries',
    'Wet Wipes': 'Toiletries',
}

SHEET_MAP = {
    'Grocery JUNE':       (6, 2024),
    'Grocery JULY':       (7, 2024),
    'Grocery AUGUST':     (8, 2024),
    'Grocery SEPTEMEBER': (9, 2024),
}


def extract_records(filepath: str) -> list[dict]:
    records = []

    for sheet_name, (month_num, year) in SHEET_MAP.items():
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

        # Row index 1 contains day numbers starting at col 2
        day_row = df.iloc[1]
        day_cols = {}
        for col_idx in range(2, len(day_row)):
            val = day_row.iloc[col_idx]
            try:
                day = int(float(val))
                if 1 <= day <= 31:
                    day_cols[col_idx] = day
            except (ValueError, TypeError):
                pass

        current_category = 'General'

        for row_idx in range(3, len(df)):
            item_name = str(df.iloc[row_idx, 0]).strip()
            if item_name in ('nan', '', 'NaN'):
                continue

            # Detect category-header rows (no numeric prices)
            row_prices = []
            for col_idx in day_cols:
                val = df.iloc[row_idx, col_idx]
                try:
                    if pd.notna(val):
                        p = float(val)
                        if p > 0:
                            row_prices.append(p)
                except (ValueError, TypeError):
                    pass

            if not row_prices:
                current_category = item_name
                continue

            # Resolve unit
            unit_raw = str(df.iloc[row_idx, 1]).strip()
            if unit_raw in ('nan', '', 'NaN', 'pc', 'pcs'):
                unit = 'each'
            elif unit_raw == 'kg':
                unit = 'kg'
            elif unit_raw in ('L', 'l', 'litre'):
                unit = 'L'
            else:
                unit = unit_raw

            category = CATEGORY_MAP.get(item_name, current_category)

            for col_idx, day in day_cols.items():
                val = df.iloc[row_idx, col_idx]
                try:
                    if pd.notna(val):
                        price = float(val)
                        if price > 0:
                            try:
                                date = datetime(year, month_num, day)
                            except ValueError:
                                continue  # skip invalid dates like Feb 30
                            records.append({
                                'item_name': item_name,
                                'price': round(price, 2),
                                'unit': unit,
                                'store': 'Unknown',
                                'suburb': 'Brisbane CBD',
                                'state': 'QLD',
                                'category': category,
                                'submitted_at': date,
                                'user_hash': 'seed_data',
                                'source': 'Expense_Tracker_2024.xlsx',
                            })
                except (ValueError, TypeError):
                    pass

    return records


def get_uri(from_secrets: bool) -> str:
    if from_secrets:
        try:
            import toml
            secrets = toml.load('.streamlit/secrets.toml')
            return secrets['MONGO_URI']
        except Exception as e:
            print(f"Could not read secrets.toml: {e}")
            sys.exit(1)
    uri = os.environ.get('MONGO_URI', '')
    if not uri:
        print("Set MONGO_URI env var or use --from-secrets")
        sys.exit(1)
    return uri


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-secrets', action='store_true',
                        help='Read MONGO_URI from .streamlit/secrets.toml')
    parser.add_argument('--file', default='Expense_Tracker_2024.xlsx',
                        help='Path to the Excel file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print records without inserting')
    args = parser.parse_args()

    print(f"Reading: {args.file}")
    records = extract_records(args.file)
    print(f"Extracted {len(records)} price records")

    if args.dry_run:
        for r in records[:5]:
            print(r)
        print("... dry run, not inserting.")
        return

    uri = get_uri(args.from_secrets)
    client = MongoClient(uri)
    db = client['price_tracker']
    col = db['prices']

    # Remove previous seed data to avoid duplicates on re-run
    del_result = col.delete_many({'user_hash': 'seed_data'})
    print(f"Removed {del_result.deleted_count} previous seed records")

    result = col.insert_many(records)
    print(f"Inserted {len(result.inserted_ids)} records into prices collection")

    # Also ensure items collection has these items
    items_col = db['items']
    seen = {}
    for r in records:
        name = r['item_name']
        if name not in seen:
            seen[name] = r['category']

    ins = 0
    for name, cat in seen.items():
        res = items_col.update_one(
            {'name': name},
            {'$setOnInsert': {
                'name': name,
                'category': cat,
                'aliases': [name.lower()],
                'unit_default': 'each',
            }},
            upsert=True,
        )
        if res.upserted_id:
            ins += 1

    print(f"Added {ins} new items to items collection ({len(seen)} unique items total)")
    print("Done!")


if __name__ == '__main__':
    main()
