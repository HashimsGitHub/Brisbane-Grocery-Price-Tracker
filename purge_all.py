"""
purge_all.py  –  Wipe all prices AND items from MongoDB
────────────────────────────────────────────────────────
Clears:
  • prices      — every price entry (crowdsourced + auto-scraped + seeded)
  • items       — the entire canonical item list

The items list will be re-seeded automatically on next app startup
(db.py calls _seed_items on every cold start).

Usage:
    python purge_all.py --from-secrets            # uses .streamlit/secrets.toml
    MONGO_URI="..." python purge_all.py           # uses env var
    python purge_all.py --from-secrets --dry-run  # preview only, no deletions
"""

import os, sys, argparse
from pymongo import MongoClient


def get_uri(from_secrets: bool) -> str:
    if from_secrets:
        try:
            import toml
            return toml.load(".streamlit/secrets.toml")["MONGO_URI"]
        except Exception as e:
            print(f"Could not read secrets.toml: {e}"); sys.exit(1)
    uri = os.environ.get("MONGO_URI", "")
    if not uri:
        print("Set MONGO_URI env var or use --from-secrets"); sys.exit(1)
    return uri


def main():
    parser = argparse.ArgumentParser(description="Wipe all prices and items from MongoDB")
    parser.add_argument("--from-secrets", action="store_true",
                        help="Read MONGO_URI from .streamlit/secrets.toml")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show counts only — do not delete anything")
    args = parser.parse_args()

    uri = get_uri(args.from_secrets)
    db  = MongoClient(uri)["price_tracker"]

    # ── Count what's there ──────────────────────────────────────────────────
    n_prices = db["prices"].count_documents({})
    n_items  = db["items"].count_documents({})

    print("=" * 50)
    print("  PURGE SUMMARY")
    print("=" * 50)
    print(f"  prices collection : {n_prices:,} documents")
    print(f"  items  collection : {n_items:,} documents")
    print("=" * 50)

    if n_prices == 0 and n_items == 0:
        print("  Nothing to delete — database is already empty.")
        return

    if args.dry_run:
        print("  DRY RUN — no changes made.")
        print("  Re-run without --dry-run to delete.")
        return

    # ── Confirm ─────────────────────────────────────────────────────────────
    print("\n  ⚠️  This will permanently delete ALL prices and items.")
    print("  The items list will be re-seeded on next app startup.")
    confirm = input("\n  Type YES to confirm: ").strip()
    if confirm != "YES":
        print("  Aborted.")
        return

    # ── Delete ───────────────────────────────────────────────────────────────
    deleted_prices = db["prices"].delete_many({}).deleted_count
    deleted_items  = db["items"].delete_many({}).deleted_count

    print(f"\n  ✅ Deleted {deleted_prices:,} price records.")
    print(f"  ✅ Deleted {deleted_items:,} items.")
    print("\n  Items will be automatically re-seeded on next app startup.")
    print("  Done.")


if __name__ == "__main__":
    main()
