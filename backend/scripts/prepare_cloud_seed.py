import os
import shutil
import json
from app.database import SessionLocal, UserRecord, DesignRecord

def prepare_seed():
    seed_dir = os.path.join(os.path.dirname(__file__), "..", "seed_data")
    images_dir = os.path.join(seed_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    db = SessionLocal()
    try:
        user = db.query(UserRecord).first()
        if not user:
            print("No user found in local database!")
            return

        designs = db.query(DesignRecord).all()

        user_data = {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "access_token": user.access_token,
            "refresh_token": user.refresh_token,
            "connected_at": user.connected_at.isoformat() if user.connected_at else None,
            "last_synced_at": user.last_synced_at.isoformat() if user.last_synced_at else None,
            "selected_notebooks_json": user.selected_notebooks_json,
            "total_designs": user.total_designs
        }

        designs_data = []
        for d in designs:
            designs_data.append({
                "id": d.id,
                "design_id": d.design_id,
                "user_id": d.user_id,
                "title": d.title,
                "notebook_id": d.notebook_id,
                "notebook_name": d.notebook_name,
                "section_id": d.section_id,
                "section_name": d.section_name,
                "page_title": d.page_title,
                "page_id": d.page_id,
                "object_id": d.object_id,
                "image_order": d.image_order,
                "resource_id": d.resource_id,
                "resource_url": d.resource_url,
                "object_client_url": d.object_client_url,
                "object_web_url": d.object_web_url,
                "page_web_url": d.page_web_url,
                "onenote_web_url": d.onenote_web_url,
                "onenote_client_url": d.onenote_client_url,
                "image_url": d.image_url,
                "structural_preview_url": d.structural_preview_url,
                "category": d.category,
                "colorway": d.colorway,
                "weave_type": d.weave_type,
                "source_type": d.source_type,
                "created_at": d.created_at.isoformat() if d.created_at else None
            })

        payload = {
            "user": user_data,
            "designs": designs_data
        }

        with open(os.path.join(seed_dir, "seed_data.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # Copy FAISS index and metadata
        user_idx_dir = os.path.join("data", "indexes", "users", user.id)
        faiss_src = os.path.join(user_idx_dir, "saree_faiss.index")
        meta_src = os.path.join(user_idx_dir, "saree_meta.json")

        if os.path.exists(faiss_src):
            shutil.copy2(faiss_src, os.path.join(seed_dir, "saree_faiss.bin"))
        if os.path.exists(meta_src):
            shutil.copy2(meta_src, os.path.join(seed_dir, "saree_meta.json"))

        # Copy image files for the 5 designs
        user_storage_dir = os.path.join("data", "storage", "users", user.id)
        with open(meta_src, "r", encoding="utf-8") as f:
            meta_items = json.load(f)

        copied_count = 0
        for item in meta_items:
            img_url = item.get("image_url", "")
            struct_url = item.get("structural_preview_url", "")
            for url in [img_url, struct_url]:
                if url:
                    fname = os.path.basename(url)
                    src_path = os.path.join(user_storage_dir, fname)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, os.path.join(images_dir, fname))
                        copied_count += 1

        print(f"Successfully exported seed data for user {user.email}:")
        print(f"- User Record: {user.display_name}")
        print(f"- Designs: {len(designs_data)}")
        print(f"- Images copied: {copied_count}")
        print(f"- Saved in: {os.path.abspath(seed_dir)}")

    finally:
        db.close()

if __name__ == "__main__":
    prepare_seed()
