#!/usr/bin/env python3
"""Generate sitemap.xml for the Iowa Business Directory."""

import os, glob
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://directory.grasshopperlocal.com"

def generate_sitemap():
    today = datetime.now().strftime("%Y-%m-%d")
    pages = []

    # Walk all HTML files
    for root, dirs, files in os.walk(REPO_DIR):
        for f in files:
            if f.endswith(".html"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, REPO_DIR)
                # Skip cloudflare-worker directory
                if "cloudflare-worker" in rel:
                    continue
                url_path = "/" + rel.replace("\\", "/")
                pages.append((url_path, today))

    # Sort for consistency
    pages.sort()

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url_path, lastmod in pages:
        xml += f'  <url>\n    <loc>{BASE_URL}{url_path}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n'
    xml += '</urlset>\n'

    path = os.path.join(REPO_DIR, "sitemap.xml")
    with open(path, "w") as f:
        f.write(xml)
    print(f"Sitemap: {len(pages)} pages → sitemap.xml")

if __name__ == "__main__":
    generate_sitemap()
