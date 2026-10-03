import json
import os
from app.database import SessionLocal, DesignRecord

def find_img_223():
    meta_path = os.path.join("data", "indexes", "users", "b6ecec459b998637", "saree_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            if it.get("image_order") == 223 or it.get("index_id") == 223 or "223" in str(it.get("id")):
                print("Found in saree_meta.json:")
                print(json.dumps(it, indent=2))
                return it

    db = SessionLocal()
    try:
        rec = db.query(DesignRecord).filter((DesignRecord.image_order == 223)).first()
        if rec:
            print("Found in DB:")
            d = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
            print(json.dumps(d, indent=2, default=str))
            return d
    finally:
        db.close()
    print("Image 223 not found")

if __name__ == "__main__":
    find_img_223()
