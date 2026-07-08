"""Check Notion database status"""
import os
import json
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DB_ID = "38d69edd-f301-802c-b2cf-e385ad2a9961"
HEADERS = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# Check schema
resp = requests.get("https://api.notion.com/v1/databases/" + DB_ID, headers=HEADERS)
db = resp.json()
print("Title:", db.get("title", [{}])[0].get("plain_text", ""))
print("Properties:")
for name, prop in db.get("properties", {}).items():
    print("  - {} ({})".format(name, prop["type"]))

# Count existing pages
print()
print("Counting existing pages...")
has_more = True
start_cursor = None
total = 0
while has_more:
    params = {"page_size": 100}
    if start_cursor:
        params["start_cursor"] = start_cursor
    resp = requests.post(
        "https://api.notion.com/v1/databases/" + DB_ID + "/query",
        headers=HEADERS, json=params
    )
    data = resp.json()
    results = data.get("results", [])
    total += len(results)
    has_more = data.get("has_more", False)
    start_cursor = data.get("next_cursor")
    print("  Got {} results, total so far: {}".format(len(results), total))

print("Total existing pages:", total)
