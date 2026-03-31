import gzip
import json
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import requests

# 🔧 SETTINGS
FEED_URL = "https://www.ziprecruiter.com/feed/cpc_joblink_uk_test30.xml.gz"
OUTPUT_FILE = "docs/jobs.json"
MAX_JOBS = 500

# 🎯 FILTER SETTINGS
ALLOWED_CATEGORIES = [
    "Retail",
    "Sports and Recreation",
    "Business",
    "Personal Care",
    "Arts and Entertainment",
    "Education",
    "Food",
    "Non profit"
]

ALLOWED_CITIES = [
    "Leeds",
    "Bradford",
    "York",
    "Harrogate"
]

os.makedirs("docs", exist_ok=True)


def text_or_empty(node, tag):
    value = node.findtext(tag)
    return value.strip() if isinstance(value, str) else ""


# ✅ NEW: Clean description formatting
import re

def clean_description(desc):
    if not desc:
        return ""

    # 1. Fix escaped newlines
    desc = desc.replace("\\n", "\n")

    # 2. Add line breaks before common headings
    headings = [
        "Job Description",
        "Key Responsibilities",
        "Responsibilities",
        "What We're Looking For",
        "Requirements",
        "Role Overview",
        "Key Requirements",
        "Why Apply",
        "Contacts to Apply"
    ]

    for h in headings:
        desc = re.sub(rf"\s*({h})\s*", r"\n\n\1\n", desc, flags=re.IGNORECASE)

    # 3. Add line breaks after full stops (basic paragraph splitting)
    desc = re.sub(r"\.\s+", ".\n", desc)

    # 4. Clean excessive whitespace
    desc = re.sub(r"\n{3,}", "\n\n", desc)

    return desc.strip()


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        gz_path = os.path.join(tmpdir, "feed.xml.gz")
        xml_path = os.path.join(tmpdir, "feed.xml")

        # Download
        response = requests.get(FEED_URL, timeout=60)
        response.raise_for_status()

        with open(gz_path, "wb") as f:
            f.write(response.content)

        print("Downloaded feed")

        # Decompress
        with gzip.open(gz_path, "rb") as f_in:
            with open(xml_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        print("Decompressed feed")

        # Parse
        tree = ET.parse(xml_path)
        root = tree.getroot()

        jobs = []

        for job in root.findall(".//job"):

            category = text_or_empty(job, "category")
            city = text_or_empty(job, "city")
            country = text_or_empty(job, "country")

            # ❌ Skip if category missing
            if not category:
                continue

            # Country filter
            if country != "GB":
                continue

            # City filter
            if city.lower() not in [c.lower() for c in ALLOWED_CITIES]:
                continue

            # Category filter
            if not any(cat.lower() in category.lower() for cat in ALLOWED_CATEGORIES):
                continue

            # Extract fields
            jobtype = text_or_empty(job, "jobtype").lower()
            title = text_or_empty(job, "title")
            company = text_or_empty(job, "company")
            salary = text_or_empty(job, "salary")
            description = clean_description(text_or_empty(job, "description"))
            url = text_or_empty(job, "url")
            ref = text_or_empty(job, "referencenumber")
            date = text_or_empty(job, "date")

            location_parts = [p for p in [city, country] if p]
            location = ", ".join(location_parts)

            jobs.append({
                "id": ref,
                "title": title,
                "company": company,
                "location": location,
                "city": city,
                "salary": salary,
                "description": description,
                "url": url,
                "job_type": jobtype,
                "category": category,
                "date": date,
                "country": country
            })

            if len(jobs) >= MAX_JOBS:
                break

        # Save JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False)

        print(f"Saved {len(jobs)} jobs to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
