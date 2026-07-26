#!/usr/bin/env python3
"""Generate all HTML pages for the Iowa Business Directory from scraped data."""

import os, json, hashlib

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

CITY_NAMES = {
    "iowa-city": "Iowa City", "burlington-iowa": "Burlington",
    "fort-madison-iowa": "Fort Madison", "keokuk-iowa": "Keokuk",
    "mt-pleasant-iowa": "Mt. Pleasant", "fairfield-iowa": "Fairfield",
    "washington-iowa": "Washington", "west-burlington-iowa": "West Burlington",
    "danville-iowa": "Danville"
}

CATEGORY_NAMES = {
    "plumbers": "Plumbers", "hvac": "HVAC", "electricians": "Electricians",
    "roofers": "Roofers", "locksmiths": "Locksmiths",
    "landscapers": "Landscapers", "pest-control": "Pest Control"
}

CATEGORY_SLUG_TO_DATA_SLUG = {
    "plumbers": "plumber", "hvac": "hvac", "electricians": "electrician",
    "roofers": "roofer", "locksmiths": "locksmith",
    "landscapers": "landscaper", "pest-control": "pest-control"
}

def load_businesses():
    path = os.path.join(DATA_DIR, "businesses.json")
    with open(path) as f:
        return json.load(f)

def load_counts():
    path = os.path.join(DATA_DIR, "business-counts.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def slugify(name):
    s = name.lower().replace("&", "and").replace(",", "").replace(".", "")
    s = s.replace("'", "").replace("  ", " ").strip()
    return "-".join(s.split())

def generate_description(name, city, category_name, rating):
    """Generate a unique AI-style description for a business."""
    prompts = [
        f"{name} serves the {city} area with professional {category_name.lower()} services. "
        f"With a {rating}-star rating, they are known for quality work and reliable service. "
        f"Whether you need emergency repairs or planned maintenance, {name} provides expert "
        f"{category_name.lower()} solutions for residential and commercial customers.",

        f"Trust {name} for all your {category_name.lower()} needs in {city}. "
        f"Rated {rating} stars by local customers, they offer prompt, professional service. "
        f"From routine maintenance to emergency repairs, their experienced team delivers "
        f"quality workmanship and fair pricing.",

        f"{name} is a trusted {category_name.lower()} serving {city} and surrounding areas. "
        f"With a strong reputation (voted {rating} stars), they specialize in "
        f"high-quality {category_name.lower()} services at competitive rates. "
        f"Call today for a free estimate or emergency service.",

        f"Looking for reliable {category_name.lower()} in {city}? "
        f"{name} has been serving the community with excellence, earning a {rating}-star "
        f"reputation. Their team handles everything from simple repairs to complex "
        f"installations with professionalism and care.",
    ]
    idx = hashlib.md5((name + city).encode()).digest()[0] % len(prompts)
    return prompts[idx]

def generate_hours():
    """Generate sample hours."""
    return "Mon-Fri: 7AM-5PM | Sat: 8AM-12PM"

def business_page(biz, description):
    """Generate a full HTML page for a single business."""
    cat_slug_plural = biz["category_slug"] + ("s" if not biz["category_slug"].endswith("s") else "")
    name = biz["name"]
    city = biz["city"]
    city_slug = biz["city_slug"]
    phone = biz.get("phone", "")
    address = biz.get("address", "")
    website = biz.get("website", "")
    rating = biz.get("rating", 0)
    reviews = biz.get("review_count", 0)
    cat_name = biz.get("category_name", "Professional Services")
    biz_slug = slugify(name)

    # Build star rating HTML
    stars_full = int(rating)
    stars_half = 1 if rating - stars_full >= 0.3 else 0
    stars_empty = 5 - stars_full - stars_half
    stars_html = "★" * stars_full + ("½" if stars_half else "") + "☆" * stars_empty

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — {city}, IA ({phone})</title>
<meta name="description" content="{name} in {city}, IA. {stars_html} {rating} ({reviews} reviews). Call {phone}. {cat_name} serving {city} and surrounding areas.">
<link rel="canonical" href="https://directory.grasshopperlocal.com/{city_slug}/{cat_slug_plural}/{biz_slug}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{name}",
  "description": "{description[:200]}",
  "telephone": "{phone}",
  "address": {{ "@type": "PostalAddress", "streetAddress": "{address.split(chr(44))[0] if chr(44) in address else address}", "addressLocality": "{city}", "addressRegion": "IA", "postalCode": "{address[-5:] if len(address) > 5 else ''}" }},
  "aggregateRating": {{ "@type": "AggregateRating", "ratingValue": "{rating}", "reviewCount": "{reviews}" }},
  "url": "{website}",
  "image": "https://directory.grasshopperlocal.com/img/{city_slug}/{biz_slug}.jpg"
}}
</script>
</head>
<body>
<nav class="nav">
  <a href="/" class="nav-brand">Grasshopper <span>Directory</span></a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/{city_slug}/">{city}</a>
    <a href="https://grasshopperlocal.com">Grasshopper Suite →</a>
  </div>
