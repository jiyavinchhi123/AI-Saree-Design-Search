import os
import json
import shutil
from datetime import datetime
from app.database import UserRecord, DesignRecord

def run_auto_seed(db):
    """
    If the database has no registered users (e.g. freshly deployed on Render),
    seeds the database and storage with initial verified OneNote designs and user session.
    """
    try:
        user_count = db.query(UserRecord).count()
        if user_count > 0:
            return

        seed_file = os.path.join("seed_data", "seed_data.json")
        if not os.path.exists(seed_file):
            seed_file = os.path.join(os.path.dirname(__file__), "..", "seed_data", "seed_data.json")
            if not os.path.exists(seed_file):
                print("[Seeder] No seed_data.json found. Skipping auto-seed.")
                return

        seed_dir = os.path.dirname(os.path.abspath(seed_file))
        print(f"[Seeder] Empty database detected. Seeding from {seed_dir}...")

        with open(seed_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_info = data.get("user")
        if user_info:
            connected_at = datetime.fromisoformat(user_info["connected_at"]) if user_info.get("connected_at") else datetime.utcnow()
            last_synced_at = datetime.fromisoformat(user_info["last_synced_at"]) if user_info.get("last_synced_at") else None
            
            user = UserRecord(
                id=user_info["id"],
                email=user_info["email"],
                display_name=user_info["display_name"],
                access_token=user_info.get("access_token"),
                refresh_token=user_info.get("refresh_token"),
                connected_at=connected_at,
                last_synced_at=last_synced_at,
                selected_notebooks_json=user_info.get("selected_notebooks_json", "[]"),
                total_designs=user_info.get("total_designs", 0)
            )
            db.add(user)

            user_id = user_info["id"]

            # Copy FAISS index and metadata
            user_idx_dir = os.path.join("data", "indexes", "users", user_id)
            os.makedirs(user_idx_dir, exist_ok=True)

            bin_src = os.path.join(seed_dir, "saree_faiss.bin")
            idx_dst = os.path.join(user_idx_dir, "saree_faiss.index")
            if os.path.exists(bin_src):
                shutil.copy2(bin_src, idx_dst)

            meta_src = os.path.join(seed_dir, "saree_meta.json")
            meta_dst = os.path.join(user_idx_dir, "saree_meta.json")
            if os.path.exists(meta_src):
                shutil.copy2(meta_src, meta_dst)

            # Copy images
            user_storage_dir = os.path.join("data", "storage", "users", user_id)
            os.makedirs(user_storage_dir, exist_ok=True)
            seed_images_dir = os.path.join(seed_dir, "images")
            if os.path.exists(seed_images_dir):
                for fname in os.listdir(seed_images_dir):
                    src = os.path.join(seed_images_dir, fname)
                    dst = os.path.join(user_storage_dir, fname)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)

        # Seed DesignRecords
        for d in data.get("designs", []):
            created_at = datetime.fromisoformat(d["created_at"]) if d.get("created_at") else datetime.utcnow()
            rec = DesignRecord(
                id=d["id"],
                design_id=d.get("design_id"),
                user_id=d.get("user_id"),
                title=d.get("title"),
                notebook_id=d.get("notebook_id"),
                notebook_name=d.get("notebook_name"),
                section_id=d.get("section_id"),
                section_name=d.get("section_name"),
                page_title=d.get("page_title"),
                page_id=d.get("page_id"),
                object_id=d.get("object_id"),
                image_order=d.get("image_order", 1),
                resource_id=d.get("resource_id"),
                resource_url=d.get("resource_url"),
                object_client_url=d.get("object_client_url"),
                object_web_url=d.get("object_web_url"),
                page_web_url=d.get("page_web_url"),
                onenote_web_url=d.get("onenote_web_url"),
                onenote_client_url=d.get("onenote_client_url"),
                image_url=d.get("image_url"),
                structural_preview_url=d.get("structural_preview_url"),
                category=d.get("category", "Traditional"),
                colorway=d.get("colorway"),
                weave_type=d.get("weave_type"),
                source_type=d.get("source_type", "onenote_live_sync"),
                created_at=created_at
            )
            db.add(rec)

        db.commit()
        print(f"[Seeder] Auto-seed complete. Seeded user {user_info.get('email')} and {len(data.get('designs', []))} designs.")

    except Exception as e:
        db.rollback()
        print(f"[Seeder] Error during auto-seed: {e}")
