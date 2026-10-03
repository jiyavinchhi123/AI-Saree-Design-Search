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

    # Live notebooks count directly from Graph if connected
    notebooks_count = len(notebooks)
    if is_connected and token:
        try:
            live_nbs = await onenote_client.list_notebooks(token)
            notebooks_count = len(live_nbs)
        except Exception:
            pass

    return OneNoteSyncStatus(
        is_configured=onenote_client.is_configured(),
        is_connected=is_connected,
        user_id=user.id,
        user_email=user.email,
        display_name=user.display_name,
        notebooks_count=notebooks_count,
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

def validate_graph_page_web_url(url: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validates that a URL is a valid, specific page-level web navigation URL
    directly from Microsoft Graph's links.oneNoteWebUrl.href.
    
    Backend Validation Requirements:
    - URL must start with https://
    - URL must NOT start with onenote:
    - URL must NOT be a generic OneNote homepage
    - URL must come directly from Graph's links.oneNoteWebUrl.href without synthetic construction
    """
    if not url or not isinstance(url, str):
        return False, "Microsoft Graph did not return links.oneNoteWebUrl.href for this page."
    cleaned = url.strip()
    if not cleaned.startswith("https://"):
        return False, f"Invalid URL scheme: URL must start with https:// ({cleaned[:40]}...)"
    if cleaned.lower().startswith("onenote:"):
        return False, "Invalid protocol: URL must not use the onenote: desktop protocol."
    lower = cleaned.lower()
    if (
        lower in ("https://onenote.com", "https://onenote.com/", "https://www.onenote.com", "https://www.onenote.com/", "https://onedrive.live.com", "https://onedrive.live.com/")
        or lower.startswith("https://www.onenote.com/notebooks")
    ):
        return False, f"Generic OneNote homepage rejected; must be a specific page web URL ({cleaned})"
    return True, None


@router.post("/onenote/sync")
async def sync_onenote(
    sync_req: Optional[NotebookSyncRequest] = None,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """
    Microsoft OneNote Cloud is the SINGLE SOURCE OF TRUTH.
    Scans the authenticated user's actual OneNote cloud pages, extracts embedded saree images,
    computes color-invariant embeddings (DINOv2), and reconciles the user's isolated index.
    - Cloud addition -> added to index and database
    - Cloud deletion -> removed from index and database
    - Stale / local backup / unverified records -> completely purged
    Zero write access: strictly Read-Only (Notes.Read, User.Read).
    """
    from app.main import onenote_client, extractor, vector_index_mgr
    from app.onenote.link_builder import build_object_client_url, build_object_web_url, extract_page_web_url

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

        pages_scanned = 0
        total_sections_scanned = 0
        cloud_embeddings = []
        cloud_metadatas = []
        cloud_design_ids = set()
        unsupported_pages = []

        for nb in notebooks:
            nb_id = nb.get("id")
            nb_name = nb.get("displayName", "Notebook")
            sections = await onenote_client.list_sections(nb_id, token)
            total_sections_scanned += len(sections)

            for sec in sections:
                sec_id = sec.get("id")
                sec_name = sec.get("displayName", "Section")
                pages = await onenote_client.list_pages(sec_id, token)

                for page in pages:
                    pages_scanned += 1
                    page_id = page.get("id")
                    page_title = page.get("title", "Untitled Page")
                    content_url = page.get("contentUrl")

                    # Requirement 1, 2, 5, 7, 10, 11:
                    # Retrieve official Graph links.oneNoteWebUrl.href directly
                    raw_graph_web_url = page.get("links", {}).get("oneNoteWebUrl", {}).get("href")
                    is_valid_url, url_err = validate_graph_page_web_url(raw_graph_web_url)
                    if not is_valid_url:
                        print(f"[OneNote Ingest] Skipping page '{page_title}' ({page_id}): {url_err}", flush=True)
                        unsupported_pages.append({
                            "page_id": page_id,
                            "page_title": page_title,
                            "reason": f"No valid web navigation URL: {url_err}"
                        })
                        continue

                    # Exact HTTPS value returned by Microsoft Graph (do NOT generate or transform)
                    page_web_url = raw_graph_web_url.strip()

                    if not content_url:
                        continue

                    _, images = await onenote_client.get_page_content_and_images(content_url, token)

                    # Rule 5 & 6: Each indexed OneNote page represents exactly ONE saree design/image.
                    # If a page contains multiple images, mark it unsupported and reject it from the exact-match index.
                    if not images or len(images) == 0:
                        print(f"[OneNote Ingest] Skipping page '{page_title}': No images found.", flush=True)
                        continue

                    if len(images) > 1:
                        print(f"[OneNote Ingest] REJECTED page '{page_title}' ({len(images)} images found): "
                              f"Under exact-match rules, each page must represent exactly ONE saree design. "
                              f"Multi-image pages are marked unsupported and excluded from exact-match index.", flush=True)
                        unsupported_pages.append({
                            "page_id": page_id,
                            "page_title": page_title,
                            "image_count": len(images),
                            "reason": "Contains multiple images; exact-match requires exactly 1 design per page."
                        })
                        continue

                    # Exactly ONE saree image on this page:
                    img_info = images[0]
                    order_num = 1
                    res_url = img_info.get("resource_url")
                    obj_id = img_info.get("object_id")
                    res_id = img_info.get("resource_id") or f"res_{page_id}_{order_num}"

                    # Strict Production Ingestion Validation:
                    if not obj_id:
                        print(f"[OneNote Ingest] Skipping image on page '{page_title}' (order #{order_num}): Missing real Microsoft Graph object_id.", flush=True)
                        continue

                    if not res_url or not page_id:
                        print(f"[OneNote Ingest] Skipping image on page '{page_title}' (order #{order_num}): Incomplete Graph metadata.", flush=True)
                        continue

                    # Deterministic design_id based on user_id, page_id and object_id
                    clean_key = f"{page_id}_{obj_id}"
                    key_hash = hashlib.sha256(clean_key.encode('utf-8')).hexdigest()[:8].upper()
                    design_id = f"MS-{safe_uid[:6]}-{key_hash}"
                    filename = f"{design_id}.jpg"
                    save_path = os.path.join(user_storage_dir, filename)

                    # Download binary image attachment from Graph if not already downloaded
                    if not os.path.exists(save_path):
                        ok = await onenote_client.download_image_resource(res_url, save_path, token)
                    else:
                        ok = True

                    if ok and os.path.exists(save_path):
                        try:
                            embedding, structural_map = extractor.extract_features_from_image(save_path)
                            prev_name = f"struct_{design_id}.jpg"
                            struct_path = os.path.join(user_storage_dir, prev_name)
                            cv2.imwrite(struct_path, structural_map)

                            # Exact metadata storage:
                            # Requirement 6 & 7: Store exact links.oneNoteWebUrl.href without modification
                            item_meta = {
                                "image_id": design_id,
                                "id": design_id,
                                "design_id": design_id,
                                "user_id": user.id,
                                "title": page_title,
                                "notebook_id": nb_id,
                                "notebook_name": nb_name,
                                "section_id": sec_id,
                                "section_name": sec_name,
                                "page_id": page_id,
                                "page_title": page_title,
                                "object_id": obj_id,
                                "image_order": 1,
                                "image_position": "Image #1 on page",
                                "resource_id": res_id,
                                "resource_url": res_url,
                                "page_web_url": page_web_url,
                                "oneNoteWebUrl": page_web_url,
                                "onenote_web_url": page_web_url,
                                "image_url": f"/api/storage/users/{safe_uid}/{filename}",
                                "structural_preview_url": f"/api/storage/users/{safe_uid}/{prev_name}",
                                "category": sec_name,
                                "source_type": "onenote_live_sync",
                                "is_verified_graph": True,
                                "synced_at": datetime.utcnow().isoformat()
                            }
                            cloud_embeddings.append(embedding)
                            cloud_metadatas.append(item_meta)
                            cloud_design_ids.add(design_id)
                            print(f"[OneNote Ingest] Verified cloud design page: '{page_title}' ({page_id}) -> {design_id}", flush=True)
                            print(f"  Exact Graph links.oneNoteWebUrl.href: {page_web_url}", flush=True)
                        except Exception as img_err:
                            print(f"[OneNote Ingest] Error indexing image {res_url}: {img_err}", flush=True)

        # RECONCILIATION: CLOUD IS THE ONLY SOURCE OF TRUTH
        # Rebuild vector index completely from active cloud items (handles additions, updates & deletions)
        user_index.rebuild(cloud_embeddings, cloud_metadatas)

        # In Database: Remove any designs for this user that no longer exist in OneNote cloud
        all_user_db_records = db.query(DesignRecord).filter(DesignRecord.user_id == user.id).all()
        for rec in all_user_db_records:
            if rec.id not in cloud_design_ids:
                db.delete(rec)

        # Upsert active cloud designs in Database
        for meta in cloud_metadatas:
            db_record = DesignRecord(
                id=meta["design_id"],
                design_id=meta["design_id"],
                user_id=user.id,
                title=meta["title"],
                notebook_id=meta.get("notebook_id"),
                notebook_name=meta.get("notebook_name"),
                section_id=meta.get("section_id"),
                section_name=meta.get("section_name"),
                page_title=meta.get("page_title"),
                page_id=meta.get("page_id"),
                object_id=meta.get("object_id"),
                image_order=meta.get("image_order", 1),
                resource_id=meta.get("resource_id"),
                resource_url=meta.get("resource_url"),
                page_web_url=meta["page_web_url"],
                onenote_web_url=meta["page_web_url"],
                image_url=meta["image_url"],
                structural_preview_url=meta["structural_preview_url"],
                category=meta["category"],
                source_type="onenote_live_sync"
            )
            db.merge(db_record)

        user.last_synced_at = datetime.utcnow()
        user.total_designs = user_index.count()
        db.commit()

        return {
            "status": "success",
            "message": f"Cloud synchronization complete. {user_index.count()} cloud saree designs indexed across {pages_scanned} pages.",
            "notebooks_found": len(notebooks),
            "sections_found": total_sections_scanned,
            "pages_scanned": pages_scanned,
            "total_images_found": len(cloud_metadatas),
            "indexed_count": user_index.count(),
            "total_user_designs": user_index.count(),
            "unsupported_pages": unsupported_pages
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
