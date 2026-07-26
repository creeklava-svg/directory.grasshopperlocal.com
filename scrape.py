#!/usr/bin/env python3
"""Scrape business data from Google Places API for Iowa directory."""

import os, json, time, sys
from datetime import datetime

CITIES = [
    "Iowa City", "Burlington", "Fort Madison", "Keokuk",
    "Mt. Pleasant", "Fairfield", "Washington",
    "West Burlington", "Danville"
]

CITY_SLUGS = {
    "Iowa City": "iowa-city",
    "Burlington": "burlington-iowa",
    "Fort Madison": "fort-madison-iowa",
    "Keokuk": "keokuk-iowa",
    "Mt. Pleasant": "mt-pleasant-iowa",
    "Fairfield": "fairfield-iowa",
    "Washington": "washington-iowa",
    "West Burlington": "west-burlington-iowa",
    "Danville": "danville-iowa"
}

CATEGORIES = {
    "plumber": "Plumber",
    "hvac": "HVAC",
    "electrician": "Electrician",
    "roofer": "Roofer",
    "locksmith": "Locksmith",
    "landscaper": "Landscaper",
    "pest-control": "Pest Control"
}

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def scrape_city_category(city, category_slug, category_name):
    """Query Google Places API for businesses in a city+category."""
    if not API_KEY:
        print(f"  NO API KEY — using sample data for {city} {category_name}")
        return []

    import urllib.request, urllib.parse
    query = f"{category_name} in {city} Iowa"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json?" + urllib.parse.urlencode({
        "query": query,
        "key": API_KEY
    })

    results = []
    while url:
        try:
            resp = urllib.request.urlopen(url)
            data = json.loads(resp.read())
            for place in data.get("results", []):
                results.append(process_place(place, city, category_slug))
            url = None
            if "next_page_token" in data:
                time.sleep(2)
                url = "https://maps.googleapis.com/maps/api/place/textsearch/json?" + urllib.parse.urlencode({
                    "pagetoken": data["next_page_token"],
                    "key": API_KEY
                })
        except Exception as e:
            print(f"  Error scraping {city} {category_name}: {e}")
            url = None

    return results

def process_place(place, city, category_slug):
    """Extract relevant fields from a Google Places result."""
    return {
        "name": place.get("name", ""),
        "address": place.get("formatted_address", ""),
        "phone": place.get("formatted_phone_number", ""),
        "website": place.get("website", ""),
        "rating": place.get("rating", 0),
        "review_count": place.get("user_ratings_total", 0),
        "place_id": place.get("place_id", ""),
        "types": place.get("types", []),
        "city": city,
        "city_slug": CITY_SLUGS.get(city, city.lower().replace(" ", "-")),
        "category_slug": category_slug,
        "category_name": CATEGORIES.get(category_slug, category_slug),
        "scraped_at": datetime.now().isoformat()
    }

