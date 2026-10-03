import asyncio
import sys
import httpx
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database import SessionLocal, UserRecord
from app.onenote.graph_client import MicrosoftOneNoteClient

async def inspect_pages_html():
    db = SessionLocal()
    u = db.query(UserRecord).first()
    client = MicrosoftOneNoteClient()
    token = await client.get_valid_token_for_user(u.id, db)
    db.close()
    
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30.0) as http:
        r = await http.get("https://graph.microsoft.com/v1.0/me/onenote/pages?$select=id,title,links,contentUrl", headers=headers)
        pages = r.json().get("value", [])
        print(f"Total pages in Microsoft Graph: {len(pages)}")
        
        for p in pages:
            pid = p.get("id")
            title = p.get("title")
            content_url = p.get("contentUrl")
            if "includeIDs" not in content_url:
                delimiter = "&" if "?" in content_url else "?"
                content_url = f"{content_url}{delimiter}includeIDs=true"
            
            resp = await http.get(content_url, headers=headers)
            html = resp.text
            
            print("==================================================")
            print(f"PAGE: '{title}' (ID: {pid})")
            print(f"HTTP Status: {resp.status_code}")
            print(f"Response Length: {len(html)} bytes")
            
            img_tags = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
            print(f"All <img> elements found: {len(img_tags)}")
            for img in img_tags:
                print("  RAW TAG:", img)
                id_m = re.search(r'\bid=["\']([^"\']+)["\']', img, re.IGNORECASE)
                data_id_m = re.search(r'\bdata-id=["\']([^"\']+)["\']', img, re.IGNORECASE)
                data_data_id_m = re.search(r'\bdata-data-id=["\']([^"\']+)["\']', img, re.IGNORECASE)
                fullres_m = re.search(r'\bdata-fullres-src=["\']([^"\']+)["\']', img, re.IGNORECASE)
                src_m = re.search(r'\bsrc=["\']([^"\']+)["\']', img, re.IGNORECASE)
                
                print(f"    <img id=\"...\">:         {id_m.group(1) if id_m else None}")
                print(f"    data-id:                  {data_id_m.group(1) if data_id_m else None}")
                print(f"    data-data-id:             {data_data_id_m.group(1) if data_data_id_m else None}")
                print(f"    data-fullres-src:         {fullres_m.group(1) if fullres_m else None}")
                print(f"    src:                      {src_m.group(1) if src_m else None}")

            print("\nRAW HTML (first 400 chars):")
            print(html[:400].strip())

if __name__ == "__main__":
    asyncio.run(inspect_pages_html())
