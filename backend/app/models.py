from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SareeDesignBase(BaseModel):
    image_id: Optional[str] = None
    title: str
    notebook_id: Optional[str] = None
    notebook_name: str
    section_id: Optional[str] = None
    section_name: str
    page_id: Optional[str] = None
    page_title: str
    object_id: Optional[str] = None
    image_order: Optional[int] = 1
    image_position: Optional[str] = "Position #1 on page"
    resource_id: Optional[str] = None
    resource_url: Optional[str] = None
    object_client_url: Optional[str] = None
    object_web_url: Optional[str] = None
    page_web_url: Optional[str] = None
    onenote_web_url: Optional[str] = None
    onenote_client_url: Optional[str] = None
    oneNoteWebUrl: Optional[str] = None
    oneNoteClientUrl: Optional[str] = None
    category: Optional[str] = "Traditional"
    colorway: Optional[str] = None
    motifs: Optional[List[str]] = []
    weave_type: Optional[str] = None

class SareeDesignResponse(SareeDesignBase):
    id: str
    design_id: str
    image_url: str
    structural_preview_url: Optional[str] = None
    similarity_score: Optional[float] = None
    similarity_percentage: Optional[float] = None
    is_match: Optional[bool] = None

class SearchResponse(BaseModel):
    is_strong_match: bool
    status_message: str
    top_score: float
    top_percentage: float
    threshold: float
    query_image_url: str
    query_structural_preview_url: str
    matches: List[Dict[str, Any]]
    total_indexed: int

class SearchHistoryEntry(BaseModel):
    id: str
    timestamp: str
    query_image_url: str
    top_match_title: Optional[str] = None
    top_match_image_url: Optional[str] = None
    similarity_percentage: float
    is_strong_match: bool
    notebook_name: Optional[str] = None
    section_name: Optional[str] = None
    page_title: Optional[str] = None
    top_match_page_id: Optional[str] = None
    top_match_object_id: Optional[str] = None
    top_match_object_url: Optional[str] = None
    top_match_order: Optional[int] = None
    onenote_web_url: Optional[str] = None

class MicrosoftAuthConfig(BaseModel):
    client_id: str
    tenant_id: Optional[str] = "common"
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = "https://ai-saree-design-search.onrender.com/api/data-sources/onenote/auth/callback"

class OneNoteSyncStatus(BaseModel):
    is_configured: bool
    is_connected: bool
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    display_name: Optional[str] = None
    notebooks_count: int = 0
    indexed_designs_count: int = 0
    last_synced: Optional[str] = None

class NotebookSyncRequest(BaseModel):
    notebook_ids: Optional[List[str]] = None

