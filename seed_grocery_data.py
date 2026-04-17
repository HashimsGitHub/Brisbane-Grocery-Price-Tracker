"""
Seed MongoDB with grocery price data from Expense_Tracker_2024.xlsx
(per-item breakdown, Jun-Sep 2024 — 412 records)

Note: 2025 data is basket-level totals only (not itemised) so it is excluded.

Usage:
    MONGO_URI="..." python seed_grocery_data.py --file Expense_Tracker_2024.xlsx
    python seed_grocery_data.py --file Expense_Tracker_2024.xlsx --from-secrets
    python seed_grocery_data.py --file Expense_Tracker_2024.xlsx --dry-run
"""

import os, sys, argparse
from datetime import datetime
import pandas as pd
from pymongo import MongoClient

CATEGORY_MAP = {
    'Bread':'Bakery','Amin Bhai Roti':'Bakery','Bread Crumb':'Bakery',
    'Baking powder':'Pantry','Baking Paper':'Pantry',
    'Milk 1l':'Dairy','Milk 2L':'Dairy','Milk 3l':'Dairy',
    'Eggs 18':'Dairy','Eggs 12':'Dairy','Eggs liquid':'Dairy',
    'Butter':'Dairy','Cheese':'Dairy',
    'Chicken Maryland':'Meat','Chicken Drumsticks':'Meat',
    'Chicken Curry pcs':'Meat','Chicken Whole':'Meat','Chicken Breast':'Meat',
    'Chicken Seekh':'Meat','Chicken Qorma':'Meat','Qeema':'Meat',
    'Mutton':'Meat','Beef':'Meat','Mince':'Meat',
    'Bananas':'Produce','Apple':'Produce','Tomatoes':'Produce',
    'Carrots':'Produce','Potatoes':'Produce','Capsicum':'Produce',
    'Cabbage':'Produce','Cauliflower':'Produce','Celery Stick':'Produce',
    'Spinach':'Produce','Ginger':'Produce','Garlic':'Produce',
    'Onion':'Produce','Lemon':'Produce','Black lemon':'Produce',
    'Rice 5kg':'Pantry','Rice 10kg':'Pantry','Aata 5kg':'Pantry',
    'Barlley Flour':'Pantry','Olive Oil':'Pantry','Almond Raw':'Pantry',
    'Baked beans':'Pantry','Water':'Drinks','Apple Juice':'Drinks',
    'Toiler Cleaner':'Toiletries','Handsoap':'Toiletries','Shampoo':'Toiletries',
    'Conditioner':'Toiletries','Bodywash':'Toiletries','Veet':'Toiletries',
    'Toilet Wipes':'Toiletries','Razor Blades':'Toiletries','Extra pad':'Toiletries',
    'Nivea Moisture':'Toiletries','Electric Toothbrish':'Toiletries',
    'Smiles Herbal Toothpaste':'Toiletries','Smiles Toothpaste':'Toiletries',
    'Air Freshner':'Cleaning','Cotton Buds 200pc':'Toiletries',
    'Disinfectant':'Cleaning','Vasiline':'Toiletries','Wet Wipes':'Toiletries',
}

SHEET_MAP = {
    'Grocery JUNE':       (6, 2024),
    'Grocery JULY':       (7, 2024),
    'Grocery AUGUST':     (8, 2024),
    'Grocery SEPTEMEBER': (9, 2024),
}


def _is_num(val):
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def extract(filepath):
    records = []
    for sheet_name, (month_num, year) in SHEET_MAP.items():
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
        day_row = df.iloc[1]
        day_cols = {}
        for col_idx in range(2, len(day_row)):
            try:
                day = int(float(day_row.iloc[col_idx]))
                if 1 <= day <= 31:
                    day_cols[col_idx] = day
            except (ValueError, TypeError):
                pass

        current_category = 'General'
        for row_idx in range(3, len(df)):
            item_name = str(df.iloc[row_idx, 0]).strip()
            if item_name in ('nan', '', 'NaN'):
                continue

            row_prices = [float(df.iloc[row_idx, c]) for c in day_cols
                          if _is_num(df.iloc[row_idx, c]) and float(df.iloc[row_idx, c]) > 0]
            if not row_prices:
                current_category = item_name
                continue

            unit_raw = str(df.iloc[row_idx, 1]).strip()
            unit = 'kg' if unit_raw == 'kg' else ('L' if unit_raw in ('L', 'l') else 'each')
            category = CATEGORY_MAP.get(item_name, current_category)

            for col_idx, day in day_cols.items():
                val = df.iloc[row_idx, col_idx]
                if _is_num(val) and float(val) > 0:
                    try:
                        records.append({
                            'item_name': item_name,
                            'price': round(float(val), 2),
                            'unit': unit,
                            'store': 'Unknown',
                            'suburb': 'Brisbane CBD',
                            'state': 'QLD',
                            'category': category,
                            'submitted_at': datetime(year, month_num, day),
                            'user_hash': 'seed_data',
                            'source': 'Expense_Tracker_2024.xlsx',
                        })
                    except ValueError:
                        pass
    return records


def get_uri(from_secrets):
    if from_secrets:
        try:
            import toml
            return toml.load('.streamlit/secrets.toml')['MONGO_URI']
        except Exception as e:
            print(f"Could not read secrets.toml: {e}"); sys.exit(1)
    uri = os.environ.get('MONGO_URI', '')
    if not uri:
        print("Set MONGO_URI env var or use --from-secrets"); sys.exit(1)
    return uri


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default='Expense_Tracker_2024.xlsx')
    parser.add_argument('--from-secrets', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}"); sys.exit(1)

    print(f"Reading: {args.file}")
    records = extract(args.file)
    print(f"Extracted {len(records)} records")

    if args.dry_run:
        for r in records[:5]: print(r)
        print("Dry run — not inserting."); return

    uri = get_uri(args.from_secrets)
    db = MongoClient(uri)['price_tracker']

    deleted = db['prices'].delete_many({'user_hash': 'seed_data'}).deleted_count
    print(f"Removed {deleted} previous seed records")

    inserted = 0
    for i in range(0, len(records), 50):
        batch = records[i:i+50]
        try:
            result = db['prices'].insert_many(batch)
            inserted += len(result.inserted_ids)
        except Exception as e:
            print(f"Error on batch {i//50}: {e}")
    print(f"Inserted {inserted} records")

    seen = {r['item_name']: r['category'] for r in records}
    new_items = sum(
        1 for name, cat in seen.items()
        if db['items'].update_one(
            {'name': name},
            {'$setOnInsert': {'name': name, 'category': cat, 'aliases': [name.lower()], 'unit_default': 'each'}},
            upsert=True).upserted_id
    )
    print(f"Added {new_items} new items to items collection")

    by_month = {}
    for r in records:
        k = r['submitted_at'].strftime('%Y-%m')
        by_month[k] = by_month.get(k, 0) + 1
    print("\nSummary by month:")
    for m in sorted(by_month):
        print(f"  {m}: {by_month[m]} records")


if __name__ == '__main__':
    main()
