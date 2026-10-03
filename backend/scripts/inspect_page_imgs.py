import asyncio
import re
import httpx
from app.database import SessionLocal
from app.onenote.graph_client import MicrosoftOneNoteClient

async def inspect_images():
    c = MicrosoftOneNoteClient()
    db = SessionLocal()
    try:
        token = await c.get_valid_token_for_user('b6ecec459b998637', db)
        if not token:
            print("No token")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0) as http:
            # Let's inspect the page 'Difference between Git and GitHub'
            # Page ID: 0-6330ba86b8cc40f9bb7545f553492ae6!1-B6ECEC459B998637!1013
            pg_id = "0-6330ba86b8cc40f9bb7545f553492ae6!1-B6ECEC459B998637!1013"
            content_url = f"https://graph.microsoft.com/v1.0/me/onenote/pages/{pg_id}/content?includeIDs=true"
            r = await http.get(content_url, headers=headers)
            print(f"Content fetch status: {r.status_code}")
            html = r.text
            print(f"HTML length: {len(html)}")
            
            # Find all img tags and their attributes
            imgs = re.findall(r'<img\s+([^>]+)>', html, re.I)
            print(f"Found {len(imgs)} <img> tags:")
            for idx, img_tag in enumerate(imgs, 1):
                print(f"\n--- Image #{idx} ---")
                print(f"Tag attributes: {img_tag}")
                id_m = re.search(r'\bid=["\']([^"\']+)["\']', img_tag, re.I)
                src_m = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.I)
                data_id_m = re.search(r'data-id=["\']([^"\']+)["\']', img_tag, re.I)
                print(f"Extracted id: {id_m.group(1) if id_m else None}")
                print(f"Extracted data-id: {data_id_m.group(1) if data_id_m else None}")
                print(f"Extracted src: {src_m.group(1)[:80] if src_m else None}...")
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(inspect_images())
