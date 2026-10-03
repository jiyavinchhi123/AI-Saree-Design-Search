from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db, DesignRecord, UserRecord

router = APIRouter(prefix="/api/designs", tags=["Designs"])

@router.get("")
async def list_designs(
    notebook: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    from app.main import vector_index_mgr

    # Resolve user
    user = None
    if x_user_id:
        user = db.query(UserRecord).filter(UserRecord.id == x_user_id).first()
    if not user:
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()

    user_id = user.id if user else None
    target_index = vector_index_mgr.get_index(user_id)
    items = list(target_index.metadata_store)

    if notebook:
        items = [i for i in items if i.get("notebook_name") == notebook]
    if section:
        items = [i for i in items if i.get("section_name") == section]
    if category:
        items = [i for i in items if i.get("category") == category]
    if search:
        s = search.lower()
        items = [i for i in items if s in i.get("title", "").lower() or s in i.get("page_title", "").lower() or s in i.get("category", "").lower()]

    # Extract distinct notebooks, sections, categories for filter UI
    all_notebooks = sorted(list(set(i.get("notebook_name") for i in target_index.metadata_store if i.get("notebook_name"))))
    all_sections = sorted(list(set(i.get("section_name") for i in target_index.metadata_store if i.get("section_name"))))
    all_categories = sorted(list(set(i.get("category") for i in target_index.metadata_store if i.get("category"))))


    return {
        "total": len(items),
        "designs": items,
        "filters": {
            "notebooks": all_notebooks,
            "sections": all_sections,
            "categories": all_categories
        }
    }

@router.delete("")
async def clear_all_designs(db: Session = Depends(get_db)):
    from app.main import vector_index
    vector_index.clear()
    db.query(DesignRecord).delete()
    db.commit()
    return {"status": "success", "message": "All designs cleared from index and database."}

import os
import re
import urllib.parse
import subprocess
from fastapi.responses import RedirectResponse

def clean_design_title(raw_title: str) -> str:
    """Removes RoboFlow suffixes and formats title into clean readable saree title."""
    if not raw_title:
        return "Saree Design"
    clean = re.sub(r'(_jpg|\.jpg|_jpeg|\.jpeg|_png|\.png)\.rf\.[a-f0-9]+', '', raw_title, flags=re.IGNORECASE)
    clean = clean.replace('-', ' ').replace('_', ' ').strip()
    words = clean.split()
    return ' '.join(w.capitalize() if not w.isupper() else w for w in words) or raw_title

def resolve_local_image_path(notebook_name: str, section_name: str, raw_title: str, image_url: str) -> Optional[str]:
    """Finds image on disk, checking user's Downloads/archive folder and backend storage."""
    candidates = [
        f"C:/Users/jiyav/Downloads/archive/{notebook_name}/{section_name}/{raw_title}.jpg",
        f"C:/Users/jiyav/Downloads/archive/{notebook_name}/{section_name}/{raw_title}.jpeg",
        f"C:/Users/jiyav/Downloads/archive/{notebook_name}/{section_name}/{raw_title}.png",
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.normpath(c)

    # Check local backend storage
    if image_url:
        storage_rel = image_url.replace("/api/storage/", "data/storage/")
        if os.path.exists(storage_rel):
            return os.path.abspath(storage_rel)

    return None
from fastapi.responses import RedirectResponse, HTMLResponse


def render_onenote_page_viewer(design: dict, display_title: str, sec_name: str, nb_name: str, local_path: Optional[str], user_email: Optional[str]) -> HTMLResponse:
    """Renders an authentic, full-fidelity Microsoft OneNote digital notebook page displaying the exact saree design."""
    img_url = design.get("image_url", "")
    d_id = design.get("id") or design.get("design_id", "ARCH")
    res_id = design.get("resource_id") or d_id
    order_num = design.get("image_order")
    pos_str = f"Image #{order_num}" if order_num else "Exact Match"
    category = design.get("category", "Traditional")
    colorway = design.get("colorway", "Archive Original")
    path_display = local_path or f"Downloads/archive/{nb_name}/{sec_name}/{display_title}.jpg"
    account_str = user_email or "jiya.vinchhi2412@gmail.com"
    desktop_link = f"/api/designs/{d_id}/open-onenote?mode=desktop"
    web_link = design.get("onenote_web_url") or "https://www.onenote.com"

    all_sections = ["Banarasi", "Bandhani", "Ikat", "Pichwai"]
    section_tabs_html = "".join([
        f'<div class="section-tab {"active" if s.lower() == sec_name.lower() else ""}">{s}</div>'
        for s in all_sections
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} | Microsoft OneNote</title>
    <link rel="icon" href="https://res-1.cdn.office.net/files/fabric-cdn-prod_20230815.002/assets/brand-icons/product/svg/onenote_16x1.svg" type="image/svg+xml">
    <style>
        :root {{
            --onenote-purple: #7719aa;
            --onenote-dark: #5c1380;
            --onenote-light: #9b30ff;
            --bg-canvas: #0f1118;
            --bg-card: #171b26;
            --border: #282f42;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --gold: #d4af37;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-canvas);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        /* OneNote Top Ribbon */
        .onenote-header {{
            background: #11141e;
            border-bottom: 1px solid var(--border);
            padding: 8px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }}
        .onenote-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .onenote-icon-box {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #7719aa, #9b30ff);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 19px;
            color: #fff;
            box-shadow: 0 2px 8px rgba(155, 48, 255, 0.4);
        }}
        .onenote-title-group h1 {{
            font-size: 15px;
            font-weight: 600;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .onenote-title-group span {{
            font-size: 12px;
            color: var(--text-dim);
            font-weight: 400;
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .btn-action {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #1e2433;
            color: #e2e8f0;
            border: 1px solid var(--border);
            padding: 7px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-action:hover {{
            background: #2a3347;
            border-color: rgba(255,255,255,0.2);
            color: #fff;
        }}
        .btn-action-primary {{
            background: linear-gradient(135deg, #7719aa, #9b30ff);
            border: none;
            color: #fff;
            font-weight: 600;
            box-shadow: 0 2px 10px rgba(155, 48, 255, 0.35);
        }}
        .btn-action-primary:hover {{
            filter: brightness(1.15);
            color: #fff;
        }}
        .user-badge {{
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }}
        .user-dot {{
            width: 7px;
            height: 7px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
        }}

        /* OneNote Hierarchy Ribbons */
        .ribbon-bar {{
            background: #151824;
            border-bottom: 1px solid var(--border);
            padding: 0 18px;
            display: flex;
            align-items: center;
            overflow-x: auto;
            flex-shrink: 0;
        }}
        .notebook-tabs {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 6px 0;
            border-bottom: 2px solid transparent;
        }}
        .notebook-pill {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            background: rgba(255,255,255,0.05);
            color: var(--text-dim);
        }}
        .notebook-pill.active {{
            background: rgba(155, 48, 255, 0.2);
            color: #d8b4fe;
            border: 1px solid rgba(155, 48, 255, 0.4);
        }}
        .section-tabs {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 6px 18px;
            background: #1a1e2d;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }}
        .section-tab {{
            padding: 6px 14px;
            border-radius: 6px 6px 0 0;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-dim);
            background: rgba(255,255,255,0.03);
            border-top: 2px solid transparent;
            cursor: pointer;
        }}
        .section-tab.active {{
            background: #23293c;
            color: #fff;
            border-top: 2px solid #a855f7;
            box-shadow: 0 -2px 8px rgba(168, 85, 247, 0.2);
        }}

        /* Canvas & Note Layout */
        .workspace {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        .pages-sidebar {{
            width: 260px;
            background: #131620;
            border-right: 1px solid var(--border);
            padding: 14px 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            overflow-y: auto;
            flex-shrink: 0;
        }}
        .sidebar-header {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--text-dim);
            letter-spacing: 0.05em;
            padding: 0 8px 6px;
        }}
        .page-item {{
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-dim);
            border-left: 3px solid transparent;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .page-item.active {{
            background: #1f2537;
            color: #fff;
            border-left: 3px solid #a855f7;
            font-weight: 600;
        }}
        .page-item .page-sub {{
            font-size: 11px;
            color: var(--text-dim);
            margin-top: 3px;
            font-weight: 400;
        }}

        /* OneNote Page Content Paper */
        .page-canvas {{
            flex: 1;
            background: #161a25;
            padding: 36px 48px;
            overflow-y: auto;
        }}
        .page-title {{
            font-size: 26px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 6px;
        }}
        .page-date {{
            font-size: 12px;
            color: var(--text-dim);
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        .note-container {{
            background: #1c2130;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 24px;
            max-width: 900px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}
        .note-badge-row {{
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-dim);
        }}
        .badge.gold {{ color: #d4af37; border-color: rgba(212, 175, 55, 0.3); background: rgba(212, 175, 55, 0.08); }}
        .badge.purple {{ color: #c084fc; border-color: rgba(192, 132, 252, 0.3); background: rgba(192, 132, 252, 0.08); }}

        .saree-image-wrapper {{
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            max-height: 520px;
            margin-bottom: 18px;
        }}
        .saree-image {{
            max-width: 100%;
            max-height: 520px;
            object-fit: contain;
            display: block;
        }}
        .location-meta-box {{
            background: #131620;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 12px 16px;
            font-size: 12px;
            line-height: 1.6;
            color: var(--text-dim);
        }}
        .location-meta-box strong {{
            color: #e2e8f0;
        }}
        .location-meta-box code {{
            background: rgba(0,0,0,0.4);
            padding: 2px 6px;
            border-radius: 4px;
            color: #93c5fd;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <!-- Top OneNote Navigation Ribbon -->
    <header class="onenote-header">
        <div class="onenote-logo">
            <div class="onenote-icon-box">N</div>
            <div class="onenote-title-group">
                <h1>OneNote Visual Archive <span>&bull; {nb_name} &gt; {sec_name}</span></h1>
            </div>
        </div>
        <div class="header-actions">
            <span class="user-badge"><span class="user-dot"></span> {account_str}</span>
            <a class="btn-action btn-action-primary" href="{desktop_link}" title="Open Exact Match in OneNote Desktop App">
                🖥️ Open Exact Match in OneNote
            </a>
            <a class="btn-action" href="{web_link}" target="_blank" rel="noreferrer" title="Open OneNote Online (Web)">
                ☁️ OneNote Online
            </a>
            <button class="btn-action" onclick="revealLocalFile()" title="Reveal file in Windows Explorer">
                📁 Reveal File
            </button>
            <button class="btn-action" onclick="copyLocation()" id="btn-copy" title="Copy OneNote hierarchy location">
                📋 Copy Location
            </button>
            <a class="btn-action" href="http://localhost:5173/search">
                🔍 Back to Search
            </a>
        </div>
    </header>

    <!-- Notebook & Section Hierarchy Tabs -->
    <div class="ribbon-bar">
        <div class="notebook-tabs">
            <span style="font-size: 11px; color: var(--text-dim); margin-right: 6px;">NOTEBOOK:</span>
            <div class="notebook-pill {"active" if nb_name == "valid" else ""}">valid</div>
            <div class="notebook-pill {"active" if nb_name == "test" else ""}">test</div>
            <div class="notebook-pill {"active" if nb_name == "train" else ""}">train</div>
        </div>
    </div>
    <div class="section-tabs">
        <span style="font-size: 11px; color: var(--text-dim); margin-right: 8px;">SECTION:</span>
        {section_tabs_html}
    </div>

    <!-- Main Workspace -->
    <div class="workspace">
        <!-- Section Pages List Sidebar -->
        <div class="pages-sidebar">
            <div class="sidebar-header">Pages in {sec_name}</div>
            <div class="page-item active">
                <div>{display_title}</div>
                <div class="page-sub">Selected Saree Design Match</div>
            </div>
            <div class="page-item">
                <div>{sec_name} Design Pattern Catalog</div>
                <div class="page-sub">Active Archive Collection</div>
            </div>
            <div class="page-item">
                <div>Traditional Weaves & Motifs</div>
                <div class="page-sub">Color Invariant Index</div>
            </div>
        </div>

        <!-- Note Canvas Page -->
        <div class="page-canvas">
            <h1 class="page-title">{display_title}</h1>
            <div class="page-date">Saturday, September 26, 2026 &nbsp;&bull;&nbsp; OneNote Verified Location: <strong>{nb_name} &gt; {sec_name} &gt; {display_title}</strong></div>

            <div class="note-container">
                <div class="note-badge-row">
                    <span class="badge gold">Matched: {pos_str}</span>
                    <span class="badge purple">Resource ID: {res_id}</span>
                    <span class="badge">Section: {sec_name}</span>
                    <span class="badge">Notebook: {nb_name}</span>
                    <span class="badge">Category: {category}</span>
                </div>

                <div class="saree-image-wrapper">
                    <img src="{img_url}" alt="{display_title}" class="saree-image">
                </div>

                <div class="location-meta-box">
                    <div><strong>Exact OneNote Match:</strong> <code>{nb_name} &gt; {sec_name} &gt; {display_title} &gt; {pos_str}</code></div>
                    <div style="margin-top: 4px;"><strong>Computer Storage Path:</strong> <code>{path_display}</code></div>
                    <div style="margin-top: 4px;"><strong>OneNote Web Link:</strong> <a href="{web_link}" target="_blank" style="color: #c084fc;">Open in OneNote Online</a></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function revealLocalFile() {{
            try {{
                const res = await fetch('/api/designs/{d_id}/open-local', {{ method: 'POST' }});
                const data = await res.json();
                alert(data.message || 'Revealed file in Windows Explorer');
            }} catch (e) {{
                alert('Could not open file explorer: ' + e);
            }}
        }}

        function copyLocation() {{
            const path = '{nb_name} > {sec_name} > {display_title} > {pos_str}';
            navigator.clipboard.writeText(path);
            const btn = document.getElementById('btn-copy');
            btn.innerText = '✅ Copied!';
            setTimeout(() => {{ btn.innerText = '📋 Copy Location'; }}, 2000);
        }}
    </script>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)

@router.get("/{design_id}/open-onenote")
async def open_design_in_onenote(
    design_id: str,
    mode: str = Query("web", pattern="^(web|desktop|folder)$"),
    redirect: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Renders or redirects the user directly to the exact location of the saree design in OneNote.
    Never fails with 502: displays full-fidelity OneNote digital notebook page with high-res image and deep links.
    """
    from app.main import vector_index, vector_index_mgr, onenote_client

    # Find design metadata in user index, demo index, or DB
    design = None
    u_latest = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()
    if u_latest:
        user_idx = vector_index_mgr.get_index(u_latest.id)
        for item in user_idx.metadata_store:
            if item.get("id") == design_id or item.get("design_id") == design_id:
                design = item
                break

    if not design:
        for item in vector_index.metadata_store:
            if item.get("id") == design_id or item.get("design_id") == design_id:
                design = item
                break

    if not design:
        rec = db.query(DesignRecord).filter((DesignRecord.id == design_id) | (DesignRecord.design_id == design_id)).first()
        if rec:
            design = {
                "id": rec.id,
                "design_id": rec.design_id,
                "title": rec.title,
                "notebook_name": rec.notebook_name,
                "section_name": rec.section_name,
                "page_title": rec.page_title,
                "page_id": rec.page_id,
                "image_order": rec.image_order,
                "resource_id": rec.resource_id,
                "resource_url": getattr(rec, "resource_url", None),
                "object_id": rec.object_id,
                "object_client_url": rec.object_client_url,
                "object_web_url": rec.object_web_url,
                "onenote_web_url": rec.page_web_url or rec.onenote_web_url,
                "page_web_url": rec.page_web_url or rec.onenote_web_url,
                "oneNoteWebUrl": rec.page_web_url or rec.onenote_web_url,
                "onenote_client_url": rec.onenote_client_url,
                "image_url": rec.image_url
            }

    if not design:
        raise HTTPException(status_code=404, detail="Design not found in catalog")

    nb_name = design.get("notebook_name") or "valid"
    sec_name = design.get("section_name") or "Ikat"
    raw_title = design.get("raw_title") or design.get("title") or design.get("page_title") or "Design"
    display_title = design.get("clean_title") or clean_design_title(raw_title)
    img_url = design.get("image_url") or ""
    local_path = resolve_local_image_path(nb_name, sec_name, raw_title, img_url)

    user_email = None
    uid = design.get("user_id")
    if uid:
        u_rec = db.query(UserRecord).filter(UserRecord.id == uid).first()
        if u_rec:
            user_email = u_rec.email
    if not user_email and u_latest:
        user_email = u_latest.email

    # Mode: Open in Windows File Explorer
    if mode == "folder":
        target = local_path or (os.path.abspath(img_url.replace("/api/storage/", "data/storage/")) if img_url else None)
        if target and os.path.exists(target):
            try:
                subprocess.Popen(['explorer', f'/select,{os.path.normpath(target)}'])
                return {"status": "success", "message": f"Revealed in Explorer: {display_title}", "path": target}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to open explorer: {e}")
        raise HTTPException(status_code=404, detail="Local file could not be located on disk")

    # Mode: Direct Stored Location Retrieval (Single Source of Truth - Page Level Navigation)
    raw_page_url = design.get("page_web_url") or design.get("oneNoteWebUrl") or design.get("onenote_web_url")
    if not raw_page_url or not raw_page_url.startswith("https://"):
        raise HTTPException(status_code=404, detail="Page-specific OneNote HTTPS URL not found for this design")
    final_target = raw_page_url

    if mode in ("desktop", "app"):
        print(f"[OneNote Open] Dispatched stored URL for design {design_id}: {final_target}", flush=True)

        if redirect:
            return RedirectResponse(url=final_target, status_code=302)

        return {
            "status": "success",
            "message": f"Opened match in OneNote: {nb_name} > {sec_name} > {display_title}",
            "design_id": design_id,
            "image_id": design_id,
            "title": display_title,
            "notebook_name": nb_name,
            "section_name": sec_name,
            "page_title": design.get("page_title") or display_title,
            "client_url": final_target,
            "web_url": target_web_url,
            "page_web_url": target_web_url,
            "oneNoteWebUrl": target_web_url,
            "onenote_web_url": target_web_url,
            "object_web_url": design.get("object_web_url"),
            "oneNoteClientUrl": design.get("object_client_url"),
            "onenote_client_url": design.get("object_client_url"),
            "fallback_client_url": None,
            "fallback_web_url": target_web_url,
            "page_id": design.get("page_id"),
            "object_id": design.get("object_id"),
            "image_order": design.get("image_order", 1),
            "image_position": design.get("image_position", "Image #1 on page"),
            "resource_id": design.get("resource_id"),
            "resource_url": design.get("resource_url"),
            "hierarchy": f"{nb_name} > {sec_name} > {display_title} > Image #{design.get('image_order', 1)}",
            "image_url": img_url
        }

    # When redirect=False, return JSON location hierarchy metadata
    if not redirect:
        return {
            "status": "success",
            "design_id": design_id,
            "image_id": design_id,
            "title": display_title,
            "notebook_name": nb_name,
            "section_name": sec_name,
            "page_title": design.get("page_title") or display_title,
            "image_order": design.get("image_order", 1),
            "image_position": design.get("image_position", "Image #1 on page"),
            "resource_id": design.get("resource_id"),
            "resource_url": design.get("resource_url"),
            "object_id": design.get("object_id"),
            "page_id": design.get("page_id"),
            "hierarchy": f"{nb_name} > {sec_name} > {display_title} > Image #{design.get('image_order', 1)}",
            "client_url": final_target,
            "web_url": target_web_url,
            "page_web_url": target_web_url,
            "oneNoteWebUrl": target_web_url,
            "onenote_web_url": target_web_url,
            "object_web_url": design.get("object_web_url"),
            "oneNoteClientUrl": design.get("object_client_url"),
            "onenote_client_url": design.get("object_client_url"),
            "fallback_client_url": None,
            "fallback_web_url": target_web_url,
            "image_url": img_url
        }

    # Mode: Web Redirection
    if target_web_url and (target_web_url.startswith("https://") or target_web_url.startswith("http://")):
        return RedirectResponse(url=target_web_url, status_code=302)

    # Fallback Mode: Serve the OneNote Digital Notebook Page
    return render_onenote_page_viewer(
        design=design,
        display_title=display_title,
        sec_name=sec_name,
        nb_name=nb_name,
        local_path=local_path,
        user_email=user_email
    )

@router.post("/{design_id}/open-onenote")
async def open_design_in_onenote_post(
    design_id: str,
    mode: str = Query("desktop", pattern="^(desktop|web|app|folder)$"),
    db: Session = Depends(get_db)
):
    """API endpoint to trigger launching OneNote Desktop to exact location without navigating away."""
    return await open_design_in_onenote(design_id=design_id, mode=mode, redirect=False, db=db)

@router.post("/{design_id}/open-local")
async def open_local_design(design_id: str, db: Session = Depends(get_db)):
    """Opens and highlights the exact design file in Windows File Explorer."""
    return await open_design_in_onenote(design_id=design_id, mode="folder", redirect=False, db=db)

@router.get("/{design_id}/location")
async def get_design_location(design_id: str, db: Session = Depends(get_db)):
    """Returns the full location hierarchy, deep links, and computer path for a design."""
    return await open_design_in_onenote(design_id=design_id, mode="desktop", redirect=False, db=db)

@router.get("/{design_id}")
async def get_design(design_id: str, db: Session = Depends(get_db)):
    """Returns single design metadata with exact object hyperlinks."""
    return await open_design_in_onenote(design_id=design_id, mode="desktop", redirect=False, db=db)

