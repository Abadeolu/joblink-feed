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
MAX_JOBS = 500  # limit number of jobs

# Ensure output folder exists
os.makedirs("docs", exist_ok=True)


def text_or_empty(node, tag):
    value = node.findtext(tag)
    return value.strip() if isinstance(value, str) else ""


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        gz_path = os.path.join(tmpdir, "feed.xml.gz")
        xml_path = os.path.join(tmpdir, "feed.xml")

        # Step 1: Download feed
        response = requests.get(FEED_URL, timeout=60)
        response.raise_for_status()

        with open(gz_path, "wb") as f:
            f.write(response.content)

        print("Downloaded feed")

        # Step 2: Decompress
        with gzip.open(gz_path, "rb") as f_in:
            with open(xml_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        print("Decompressed feed")

        # Step 3: Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        jobs = []

        # Step 4: Extract + filter + limit
        for job in root.findall(".//job"):
            jobtype = text_or_empty(job, "jobtype").lower()

            # 🎯 FILTER: only part-time & internship
            #if jobtype not in ["part_time", "internship"]:
               # continue

            title = text_or_empty(job, "title")
            company = text_or_empty(job, "company")
            city = text_or_empty(job, "city")
            state = text_or_empty(job, "state")
            country = text_or_empty(job, "country")
            salary = text_or_empty(job, "salary")
            description = text_or_empty(job, "description")
            url = text_or_empty(job, "url")
            category = text_or_empty(job, "category")
            ref = text_or_empty(job, "referencenumber")
            date = text_or_empty(job, "date")

            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts)

            jobs.append({
                "id": ref,
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "description": description,
                "url": url,
                "job_type": jobtype,
                "category": category,
                "date": date
            })

            # 🔒 LIMIT jobs
            if len(jobs) >= MAX_JOBS:
                break

        # Step 5: Save JSON (compressed)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False)

        print(f"Saved {len(jobs)} jobs to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
