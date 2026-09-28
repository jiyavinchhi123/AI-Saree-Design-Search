"""
Universal Microsoft OneNote Object-Level Hyperlink Builder.

Constructs object-level deep links for Desktop and Web to navigate directly to
a specific image or object inside any user's OneNote notebook/section/page.
Ensures desktop protocol URL format:
onenote:https://d.docs.live.net/{cid}/OneNote%20Notebooks/{notebook}/{section}.one#{page_title}&section-id={section_id}&page-id={page_id}&object-id={object_id}&end
"""

import re
import urllib.parse
from typing import Optional, Dict, Any

def is_real_onenote_object_id(val: Optional[str]) -> bool:
    """
    Checks whether val is a real OneNote element object ID (GUID-based)
    extracted from Microsoft Graph HTML <img id="..."> when includeIDs=true.
    Rejects synthetic hashes, resource IDs, and item identifiers.
    """
    if not val:
        return False
    s = str(val).strip()
    # Reject known synthetic / resource ID prefixes
    if any(s.startswith(p) for p in ["img-obj-", "res_", "ONENOTE-", "MS-", "ARCH-", "temp_"]):
        return False
    # Must contain a standard GUID (8-4-4-4-12 hex format)
    guid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    return bool(re.search(guid_pattern, s))

def is_real_graph_id(val: Optional[str]) -> bool:
    """
    Checks whether val is a real Microsoft Graph page or section ID
    rather than a synthetic placeholder string.
    """
    if not val:
        return False
    s = str(val).strip()
    if s.startswith("0-") and "-p-" in s:
        return False
    guid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    if re.search(guid_pattern, s):
        return True
    if re.match(r'^[0-9]-[A-Fa-f0-9]+![a-zA-Z0-9]+', s):
        return True
    return False

def clean_guid(val: Optional[str]) -> str:
    """Strips curly braces and whitespace from a GUID or ID."""
    if not val:
        return ""
    return str(val).strip().strip("{}").strip()

def format_object_id_for_onenote(val: Optional[str]) -> Optional[str]:
    """
    Formats the real OneNote page-content object ID returned by Microsoft Graph
    for use in object-level hyperlinks.
    
    Microsoft Graph returns:
    - id="img:{4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}"
    OneNote Desktop protocol expects:
    - &object-id={4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}&end
    """
    if not is_real_onenote_object_id(val):
        return None
    s = str(val).strip()
    # Strip HTML tag prefixes like img:, image:, etc.
    s = re.sub(r'^(img|image|div|p|span|li|tr|td|table):', '', s, flags=re.IGNORECASE).strip()

    # If it already starts with { and ends with }, ensure braces structure
    if s.startswith("{") and s.endswith("}"):
        return s

    if "}{" in s:
        if not s.startswith("{"):
            s = "{" + s
        if not s.endswith("}"):
            s = s + "}"
        return s

    s_clean = s.strip("{}")
    return f"{{{s_clean}}}"

def format_id_param(val: Optional[str]) -> Optional[str]:
    """Wraps real Graph section or page ID in single curly braces without double-wrapping."""
    if not val:
        return None
    s = str(val).strip()
    if not is_real_graph_id(s):
        return None
    s_clean = s.strip("{}")
    return f"{{{s_clean}}}"

def build_object_client_url(
    base_client_url: Optional[str] = None,
    notebook_name: Optional[str] = None,
    section_name: Optional[str] = None,
    page_title: Optional[str] = None,
    page_id: Optional[str] = None,
    object_id: Optional[str] = None,
    section_id: Optional[str] = None,
    cid: Optional[str] = None
) -> Optional[str]:
    """
    Generates the exact OneNote desktop protocol URL:
    onenote:https://d.docs.live.net/{cid}/...#{page_title}&section-id={section_id}&page-id={page_id}&object-id={object_id}&end

    Ensures:
    - No synthetic object IDs
    - No .one path + #page-title-only links
    - Real section_id, page_id, and object_id parameters are present
    - No URL encoding corruption of braces, ampersands, or spaces
    - Returns None if real object-level targeting cannot be reliably constructed
    """
    formatted_obj = format_object_id_for_onenote(object_id)
    sec_param = format_id_param(section_id)
    pg_param = format_id_param(page_id)

    # Priority 1: Check existing Graph API client URL
    if base_client_url and base_client_url.startswith("onenote:"):
        url = base_client_url

        has_sec = "section-id=" in url
        has_pg = "page-id=" in url
        has_obj = "object-id=" in url

        # If it already contains verified parameters
        if has_sec and has_pg and has_obj:
            obj_m = re.search(r'object-id=([^&]+)', url)
            if obj_m and is_real_onenote_object_id(obj_m.group(1)):
                print(f"[OneNote DeepLink] Verified existing object client URL: {url}", flush=True)
                return url

        # If it has section-id and page-id from Graph, inject real object-id
        if has_sec and has_pg and formatted_obj:
            if "object-id=" in url:
                url = re.sub(r'object-id=[^&]+', f'object-id={formatted_obj}', url)
            elif "&end" in url:
                url = url.replace("&end", f"&object-id={formatted_obj}&end")
            else:
                url = f"{url}&object-id={formatted_obj}&end"
            print(f"[OneNote DeepLink] Injected object-id into Graph client URL: {url}", flush=True)
            return url

    # Priority 2: Construct from real Graph metadata
    if sec_param and pg_param and formatted_obj:
        user_cid = (cid or "b6ecec459b998637").lower()
        nb_str = (notebook_name or "My Notebook").replace(" ", "%20")
        sec_str = (section_name or "Quick Notes").replace(" ", "%20")
        title_str = (page_title or "Page").replace(" ", "%20")

        base_prefix = f"onenote:https://d.docs.live.net/{user_cid}/OneNote%20Notebooks/{nb_str}/{sec_str}.one"
        if base_client_url and "#" in base_client_url:
            base_prefix = base_client_url.split("#")[0]

        final_url = f"{base_prefix}#{title_str}&section-id={sec_param}&page-id={pg_param}&object-id={formatted_obj}&end"
        print(f"[OneNote DeepLink] Final generated URL: {final_url}", flush=True)
        return final_url

    # Return None if object-level parameters cannot be reliably constructed
    return None

