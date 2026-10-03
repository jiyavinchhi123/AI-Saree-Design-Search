import json
import os
import re
from app.database import SessionLocal, DesignRecord
from app.onenote.link_builder import is_real_onenote_object_id, is_real_graph_id

def sanitize():
    meta_path = os.path.join("data", "indexes", "users", "b6ecec459b998637", "saree_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        
        cleaned_count = 0
        for it in items:
            raw_obj = it.get("object_id")
            raw_pg = it.get("page_id")
            raw_client = it.get("onenote_client_url")
            
            # Check if synthetic
            if not is_real_onenote_object_id(raw_obj):
                it["object_id"] = None
                it["object_client_url"] = None
            if not is_real_graph_id(raw_pg):
                it["page_id"] = None
            if raw_client and ("img-obj-" in raw_client or "00000000000" in raw_client or "section-id=" not in raw_client):
                it["onenote_client_url"] = None
                cleaned_count += 1
            
            # Clean web url
            web_url = it.get("onenote_web_url") or it.get("object_web_url")
            if web_url and "object-id=" in web_url:
                web_url = re.sub(r'[?&]object-id=[^&]+', '', web_url)
                it["onenote_web_url"] = web_url
                it["object_web_url"] = web_url

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        print(f"Sanitized {cleaned_count} items in {meta_path}")

    db = SessionLocal()
    try:
        recs = db.query(DesignRecord).all()
        db_cleaned = 0
        for r in recs:
            if not is_real_onenote_object_id(r.object_id):
                r.object_id = None
                r.object_client_url = None
            if not is_real_graph_id(r.page_id):
                r.page_id = None
            if r.onenote_client_url and ("img-obj-" in r.onenote_client_url or "00000000000" in r.onenote_client_url or "section-id=" not in r.onenote_client_url):
                r.onenote_client_url = None
                db_cleaned += 1
            if r.onenote_web_url and "object-id=" in r.onenote_web_url:
                r.onenote_web_url = re.sub(r'[?&]object-id=[^&]+', '', r.onenote_web_url)
                r.object_web_url = r.onenote_web_url
        db.commit()
        print(f"Sanitized {db_cleaned} records in DB")
    finally:
        db.close()

if __name__ == "__main__":
    sanitize()
