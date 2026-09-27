import json
import re
import urllib.parse
import sqlite3
import os

def run():
    meta_path = os.path.join("data", "indexes", "saree_meta.json")
    if not os.path.exists(meta_path):
        print(f"File {meta_path} not found.")
        return

    with open(meta_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"Updating {len(items)} catalog items...")

    for it in items:
        raw = it.get("raw_title") or it.get("title") or it.get("page_title") or ""
        clean = re.sub(r'(_jpg|\.jpg|_jpeg|\.jpeg|_png|\.png)\.rf\.[a-f0-9]+', '', raw, flags=re.IGNORECASE)
        clean = clean.replace('-', ' ').replace('_', ' ').strip()
        words = clean.split()
        display_title = ' '.join(w.capitalize() if not w.isupper() else w for w in words) or "Saree Design"

        d_id = it.get("id") or it.get("design_id")
        nb = it.get("notebook_name") or "valid"
        sec = it.get("section_name") or "General"

        it["clean_title"] = display_title
        it["page_title"] = display_title
        it["title"] = display_title
        it["raw_title"] = raw
        it["onenote_web_url"] = f"/api/designs/{d_id}/open-onenote"
        it["onenote_client_url"] = f"onenote:?title={urllib.parse.quote(f'{sec} {display_title}')}"
        it["local_path"] = f"C:/Users/jiyav/Downloads/archive/{nb}/{sec}/{raw}.jpg"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    print("Updated saree_meta.json successfully!")

    db_path = os.path.join("data", "saree_search.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, top_match_id, top_match_title, section_name FROM search_history")
        rows = cur.fetchall()
        for row in rows:
            hid, mid, mtitle, sec = row
            if mid:
                clean = re.sub(r'(_jpg|\.jpg|_jpeg|\.jpeg|_png|\.png)\.rf\.[a-f0-9]+', '', mtitle or '', flags=re.IGNORECASE)
                clean = clean.replace('-', ' ').replace('_', ' ').strip()
                words = clean.split()
                display_title = ' '.join(w.capitalize() if not w.isupper() else w for w in words) or mtitle
                new_url = f"/api/designs/{mid}/open-onenote"
                cur.execute(
                    "UPDATE search_history SET top_match_title = ?, page_title = ?, onenote_web_url = ? WHERE id = ?",
                    (display_title, display_title, new_url, hid)
                )
        conn.commit()
        conn.close()
        print("Updated search_history in database successfully!")

if __name__ == "__main__":
    run()
