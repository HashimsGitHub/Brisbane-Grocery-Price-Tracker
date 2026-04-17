"""
Run once to seed the suburbs collection with lat/lng coordinates.
Usage: python seed_suburbs.py
(Make sure your .streamlit/secrets.toml has MONGO_URI set first)
"""
import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "")  # or paste directly for one-time run

SUBURBS = [
    {"name": "Brisbane CBD",    "state": "QLD", "postcode": "4000", "lat": -27.4698,  "lng": 153.0251},
    {"name": "South Brisbane",  "state": "QLD", "postcode": "4101", "lat": -27.4820,  "lng": 153.0187},
    {"name": "Fortitude Valley","state": "QLD", "postcode": "4006", "lat": -27.4562,  "lng": 153.0339},
    {"name": "West End",        "state": "QLD", "postcode": "4101", "lat": -27.4815,  "lng": 153.0111},
    {"name": "Woolloongabba",   "state": "QLD", "postcode": "4102", "lat": -27.4906,  "lng": 153.0345},
    {"name": "Paddington",      "state": "QLD", "postcode": "4064", "lat": -27.4594,  "lng": 152.9963},
    {"name": "Kelvin Grove",    "state": "QLD", "postcode": "4059", "lat": -27.4479,  "lng": 152.9993},
    {"name": "Toowong",         "state": "QLD", "postcode": "4066", "lat": -27.4844,  "lng": 152.9816},
    {"name": "St Lucia",        "state": "QLD", "postcode": "4067", "lat": -27.4977,  "lng": 153.0026},
    {"name": "Indooroopilly",   "state": "QLD", "postcode": "4068", "lat": -27.5022,  "lng": 152.9749},
    {"name": "Carindale",       "state": "QLD", "postcode": "4152", "lat": -27.5019,  "lng": 153.1018},
    {"name": "Mount Gravatt",   "state": "QLD", "postcode": "4122", "lat": -27.5436,  "lng": 153.0779},
    {"name": "Sunnybank",       "state": "QLD", "postcode": "4109", "lat": -27.5766,  "lng": 153.0550},
    {"name": "Springwood",      "state": "QLD", "postcode": "4127", "lat": -27.6126,  "lng": 153.1063},
    {"name": "Logan Central",   "state": "QLD", "postcode": "4114", "lat": -27.6394,  "lng": 153.1083},
    {"name": "Beenleigh",       "state": "QLD", "postcode": "4207", "lat": -27.7135,  "lng": 153.1978},
    {"name": "Ipswich",         "state": "QLD", "postcode": "4305", "lat": -27.6144,  "lng": 152.7600},
    {"name": "Redbank Plains",  "state": "QLD", "postcode": "4301", "lat": -27.6367,  "lng": 152.8534},
    {"name": "Springfield",     "state": "QLD", "postcode": "4300", "lat": -27.6571,  "lng": 152.9162},
    {"name": "Chermside",       "state": "QLD", "postcode": "4032", "lat": -27.3877,  "lng": 153.0307},
    {"name": "Aspley",          "state": "QLD", "postcode": "4034", "lat": -27.3682,  "lng": 153.0241},
    {"name": "Nundah",          "state": "QLD", "postcode": "4012", "lat": -27.4013,  "lng": 153.0683},
    {"name": "Sandgate",        "state": "QLD", "postcode": "4017", "lat": -27.3302,  "lng": 153.0697},
    {"name": "Redcliffe",       "state": "QLD", "postcode": "4020", "lat": -27.2305,  "lng": 153.1023},
    {"name": "Strathpine",      "state": "QLD", "postcode": "4500", "lat": -27.2974,  "lng": 152.9881},
    {"name": "Kallangur",       "state": "QLD", "postcode": "4503", "lat": -27.2503,  "lng": 152.9874},
    {"name": "Caboolture",      "state": "QLD", "postcode": "4510", "lat": -27.0772,  "lng": 152.9511},
    {"name": "Gold Coast CBD",  "state": "QLD", "postcode": "4217", "lat": -28.0167,  "lng": 153.4000},
    {"name": "Surfers Paradise","state": "QLD", "postcode": "4217", "lat": -27.9927,  "lng": 153.4303},
    {"name": "Broadbeach",      "state": "QLD", "postcode": "4218", "lat": -28.0283,  "lng": 153.4312},
    {"name": "Robina",          "state": "QLD", "postcode": "4226", "lat": -28.0787,  "lng": 153.3793},
    {"name": "Sunshine Coast",  "state": "QLD", "postcode": "4557", "lat": -26.6500,  "lng": 153.0667},
    {"name": "Maroochydore",    "state": "QLD", "postcode": "4558", "lat": -26.6538,  "lng": 153.0997},
    {"name": "Noosa Heads",     "state": "QLD", "postcode": "4567", "lat": -26.3927,  "lng": 153.0958},
    {"name": "Toowoomba",       "state": "QLD", "postcode": "4350", "lat": -27.5598,  "lng": 151.9507},
    {"name": "Townsville",      "state": "QLD", "postcode": "4810", "lat": -19.2576,  "lng": 146.8178},
    {"name": "Cairns",          "state": "QLD", "postcode": "4870", "lat": -16.9203,  "lng": 145.7710},
    {"name": "Rockhampton",     "state": "QLD", "postcode": "4700", "lat": -23.3792,  "lng": 150.5100},
    {"name": "Mackay",          "state": "QLD", "postcode": "4740", "lat": -21.1411,  "lng": 149.1861},
]


def seed():
    if not MONGO_URI:
        print("Set MONGO_URI env var first.")
        return
    client = MongoClient(MONGO_URI)
    db = client["price_tracker"]
    col = db["suburbs"]
    inserted = 0
    for s in SUBURBS:
        result = col.update_one(
            {"name": s["name"], "state": s["state"]},
            {"$setOnInsert": s},
            upsert=True,
        )
        if result.upserted_id:
            inserted += 1
    print(f"Done. {inserted} suburbs inserted, {len(SUBURBS) - inserted} already existed.")


if __name__ == "__main__":
    seed()