def build_object_web_url(
    base_web_url: Optional[str],
    page_id: Optional[str] = None,
    object_id: Optional[str] = None,
    notebook_name: Optional[str] = None,
    section_name: Optional[str] = None,
    page_title: Optional[str] = None
) -> str:
    """
    Generates an object-level OneNote web URL (https://...).
    If object_id is a real OneNote element ID, appends &object-id={object_id}.
    Otherwise returns official page web URL.
    """
    formatted_obj = format_object_id_for_onenote(object_id)
    clean_pg = clean_guid(page_id) if is_real_graph_id(page_id) else None

    # Enhance official Graph web URL
    if base_web_url and (base_web_url.startswith("https://") or base_web_url.startswith("http://")):
        url = base_web_url
        if "object-id=" in url:
            if formatted_obj:
                url = re.sub(r'object-id=[^&]+', f'object-id={urllib.parse.quote(formatted_obj)}', url)
            else:
                url = re.sub(r'[?&]object-id=[^&]+', '', url)
            return url

        if formatted_obj:
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}object-id={urllib.parse.quote(formatted_obj)}"
        return url

    # Official OneNote web redirector
    if clean_pg and formatted_obj:
        return f"https://www.onenote.com/redir?pageid={clean_pg}&objectid={urllib.parse.quote(formatted_obj)}"
    elif clean_pg:
        return f"https://www.onenote.com/redir?pageid={clean_pg}"

    return "https://www.onenote.com/notebooks"

def get_exact_image_hyperlinks(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts or dynamically constructs all exact object-level and fallback
    hyperlinks for an indexed OneNote design item.
    """
    page_id = item.get("page_id")
    object_id = item.get("object_id")
    section_id = item.get("section_id")
    notebook_name = item.get("notebook_name")
    section_name = item.get("section_name")
    page_title = item.get("page_title") or item.get("title")
    user_id = item.get("user_id")

    raw_client = item.get("onenote_client_url")
    raw_web = item.get("onenote_web_url")

    # Clean local file URLs from legacy index if present
    if raw_client and (":\\" in raw_client or "/Users/" in raw_client):
        raw_client = None

    # Clean synthetic parameters from raw_client if present
    if raw_client:
        if "img-obj-" in raw_client:
            raw_client = re.sub(r'&object-id=\{?img-obj-[^&}]+\}?', '', raw_client)
        sec_m = re.search(r'section-id=([^&]+)', raw_client)
        pg_m = re.search(r'page-id=([^&]+)', raw_client)
        if not (sec_m and is_real_graph_id(sec_m.group(1)) and pg_m and is_real_graph_id(pg_m.group(1))):
            raw_client = None

    # Check if object_id is synthetic; if so, do NOT use it as object_id
    if not is_real_onenote_object_id(object_id):
        object_id = None

    # Try building verified object client URL
    object_client_url = build_object_client_url(
        base_client_url=raw_client,
        notebook_name=notebook_name,
        section_name=section_name,
        page_title=page_title,
        page_id=page_id,
        object_id=object_id,
        section_id=section_id,
        cid=user_id
    )

    object_web_url = build_object_web_url(
        base_web_url=raw_web,
        page_id=page_id,
        object_id=object_id,
        notebook_name=notebook_name,
        section_name=section_name,
        page_title=page_title
    )

    # Clean official page web URL (fallback)
    clean_page_web = raw_web
    if clean_page_web and "object-id=" in clean_page_web:
        clean_page_web = re.sub(r'[?&]object-id=[^&]+', '', clean_page_web)

    fallback_web = clean_page_web or "https://www.onenote.com/notebooks"

    # Fallback client URL (official page level with verified real IDs)
    fallback_client = raw_client if (raw_client and "section-id=" in raw_client and "page-id=" in raw_client) else None

    # Final desktop protocol URL: only use if object-level is reliably constructed
    final_client_url = object_client_url or fallback_client

    if final_client_url:
        print(f"[OneNote ExactMatch] Verified Desktop DeepLink: {final_client_url}", flush=True)
    else:
        print(f"[OneNote ExactMatch] Desktop object link not available; falling back to official page Web: {fallback_web}", flush=True)

    return {
        "page_id": page_id if is_real_graph_id(page_id) else None,
        "object_id": object_id if is_real_onenote_object_id(object_id) else None,
        "image_order": item.get("image_order", 1),
        "image_position": item.get("image_position", "Image #1 on page"),
        "resource_id": item.get("resource_id"),
        "object_client_url": object_client_url,
        "object_web_url": object_web_url,
        "client_url": final_client_url or fallback_web,
        "fallback_client_url": fallback_client,
        "fallback_web_url": fallback_web
    }