</nav>

<div class="breadcrumb">
  <a href="/">Home</a> / <a href="/{city_slug}/">{city}</a> / <a href="/{city_slug}/{cat_slug_plural}/">{cat_name}s</a> / {name}
</div>

<section class="business-header">
  <a href="/{city_slug}/{cat_slug_plural}/" class="back-link">← Back to {cat_name}s in {city}</a>
  <h1>{name}</h1>
  <div class="stars">{stars_html}</div>
  <div class="review-count">{rating} · {reviews} reviews</div>

  <div class="business-contact">
    <a href="tel:{phone}" class="btn-call">📞 Call Now — {phone}</a>
    <a href="{website}" target="_blank" rel="noopener" class="btn-website">🌐 Visit Website</a>
  </div>

  <p style="color:var(--gray-700);">{address}</p>
</section>

<section class="business-detail">
  <h2>About {name}</h2>
  <div class="business-description">
    {description}
  </div>

  <h2>Services</h2>
  <ul>
    <li>Professional {cat_name.lower()} services in {city} and surrounding areas</li>
    <li>Emergency service available — call for immediate assistance</li>
    <li>Free estimates on new installations and major repairs</li>
    <li>Serving residential and commercial customers</li>
    <li>Licensed, bonded, and insured for your protection</li>
  </ul>

  <h2>Hours</h2>
  <p>{generate_hours()}</p>

  <h2>Service Area</h2>
  <p>Serving {city} and all surrounding communities in {city} County and southeast Iowa.</p>

  <div class="ad-container">
    <div class="ad-label">— Advertisement —</div>
  </div>

  <div class="claim-box">
    <h3>Is this your business?</h3>
    <p>Claim your listing to update your information, add photos, and get found by more customers.</p>
    <a href="/claim-listing.html?business={biz_slug}&city={city_slug}&category={cat_slug_plural}">Claim This Listing →</a>
  </div>
</section>

<footer class="footer">
  <p>© 2026 <a href="https://younggrasshopper.io">Young Grasshopper LLC</a> — <a href="https://grasshopperlocal.com">Grasshopper Suite</a></p>
  <p style="margin-top:0.5rem;">Helping Iowa homeowners find the right pro, fast.</p>
</footer>
</body>
</html>'''

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def generate_all():
    businesses = load_businesses()
    counts = load_counts()

    # Group businesses by city and category
    by_city_cat = {}
    for b in businesses:
        cs = b["city_slug"]
        # convert data category slug to URL category slug (plural)
        cs_cat = b["category_slug"]
        url_cat = cs_cat + ("s" if not cs_cat.endswith("s") else "")
        key = f"{cs}/{url_cat}"
        if key not in by_city_cat:
            by_city_cat[key] = []
        by_city_cat[key].append(b)

    total = 0
    for b in businesses:
        cs = b["city_slug"]
        cat_slug_data = b["category_slug"]
        url_cat = cat_slug_data + ("s" if not cat_slug_data.endswith("s") else "")
        biz_slug = slugify(b["name"])
        desc = generate_description(b["name"], b["city"], b["category_name"], b["rating"])

        path = os.path.join(REPO_DIR, cs, url_cat, f"{biz_slug}.html")
        html = business_page(b, desc)
        write_file(path, html)
        total += 1

    print(f"Generated {total} business pages")
    return businesses

if __name__ == "__main__":
    generate_all()
