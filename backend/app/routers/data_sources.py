import os
import re
import cv2
import uuid
import hashlib
import numpy as np
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Header, Depends, HTTPException, Query, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.models import OneNoteSyncStatus, NotebookSyncRequest
from app.database import get_db, UserRecord, DesignRecord, SettingsRecord

router = APIRouter(prefix="/api/data-sources", tags=["Data Sources"])

@router.get("/onenote/status", response_model=OneNoteSyncStatus)
async def get_onenote_status(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """
    Returns connection and sync status for the current active user.
    """
    from app.main import onenote_client, vector_index_mgr

    # If no specific user ID provided, look for the most recently connected user or check settings
    user = None
    if x_user_id:
        user = db.query(UserRecord).filter(UserRecord.id == x_user_id).first()
    if not user:
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()

    if not user:
        return OneNoteSyncStatus(
            is_configured=onenote_client.is_configured(),
            is_connected=False,
            user_id=None,
            user_email=None,
            display_name=None,
            notebooks_count=0,
            indexed_designs_count=0,
            last_synced=None
        )

    # Check if user's token is valid
    token = await onenote_client.get_valid_token_for_user(user.id, db)
    is_connected = bool(token)

    # Count distinct notebooks and designs for this specific user
    user_index = vector_index_mgr.get_index(user.id)
    notebooks = set()
    for item in user_index.metadata_store:
        if "notebook_name" in item:
            notebooks.add(item["notebook_name"])

    return OneNoteSyncStatus(
        is_configured=onenote_client.is_configured(),
        is_connected=is_connected,
        user_id=user.id,
        user_email=user.email,
        display_name=user.display_name,
        notebooks_count=len(notebooks),
        indexed_designs_count=user_index.count(),
        last_synced=user.last_synced_at.isoformat() if user.last_synced_at else None
    )

@router.get("/onenote/auth/url")
async def get_auth_url():
    """Generates standard Microsoft OAuth2 login authorization URL."""
    from app.main import onenote_client
    return onenote_client.get_auth_url()

@router.get("/onenote/auth/callback")
async def auth_callback(code: str = None, error: str = None, redirect_uri: str = None, db: Session = Depends(get_db)):
    """Handles OAuth redirect callback from Microsoft."""
    from app.main import onenote_client
    if error:
        raise HTTPException(status_code=400, detail=f"Authentication error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    result = await onenote_client.exchange_code_for_token(code, redirect_uri=redirect_uri, db=db)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Token exchange failed"))

    user_info = result.get("user", {})
    user_id = user_info.get("id", "")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OneNote Connected - AI Saree Design Search</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0d0f17;
                color: #f1f5f9;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }}
            .card {{
                background: #171b26;
                border: 1px solid rgba(212, 175, 55, 0.3);
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                max-width: 440px;
            }}
            h2 {{ color: #d4af37; margin-bottom: 12px; }}
            p {{ color: #94a3b8; font-size: 15px; line-height: 1.6; }}
            a {{ color: #d4af37; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Authentication Successful!</h2>
            <p>Connected as <strong>{user_info.get("displayName", "User")}</strong> ({user_info.get("email", "")})</p>
            <p>Redirecting to your saree workspace...</p>
        </div>
        <script>
            try {{
                localStorage.setItem('saree_current_user_id', '{user_id}');
            }} catch(e) {{}}
            if (window.opener) {{
                window.opener.postMessage({{ type: 'ONENOTE_AUTH_SUCCESS', userId: '{user_id}' }}, '*');
                setTimeout(() => window.close(), 1200);
            }} else {{
                setTimeout(() => {{ window.location.href = 'http://localhost:5173/data-sources?user_id={user_id}'; }}, 1200);
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/onenote/device-flow/start")
async def start_device_login():
    """
    Initiates Microsoft Device Login for any user.
    Returns user_code, verification_uri, and session_id.
    """
    from app.main import onenote_client
    try:
        flow = onenote_client.start_device_flow()
        return {
            "status": "success",
            "session_id": flow.get("session_id"),
            "user_code": flow.get("user_code"),
            "verification_uri": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
            "message": flow.get("message"),
            "expires_in": flow.get("expires_in")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate device login: {str(e)}")

@router.post("/onenote/device-flow/complete")
async def complete_device_login(
    session_id: str = Query("default"),
    db: Session = Depends(get_db)
):
    """
    Completes device code login after user authenticates on microsoft.com/devicelogin.
    Registers the authenticated user session.
    """
    from app.main import onenote_client
    result = await onenote_client.complete_device_flow(session_id=session_id, db=db)
    
    if result.get("status") == "pending" or result.get("error") == "authorization_pending":
        return {"status": "pending", "message": "Waiting for authorization on microsoft.com/devicelogin"}

    if not result.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=result.get("error", "Login authorization still pending. Please approve code on microsoft.com/devicelogin")
        )
    
    user_info = result.get("user", {})
    return {
        "status": "success",
        "message": f"Successfully connected as {user_info.get('displayName')}!",
        "user": user_info
    }

@router.get("/onenote/notebooks")
async def get_user_notebooks(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """
    Fetches the authenticated user's actual OneNote notebooks and sections directly from Microsoft Graph API.
    """
    from app.main import onenote_client

    user = None
    if x_user_id:
        user = db.query(UserRecord).filter(UserRecord.id == x_user_id).first()
    if not user:
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()

    if not user:
        raise HTTPException(status_code=401, detail="No connected Microsoft OneNote account. Please connect first.")

    token = await onenote_client.get_valid_token_for_user(user.id, db)
    if not token:
        raise HTTPException(status_code=401, detail="Microsoft session expired. Please reconnect your account.")

    raw_notebooks = await onenote_client.list_notebooks(token)
    notebooks = []

    for nb in raw_notebooks:
        nb_id = nb.get("id")
        nb_name = nb.get("displayName", "Notebook")
        sections_raw = await onenote_client.list_sections(nb_id, token)
        sections = [
            {"id": s.get("id"), "displayName": s.get("displayName")}
            for s in sections_raw
        ]
        notebooks.append({
            "id": nb_id,
            "displayName": nb_name,
            "createdDateTime": nb.get("createdDateTime"),
            "sections": sections,
            "sectionsCount": len(sections)
        })

    return {
        "status": "success",
        "user_id": user.id,
        "user_email": user.email,
        "notebooks": notebooks,
        "total_notebooks": len(notebooks)
    }

def sync_local_onenote_backups(user_id: str, user_storage_dir: str, user_index, db: Session, extractor, selected_nb_names=None) -> int:
    """
    Scans Windows OneNote local backup/cache sections for designs.
    Ensures sections held locally (or blocked from cloud sync due to OneDrive storage quota)
    are seamlessly ingested into the AI index with full hierarchy and deep links.
    """
    backup_root = os.path.expanduser(r"~\AppData\Local\Microsoft\OneNote\16.0\Backup")
    if not os.path.exists(backup_root):
        return 0

    safe_uid = re.sub(r'[^a-zA-Z0-9_\-]', '_', user_id)
    existing_ids = {item.get("id") or item.get("design_id") for item in user_index.metadata_store}
    indexed_from_local = 0

    for nb_dir_name in os.listdir(backup_root):
        nb_dir = os.path.join(backup_root, nb_dir_name)
        if not os.path.isdir(nb_dir):
            continue
        if selected_nb_names and nb_dir_name not in selected_nb_names:
            continue

        for fname in os.listdir(nb_dir):
            if not fname.endswith(".one") or "OneNote_RecycleBin" in fname:
                continue

            clean_sec_name = re.sub(r'\s*\(On\s+[\d\-]+\)\.one$', '', fname)
            clean_sec_name = re.sub(r'\.one$', '', clean_sec_name).strip()

            file_path = os.path.join(nb_dir, fname)
            try:
                file_size = os.path.getsize(file_path)
                if file_size < 100000:
                    continue

                with open(file_path, "rb") as f:
                    data = f.read()

                pos = 0
                while True:
                    start = data.find(b"\xff\xd8\xff", pos)
                    if start == -1:
                        break
                    end = data.find(b"\xff\xd9", start)
                    if end == -1:
                        break
                    img_bytes = data[start:end+2]
                    pos = end + 2

                    if len(img_bytes) > 20000:
                        img_hash = hashlib.sha256(img_bytes).hexdigest()[:8].upper()
                        design_id = f"ONENOTE-{safe_uid[:6]}-{img_hash}"

                        if design_id in existing_ids:
                            continue

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

                            web_url = f"https://onedrive.live.com/redir.aspx?cid={user_id.upper()}&page=edit&resid={user_id.upper()}!1012&wd=target%28{clean_sec_name}.one%7CSaree%20designs%29"
                            client_url = f"onenote:https://d.docs.live.net/{user_id.lower()}/OneNote%20Notebooks/{nb_dir_name}/{clean_sec_name}.one#Saree%20designs"

                            item_meta = {
                                "id": design_id,
                                "design_id": design_id,
                                "user_id": user_id,
                                "title": "Saree designs",
                                "notebook_name": nb_dir_name,
                                "section_name": clean_sec_name,
                                "page_title": "Saree designs",
                                "onenote_web_url": web_url,
                                "onenote_client_url": client_url,
                                "image_url": f"/api/storage/users/{safe_uid}/{filename}",
                                "structural_preview_url": f"/api/storage/users/{safe_uid}/{prev_name}",
                                "category": "Ikat & Silk",
                                "source_type": "onenote_app_sync",
                                "synced_at": datetime.utcnow().isoformat()
                            }
                            user_index.add_design(embedding, item_meta)
                            existing_ids.add(design_id)

                            db_record = DesignRecord(
                                id=design_id,
                                design_id=design_id,
                                user_id=user_id,
                                title="Saree designs",
                                notebook_name=nb_dir_name,
                                section_name=clean_sec_name,
                                page_title="Saree designs",
                                onenote_web_url=web_url,
                                onenote_client_url=client_url,
                                image_url=item_meta["image_url"],
                                structural_preview_url=item_meta["structural_preview_url"],
                                category="Ikat & Silk",
                                source_type="onenote_app_sync"
                            )
                            db.merge(db_record)
                            indexed_from_local += 1
                        except Exception as e:
                            print(f"[OneNote Ingest] Error indexing local image: {e}")
            except Exception as err:
                print(f"[OneNote Ingest] Error reading backup file {file_path}: {err}")

    return indexed_from_local

@router.post("/onenote/sync")
async def sync_onenote(
    sync_req: Optional[NotebookSyncRequest] = None,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """
    Scans the authenticated user's actual OneNote pages, extracts embedded saree images,
    computes color-invariant embeddings (DINOv2), and indexes them into their isolated user index.
    Zero write access: strictly Read-Only.
    """
    from app.main import onenote_client, extractor, vector_index_mgr

    user = None
    if x_user_id:
        user = db.query(UserRecord).filter(UserRecord.id == x_user_id).first()
    if not user:
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()

    if not user:
        raise HTTPException(status_code=401, detail="No Microsoft OneNote account connected.")

    token = await onenote_client.get_valid_token_for_user(user.id, db)
    if not token:
        raise HTTPException(status_code=401, detail="Session expired. Please reconnect to Microsoft.")

    user_index = vector_index_mgr.get_index(user.id)
    safe_uid = re.sub(r'[^a-zA-Z0-9_\-]', '_', user.id)
    user_storage_dir = os.path.join("data", "storage", "users", safe_uid)
    os.makedirs(user_storage_dir, exist_ok=True)

    selected_nb_ids = sync_req.notebook_ids if (sync_req and sync_req.notebook_ids) else None

    try:
        notebooks = await onenote_client.list_notebooks(token)
        if selected_nb_ids:
            notebooks = [nb for nb in notebooks if nb.get("id") in selected_nb_ids]

        indexed_count = 0
        pages_scanned = 0
        total_images_found = 0

        for nb in notebooks:
            nb_id = nb.get("id")
            nb_name = nb.get("displayName", "Notebook")
            sections = await onenote_client.list_sections(nb_id, token)

            for sec in sections:
                sec_id = sec.get("id")
                sec_name = sec.get("displayName", "Section")
                pages = await onenote_client.list_pages(sec_id, token)

                for page in pages:
                    pages_scanned += 1
                    page_id = page.get("id")
                    page_title = page.get("title", "Untitled Page")
                    content_url = page.get("contentUrl")
                    web_url = page.get("links", {}).get("oneNoteWebUrl", {}).get("href")
                    client_url = page.get("links", {}).get("oneNoteClientUrl", {}).get("href")

                    if not content_url:
                        continue

                    _, images = await onenote_client.get_page_content_and_images(content_url, token)
                    total_images_found += len(images)

                    for idx, img_info in enumerate(images):
                        res_url = img_info.get("resource_url")
                        if not res_url:
                            continue

                        design_id = f"MS-{safe_uid[:6]}-{uuid.uuid4().hex[:6].upper()}"
                        filename = f"{design_id}_p{idx}.jpg"
                        save_path = os.path.join(user_storage_dir, filename)

                        ok = await onenote_client.download_image_resource(res_url, save_path, token)
                        if ok and os.path.exists(save_path):
                            try:
                                embedding, structural_map = extractor.extract_features_from_image(save_path)
                                prev_name = f"struct_{design_id}.jpg"
                                struct_path = os.path.join(user_storage_dir, prev_name)
                                cv2.imwrite(struct_path, structural_map)

                                item_meta = {
                                    "id": design_id,
                                    "design_id": design_id,
                                    "user_id": user.id,
                                    "title": page_title,
                                    "notebook_name": nb_name,
                                    "notebook_id": nb_id,
                                    "section_name": sec_name,
                                    "section_id": sec_id,
                                    "page_title": page_title,
                                    "page_id": page_id,
                                    "onenote_web_url": web_url,
                                    "onenote_client_url": client_url,
                                    "image_url": f"/api/storage/users/{safe_uid}/{filename}",
                                    "structural_preview_url": f"/api/storage/users/{safe_uid}/{prev_name}",
                                    "category": sec_name,
                                    "source_type": "onenote_live_sync",
                                    "synced_at": datetime.utcnow().isoformat()
                                }
                                user_index.add_design(embedding, item_meta)

                                db_record = DesignRecord(
                                    id=design_id,
                                    design_id=design_id,
                                    user_id=user.id,
                                    title=page_title,
                                    notebook_name=nb_name,
                                    section_name=sec_name,
                                    page_title=page_title,
                                    onenote_web_url=web_url,
                                    onenote_client_url=client_url,
                                    image_url=item_meta["image_url"],
                                    structural_preview_url=item_meta["structural_preview_url"],
                                    category=sec_name,
                                    source_type="onenote_live_sync"
                                )
                                db.merge(db_record)
                                indexed_count += 1
                            except Exception as img_err:
                                print(f"[OneNote Ingest] Error indexing image {res_url}: {img_err}")

        # Scan local OneNote backup sections for sections not synced to cloud
        local_added = sync_local_onenote_backups(
            user_id=user.id,
            user_storage_dir=user_storage_dir,
            user_index=user_index,
            db=db,
            extractor=extractor
        )
        indexed_count += local_added

        # Save user's isolated index
        user_index.save()
        user.last_synced_at = datetime.utcnow()
        user.total_designs = user_index.count()
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully indexed {indexed_count} saree design images from OneNote ({pages_scanned} pages scanned, {local_added} from local desktop section).",
            "indexed_count": indexed_count,
            "pages_scanned": pages_scanned,
            "total_images_found": total_images_found + local_added,
            "total_user_designs": user_index.count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OneNote sync failed: {str(e)}")

@router.post("/onenote/disconnect")
async def disconnect_onenote(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """
    Disconnects the active user session.
    """
    user = None
    if x_user_id:
        user = db.query(UserRecord).filter(UserRecord.id == x_user_id).first()
    if not user:
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()

    if user:
        user.access_token = None
        user.refresh_token = None
        db.commit()

    return {"status": "success", "message": "Successfully disconnected Microsoft OneNote"}
