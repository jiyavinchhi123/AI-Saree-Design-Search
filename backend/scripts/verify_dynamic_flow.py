import os
import sys
import json
import cv2

# Set backend working directory context
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.database import SessionLocal, UserRecord
from app.main import extractor, vector_index_mgr

def run_debug_verification():
    db = SessionLocal()
    u = db.query(UserRecord).first()
    user_id = u.id if u else "b6ecec459b998637"
    email = u.email if u else "N/A"
    name = u.display_name if u else "N/A"
    db.close()

    print("==================================================")
    print("   DYNAMIC ONENOTE METADATA VERIFICATION TEST   ")
    print("==================================================")
    print(f"Connected User ID:      {user_id}")
    print(f"Connected User Email:   {email}")
    print(f"Connected Display Name: {name}")

    user_index = vector_index_mgr.get_index(user_id)
    print(f"Total Designs in Index: {user_index.count()}")
    print("--------------------------------------------------")

    # Select real image (defaults to ONENOTE-b6ecec-8C424B Image #223, or user-provided)
    target_id = sys.argv[1] if len(sys.argv) > 1 else "ONENOTE-b6ecec-8C424B"
    indexed_record = None
    for item in user_index.metadata_store:
        if item.get("image_id") == target_id or item.get("id") == target_id or item.get("design_id") == target_id:
            indexed_record = item
            break

    if not indexed_record:
        indexed_record = user_index.metadata_store[0]
        target_id = indexed_record.get("image_id")

    print("\n[INDEXING TIME METADATA STORED]")
    print(f"  image_id:          {indexed_record.get('image_id')}")
    print(f"  notebook_name:     {indexed_record.get('notebook_name')}")
    print(f"  section_name:      {indexed_record.get('section_name')}")
    print(f"  page_title:        {indexed_record.get('page_title')}")
    print(f"  object_id:         {indexed_record.get('object_id')}")
    print(f"  oneNoteWebUrl:     {indexed_record.get('oneNoteWebUrl')}")
    print(f"  oneNoteClientUrl:  {indexed_record.get('oneNoteClientUrl')}")

    # Load the actual image file from storage
    img_path = os.path.join(backend_dir, "data", "storage", "users", user_id, f"{target_id}.jpg")
    print(f"\n[QUERY IMAGE]")
    print(f"  File: {img_path}")
    print(f"  Exists: {os.path.exists(img_path)}")

    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        print("ERROR: Failed to read image file!")
        return

    # Extract embedding and search
    embedding, _ = extractor.extract_features_from_image(img_bgr)
    search_res = user_index.search(query_embedding=embedding, top_k=1, threshold=0.82)
    top_match = search_res["matches"][0]

    print("\n[SEARCH RESULT MATCH METADATA]")
    print(f"  image_id:          {top_match.get('image_id')}")
    print(f"  notebook_name:     {top_match.get('notebook_name')}")
    print(f"  section_name:      {top_match.get('section_name')}")
    print(f"  page_title:        {top_match.get('page_title')}")
    print(f"  object_id:         {top_match.get('object_id')}")
    print(f"  oneNoteWebUrl:     {top_match.get('oneNoteWebUrl')}")
    print(f"  oneNoteClientUrl:  {top_match.get('oneNoteClientUrl')}")
    print(f"  similarity_score:  {top_match.get('similarity_score')}")
    print(f"  similarity_pct:    {top_match.get('similarity_percentage')}%")

    # Strict Equality Verification
    fields = [
        "image_id",
        "notebook_name",
        "section_name",
        "page_title",
        "object_id",
        "oneNoteWebUrl",
        "oneNoteClientUrl"
    ]

    print("\n[FIELD-BY-FIELD COMPARISON]")
    all_match = True
    for f in fields:
        stored = indexed_record.get(f)
        returned = top_match.get(f)
        status = "MATCH" if stored == returned else "MISMATCH"
        if stored != returned:
            all_match = False
        print(f"  {f:18}: Stored='{stored}' | Returned='{returned}' [{status}]")

    print("\n==================================================")
    if all_match:
        print("  VERIFICATION RESULT: PASSED (100% IDENTICAL)  ")
        print("  Zero reconstruction. Single source of truth.   ")
    else:
        print("  VERIFICATION RESULT: FAILED                    ")
    print("==================================================")

if __name__ == "__main__":
    run_debug_verification()
