import asyncio
import sys
import httpx
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database import SessionLocal, UserRecord
from app.onenote.graph_client import MicrosoftOneNoteClient

async def inspect():
    db = SessionLocal()
    u = db.query(UserRecord).first()
    client = MicrosoftOneNoteClient()
    token = await client.get_valid_token_for_user(u.id, db)
    db.close()
    
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30.0) as http:
        # 1. All pages
        r = await http.get("https://graph.microsoft.com/v1.0/me/onenote/pages?$select=id,title,links,contentUrl,createdDateTime,lastModifiedDateTime", headers=headers)
        pages = r.json().get("value", [])
        print(f"Total pages in Graph across all notebooks: {len(pages)}")
        for p in pages:
            print(f"  PAGE ID: {p.get('id')} | TITLE: '{p.get('title')}'")
            
        # 2. Check if any page title contains saree or design (case-insensitive)
        saree_pages = [p for p in pages if "saree" in p.get("title", "").lower() or "design" in p.get("title", "").lower()]
        print(f"\nPages matching 'saree' or 'design': {len(saree_pages)}")
        for sp in saree_pages:
            print("Matched Page:", json.dumps(sp, indent=2))

        # 3. All sections
        r_sec = await http.get("https://graph.microsoft.com/v1.0/me/onenote/sections", headers=headers)
        secs = r_sec.json().get("value", [])
        print(f"\nTotal sections in Graph: {len(secs)}")
        for s in secs:
            print(f"  SEC ID: {s.get('id')} | NAME: '{s.get('displayName')}'")

        # 4. All notebooks
        r_nb = await http.get("https://graph.microsoft.com/v1.0/me/onenote/notebooks", headers=headers)
        nbs = r_nb.json().get("value", [])
        print(f"\nTotal notebooks in Graph: {len(nbs)}")
        for nb in nbs:
            print(f"  NB ID: {nb.get('id')} | NAME: '{nb.get('displayName')}'")

        # 5. Section groups
        r_sg = await http.get("https://graph.microsoft.com/v1.0/me/onenote/sectionGroups", headers=headers)
        sgs = r_sg.json().get("value", [])
        print(f"\nTotal section groups in Graph: {len(sgs)}")
        for sg in sgs:
            print(f"  SG ID: {sg.get('id')} | NAME: '{sg.get('displayName')}'")

if __name__ == "__main__":
    asyncio.run(inspect())
