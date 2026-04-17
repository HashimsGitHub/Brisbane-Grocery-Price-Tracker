"""
purge_2025_data.py  –  Remove corrupted 2025 seed data from MongoDB
────────────────────────────────────────────────────────────────────
The Expense_Tracker_2025.xlsx file contains basket-level store totals,
NOT individual item prices. Any records seeded from it are invalid and
must be removed.

Usage:
    python purge_2025_data.py --from-secrets
    MONGO_URI="..." python purge_2025_data.py
    python purge_2025_data.py --from-secrets --dry-run
"""

import os, sys, argparse
from pymongo import MongoClient


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
    parser.add_argument('--from-secrets', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    uri = get_uri(args.from_secrets)
    db  = MongoClient(uri)['price_tracker']

    # Match any record that came from the 2025 file (by source tag or by date range
    # combined with user_hash='seed_data' — covers both tagging conventions)
    query = {
        "$or": [
            {"source": "Expense_Tracker_2025.xlsx"},
            {"source": {"$regex": "2025", "$options": "i"}},
            # Seed records from 2025 calendar year (user_hash='seed_data' + year=2025)
            {
                "user_hash": "seed_data",
                "submitted_at": {
                    "$gte": __import__('datetime').datetime(2025, 1, 1),
                    "$lt":  __import__('datetime').datetime(2026, 1, 1),
                }
            },
        ]
    }

    count = db['prices'].count_documents(query)
    print(f"Found {count} records matching 2025 seed data criteria.")

    if count == 0:
        print("Nothing to delete. Database is clean.")
        return

    # Show a sample before deleting
    print("\nSample records to be deleted:")
    for doc in db['prices'].find(query, {"item_name": 1, "price": 1, "store": 1, "submitted_at": 1, "source": 1}).limit(10):
        print(f"  {doc.get('submitted_at','?'):%Y-%m-%d} | {doc.get('item_name','?'):30s} | ${doc.get('price',0):7.2f} | {doc.get('store','?')} | source={doc.get('source','?')}")

    if args.dry_run:
        print(f"\nDry run — would delete {count} records. Re-run without --dry-run to apply.")
        return

    confirm = input(f"\nDelete {count} records? [y/N] ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    deleted = db['prices'].delete_many(query).deleted_count
    print(f"Deleted {deleted} records.")


if __name__ == '__main__':
    main()
