"""
Seed MongoDB with grocery price data from either:
  - Expense_Tracker_2024.xlsx  (per-item breakdown, Jun-Sep 2024)
  - Expense_Tracker_2025.xlsx  (store transactions, Jan-Apr 2025)

Usage:
    MONGO_URI="..." python seed_grocery_data.py --file Expense_Tracker_2024.xlsx
    MONGO_URI="..." python seed_grocery_data.py --file2025 Expense_Tracker_2025.xlsx
    MONGO_URI="..." python seed_grocery_data.py --file Expense_Tracker_2024.xlsx --file2025 Expense_Tracker_2025.xlsx
    python seed_grocery_data.py --file Expense_Tracker_2024.xlsx --from-secrets
"""

import os, sys, argparse
from datetime import datetime
import pandas as pd
from pymongo import MongoClient

CATEGORY_MAP_2024 = {
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

SHEET_MAP_2024 = {
    'Grocery JUNE':(6,2024),'Grocery JULY':(7,2024),
    'Grocery AUGUST':(8,2024),'Grocery SEPTEMEBER':(9,2024),
}

GROCERY_STORES_2025 = {
    'woolworths':'Woolworths','coles':'Coles','aldi':'ALDI','costco':'Costco',
    'harris farm':'Harris Farm','iga':'IGA','pa halal':'PA Halal Butcher',
    'hamid bakery':'Hamid Bakery','burmese store':'Burmese Store',
    'fruit depot':'The Fruit Depot','fruity capers':'Fruity Capers Deli',
    'ferny way':'Ferny Way Bakery','foodtown':'Foodtown','coco':'Coco Annerly',
    'sunlit asian':'Sunlit Asian Supermarket','bosnia masjid':'Bosnia Masjid Bakery',
    'mcwhirters':'McWhirters Farmers Market','woodrige':'Woodridge Store',
    'hanaro':'Hanaro Mart','noori':'Noori Fresh Butcher',
    'banana fruit':'Banana Fruit Barn','kmart':'Kmart','bigw':'BigW',
}

STORE_SUBURB_2025 = {
    'Woolworths':'Brisbane CBD','Coles':'Brisbane CBD','ALDI':'Brisbane CBD',
    'Costco':'North Lakes','Harris Farm':'West End','PA Halal Butcher':'Woodridge',
    'Hamid Bakery':'Woodridge','The Fruit Depot':'South Brisbane',
    'Coco Annerly':'Annerley','Fruity Capers Deli':'Spring Hill',
    'McWhirters Farmers Market':'Fortitude Valley','Burmese Store':'Woodridge',
    'Ferny Way Bakery':'Ferny Grove','Hanaro Mart':'Sunnybank',
    'Woodridge Store':'Woodridge','Bosnia Masjid Bakery':'West End',
    'Noori Fresh Butcher':'Woodridge','Banana Fruit Barn':'Sunnybank',
}

SUBURB_OVERRIDES_2025 = {
    'spring hill':'Spring Hill','macarthur':'Macarthur','buranda':'Woolloongabba',
    'fortitude':'Fortitude Valley','upper mt':'Upper Mount Gravatt',
    'annerley':'Annerley','toowong':'Toowong','local':'Brisbane CBD','metro':'Brisbane CBD',
}

SHEET_MAP_2025 = {
    'JAN expense ':(1,2025),'FEB expense':(2,2025),
    'MAR expense ':(3,2025),'APR expense ':(4,2025),
}


def extract_2024(filepath):
    records = []
    for sheet_name,(month_num,year) in SHEET_MAP_2024.items():
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
            if item_name in ('nan','','NaN'):
                continue
            row_prices = [float(df.iloc[row_idx,c]) for c in day_cols
                          if pd.notna(df.iloc[row_idx,c]) and float(df.iloc[row_idx,c]) > 0
                          if _is_num(df.iloc[row_idx,c])]
            if not row_prices:
                current_category = item_name
                continue
            unit_raw = str(df.iloc[row_idx, 1]).strip()
            unit = 'kg' if unit_raw=='kg' else ('L' if unit_raw in ('L','l') else 'each')
            category = CATEGORY_MAP_2024.get(item_name, current_category)
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


def extract_2025(filepath):
    records = []
    for sheet_name,(month_num,year) in SHEET_MAP_2025.items():
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
        for row_idx in range(2, len(df)):
            store_val  = df.iloc[row_idx, 13]
            date_val   = df.iloc[row_idx, 14]
            price_val  = df.iloc[row_idx, 15]
            if pd.isna(store_val) or not _is_num(price_val):
                continue
            store_str = str(store_val).strip()
            if store_str in ('nan','','NaN','Date','Groceries (JointANZ)'):
                continue
            if any(x in store_str.upper() for x in ('TOTAL','BUDGET','GROCERIES')):
                continue
            price = float(price_val)
            if price <= 0:
                continue
            try:
                txn_date = date_val if isinstance(date_val, datetime) else pd.to_datetime(date_val).to_pydatetime()
                if txn_date.year not in (2024,2025):
                    txn_date = datetime(year, month_num, 15)
            except Exception:
                txn_date = datetime(year, month_num, 15)
            store_lower = store_str.lower()
            matched = store_str
            for key, canonical in GROCERY_STORES_2025.items():
                if key in store_lower:
                    matched = canonical
                    break
            suburb = STORE_SUBURB_2025.get(matched, 'Brisbane CBD')
            for key, sub in SUBURB_OVERRIDES_2025.items():
                if key in store_lower:
                    suburb = sub
                    break
            if any(x in store_lower for x in ['woolworths','coles','aldi','costco','iga','foodtown','hanaro','sunlit']):
                category = 'Supermarket'
            elif any(x in store_lower for x in ['halal','butcher','bakery','burmese','fruit','coco','fruity','mcwhirters','woodrige','harris','noori','banana']):
                category = 'Specialty Grocery'
            else:
                category = 'Grocery'
            records.append({
                'item_name': f'Grocery shop — {matched}',
                'price': round(price, 2),
                'unit': 'basket',
                'store': matched,
                'suburb': suburb,
                'state': 'QLD',
                'category': category,
                'submitted_at': txn_date,
                'user_hash': 'seed_data',
                'source': 'Expense_Tracker_2025.xlsx',
            })
    return records


def _is_num(val):
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def get_uri(from_secrets):
    if from_secrets:
        try:
            import toml
            return toml.load('.streamlit/secrets.toml')['MONGO_URI']
        except Exception as e:
            print(f"Could not read secrets.toml: {e}"); sys.exit(1)
    uri = os.environ.get('MONGO_URI','')
    if not uri:
        print("Set MONGO_URI env var or use --from-secrets"); sys.exit(1)
    return uri


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default=None, help='Path to Expense_Tracker_2024.xlsx')
    parser.add_argument('--file2025', default=None, help='Path to Expense_Tracker_2025.xlsx')
    parser.add_argument('--from-secrets', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    all_records = []

    if args.file and os.path.exists(args.file):
        print(f"Reading 2024 data: {args.file}")
        r = extract_2024(args.file)
        print(f"  -> {len(r)} item-level price records")
        all_records.extend(r)
    elif args.file:
        print(f"File not found: {args.file}")

    if args.file2025 and os.path.exists(args.file2025):
        print(f"Reading 2025 data: {args.file2025}")
        r = extract_2025(args.file2025)
        print(f"  -> {len(r)} grocery transaction records")
        all_records.extend(r)
    elif args.file2025:
        print(f"File not found: {args.file2025}")

    if not all_records:
        print("No records extracted. Pass --file and/or --file2025."); return

    print(f"\nTotal records: {len(all_records)}")

    if args.dry_run:
        for r in all_records[:5]: print(r)
        print("Dry run — not inserting."); return

    uri = get_uri(args.from_secrets)
    db = MongoClient(uri)['price_tracker']

    deleted = db['prices'].delete_many({'user_hash':'seed_data'}).deleted_count
    print(f"Removed {deleted} previous seed records")

    db['prices'].insert_many(all_records)
    print(f"Inserted {len(all_records)} records")

    seen = {r['item_name']: r['category'] for r in all_records}
    new_items = sum(
        1 for name, cat in seen.items()
        if db['items'].update_one({'name':name},
            {'$setOnInsert':{'name':name,'category':cat,'aliases':[name.lower()],'unit_default':'each'}},
            upsert=True).upserted_id
    )
    print(f"Added {new_items} new items to items collection")

    by_month = {}
    for r in all_records:
        k = r['submitted_at'].strftime('%Y-%m')
        by_month[k] = by_month.get(k,0) + 1
    print("\nSummary by month:")
    for m in sorted(by_month):
        print(f"  {m}: {by_month[m]} records")

if __name__ == '__main__':
    main()
