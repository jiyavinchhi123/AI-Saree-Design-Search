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
    if any(s.startswith(p) for p in ["img-obj-", "res_", "ONENOTE-", "MS-", "ARCH-", "temp_", "obj_"]):
        return False
    # Reject if it's a Graph resource ID like 0-b6ecec...
    if s.startswith("0-") and "!" in s:
        return False
    # Must contain a standard GUID (8-4-4-4-12 hex format)
    guid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    return bool(re.search(guid_pattern, s))

def is_real_graph_id(val: Optional[str]) -> bool:
    """
    Checks whether val is a real Microsoft Graph page or section GUID / identifier
    rather than a synthetic placeholder string.
    """
    if not val:
        return False
    s = str(val).strip()
    if s.startswith("0-") and "-p-" in s:
        return False
    if "00000000000" in s:
        return False
    guid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    return bool(re.search(guid_pattern, s))

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

    # Matches {guid}{order} format: e.g. {4cdb24f8-79bd-48ac-85fd-3f084ee70322}{207}
    double_braced = re.match(r'^\{([0-9a-fA-F\-]{36})\}(\{\d+\})$', s)
    if double_braced:
        return s

    # Matches {guid} format without order: e.g. {4cdb24f8-79bd-48ac-85fd-3f084ee70322}
    single_braced = re.match(r'^\{([0-9a-fA-F\-]{36})\}$', s)
    if single_braced:
        return s

    # Matches guid{order} unbraced guid: e.g. 4cdb24f8-79bd-48ac-85fd-3f084ee70322{207}
    unbraced_guid_with_order = re.match(r'^([0-9a-fA-F\-]{36})(\{\d+\})$', s)
    if unbraced_guid_with_order:
        return f"{{{unbraced_guid_with_order.group(1)}}}{unbraced_guid_with_order.group(2)}"

    # Matches guid alone: e.g. 4cdb24f8-79bd-48ac-85fd-3f084ee70322
    unbraced_guid = re.match(r'^([0-9a-fA-F\-]{36})$', s)
    if unbraced_guid:
        return f"{{{unbraced_guid.group(1)}}}"

    # Extract any guid and order
    guid_m = re.search(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', s)
    order_m = re.search(r'\{?(\d+)\}?$', s)
    if guid_m:
        if order_m and order_m.group(1) != guid_m.group(1):
            return f"{{{guid_m.group(1)}}}{{{order_m.group(1)}}}"
        return f"{{{guid_m.group(1)}}}"

    return None

def format_id_param(val: Optional[str]) -> Optional[str]:
    """Wraps real Graph section or page GUID in single curly braces without double-wrapping."""
    if not val:
        return None
    s = str(val).strip()
    if not is_real_graph_id(s):
        return None
    guid_m = re.search(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', s)
    if guid_m:
        return f"{{{guid_m.group(1)}}}"
    return None

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
    onenote:https://d.docs.live.net/{cid}/...#{page_title}&section-id={section_id}&page-id={page_id}&object-id={real_object_guid_and_order}&end

    Ensures:
    - No synthetic object IDs
    - No .one path + #page-title-only links
    - Real section_id, page_id, and object_id parameters are present
    - No URL encoding corruption of braces, ampersands, or spaces
    - Returns None if real object-level targeting cannot be reliably constructed
    """
    formatted_obj = format_object_id_for_onenote(object_id)
    if not formatted_obj:
        return None

    user_cid = (cid or "b6ecec459b998637").lower()

    # Extract section_id and page_id from base_client_url if present
    extracted_sec = None
    extracted_pg = None
    base_prefix = None
    extracted_title = None

    if base_client_url and base_client_url.startswith("onenote:"):
        sec_m = re.search(r'[?&]section-id=([^&]+)', base_client_url)
        pg_m = re.search(r'[?&]page-id=([^&]+)', base_client_url)
        if sec_m:
            extracted_sec = sec_m.group(1)
        if pg_m:
            extracted_pg = pg_m.group(1)

        if "#" in base_client_url:
            parts = base_client_url.split("#", 1)
            base_prefix = parts[0]
            frag = parts[1]
            title_part = frag.split("&")[0] if "&" in frag else frag
            if title_part and not title_part.startswith("section-id=") and not title_part.startswith("page-id="):
                extracted_title = urllib.parse.unquote(title_part)

    effective_sec = extracted_sec or section_id
    effective_pg = extracted_pg or page_id
    effective_title = page_title or extracted_title or "Page"

    sec_param = format_id_param(effective_sec)
    pg_param = format_id_param(effective_pg)

    # Both section_id and page_id MUST be real, valid GUIDs
    if not sec_param or not pg_param:
        return None

    # Construct or sanitize the base prefix
    if not base_prefix:
        nb_str = urllib.parse.quote(notebook_name or "My Notebook", safe="").replace("+", "%20")
        sec_str = urllib.parse.quote(section_name or "Quick Notes", safe="").replace("+", "%20")
        base_prefix = f"onenote:https://d.docs.live.net/{user_cid}/OneNote%20Notebooks/{nb_str}/{sec_str}.one"
    else:
        # Ensure spaces in base_prefix are %20, not raw spaces
        base_prefix = base_prefix.replace(" ", "%20")

    # Encode page title with spaces as %20
    title_str = urllib.parse.quote(effective_title, safe="").replace("+", "%20")

    final_url = f"{base_prefix}#{title_str}&section-id={sec_param}&page-id={pg_param}&object-id={formatted_obj}&end"
    print(f"[OneNote DeepLink] Final generated URL: {final_url}", flush=True)
    return final_url

def extract_page_web_url(url: Optional[str]) -> Optional[str]:
    """
    Extracts or cleans the pure page-level HTTPS OneNote Web URL by removing
    any intra-page object identifiers (&object-id=... or #object-id=...).
    """
    if not url or not (str(url).startswith("https://") or str(url).startswith("http://")):
        return None
    cleaned = str(url).strip()
    cleaned = re.sub(r'([?&])object-id=[^&#]*(&|$)', r'\2', cleaned)
    cleaned = re.sub(r'#object-id=[^&]*', '', cleaned)
    cleaned = re.sub(r'[?&]$', '', cleaned)
    cleaned = cleaned.replace("?&", "?")
    return cleaned

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
    Extracts or dynamically constructs all exact page-level and preserved object-level
    hyperlinks for an indexed OneNote design item.

    Page-level HTTPS URL is strictly used for navigation (OneNote Web).
    """
    page_id = item.get("page_id")
    object_id = item.get("object_id")
    section_id = item.get("section_id")
    notebook_name = item.get("notebook_name")
    section_name = item.get("section_name")
    page_title = item.get("page_title") or item.get("title")
    user_id = item.get("user_id")

    raw_client = item.get("onenote_client_url")
    raw_web = item.get("onenote_web_url") or item.get("page_web_url") or item.get("oneNoteWebUrl")

    # Clean local file URLs from legacy index if present
    if raw_client and (":\\" in raw_client or "/Users/" in raw_client):
        raw_client = None

    # Discard any raw_client that is just a .one path + #title without required section-id and page-id
    if raw_client:
        if "section-id=" not in raw_client or "page-id=" not in raw_client:
            raw_client = None
        elif "img-obj-" in raw_client or "00000000000" in raw_client:
            raw_client = None

    # Check if object_id is synthetic; if so, do NOT use it
    if not is_real_onenote_object_id(object_id):
        object_id = None

    # Preserved object-level URLs (retained for database/metadata preservation)
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

    object_web_url = item.get("object_web_url") or build_object_web_url(
        base_web_url=raw_web,
        page_id=page_id,
        object_id=object_id,
        notebook_name=notebook_name,
        section_name=section_name,
        page_title=page_title
    )

    # Pure page-level OneNote web URL (Primary navigation destination)
    clean_page_web = raw_web if (raw_web and str(raw_web).startswith("https://")) else None

    return {
        "page_id": page_id if is_real_graph_id(page_id) else None,
        "object_id": object_id if is_real_onenote_object_id(object_id) else None,
        "image_order": item.get("image_order", 1),
        "image_position": item.get("image_position", "Image #1 on page"),
        "resource_id": item.get("resource_id"),
        "object_client_url": object_client_url,
        "object_web_url": object_web_url,
        "page_web_url": clean_page_web,
        "oneNoteWebUrl": clean_page_web,
        "onenote_web_url": clean_page_web,
        "client_url": clean_page_web,
        "fallback_client_url": None,
        "fallback_web_url": clean_page_web
    }
