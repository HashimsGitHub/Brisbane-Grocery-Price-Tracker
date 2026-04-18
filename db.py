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

    # TTL index: retain price records for 5 years
    try:
        prices.drop_index("ttl_6months")
    except Exception:
        pass
    prices.create_index(
        [("submitted_at", ASCENDING)],
        expireAfterSeconds=60 * 60 * 24 * 365 * 5,
        name="ttl_5years",
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
    """Insert canonical item list if collection is empty.

    Items are common groceries stocked by both Woolworths and Coles in Australia.
    Aliases are the search terms used by the auto-scraper and fuzzy matcher.
    """
    if db["items"].count_documents({}) > 0:
        return

    seed = [

        # ── Dairy & Eggs ────────────────────────────────────────────────────
        {"name": "Full Cream Milk 2L",       "category": "Dairy",   "unit_default": "each", "aliases": ["full cream milk", "whole milk", "2l milk", "milk 2l"]},
        {"name": "Skim Milk 2L",             "category": "Dairy",   "unit_default": "each", "aliases": ["skim milk", "skimmed milk", "light milk 2l"]},
        {"name": "Lite Milk 2L",             "category": "Dairy",   "unit_default": "each", "aliases": ["lite milk", "low fat milk", "2l lite"]},
        {"name": "Almond Milk 1L",           "category": "Dairy",   "unit_default": "each", "aliases": ["almond milk", "almond drink"]},
        {"name": "Oat Milk 1L",              "category": "Dairy",   "unit_default": "each", "aliases": ["oat milk", "oat drink"]},
        {"name": "Free Range Eggs 12pk",     "category": "Dairy",   "unit_default": "each", "aliases": ["free range eggs", "eggs 12", "dozen eggs", "12 eggs"]},
        {"name": "Cage Eggs 12pk",           "category": "Dairy",   "unit_default": "each", "aliases": ["cage eggs", "eggs", "12pk eggs"]},
        {"name": "Cheddar Cheese 500g",      "category": "Dairy",   "unit_default": "each", "aliases": ["cheddar cheese", "tasty cheese", "cheese 500g", "block cheese"]},
        {"name": "Shredded Mozzarella 250g", "category": "Dairy",   "unit_default": "each", "aliases": ["mozzarella", "shredded cheese", "pizza cheese", "grated mozzarella"]},
        {"name": "Butter 500g",              "category": "Dairy",   "unit_default": "each", "aliases": ["butter", "unsalted butter", "salted butter"]},
        {"name": "Greek Yoghurt 500g",       "category": "Dairy",   "unit_default": "each", "aliases": ["greek yoghurt", "greek yogurt", "natural yoghurt"]},
        {"name": "Sour Cream 300ml",         "category": "Dairy",   "unit_default": "each", "aliases": ["sour cream"]},
        {"name": "Thickened Cream 300ml",    "category": "Dairy",   "unit_default": "each", "aliases": ["thickened cream", "heavy cream", "cooking cream"]},

        # ── Bakery ──────────────────────────────────────────────────────────
        {"name": "White Bread Loaf 700g",    "category": "Bakery",  "unit_default": "each", "aliases": ["white bread", "bread loaf", "sliced white bread", "sandwich bread"]},
        {"name": "Wholemeal Bread 700g",     "category": "Bakery",  "unit_default": "each", "aliases": ["wholemeal bread", "whole wheat bread", "brown bread"]},
        {"name": "Sourdough Loaf",           "category": "Bakery",  "unit_default": "each", "aliases": ["sourdough", "sourdough bread", "sourdough loaf"]},
        {"name": "Croissants 4pk",           "category": "Bakery",  "unit_default": "each", "aliases": ["croissants", "croissant 4 pack"]},
        {"name": "Plain Flour 1kg",          "category": "Bakery",  "unit_default": "each", "aliases": ["plain flour", "all purpose flour", "flour 1kg"]},
        {"name": "Self Raising Flour 1kg",   "category": "Bakery",  "unit_default": "each", "aliases": ["self raising flour", "sr flour"]},

        # ── Meat & Seafood ───────────────────────────────────────────────────
        {"name": "Chicken Breast",           "category": "Meat",    "unit_default": "kg",   "aliases": ["chicken breast", "chicken fillet", "chicken breast fillet"]},
        {"name": "Chicken Thigh Fillets",    "category": "Meat",    "unit_default": "kg",   "aliases": ["chicken thigh", "thigh fillet", "chicken thighs"]},
        {"name": "Whole Chicken",            "category": "Meat",    "unit_default": "each", "aliases": ["whole chicken", "roast chicken", "fresh whole chicken"]},
        {"name": "Beef Mince 500g",          "category": "Meat",    "unit_default": "each", "aliases": ["beef mince", "mince", "ground beef", "mince meat"]},
        {"name": "Beef Sausages 1kg",        "category": "Meat",    "unit_default": "each", "aliases": ["beef sausages", "sausages", "snags", "bbq sausages"]},
        {"name": "Lamb Chops",               "category": "Meat",    "unit_default": "kg",   "aliases": ["lamb chops", "chump chops", "lamb cutlets"]},
        {"name": "Pork Mince 500g",          "category": "Meat",    "unit_default": "each", "aliases": ["pork mince", "ground pork"]},
        {"name": "Bacon Rashers 500g",       "category": "Meat",    "unit_default": "each", "aliases": ["bacon", "bacon rashers", "streaky bacon", "middle bacon"]},
        {"name": "Salmon Fillets",           "category": "Seafood", "unit_default": "kg",   "aliases": ["salmon", "salmon fillet", "atlantic salmon"]},
        {"name": "Barramundi Fillets",       "category": "Seafood", "unit_default": "kg",   "aliases": ["barramundi", "barra fillet"]},
        {"name": "Frozen Fish Fillets 400g", "category": "Seafood", "unit_default": "each", "aliases": ["fish fillets", "frozen fish", "battered fish"]},
        {"name": "Prawns 500g",              "category": "Seafood", "unit_default": "each", "aliases": ["prawns", "shrimp", "peeled prawns", "green prawns"]},

        # ── Deli ─────────────────────────────────────────────────────────────
        {"name": "Shaved Ham 200g",          "category": "Deli",    "unit_default": "each", "aliases": ["shaved ham", "leg ham", "sandwich ham"]},
        {"name": "Salami 100g",              "category": "Deli",    "unit_default": "each", "aliases": ["salami", "mild salami", "hot salami"]},

        # ── Fruit & Vegetables ───────────────────────────────────────────────
        {"name": "Bananas",                  "category": "Produce", "unit_default": "kg",   "aliases": ["bananas", "banana", "cavendish banana"]},
        {"name": "Apples 1kg",               "category": "Produce", "unit_default": "each", "aliases": ["apples", "red apples", "green apples", "pink lady", "granny smith"]},
        {"name": "Oranges 1kg",              "category": "Produce", "unit_default": "each", "aliases": ["oranges", "navel oranges", "orange bag"]},
        {"name": "Strawberries 250g",        "category": "Produce", "unit_default": "each", "aliases": ["strawberries", "strawberry punnet"]},
        {"name": "Blueberries 125g",         "category": "Produce", "unit_default": "each", "aliases": ["blueberries", "blueberry punnet"]},
        {"name": "Watermelon",               "category": "Produce", "unit_default": "each", "aliases": ["watermelon", "seedless watermelon"]},
        {"name": "Tomatoes",                 "category": "Produce", "unit_default": "kg",   "aliases": ["tomatoes", "tomato", "ripe tomatoes"]},
        {"name": "Potatoes 2kg",             "category": "Produce", "unit_default": "each", "aliases": ["potatoes", "spuds", "washed potatoes", "brushed potatoes"]},
        {"name": "Sweet Potato",             "category": "Produce", "unit_default": "kg",   "aliases": ["sweet potato", "kumara", "gold sweet potato"]},
        {"name": "Carrots 1kg",              "category": "Produce", "unit_default": "each", "aliases": ["carrots", "carrot", "carrot bag"]},
        {"name": "Broccoli",                 "category": "Produce", "unit_default": "each", "aliases": ["broccoli", "broccoli head"]},
        {"name": "Cauliflower",              "category": "Produce", "unit_default": "each", "aliases": ["cauliflower", "cauli"]},
        {"name": "Spinach 120g",             "category": "Produce", "unit_default": "each", "aliases": ["baby spinach", "spinach leaves", "spinach bag"]},
        {"name": "Iceberg Lettuce",          "category": "Produce", "unit_default": "each", "aliases": ["iceberg lettuce", "lettuce", "lettuce head"]},
        {"name": "Cucumber",                 "category": "Produce", "unit_default": "each", "aliases": ["cucumber", "lebanese cucumber", "continental cucumber"]},
        {"name": "Capsicum",                 "category": "Produce", "unit_default": "each", "aliases": ["capsicum", "red capsicum", "green capsicum", "bell pepper"]},
        {"name": "Brown Onions 1kg",         "category": "Produce", "unit_default": "each", "aliases": ["onions", "brown onions", "onion bag"]},
        {"name": "Garlic",                   "category": "Produce", "unit_default": "each", "aliases": ["garlic", "garlic bulb", "garlic loose"]},
        {"name": "Mushrooms 200g",           "category": "Produce", "unit_default": "each", "aliases": ["mushrooms", "cup mushrooms", "white mushrooms"]},
        {"name": "Zucchini",                 "category": "Produce", "unit_default": "kg",   "aliases": ["zucchini", "courgette"]},
        {"name": "Corn Cob",                 "category": "Produce", "unit_default": "each", "aliases": ["corn cob", "corn on the cob", "sweet corn"]},
        {"name": "Avocado",                  "category": "Produce", "unit_default": "each", "aliases": ["avocado", "hass avocado", "avo"]},
        {"name": "Lemon",                    "category": "Produce", "unit_default": "each", "aliases": ["lemon", "lemons"]},
        {"name": "Lime",                     "category": "Produce", "unit_default": "each", "aliases": ["lime", "limes"]},

        # ── Pantry ───────────────────────────────────────────────────────────
        {"name": "White Rice 1kg",           "category": "Pantry",  "unit_default": "each", "aliases": ["white rice", "long grain rice", "jasmine rice", "rice 1kg"]},
        {"name": "Basmati Rice 1kg",         "category": "Pantry",  "unit_default": "each", "aliases": ["basmati rice", "basmati 1kg"]},
        {"name": "Pasta 500g",               "category": "Pantry",  "unit_default": "each", "aliases": ["pasta", "spaghetti", "penne", "fettuccine", "pasta 500g"]},
        {"name": "Tinned Tomatoes 400g",     "category": "Pantry",  "unit_default": "each", "aliases": ["tinned tomatoes", "canned tomatoes", "crushed tomatoes", "diced tomatoes"]},
        {"name": "Baked Beans 420g",         "category": "Pantry",  "unit_default": "each", "aliases": ["baked beans", "heinz baked beans"]},
        {"name": "Chickpeas 400g",           "category": "Pantry",  "unit_default": "each", "aliases": ["chickpeas", "canned chickpeas", "garbanzo beans"]},
        {"name": "Lentils 400g",             "category": "Pantry",  "unit_default": "each", "aliases": ["lentils", "canned lentils", "red lentils", "brown lentils"]},
        {"name": "Olive Oil 750ml",          "category": "Pantry",  "unit_default": "each", "aliases": ["olive oil", "extra virgin olive oil", "evoo"]},
        {"name": "Vegetable Oil 750ml",      "category": "Pantry",  "unit_default": "each", "aliases": ["vegetable oil", "canola oil", "sunflower oil"]},
        {"name": "Tomato Sauce 500ml",       "category": "Pantry",  "unit_default": "each", "aliases": ["tomato sauce", "ketchup", "heinz tomato sauce"]},
        {"name": "Soy Sauce 250ml",          "category": "Pantry",  "unit_default": "each", "aliases": ["soy sauce", "light soy sauce"]},
        {"name": "Salt 1kg",                 "category": "Pantry",  "unit_default": "each", "aliases": ["salt", "table salt", "sea salt", "iodised salt"]},
        {"name": "Sugar 1kg",                "category": "Pantry",  "unit_default": "each", "aliases": ["sugar", "white sugar", "caster sugar", "raw sugar"]},
        {"name": "Honey 500g",               "category": "Pantry",  "unit_default": "each", "aliases": ["honey", "pure honey", "blended honey"]},
        {"name": "Vegemite 380g",            "category": "Pantry",  "unit_default": "each", "aliases": ["vegemite", "vegimite"]},
        {"name": "Peanut Butter 375g",       "category": "Pantry",  "unit_default": "each", "aliases": ["peanut butter", "smooth peanut butter", "crunchy peanut butter"]},
        {"name": "Strawberry Jam 375g",      "category": "Pantry",  "unit_default": "each", "aliases": ["jam", "strawberry jam", "raspberry jam"]},
        {"name": "Weet-Bix 750g",            "category": "Pantry",  "unit_default": "each", "aliases": ["weetbix", "weet-bix", "weetabix"]},
        {"name": "Rolled Oats 1kg",          "category": "Pantry",  "unit_default": "each", "aliases": ["rolled oats", "oats", "porridge oats", "quick oats"]},
        {"name": "Cornflakes 500g",          "category": "Pantry",  "unit_default": "each", "aliases": ["cornflakes", "corn flakes", "kelloggs cornflakes"]},
        {"name": "Milo 400g",                "category": "Pantry",  "unit_default": "each", "aliases": ["milo", "milo powder"]},
        {"name": "Instant Coffee 100g",      "category": "Pantry",  "unit_default": "each", "aliases": ["instant coffee", "nescafe", "coffee powder", "espresso"]},
        {"name": "Tea Bags 100pk",           "category": "Pantry",  "unit_default": "each", "aliases": ["tea bags", "black tea", "english breakfast tea", "tea 100 pack"]},
        {"name": "Breadcrumbs 250g",         "category": "Pantry",  "unit_default": "each", "aliases": ["breadcrumbs", "bread crumbs", "panko"]},
        {"name": "Chicken Stock 1L",         "category": "Pantry",  "unit_default": "each", "aliases": ["chicken stock", "chicken broth", "stock liquid"]},
        {"name": "Coconut Cream 400ml",      "category": "Pantry",  "unit_default": "each", "aliases": ["coconut cream", "coconut milk", "coconut cream 400ml"]},

        # ── Frozen ───────────────────────────────────────────────────────────
        {"name": "Frozen Peas 1kg",          "category": "Frozen",  "unit_default": "each", "aliases": ["frozen peas", "peas 1kg", "garden peas frozen"]},
        {"name": "Frozen Mixed Vegetables 1kg", "category": "Frozen", "unit_default": "each", "aliases": ["frozen vegetables", "mixed veg", "frozen mixed veg"]},
        {"name": "Frozen Chips 1kg",         "category": "Frozen",  "unit_default": "each", "aliases": ["frozen chips", "oven chips", "french fries", "chips 1kg"]},
        {"name": "Frozen Pizza",             "category": "Frozen",  "unit_default": "each", "aliases": ["frozen pizza", "pizza", "dr oetker", "frozen margherita"]},
        {"name": "Vanilla Ice Cream 2L",     "category": "Frozen",  "unit_default": "each", "aliases": ["ice cream", "vanilla ice cream", "ice cream 2l"]},

        # ── Snacks & Confectionery ───────────────────────────────────────────
        {"name": "Shapes 175g",              "category": "Snacks",  "unit_default": "each", "aliases": ["shapes", "arnotts shapes", "bbq shapes", "cheese shapes"]},
        {"name": "Tim Tams 200g",            "category": "Snacks",  "unit_default": "each", "aliases": ["tim tams", "timtam", "tim tam chocolate"]},
        {"name": "Chips 175g",               "category": "Snacks",  "unit_default": "each", "aliases": ["chips", "potato chips", "smiths chips", "grain waves"]},
        {"name": "Chocolate Block 200g",     "category": "Snacks",  "unit_default": "each", "aliases": ["chocolate block", "cadbury chocolate", "dairy milk", "chocolate 200g"]},
        {"name": "Muesli Bars 6pk",          "category": "Snacks",  "unit_default": "each", "aliases": ["muesli bars", "muesli bar", "oat bar", "snack bar"]},

        # ── Drinks ───────────────────────────────────────────────────────────
        {"name": "Orange Juice 2L",          "category": "Drinks",  "unit_default": "each", "aliases": ["orange juice", "oj", "fresh orange juice", "juice 2l"]},
        {"name": "Apple Juice 2L",           "category": "Drinks",  "unit_default": "each", "aliases": ["apple juice", "apple juice 2l"]},
        {"name": "Coca-Cola 1.25L",          "category": "Drinks",  "unit_default": "each", "aliases": ["coke", "coca cola", "coca-cola", "cola 1.25l"]},
        {"name": "Pepsi 1.25L",              "category": "Drinks",  "unit_default": "each", "aliases": ["pepsi", "pepsi cola", "pepsi 1.25l"]},
        {"name": "Sparkling Water 1.25L",    "category": "Drinks",  "unit_default": "each", "aliases": ["sparkling water", "mineral water", "soda water"]},
        {"name": "Still Water 600ml",        "category": "Drinks",  "unit_default": "each", "aliases": ["water bottle", "still water", "drinking water 600ml"]},
        {"name": "Beer 6pk",                 "category": "Drinks",  "unit_default": "each", "aliases": ["beer 6 pack", "six pack beer", "lager 6pk", "ale 6pk"]},
        {"name": "Wine 750ml",               "category": "Drinks",  "unit_default": "each", "aliases": ["wine", "red wine", "white wine", "table wine 750ml"]},

        # ── Bread & Spreads ──────────────────────────────────────────────────
        {"name": "Cream Cheese 250g",        "category": "Dairy",   "unit_default": "each", "aliases": ["cream cheese", "philadelphia", "philly cream cheese"]},
        {"name": "Hummus 200g",              "category": "Deli",    "unit_default": "each", "aliases": ["hummus", "houmous", "hommus dip"]},

        # ── Household Essentials ─────────────────────────────────────────────
        {"name": "Toilet Paper 12pk",        "category": "Household", "unit_default": "each", "aliases": ["toilet paper", "toilet rolls", "bathroom tissue", "tp 12 pack"]},
        {"name": "Paper Towels 2pk",         "category": "Household", "unit_default": "each", "aliases": ["paper towels", "kitchen towel", "paper towel roll"]},
        {"name": "Dishwashing Liquid 500ml", "category": "Household", "unit_default": "each", "aliases": ["dishwashing liquid", "dish soap", "washing up liquid", "morning fresh"]},
        {"name": "Laundry Powder 1kg",       "category": "Household", "unit_default": "each", "aliases": ["laundry powder", "washing powder", "laundry detergent"]},
        {"name": "Multipurpose Spray 500ml", "category": "Household", "unit_default": "each", "aliases": ["multipurpose spray", "surface spray", "cleaning spray", "ajax spray"]},

        # ── Health & Beauty ──────────────────────────────────────────────────
        {"name": "Shampoo 400ml",            "category": "Health",  "unit_default": "each", "aliases": ["shampoo", "hair shampoo", "pantene shampoo", "head shoulders"]},
        {"name": "Conditioner 400ml",        "category": "Health",  "unit_default": "each", "aliases": ["conditioner", "hair conditioner"]},
        {"name": "Body Wash 500ml",          "category": "Health",  "unit_default": "each", "aliases": ["body wash", "shower gel", "dove body wash"]},
        {"name": "Toothpaste 110g",          "category": "Health",  "unit_default": "each", "aliases": ["toothpaste", "colgate", "sensodyne", "oral b toothpaste"]},
        {"name": "Deodorant Roll-on",        "category": "Health",  "unit_default": "each", "aliases": ["deodorant", "roll on deodorant", "rexona", "dove deodorant"]},
        {"name": "Sunscreen SPF50 200ml",    "category": "Health",  "unit_default": "each", "aliases": ["sunscreen", "sunblock", "spf50 sunscreen", "cancer council sunscreen"]},
        {"name": "Paracetamol 500mg 20pk",   "category": "Health",  "unit_default": "each", "aliases": ["paracetamol", "panadol", "panadol 20", "pain relief"]},

        # ── Fuel ─────────────────────────────────────────────────────────────
        {"name": "Unleaded Petrol",          "category": "Fuel",    "unit_default": "L",    "aliases": ["unleaded", "91 unleaded", "e10", "regular petrol"]},
        {"name": "Premium Petrol",           "category": "Fuel",    "unit_default": "L",    "aliases": ["premium", "98 petrol", "95 petrol", "premium unleaded"]},
        {"name": "Diesel",                   "category": "Fuel",    "unit_default": "L",    "aliases": ["diesel", "highway diesel"]},

    ]

    db["items"].insert_many(seed)
