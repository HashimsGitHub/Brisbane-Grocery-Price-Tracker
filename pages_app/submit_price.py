import streamlit as st
import hashlib
from datetime import datetime
from difflib import get_close_matches

# QLD suburbs seed list (expand as needed)
QLD_SUBURBS = [
    "Brisbane CBD", "South Brisbane", "Fortitude Valley", "West End", "Woolloongabba",
    "Paddington", "Kelvin Grove", "Toowong", "St Lucia", "Indooroopilly",
    "Carindale", "Mount Gravatt", "Sunnybank", "Springwood", "Logan Central",
    "Beenleigh", "Ipswich", "Redbank Plains", "Springfield", "Brookwater",
    "Chermside", "Aspley", "Stafford", "Kedron", "Nundah",
    "Sandgate", "Redcliffe", "Strathpine", "Kallangur", "Petrie",
    "Caboolture", "Morayfield", "Narangba",
    "Gold Coast CBD", "Surfers Paradise", "Broadbeach", "Burleigh Heads",
    "Robina", "Coomera", "Nerang", "Helensvale",
    "Sunshine Coast", "Maroochydore", "Caloundra", "Noosa Heads",
    "Toowoomba", "Townsville", "Cairns", "Rockhampton", "Mackay",
]

STORES = [
    "Woolworths", "Coles", "ALDI", "IGA", "Costco",
    "Harris Farm", "Drakes", "Foodworks",
    "7-Eleven", "BP", "Caltex / Ampol", "Shell / Viva Energy",
    "United Petroleum", "Liberty Oil", "Metro Petroleum", "Puma Energy",
    "Other",
]

STATES = ["QLD", "NSW", "VIC", "WA", "SA", "TAS", "ACT", "NT"]


def fuzzy_match_item(query: str, all_items: list[dict]) -> str | None:
    """Return canonical item name from fuzzy match against names + aliases."""
    query_lower = query.strip().lower()
    all_terms = {}
    for item in all_items:
        all_terms[item["name"].lower()] = item["name"]
        for alias in item.get("aliases", []):
            all_terms[alias.lower()] = item["name"]

    # Exact match first
    if query_lower in all_terms:
        return all_terms[query_lower]

    # Fuzzy match
    matches = get_close_matches(query_lower, all_terms.keys(), n=1, cutoff=0.6)
    if matches:
        return all_terms[matches[0]]
    return None


def show(db):
    st.title("📝 Submit a Price")
    st.caption("Help the community by submitting a price you've seen today.")

    all_items = list(db["items"].find({}, {"_id": 0}))
    item_names = sorted([i["name"] for i in all_items])
    categories = sorted(set(i["category"] for i in all_items))

    with st.form("submit_price_form", clear_on_submit=True):
        st.subheader("What did you buy?")

        col1, col2 = st.columns([2, 1])
        with col1:
            # Allow picking from list OR typing custom
            item_mode = st.radio("Item entry", ["Pick from list", "Type custom name"], horizontal=True)
            if item_mode == "Pick from list":
                category_filter = st.selectbox("Category", ["All"] + categories)
                filtered = item_names if category_filter == "All" else [
                    i["name"] for i in all_items if i["category"] == category_filter
                ]
                item_input = st.selectbox("Item", filtered)
            else:
                item_input = st.text_input("Item name", placeholder="e.g. Organic oat milk 1L")

        with col2:
            price = st.number_input("Price ($)", min_value=0.01, max_value=9999.0, step=0.01, format="%.2f")
            unit = st.selectbox("Unit", ["each", "kg", "L", "100g", "100ml"])

        st.subheader("Where did you buy it?")
        col3, col4 = st.columns(2)
        with col3:
            store = st.selectbox("Store / service station", STORES)
        with col4:
            state = st.selectbox("State", STATES, index=0)

        suburb_input = st.selectbox(
            "Suburb",
            options=[""] + sorted(QLD_SUBURBS),
            help="Can't find your suburb? Type it in the box above and select 'Other'.",
        )
        custom_suburb = st.text_input("Or type suburb manually (if not listed)", placeholder="e.g. Kenmore")

        st.caption("Your submission is anonymous. We store a one-way hash so you can't submit the same item twice in 1 hour.")

        submitted = st.form_submit_button("Submit price", type="primary", width="stretch")

    if submitted:
        suburb = custom_suburb.strip() if custom_suburb.strip() else suburb_input
        if not suburb:
            st.error("Please select or enter a suburb.")
            return
        if not item_input:
            st.error("Please enter an item name.")
            return

        # Fuzzy-match to canonical name (or keep as-is for custom)
        canonical = fuzzy_match_item(item_input, all_items)
        final_item = canonical if canonical else item_input.strip()

        # Anonymous user hash (IP-ish — uses session id as proxy)
        session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id
        user_hash = hashlib.sha256(session_id.encode()).hexdigest()[:16]

        # Duplicate check: same user, same item, within 1 hour
        from datetime import timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        dup = db["prices"].find_one({
            "user_hash": user_hash,
            "item_name": final_item,
            "submitted_at": {"$gte": one_hour_ago},
        })
        if dup:
            st.warning("You already submitted this item in the last hour. Thanks!")
            return

        # Look up suburb lat/lng
        suburb_doc = db["suburbs"].find_one({"name": suburb})
        lat = suburb_doc["lat"] if suburb_doc else None
        lng = suburb_doc["lng"] if suburb_doc else None

        doc = {
            "item_name": final_item,
            "price": round(price, 2),
            "unit": unit,
            "store": store,
            "suburb": suburb,
            "state": state,
            "submitted_at": datetime.utcnow(),
            "user_hash": user_hash,
        }
        if lat and lng:
            doc["lat"] = lat
            doc["lng"] = lng
            doc["location"] = {"type": "Point", "coordinates": [lng, lat]}

        db["prices"].insert_one(doc)

        # If new item, add to items collection
        if not canonical:
            db["items"].update_one(
                {"name": final_item},
                {"$setOnInsert": {"name": final_item, "category": "Other", "aliases": [], "unit_default": unit}},
                upsert=True,
            )

        st.success(f"✅ Submitted **{final_item}** at **${price:.2f}** from **{store}, {suburb}**. Thank you!")
        st.balloons()
