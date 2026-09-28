import os
import uuid
import cv2
import numpy as np
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.models import SearchResponse
from app.database import get_db, SearchHistoryRecord, UserRecord

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.post("/upload", response_model=SearchResponse)
async def search_saree_design(
    file: UploadFile = File(...),
    threshold: float = Form(0.82),
    top_k: int = Form(6),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    from app.main import extractor, vector_index_mgr

    # 1. Resolve current user for isolation
    user = None
    if x_user_id:
        user = db.query(UserRecord).filter(UserRecord.id == x_user_id).first()
    if not user:
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()

    user_id = user.id if user else None
    user_index = vector_index_mgr.get_index(user_id)

    storage_dir = "data/storage"
    query_id = uuid.uuid4().hex[:8]
    os.makedirs(storage_dir, exist_ok=True)

    query_img_filename = f"query_{query_id}.jpg"
    query_img_path = os.path.join(storage_dir, query_img_filename)

    # 2. Handle real file upload
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")
    cv2.imwrite(query_img_path, img_bgr)

    # 3. Extract Color-Invariant Feature Vector & Structural Map
    try:
        embedding, structural_map = extractor.extract_features_from_image(img_bgr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image features: {str(e)}")

    # Save structural tensor preview for user inspection
    struct_preview_filename = f"struct_query_{query_id}.jpg"
    struct_preview_path = os.path.join(storage_dir, struct_preview_filename)
    cv2.imwrite(struct_preview_path, structural_map)

    # 4. Check if user's connected OneNote has any indexed images
    if user_index.count() == 0:
        return SearchResponse(
            is_strong_match=False,
            status_message="No saree designs indexed from your connected OneNote yet. Please open Data Sources and click 'Sync Notebooks'.",
            top_score=0.0,
            top_percentage=0.0,
            threshold=threshold,
            query_image_url=f"/api/storage/{query_img_filename}",
            query_structural_preview_url=f"/api/storage/{struct_preview_filename}",
            matches=[],
            total_indexed=0
        )

    # 5. Vector Similarity Search strictly within this user's isolated OneNote designs
    search_results = user_index.search(
        query_embedding=embedding,
        top_k=top_k,
        threshold=threshold
    )
    raw_matches = search_results["matches"]
    is_strong = search_results["is_strong_match"]
    top_score = search_results["top_score"]
    top_percentage = search_results["top_percentage"]
    status_msg = search_results["status_message"]

    from app.onenote.link_builder import get_exact_image_hyperlinks

    enriched_matches = []
    for m in raw_matches:
        links = get_exact_image_hyperlinks(m)
        m["page_id"] = links["page_id"]
        m["object_id"] = links["object_id"]
        m["object_client_url"] = links["object_client_url"]
        m["object_web_url"] = links["object_web_url"]
        m["fallback_client_url"] = links["fallback_client_url"]
        m["fallback_web_url"] = links["fallback_web_url"]
        m["image_order"] = links["image_order"]
        m["image_position"] = links["image_position"]
        # Primary URLs now point directly to the exact matched image object or reliable fallback
        m["onenote_client_url"] = links["client_url"]
        m["onenote_web_url"] = links["object_web_url"] or links["fallback_web_url"]
        enriched_matches.append(m)
    matches = enriched_matches

    # 6. Record to Search History
    top_match = matches[0] if matches else None
    history_entry = SearchHistoryRecord(
        id=f"HIST-{query_id}",
        user_id=user_id,
        timestamp=datetime.utcnow(),
        query_image_url=f"/api/storage/{query_img_filename}",
        query_structural_preview_url=f"/api/storage/{struct_preview_filename}",
        top_match_id=top_match["design_id"] if top_match else None,
        top_match_title=top_match["title"] if top_match else None,
        top_match_image_url=top_match["image_url"] if top_match else None,
        similarity_percentage=top_percentage,
        is_strong_match=is_strong,
        notebook_name=top_match["notebook_name"] if top_match else None,
        section_name=top_match["section_name"] if top_match else None,
        page_title=top_match["page_title"] if top_match else None,
        top_match_page_id=top_match.get("page_id") if top_match else None,
        top_match_object_id=top_match.get("object_id") if top_match else None,
        top_match_object_url=top_match.get("object_web_url") if top_match else None,
        top_match_order=top_match.get("image_order") if top_match else None,
        onenote_web_url=top_match.get("object_web_url") if top_match else None
    )
    db.add(history_entry)
    db.commit()

    return SearchResponse(
        is_strong_match=is_strong,
        status_message=status_msg,
        top_score=top_score,
        top_percentage=top_percentage,
        threshold=threshold,
        query_image_url=f"/api/storage/{query_img_filename}",
        query_structural_preview_url=f"/api/storage/{struct_preview_filename}",
        matches=matches,
        total_indexed=user_index.count()
    )