def generate_sample_data():
    """Generate sample data for development/testing without API key."""
    import random
    business_names = {
        "plumber": ["Smith Plumbing", "Johnson Pipe & Repair", "Burlington Drain Masters",
                     "Iowa City Plumbing Co", "Keokuk Sewer & Drain", "Fairfield Plumbing Pros",
                     "Mt. Pleasant Pipe Works", "Washington Water Works", "Fort Madison Plumbing",
                     "Danville Drain & Pipe", "West Burlington Plumbing", "Lee County Plumbing"],
        "hvac": ["Comfort Air HVAC", "Iowa Heating & Cooling", "Burlington Furnace Co",
                  "Johnson County AC", "Keokuk Climate Control", "Fairfield Furnace & Air",
                  "Mt. Pleasant HVAC Pros", "Washington Heating", "Fort Madison AC Repair",
                  "Southeast Iowa HVAC", "West Burlington Heating", "Danville Furnace"],
        "electrician": ["Bright Way Electric", "Burlington Electrical Services", "Iowa City Electric Co",
                         "Keokuk Wiring Pros", "Fairfield Electricians", "Mt. Pleasant Electric",
                         "Washington Electrical", "Fort Madison Electric", "West Burlington Electric",
                         "Danville Electric", "Lee County Electrical", "Southeast Iowa Electric"],
        "roofer": ["Top Notch Roofing", "Burlington Roofing Co", "Iowa City Roof Masters",
                    "Keokuk Roof & Gutters", "Fairfield Roofing Pros", "Mt. Pleasant Roofing",
                    "Washington Roof Works", "Fort Madison Roofing", "West Burlington Roofing",
                    "Danville Roof & Repair", "Lee County Roofing", "Southeast Iowa Roofing"],
        "locksmith": ["Able Locksmith", "Burlington Lock & Key", "Iowa City Locksmiths",
                       "Keokuk Safe & Lock", "Fairfield Lock Pros", "Mt. Pleasant Locksmith",
                       "Washington Key & Lock", "Fort Madison Locksmith", "Danville Lock & Key"],
        "landscaper": ["Green Thumb Landscaping", "Burlington Lawn Care", "Iowa City Landscape Design",
                        "Keokuk Outdoor Pros", "Fairfield Landscaping", "Mt. Pleasant Lawn & Garden",
                        "Washington Landscape Co", "Fort Madison Lawn Care", "Danville Landscaping"],
        "pest-control": ["Bug Free Pest Control", "Burlington Exterminating", "Iowa City Pest Pros",
                          "Keokuk Termite & Pest", "Fairfield Pest Management", "Mt. Pleasant Pest Control",
                          "Washington Bug Busters", "Fort Madison Exterminating", "Danville Pest Control"]
    }

    streets = ["Main St", "Jefferson St", "Washington Ave", "Broadway", "Maple St",
               "Oak Ave", "High St", "3rd St", "4th St", "Division St", "Agency St",
               "Henderson Ave", "Summer St", "Spring St", "West Ave"]

    results = []
    for city in CITIES:
        city_slug = CITY_SLUGS[city]
        for cat_slug, cat_name in CATEGORIES.items():
            names = business_names.get(cat_slug, ["Professional Services"])
            count = random.randint(3, 6)
            for i in range(count):
                name = names[i % len(names)]
                if city not in name:
                    name = f"{name} of {city}" if random.random() > 0.4 else name
                street_num = random.randint(100, 2500)
                street = random.choice(streets)
                zip_base = {"Iowa City": 52240, "Burlington": 52601, "Fort Madison": 52627,
                            "Keokuk": 52632, "Mt. Pleasant": 52641, "Fairfield": 52556,
                            "Washington": 52353, "West Burlington": 52655, "Danville": 52623}
                rating = round(random.uniform(3.0, 5.0), 1)
                reviews = random.randint(3, 80)

                results.append({
                    "name": name,
                    "address": f"{street_num} {street}, {city}, IA {zip_base.get(city, 52601)}",
                    "phone": f"(319) {random.randint(200,999)}-{random.randint(1000,9999)}",
                    "website": f"https://example.com/{name.lower().replace(' ','-')}",
                    "rating": rating,
                    "review_count": reviews,
                    "place_id": f"sample_{city_slug}_{cat_slug}_{i}",
                    "types": [cat_slug, "service_business"],
                    "city": city,
                    "city_slug": city_slug,
                    "category_slug": cat_slug,
                    "category_name": cat_name,
                    "scraped_at": datetime.now().isoformat()
                })
    return results

def main():
    print(f"=== Scraping Iowa Business Directory ===")
    print(f"Cities: {len(CITIES)} | Categories: {len(CATEGORIES)}")

    all_businesses = generate_sample_data()
    print(f"Generated {len(all_businesses)} sample businesses (no API key configured)")

    # Save raw data
    output_path = os.path.join(DATA_DIR, "businesses.json")
    with open(output_path, "w") as f:
        json.dump(all_businesses, f, indent=2)
    print(f"Saved to {output_path}")

    # Save per-city counts
    counts = {}
    for b in all_businesses:
        slug = b["city_slug"]
        counts[slug] = counts.get(slug, 0) + 1

    counts_path = os.path.join(DATA_DIR, "business-counts.json")
    with open(counts_path, "w") as f:
        json.dump(counts, f, indent=2)
    print(f"Saved counts to {counts_path}")

    return all_businesses

if __name__ == "__main__":
    main()
