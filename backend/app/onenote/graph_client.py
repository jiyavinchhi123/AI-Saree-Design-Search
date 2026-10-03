"""
Microsoft Graph API & Microsoft Entra ID Client for OneNote (Multi-User & Read-Only).

Handles:
- Microsoft Authentication (MSAL Device Code & Authorization Code flows)
- Multi-user session and token isolation
- Reading OneNote Notebooks, Sections, Pages, and Image Attachments via Graph API
- Zero write access: completely Read-Only (Notes.Read, User.Read)
"""

import os
import re
import uuid
import httpx
import msal
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
# Strictly Read-Only scopes: no Notes.ReadWrite
SCOPES = ["Notes.Read", "User.Read"]
# Microsoft Graph Command Line Tools multi-tenant public client ID (pre-consented for Microsoft Graph & OneNote)
DEFAULT_PUBLIC_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

class MicrosoftOneNoteClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: str = "common",
        redirect_uri: str = "http://localhost:8000/api/data-sources/onenote/auth/callback"
    ):
        self.client_id = client_id or os.getenv("MS_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("MS_CLIENT_SECRET", "")
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID", "common")
        self.redirect_uri = redirect_uri
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"

        # In-memory dictionary of active device code flows keyed by session_id
        self._device_flows: Dict[str, Dict[str, Any]] = {}

    def is_configured(self) -> bool:
        return True

    def get_effective_client_id(self) -> str:
        return self.client_id.strip() if self.client_id and self.client_id.strip() else DEFAULT_PUBLIC_CLIENT_ID

    def get_auth_url(self, state: str = "onenote_sync") -> Dict[str, Any]:
        """Generates Microsoft OAuth2 login authorization URL."""
        cid = self.get_effective_client_id()
        r_uri = "http://localhost" if cid == DEFAULT_PUBLIC_CLIENT_ID else self.redirect_uri
        msal_app = msal.ConfidentialClientApplication(
            cid,
            authority=self.authority,
            client_credential=self.client_secret
        ) if self.client_secret else msal.PublicClientApplication(
            cid,
            authority=self.authority
        )

        auth_url = msal_app.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=r_uri,
            state=state
        )
        return {
            "configured": True,
            "auth_url": auth_url,
            "authority": self.authority
        }

    def start_device_flow(self) -> Dict[str, Any]:
        """
        Starts device code flow (supports personal Microsoft accounts with 0 Azure setup).
        Returns user_code, verification_uri, and a session_id.
        """
        cid = self.get_effective_client_id()
        app = msal.PublicClientApplication(cid, authority=self.authority)
        flow = app.initiate_device_flow(scopes=SCOPES)
        session_id = uuid.uuid4().hex[:12]
        
        self._device_flows[session_id] = {
            "flow": flow,
            "app": app,
            "is_polling": False,
            "created_at": datetime.utcnow()
        }
        
        # Also store under default session for backwards compatibility
        self._device_flows["default"] = self._device_flows[session_id]

        return {
            "session_id": session_id,
            "user_code": flow.get("user_code"),
            "verification_uri": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
            "message": flow.get("message"),
            "expires_in": flow.get("expires_in")
        }

    async def complete_device_flow(self, session_id: str = "default", db = None) -> Dict[str, Any]:
        """
        Polls token acquisition non-blockingly for the given device flow session.
        When approved, creates/updates UserRecord in the database.
        """
        from app.database import UserRecord

        entry = self._device_flows.get(session_id) or self._device_flows.get("default")
        if not entry:
            return {"success": False, "error": "No active device login session found. Please start a new login."}

        flow = entry["flow"]
        app = entry["app"]

        if entry.get("is_polling"):
            return {"success": False, "status": "pending", "error": "authorization_pending"}

        entry["is_polling"] = True
        try:
            result = await asyncio.to_thread(
                app.acquire_token_by_device_flow,
                flow,
                exit_condition=lambda f: True
            )
        except Exception as e:
            entry["is_polling"] = False
            return {"success": False, "error": f"Token acquisition error: {str(e)}"}
        finally:
            entry["is_polling"] = False

        if "access_token" in result:
            access_token = result["access_token"]
            refresh_token = result.get("refresh_token")

            # Fetch user profile immediately
            profile = await self.fetch_user_profile(access_token)
            if not profile:
                profile = {"id": uuid.uuid4().hex[:12], "displayName": "Microsoft User", "userPrincipalName": "user@microsoft.com"}

            user_id = profile.get("id") or profile.get("userPrincipalName") or profile.get("mail")
            email = profile.get("userPrincipalName") or profile.get("mail") or "user@microsoft.com"
            display_name = profile.get("displayName") or email

            if db:
                user_rec = db.query(UserRecord).filter(UserRecord.id == user_id).first()
                if not user_rec:
                    user_rec = UserRecord(id=user_id, email=email, display_name=display_name)
                    db.add(user_rec)
                user_rec.email = email
                user_rec.display_name = display_name
                user_rec.access_token = access_token
                user_rec.refresh_token = refresh_token
                user_rec.connected_at = datetime.utcnow()
                db.commit()

            # Clean up device flow session
            self._device_flows.pop(session_id, None)

            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "email": email,
                    "displayName": display_name
                }
            }
        elif result.get("error") in ("authorization_pending", "slow_down"):
            return {"success": False, "status": "pending", "error": result.get("error")}
        else:
            return {"success": False, "error": result.get("error_description", result.get("error", "Authentication failed"))}

    async def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None, db = None) -> Dict[str, Any]:
        """Exchanges authorization code for access and refresh tokens, registering UserRecord."""
        from app.database import UserRecord

        cid = self.get_effective_client_id()
        r_uri = redirect_uri or ("http://localhost" if cid == DEFAULT_PUBLIC_CLIENT_ID else self.redirect_uri)

        msal_app = msal.ConfidentialClientApplication(
            cid,
            authority=self.authority,
            client_credential=self.client_secret
        ) if self.client_secret else msal.PublicClientApplication(
            cid,
            authority=self.authority
        )

        result = await asyncio.to_thread(
            msal_app.acquire_token_by_authorization_code,
            code=code,
            scopes=SCOPES,
            redirect_uri=r_uri
        )

        if "access_token" in result:
            access_token = result["access_token"]
            refresh_token = result.get("refresh_token")

            profile = await self.fetch_user_profile(access_token)
            if not profile:
                profile = {"id": uuid.uuid4().hex[:12], "displayName": "Microsoft User", "userPrincipalName": "user@microsoft.com"}

            user_id = profile.get("id") or profile.get("userPrincipalName") or profile.get("mail")
            email = profile.get("userPrincipalName") or profile.get("mail") or "user@microsoft.com"
            display_name = profile.get("displayName") or email

            if db:
                user_rec = db.query(UserRecord).filter(UserRecord.id == user_id).first()
                if not user_rec:
                    user_rec = UserRecord(id=user_id, email=email, display_name=display_name)
                    db.add(user_rec)
                user_rec.email = email
                user_rec.display_name = display_name
                user_rec.access_token = access_token
                user_rec.refresh_token = refresh_token
                user_rec.connected_at = datetime.utcnow()
                db.commit()

            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "email": email,
                    "displayName": display_name
                }
            }
        else:
            return {"success": False, "error": result.get("error_description", result.get("error", "Token exchange failed"))}

    async def get_valid_token_for_user(self, user_id: str, db) -> Optional[str]:
        """
        Retrieves a valid, active access token for the given user_id.
        Refreshes the token automatically via MSAL if expired.
        """
        from app.database import UserRecord

        user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
        if not user or not (user.access_token or user.refresh_token):
            return None

        # Test current token
        if user.access_token:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{GRAPH_API_BASE}/me",
                        headers={"Authorization": f"Bearer {user.access_token}"}
                    )
                    if resp.status_code == 200:
                        return user.access_token
            except Exception:
                pass

        # Refresh token via MSAL
        if user.refresh_token:
            cid = self.get_effective_client_id()
            app = msal.PublicClientApplication(cid, authority=self.authority)
            try:
                result = await asyncio.to_thread(
                    app.acquire_token_by_refresh_token,
                    user.refresh_token,
                    scopes=SCOPES
                )
                if "access_token" in result:
                    user.access_token = result["access_token"]
                    user.refresh_token = result.get("refresh_token", user.refresh_token)
                    db.commit()
                    return user.access_token
            except Exception as e:
                print(f"[OneNote] Refresh error for user {user_id}: {e}")

        return None

    async def fetch_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Fetches user profile from Microsoft Graph API."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{GRAPH_API_BASE}/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"[OneNote] Profile fetch error: {e}")
        return None

    async def list_notebooks(self, access_token: str) -> List[Dict[str, Any]]:
        """Lists all OneNote notebooks for the user."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{GRAPH_API_BASE}/me/onenote/notebooks?includeSharedNotebooks=true&$select=id,displayName,links,createdDateTime,lastModifiedDateTime",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if resp.status_code == 200:
                    return resp.json().get("value", [])
        except Exception as e:
            print(f"[OneNote] List notebooks error: {e}")
        return []

    async def list_sections(self, notebook_id: str, access_token: str) -> List[Dict[str, Any]]:
        """Lists sections inside a notebook."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{GRAPH_API_BASE}/me/onenote/notebooks/{notebook_id}/sections?$select=id,displayName,pagesUrl",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if resp.status_code == 200:
                    return resp.json().get("value", [])
        except Exception as e:
            print(f"[OneNote] List sections error: {e}")
        return []

    async def list_pages(self, section_id: str, access_token: str) -> List[Dict[str, Any]]:
        """Lists pages inside a section with deep links."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{GRAPH_API_BASE}/me/onenote/sections/{section_id}/pages?$select=id,title,links,contentUrl,createdDateTime,lastModifiedDateTime",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if resp.status_code == 200:
                    return resp.json().get("value", [])
        except Exception as e:
            print(f"[OneNote] List pages error: {e}")
        return []

    async def get_page_content_and_images(self, content_url: str, access_token: str) -> tuple[str, List[Dict[str, Any]]]:
        """
        Fetches the HTML of a OneNote page using GET .../content?includeIDs=true
        and extracts each image separately with its:
        - actual OneNote page-content element/object ID (<img id="...">)
        - image resource URL and resource ID (binary attachment)
        - position / order on the page
        """
        try:
            # Mandate ?includeIDs=true so Microsoft Graph injects real element IDs into the HTML
            req_url = content_url
            if "includeIDs" not in req_url:
                delimiter = "&" if "?" in req_url else "?"
                req_url = f"{req_url}{delimiter}includeIDs=true"

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    req_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                print(f"[OneNote Graph] Page content GET {req_url} -> HTTP {resp.status_code} ({len(resp.text)} bytes)", flush=True)
                if resp.status_code != 200:
                    print(f"[OneNote Graph] Page content fetch error: HTTP {resp.status_code} for {req_url}", flush=True)
                    return "", []

                html = resp.text
                from html.parser import HTMLParser

                class OneNoteImgTagParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.img_nodes = []
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() == 'img':
                            self.img_nodes.append({k.lower(): v for k, v in attrs})

                parser = OneNoteImgTagParser()
                parser.feed(html)
                print(f"[OneNote Graph] Total <img> elements parsed by HTMLParser: {len(parser.img_nodes)}", flush=True)

                resources = []
                for order, attrs in enumerate(parser.img_nodes, start=1):
                    # 1. Real OneNote image element/object ID from id="..."
                    real_object_id = attrs.get("id") or attrs.get("data-id")

                    # 2. Resource URL from data-fullres-src, src, or data-src
                    res_url = attrs.get("data-fullres-src") or attrs.get("src") or attrs.get("data-src")

                    # 3. Resource ID from data-data-id, data-id, or URL
                    res_id = attrs.get("data-data-id") or attrs.get("data-id")
                    if not res_id and res_url:
                        u_m = re.search(r'resources/([^/\?]+)', res_url)
                        if u_m:
                            res_id = u_m.group(1)

                    print(f"[OneNote Graph]   Image #{order}:", flush=True)
                    print(f"    <img id=\"...\">:     {real_object_id}", flush=True)
                    print(f"    data-id:              {attrs.get('data-id')}", flush=True)
                    print(f"    data-data-id:         {attrs.get('data-data-id')}", flush=True)
                    print(f"    data-fullres-src:     {attrs.get('data-fullres-src')}", flush=True)
                    print(f"    src:                  {attrs.get('src')}", flush=True)
                    print(f"    resource_id:          {res_id}", flush=True)

                    if res_url and ("onenote/resources" in res_url or "graph.microsoft.com" in res_url):
                        resources.append({
                            "resource_url": res_url,
                            "resource_id": res_id or f"res_{order}",
                            "object_id": real_object_id,
                            "image_order": order,
                            "image_position": f"Image #{order} on page"
                        })

                return html, resources
        except Exception as e:
            print(f"[OneNote Graph] Get page content error: {e}", flush=True)
            return "", []

    async def download_image_resource(self, resource_url: str, save_path: str, access_token: str) -> bool:
        """Downloads a binary image attachment from Microsoft Graph API."""
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.get(
                    resource_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    follow_redirects=True
                )
                if resp.status_code == 200:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    return True
        except Exception as e:
            print(f"[OneNote] Download image resource error: {e}")
        return False
