from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.database import get_db, SearchHistoryRecord

router = APIRouter(prefix="/api/history", tags=["Search History"])

@router.get("")
async def get_search_history(
    limit: int = Query(50, ge=1, le=200),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    query = db.query(SearchHistoryRecord)
    if x_user_id:
        query = query.filter(SearchHistoryRecord.user_id == x_user_id)
    records = query.order_by(desc(SearchHistoryRecord.timestamp)).limit(limit).all()
    history_list = []
    for r in records:
        history_list.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "query_image_url": r.query_image_url,
            "query_structural_preview_url": r.query_structural_preview_url,
            "top_match_id": r.top_match_id,
            "top_match_title": r.top_match_title,
            "top_match_image_url": r.top_match_image_url,
            "similarity_percentage": r.similarity_percentage,
            "is_strong_match": r.is_strong_match,
            "notebook_name": r.notebook_name,
            "section_name": r.section_name,
            "page_title": r.page_title,
            "onenote_web_url": r.onenote_web_url
        })
    return {"total": len(history_list), "history": history_list}

@router.delete("")
async def clear_search_history(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    query = db.query(SearchHistoryRecord)
    if x_user_id:
        query = query.filter(SearchHistoryRecord.user_id == x_user_id)
    query.delete()
    db.commit()
    return {"status": "success", "message": "Search history cleared"}
