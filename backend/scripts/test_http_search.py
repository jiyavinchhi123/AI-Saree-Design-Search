import httpx
import json
import os

url = "http://127.0.0.1:8000/api/search/upload"
img_path = "data/storage/users/b6ecec459b998637/ONENOTE-b6ecec-8C424B.jpg"
headers = {"X-User-Id": "b6ecec459b998637"}

with open(img_path, "rb") as f:
    files = {"file": ("ONENOTE-b6ecec-8C424B.jpg", f, "image/jpeg")}
    data = {"threshold": 0.82, "top_k": 1}
    r = httpx.post(url, headers=headers, files=files, data=data, timeout=30.0)

print(f"HTTP Status: {r.status_code}")
res = r.json()
top = res["matches"][0]

print("\n=== HTTP API Search Match Metadata ===")
print(f"image_id:         {top.get('image_id')}")
print(f"notebook_name:    {top.get('notebook_name')}")
print(f"section_name:     {top.get('section_name')}")
print(f"page_title:       {top.get('page_title')}")
print(f"object_id:        {top.get('object_id')}")
print(f"oneNoteWebUrl:    {top.get('oneNoteWebUrl')}")
print(f"oneNoteClientUrl: {top.get('oneNoteClientUrl')}")
print(f"similarity_pct:   {top.get('similarity_percentage')}%")
