import asyncio
import httpx
import re
from app.database import SessionLocal
from app.onenote.graph_client import MicrosoftOneNoteClient

async def inspect():
    client = MicrosoftOneNoteClient()
    db = SessionLocal()
    try:
        await client.load_tokens(db)
        headers = {"Authorization": f"Bearer {client.access_token}"}
        async with httpx.AsyncClient(timeout=30.0) as http:
            r = await http.get("https://graph.microsoft.com/v1.0/me/onenote/pages?$select=id,title,contentUrl,links", headers=headers)
            pages = r.json().get("value", [])
            print(f"Total pages retrieved: {len(pages)}", flush=True)
            for p in pages:
                curl = p.get("contentUrl")
                if curl:
                    r_c = await http.get(curl, headers=headers)
                    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', r_c.text, re.I)
                    title = p.get("title")
                    print(f"Page: '{title}' | Images: {len(imgs)}", flush=True)
                    for img in imgs:
                        print(f"   Resource URL: {img}", flush=True)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(inspect())
