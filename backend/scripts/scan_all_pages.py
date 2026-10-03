import asyncio
import re
import httpx
from app.database import SessionLocal
from app.onenote.graph_client import MicrosoftOneNoteClient

async def scan_all():
    c = MicrosoftOneNoteClient()
    db = SessionLocal()
    try:
        token = await c.get_valid_token_for_user('b6ecec459b998637', db)
        if not token:
            print("No token")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0) as http:
            r = await http.get("https://graph.microsoft.com/v1.0/me/onenote/pages?$select=id,title,contentUrl,links", headers=headers)
            pages = r.json().get("value", [])
            print(f"Total pages: {len(pages)}")
            for p in pages:
                title = p.get("title")
                pid = p.get("id")
                curl = p.get("contentUrl")
                if "includeIDs" not in curl:
                    curl = f"{curl}?includeIDs=true"
                rc = await http.get(curl, headers=headers)
                imgs = re.findall(r'<img\s+([^>]+)>', rc.text, re.I)
                objs = re.findall(r'<object\s+([^>]+)>', rc.text, re.I)
                print(f"Page: '{title}' (ID: {pid}) -> {len(imgs)} imgs, {len(objs)} objects")
                for img in imgs:
                    print(f"   IMG: {img[:160]}")
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(scan_all())
