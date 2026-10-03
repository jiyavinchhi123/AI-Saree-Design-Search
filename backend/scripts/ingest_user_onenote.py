import os
import re
import cv2
import uuid
import numpy as np
from datetime import datetime
from app.database import SessionLocal, UserRecord, DesignRecord
from app.main import extractor, vector_index_mgr

def ingest_local_onenote_section(one_file_path: str, user_id: str, nb_name: str, sec_name: str, page_title: str):
    print(f"Ingesting OneNote section from {one_file_path} for user {user_id}...")
    user_index = vector_index_mgr.get_index(user_id)
    safe_uid = re.sub(r'[^a-zA-Z0-9_\-]', '_', user_id)
    user_storage_dir = os.path.join("data", "storage", "users", safe_uid)
    os.makedirs(user_storage_dir, exist_ok=True)

    with open(one_file_path, "rb") as f:
        data = f.read()

    db = SessionLocal()
    try:
        user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
        pos = 0
        idx = 0
        added_count = 0

        while True:
            start = data.find(b"\xff\xd8\xff", pos)
            if start == -1:
                break
            end = data.find(b"\xff\xd9", start)
            if end == -1:
                break
            img_bytes = data[start:end+2]
            pos = end + 2

            # Filter out tiny icons
            if len(img_bytes) > 20000:
                design_id = f"ONENOTE-{safe_uid[:6]}-{uuid.uuid4().hex[:6].upper()}"
                filename = f"{design_id}.jpg"
                save_path = os.path.join(user_storage_dir, filename)

                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue

                cv2.imwrite(save_path, img)

                try:
                    embedding, structural_map = extractor.extract_features_from_image(img)
                    prev_name = f"struct_{design_id}.jpg"
                    struct_path = os.path.join(user_storage_dir, prev_name)
                    cv2.imwrite(struct_path, structural_map)

                    web_url = f"https://onedrive.live.com/redir.aspx?cid={user_id.upper()}&page=edit&resid={user_id.upper()}!1012&wd=target%28{sec_name}.one%7C{page_title}%29"
                    client_url = None

                    item_meta = {
                        "id": design_id,
                        "design_id": design_id,
                        "user_id": user_id,
                        "title": page_title,
                        "notebook_name": nb_name,
                        "section_name": sec_name,
                        "page_title": page_title,
                        "onenote_web_url": web_url,
                        "onenote_client_url": client_url,
                        "image_url": f"/api/storage/users/{safe_uid}/{filename}",
                        "structural_preview_url": f"/api/storage/users/{safe_uid}/{prev_name}",
                        "category": "Ikat & Silk",
                        "source_type": "onenote_app_sync",
                        "synced_at": datetime.utcnow().isoformat()
                    }
                    user_index.add_design(embedding, item_meta)

                    db_record = DesignRecord(
                        id=design_id,
                        design_id=design_id,
                        user_id=user_id,
                        title=page_title,
                        notebook_name=nb_name,
                        section_name=sec_name,
                        page_title=page_title,
                        onenote_web_url=web_url,
                        onenote_client_url=client_url,
                        image_url=item_meta["image_url"],
                        structural_preview_url=item_meta["structural_preview_url"],
                        category="Ikat & Silk",
                        source_type="onenote_app_sync"
                    )
                    db.merge(db_record)
                    added_count += 1
                    if added_count % 25 == 0:
                        print(f"Indexed {added_count} designs so far...")
                except Exception as e:
                    print(f"Error processing image {idx}: {e}")
                idx += 1

        user_index.save()
        if user:
            user.last_synced_at = datetime.utcnow()
            user.total_designs = user_index.count()
        db.commit()
        print(f"Successfully indexed {added_count} OneNote saree designs into user {user_id} index! Total in index: {user_index.count()}")
    finally:
        db.close()

if __name__ == "__main__":
    file_path = r"C:\Users\jiyav\AppData\Local\Microsoft\OneNote\16.0\Backup\My Notebook\New Section 2 (On 25-09-2026).one"
    ingest_local_onenote_section(
        one_file_path=file_path,
        user_id="b6ecec459b998637",
        nb_name="My Notebook",
        sec_name="New Section 2",
        page_title="Saree designs"
    )
