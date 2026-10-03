import os
import sys
import httpx
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

async def test_search():
    img_path = os.path.join("data", "storage", "users", "b6ecec459b998637", "MS-b6ecec-4DE3B99D.jpg")
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(img_path, "rb") as f:
            files = {"file": ("test_saree.jpg", f, "image/jpeg")}
            data = {"threshold": 0.82, "top_k": 3}
            headers = {"X-User-Id": "b6ecec459b998637"}
            resp = await client.post("http://127.0.0.1:8000/api/search/upload", files=files, data=data, headers=headers)
            print("HTTP Status:", resp.status_code)
            res = resp.json()
            print("Is Strong Match:", res.get("is_strong_match"))
            print("Top Percentage:", res.get("top_percentage"), "%")
            print("Status Message:", res.get("status_message"))
            print("Total Indexed:", res.get("total_indexed"))
            print("Matches Returned:", len(res.get("matches", [])))
            for idx, m in enumerate(res.get("matches", []), start=1):
                print(f"\nMatch #{idx}:")
                print(f"  Design ID:          {m.get('image_id')}")
                print(f"  Title:              {m.get('title')}")
                print(f"  Page Title:         {m.get('page_title')}")
                print(f"  Object ID:          {m.get('object_id')}")
                print(f"  Similarity:         {m.get('similarity_percentage')}%")
                print(f"  OneNote Client URL: {m.get('oneNoteClientUrl')}")
                print(f"  OneNote Web URL:    {m.get('oneNoteWebUrl')}")

if __name__ == "__main__":
    asyncio.run(test_search())
