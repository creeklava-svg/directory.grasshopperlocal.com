#!/usr/bin/env python3
"""Generate city homepages and category index pages."""

import os, json

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CITIES = ["iowa-city", "burlington-iowa", "fort-madison-iowa", "keokuk-iowa",
           "mt-pleasant-iowa", "fairfield-iowa", "washington-iowa",
           "west-burlington-iowa", "danville-iowa"]

CITY_NAMES = {
    "iowa-city": "Iowa City", "burlington-iowa": "Burlington",
    "fort-madison-iowa": "Fort Madison", "keokuk-iowa": "Keokuk",
    "mt-pleasant-iowa": "Mt. Pleasant", "fairfield-iowa": "Fairfield",
    "washington-iowa": "Washington", "west-burlington-iowa": "West Burlington",
    "danville-iowa": "Danville"
}

CATEGORIES = ["plumbers", "hvac", "electricians", "roofers", "locksmiths", "landscapers", "pest-control"]
CATEGORY_NAMES = {
    "plumbers": "Plumbers", "hvac": "HVAC", "electricians": "Electricians",
    "roofers": "Roofers", "locksmiths": "Locksmiths",
    "landscapers": "Landscapers", "pest-control": "Pest Control"
}

def get_businesses_for_city_category(city_slug, cat_slug):
    """Read individual business HTML files and extract info."""
    import glob, re
    pattern = os.path.join(REPO_DIR, city_slug, cat_slug, "*.html")
    businesses = []
    for path in glob.glob(pattern):
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # Extract name from H1
        m = re.search(r'<h1>(.*?)</h1>', content)
        name = m.group(1) if m else "Unknown"
        # Extract phone from tel: link
        m = re.search(r'href="tel:(.*?)"', content)
        phone = m.group(1) if m else ""
        # Extract rating
        m = re.search(r'(\d+\.?\d*)\s*·\s*(\d+) reviews', content)
        rating = m.group(1) if m else "0.0"
        reviews = m.group(2) if m else "0"
        # Extract slug from filename
        slug = os.path.splitext(os.path.basename(path))[0]
        premium = False  # No premium listings yet
        businesses.append({
            "name": name, "phone": phone, "rating": rating,
            "reviews": reviews, "slug": slug, "premium": premium
        })
    # Sort: premium first, then by rating descending
    businesses.sort(key=lambda b: (not b["premium"], -float(b["rating"])))
    return businesses

def generate_city_homepage(city_slug):
    """Generate city homepage listing all categories."""
    city_name = CITY_NAMES.get(city_slug, city_slug.replace("-", " ").title())
    cat_list = []
    total_biz = 0
    for cat in CATEGORIES:
        bizs = get_businesses_for_city_category(city_slug, cat)
        count = len(bizs)
        total_biz += count
        cat_list.append((cat, CATEGORY_NAMES.get(cat, cat), count))

    cat_rows = ""
    for cat_slug, cat_name, count in cat_list:
        cat_rows += f'''
    <a href="/{city_slug}/{cat_slug}/" class="city-card">
      <h3>{cat_name}</h3>
      <div class="count">{count} businesses</div>
    </a>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Home Services in {city_name}, IA — Plumbers, HVAC, Electricians</title>
<meta name="description" content="Find {city_name}, IA home service professionals. Browse plumbers, HVAC companies, electricians, roofers and more with reviews and contact info.">
<link rel="canonical" href="https://directory.grasshopperlocal.com/{city_slug}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "{city_name} Home Services",
  "description": "Browse home service professionals in {city_name}, IA."
}}
</script>
</head>
<body>
<nav class="nav">
  <a href="/" class="nav-brand">Grasshopper <span>Directory</span></a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/{city_slug}/">{city_name}</a>
  </div>
</nav>

<div class="breadcrumb">
  <a href="/">Home</a> / {city_name}
</div>

<section class="hero">
  <h1>Home Services in {city_name}, IA</h1>
  <p>Find {total_biz} verified local service professionals. Browse by category, check reviews, and get matched with the right pro for your job.</p>
  <a href="/lead-capture.html?city={city_slug}" class="lead-btn">Get Matched →</a>
</section>

<section class="section">
  <h2 class="section-title">Categories in {city_name}</h2>
  <div class="city-grid">{cat_rows}
  </div>
</section>

<footer class="footer">
  <p>© 2026 <a href="https://younggrasshopper.io">Young Grasshopper LLC</a> — <a href="https://grasshopperlocal.com">Grasshopper Suite</a></p>
</footer>
</body>
</html>'''

