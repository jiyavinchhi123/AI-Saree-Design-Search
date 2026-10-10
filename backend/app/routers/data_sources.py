import os
import re
import cv2
import uuid
import hashlib
import numpy as np
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Header, Depends, HTTPException, Query, Body
from fastapi.responses import HTMLResponse, RedirectResponse
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
async def get_auth_url(db: Session = Depends(get_db)):
    """Generates standard Microsoft OAuth2 login authorization URL with verified parameters."""
    from app.main import onenote_client
    return onenote_client.get_auth_url(db=db)

@router.get("/onenote/auth/config")
async def get_auth_config(db: Session = Depends(get_db)):
    """Returns the current Microsoft Entra application configuration and redirect URI."""
    from app.main import onenote_client
    from app.onenote.graph_client import PROD_REDIRECT_URI
    onenote_client._load_settings_from_db(db)
    cid = onenote_client.get_effective_client_id(db)
    is_custom = onenote_client.is_custom_app(db)
    return {
        "is_configured": is_custom,
        "is_custom": is_custom,
        "client_id": cid if is_custom else "",
        "tenant_id": onenote_client.tenant_id,
        "has_secret": bool(onenote_client.client_secret),
        "redirect_uri": PROD_REDIRECT_URI
    }

@router.post("/onenote/auth/config")
async def save_auth_config(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Saves Microsoft Entra App ID and credentials into database settings."""
    from app.main import onenote_client
    from app.onenote.graph_client import PROD_REDIRECT_URI
    client_id = (payload.get("client_id") or "").strip()
    client_secret = (payload.get("client_secret") or "").strip()
    tenant_id = (payload.get("tenant_id") or "common").strip()

    if client_id:
        rec = db.query(SettingsRecord).filter(SettingsRecord.key == "ms_client_id").first()
        if not rec:
            rec = SettingsRecord(key="ms_client_id", value=client_id)
            db.add(rec)
        else:
            rec.value = client_id

    if client_secret:
        rec = db.query(SettingsRecord).filter(SettingsRecord.key == "ms_client_secret").first()
        if not rec:
            rec = SettingsRecord(key="ms_client_secret", value=client_secret)
            db.add(rec)
        else:
            rec.value = client_secret

    if tenant_id:
        rec = db.query(SettingsRecord).filter(SettingsRecord.key == "ms_tenant_id").first()
        if not rec:
            rec = SettingsRecord(key="ms_tenant_id", value=tenant_id)
            db.add(rec)
        else:
            rec.value = tenant_id

    db.commit()
    onenote_client._load_settings_from_db(db)
    return {
        "status": "success",
        "message": "Microsoft Entra App configuration saved successfully",
        "client_id": onenote_client.client_id,
        "is_configured": onenote_client.is_custom_app(db),
        "redirect_uri": PROD_REDIRECT_URI
    }

@router.get("/onenote/auth/callback")
async def auth_callback(
    code: str = None, 
    error: str = None, 
    error_description: str = None,
    redirect_uri: str = None, 
    format: str = Query("redirect"), 
    db: Session = Depends(get_db)
):
    """
    Handles OAuth redirect callback from Microsoft.
    Saves OneNote connection and redirects to the Vercel production URL (https://ai-saree-design-search.vercel.app/).
    """
    from app.main import onenote_client
    from app.onenote.graph_client import is_production, PROD_FRONTEND_URL, PROD_REDIRECT_URI
    import urllib.parse

    prod = is_production()
    frontend_base = PROD_FRONTEND_URL if prod else (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")
    if prod and ("localhost" in frontend_base or "127.0.0.1" in frontend_base):
        frontend_base = PROD_FRONTEND_URL

    # If Microsoft reports an error during login, redirect to Vercel production URL (never localhost in production)
    if error:
        err_msg = error_description or error or "Microsoft authentication declined"
        print(f"[Microsoft OAuth Callback Error] {error}: {error_description}", flush=True)
        return RedirectResponse(url=f"{frontend_base}/?error={urllib.parse.quote(err_msg)}", status_code=302)

    if not code:
        err_msg = "Missing authorization code from Microsoft"
        print(f"[Microsoft OAuth Callback Error] Missing authorization code in callback", flush=True)
        return RedirectResponse(url=f"{frontend_base}/?error={urllib.parse.quote(err_msg)}", status_code=302)

    callback_redirect_uri = PROD_REDIRECT_URI if prod else (redirect_uri or "http://localhost")
    result = await onenote_client.exchange_code_for_token(code, redirect_uri=callback_redirect_uri, db=db)
    if not result.get("success"):
        err_msg = result.get("error", "Token exchange failed")
        print(f"[Microsoft OAuth Callback Error] Token exchange failed: {err_msg}", flush=True)
        return RedirectResponse(url=f"{frontend_base}/?error={urllib.parse.quote(str(err_msg))}", status_code=302)

    user_info = result.get("user", {})
    user_id = user_info.get("id", "")
    print(f"[Microsoft OAuth Callback Success] Successfully authenticated: {user_info.get('displayName')} ({user_info.get('email')})", flush=True)

    # In production, redirect EXACTLY to https://ai-saree-design-search.vercel.app/ (with connected=true)
    redirect_target = f"{frontend_base}/?connected=true&user_id={user_id}"
    return RedirectResponse(url=redirect_target, status_code=302)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="0; url={redirect_target}">
    <title>OneNote Connected - AI Saree Design Search</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #6d28d9;
            --primary-light: #f5f3ff;
            --emerald: #059669;
            --emerald-light: #ecfdf5;
            --text-main: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border-subtle: #e2e8f0;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            background-image: 
                radial-gradient(at 0% 0%, rgba(245, 243, 255, 0.9) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(254, 243, 199, 0.5) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(245, 243, 255, 0.8) 0px, transparent 50%);
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
            -webkit-font-smoothing: antialiased;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid rgba(226, 232, 240, 0.9);
            padding: 44px 36px 36px 36px;
            border-radius: 24px;
            text-align: center;
            box-shadow: 
                0 25px 50px -12px rgba(109, 40, 217, 0.12),
                0 4px 12px rgba(0, 0, 0, 0.03);
            max-width: 460px;
            width: 100%;
            position: relative;
            overflow: hidden;
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #6d28d9, #10b981, #d97706);
        }}
        .icon-wrap {{
            width: 68px;
            height: 68px;
            border-radius: 50%;
            background: var(--emerald-light);
            border: 2px solid #a7f3d0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
            animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        @keyframes popIn {{
            0% {{ transform: scale(0.6); opacity: 0; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        .icon-wrap svg {{
            stroke: var(--emerald);
            width: 34px;
            height: 34px;
        }}
        h2 {{
            font-size: 1.55rem;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--primary-light);
            color: var(--primary);
            border: 1px solid #ddd6fe;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.76rem;
            font-weight: 700;
            margin-bottom: 20px;
            letter-spacing: 0.02em;
        }}
        .user-profile {{
            background: #f8fafc;
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            text-align: left;
        }}
        .avatar {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6d28d9, #431407);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.05rem;
            flex-shrink: 0;
        }}
        .user-name {{
            font-size: 0.92rem;
            font-weight: 700;
            color: var(--text-main);
        }}
        .user-email {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 2px;
            word-break: break-all;
        }}
        .status-text {{
            font-size: 0.86rem;
            color: var(--text-secondary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .spinner {{
            width: 14px;
            height: 14px;
            border: 2px solid #cbd5e1;
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .progress-track {{
            width: 100%;
            height: 5px;
            background: #f1f5f9;
            border-radius: 9999px;
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .progress-fill {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #6d28d9, #10b981);
            border-radius: 9999px;
            animation: fillProgress 1.2s ease-in-out forwards;
        }}
        @keyframes fillProgress {{
            0% {{ width: 0%; }}
            100% {{ width: 100%; }}
        }}
        .btn-continue {{
            display: inline-block;
            background: var(--primary);
            color: #ffffff;
            padding: 10px 22px;
            border-radius: 10px;
            font-size: 0.86rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        .btn-continue:hover {{
            background: #5b21b6;
            transform: translateY(-1px);
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon-wrap">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </div>
        <h2>Authentication Successful!</h2>
        <div class="badge">
            <span>&#10003; Microsoft OneNote Connected</span>
        </div>

        <div class="user-profile">
            <div class="avatar">{user_initial}</div>
            <div>
                <div class="user-name">{user_display}</div>
                <div class="user-email">{user_email_display}</div>
            </div>
        </div>

        <div class="status-text">
            <span class="spinner"></span>
            <span>Redirecting to your saree workspace...</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill"></div>
        </div>

        <a id="open-link" href="{redirect_target}" class="btn-continue">
            Open Workspace &rarr;
        </a>
    </div>
    <script>
        try {{
            localStorage.setItem('saree_current_user_id', '{user_id}');
        }} catch(e) {{}}
        if (window.opener) {{
            window.opener.postMessage({{ type: 'ONENOTE_AUTH_SUCCESS', userId: '{user_id}' }}, '*');
            setTimeout(() => window.close(), 600);
        }} else {{
            window.location.replace('{redirect_target}');
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

@router.post("/onenote/auth/exchange-code")
async def exchange_auth_code(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Exchanges an OAuth code or full redirect URL for tokens.
    Handles codes from redirects like http://localhost/?code=...
    """
    from app.main import onenote_client
    raw_code = payload.get("code", "").strip()
    if not raw_code:
        raise HTTPException(status_code=400, detail="Missing authorization code or URL")

    # If the user pasted the entire redirect URL, extract the code parameter
    import urllib.parse
    if "code=" in raw_code or "?" in raw_code:
        try:
            parsed = urllib.parse.urlparse(raw_code)
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs:
                raw_code = qs["code"][0]
        except Exception:
            pass

    from app.onenote.graph_client import is_production, PROD_REDIRECT_URI
    prod = is_production()
    if prod:
        redirect_uri = PROD_REDIRECT_URI
    else:
        env_r = (os.getenv("MS_REDIRECT_URI") or "").strip()
        redirect_uri = env_r if env_r else "http://localhost"

    result = await onenote_client.exchange_code_for_token(raw_code, redirect_uri=redirect_uri, db=db)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Code exchange failed or code expired"))

    user_info = result.get("user", {})
    return {
        "status": "success",
        "message": f"Successfully connected as {user_info.get('displayName')}!",
        "user": user_info
    }

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
                        finally:
                            if 'structural_map' in locals():
                                del structural_map
                            from app.vision.feature_extractor import trim_memory
                            trim_memory()

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
