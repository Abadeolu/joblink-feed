import gzip
import json
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET

import requests

FEED_URL = "https://www.ziprecruiter.com/feed/cpc_joblink_uk_test30.xml.gz"
DOCS_DIR = "docs"
XML_OUT = os.path.join(DOCS_DIR, "jobs.xml")
JSON_OUT = os.path.join(DOCS_DIR, "jobs.json")

os.makedirs(DOCS_DIR, exist_ok=True)

def text_or_empty(node, tag):
    value = node.findtext(tag)
    return value.strip() if isinstance(value, str) else ""

def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        gz_path = os.path.join(tmpdir, "feed.xml.gz")
        raw_xml_path = os.path.join(tmpdir, "feed.xml")

        r = requests.get(FEED_URL, timeout=60)
        r.raise_for_status()

        with open(gz_path, "wb") as f:
            f.write(r.content)

        with gzip.open(gz_path, "rb") as f_in:
            with open(raw_xml_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        tree = ET.parse(raw_xml_path)
        root = tree.getroot()

        jobs = []
        out_root = ET.Element("jobs")

        for job in root.findall(".//job"):
            title = text_or_empty(job, "title")
            company = text_or_empty(job, "company")
            city = text_or_empty(job, "city")
            state = text_or_empty(job, "state")
            country = text_or_empty(job, "country")
            salary = text_or_empty(job, "salary")
            description = text_or_empty(job, "description")
            url = text_or_empty(job, "url")
            jobtype = text_or_empty(job, "jobtype")
            category = text_or_empty(job, "category")
            ref = text_or_empty(job, "referencenumber")
            date = text_or_empty(job, "date")

            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts)

            item = {
                "id": ref,
                "title": title,
                "company": company,
                "location": location,
                "city": city,
                "state": state,
                "country": country,
                "salary": salary,
                "description": description,
                "url": url,
                "job_type": jobtype,
                "category": category,
                "date": date,
            }
            jobs.append(item)

            xjob = ET.SubElement(out_root, "job")
            ET.SubElement(xjob, "id").text = ref
            ET.SubElement(xjob, "title").text = title
            ET.SubElement(xjob, "company").text = company
            ET.SubElement(xjob, "location").text = location
            ET.SubElement(xjob, "city").text = city
            ET.SubElement(xjob, "state").text = state
            ET.SubElement(xjob, "country").text = country
            ET.SubElement(xjob, "salary").text = salary
            ET.SubElement(xjob, "description").text = description
            ET.SubElement(xjob, "url").text = url
            ET.SubElement(xjob, "job_type").text = jobtype
            ET.SubElement(xjob, "category").text = category
            ET.SubElement(xjob, "date").text = date

        with open(JSON_OUT, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False, indent=2)

        ET.ElementTree(out_root).write(XML_OUT, encoding="utf-8", xml_declaration=True)

        print(f"Built {len(jobs)} jobs")
        print(f"Wrote {JSON_OUT}")
        print(f"Wrote {XML_OUT}")

if __name__ == "__main__":
    main()