def generate_category_page(city_slug, cat_slug):
    """Generate category index page listing all businesses in a category."""
    city_name = CITY_NAMES.get(city_slug, city_slug.replace("-", " ").title())
    cat_name = CATEGORY_NAMES.get(cat_slug, cat_slug.title())
    bizs = get_businesses_for_city_category(city_slug, cat_slug)

    biz_rows = ""
    for b in bizs:
        stars = "★" * int(float(b["rating"])) + "☆" * (5 - int(float(b["rating"])))
        premium_badge = '<span class="premium-badge">Premium</span>' if b["premium"] else ""
        biz_rows += f'''
    <a href="/{city_slug}/{cat_slug}/{b['slug']}.html" class="business-item">
      <div class="info">
        <h4>{b['name']} {premium_badge}</h4>
        <div class="meta">{stars} {b['rating']} · {b['reviews']} reviews</div>
      </div>
      <div class="phone">{b['phone']}</div>
    </a>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{cat_name} in {city_name}, IA — Local Directory</title>
<meta name="description" content="Find {cat_name.lower()} in {city_name}, IA. Browse {len(bizs)} local {cat_name.lower()} with reviews, ratings, and contact information.">
<link rel="canonical" href="https://directory.grasshopperlocal.com/{city_slug}/{cat_slug}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<nav class="nav">
  <a href="/" class="nav-brand">Grasshopper <span>Directory</span></a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/{city_slug}/">{city_name}</a>
  </div>
</nav>

<div class="breadcrumb">
  <a href="/">Home</a> / <a href="/{city_slug}/">{city_name}</a> / {cat_name}
</div>

<section class="hero">
  <h1>{cat_name} in {city_name}, IA</h1>
  <p>{len(bizs)} local {cat_name.lower()} listed. Compare reviews, ratings, and contact info. Need help finding the right pro?</p>
  <a href="/lead-capture.html?city={city_slug}&category={cat_slug}" class="lead-btn">Get Matched Free →</a>
</section>

<section class="section">
  <h2 class="section-title">{len(bizs)} {cat_name} Found</h2>
  <div class="business-list">{biz_rows}
  </div>
</section>

<footer class="footer">
  <p>© 2026 <a href="https://younggrasshopper.io">Young Grasshopper LLC</a> — <a href="https://grasshopperlocal.com">Grasshopper Suite</a></p>
</footer>
</body>
</html>'''

def generate_all():
    for city in CITIES:
        # City homepage
        html = generate_city_homepage(city)
        path = os.path.join(REPO_DIR, city, "index.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"City page: {city}")

        # Category pages
        for cat in CATEGORIES:
            html = generate_category_page(city, cat)
            path = os.path.join(REPO_DIR, city, cat, "index.html")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        print(f"  {len(CATEGORIES)} category pages")

    # Update homepage counts
    update_homepage_counts()
    print("Updated homepage with live counts")

def update_homepage_counts():
    """Update the homepage city card counts."""
    import glob, re
    counts = {}
    for city in CITIES:
        total = 0
        for cat in CATEGORIES:
            pattern = os.path.join(REPO_DIR, city, cat, "*.html")
            # Count HTML files excluding index.html
            files = [f for f in glob.glob(pattern) if not f.endswith("index.html")]
            total += len(files)
        counts[city] = total

    # Update the business-counts.json
    counts_path = os.path.join(REPO_DIR, "data", "business-counts.json")
    os.makedirs(os.path.dirname(counts_path), exist_ok=True)
    with open(counts_path, "w") as f:
        json.dump(counts, f, indent=2)

if __name__ == "__main__":
    generate_all()
