import asyncio
import os
import sys
import json

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.database import SessionLocal, UserRecord, DesignRecord
from app.routers.data_sources import sync_onenote
from app.main import vector_index_mgr

async def run_sync():
    db = SessionLocal()
    u = db.query(UserRecord).first()
    if not u:
        print("No user connected in DB!")
        return

    print("==================================================")
    print("      ONE NOTE CLOUD SYNCHRONIZATION RUN          ")
    print("==================================================")
    print(f"Connected User: {u.display_name} ({u.email}) [ID: {u.id}]")
    print(f"Index count BEFORE sync: {vector_index_mgr.get_index(u.id).count()}")
    print(f"Database count BEFORE sync: {db.query(DesignRecord).filter(DesignRecord.user_id == u.id).count()}")
    print("--------------------------------------------------")
    print("Executing cloud sync from Microsoft Graph...")

    result = await sync_onenote(sync_req=None, x_user_id=u.id, db=db)
    
    # Re-query user
    db.refresh(u)
    active_designs = db.query(DesignRecord).filter(DesignRecord.user_id == u.id).all()
    user_idx = vector_index_mgr.get_index(u.id)

    print("\n==================================================")
    print("           SYNCHRONIZATION RESULTS                ")
    print("==================================================")
    print(f"Status:                      {result.get('status')}")
    print(f"Message:                     {result.get('message')}")
    print(f"Graph notebooks found:       {result.get('notebooks_found')}")
    print(f"Graph sections found:        {result.get('sections_found')}")
    print(f"Graph pages found:           {result.get('pages_scanned')}")
    print(f"Graph image count:           {result.get('total_images_found')}")
    print(f"Active indexed design count: {result.get('indexed_count')}")
    print(f"User total designs:          {u.total_designs}")
    print(f"Index items in memory:       {user_idx.count()}")
    print(f"Database rows for user:      {len(active_designs)}")
    print("==================================================")

    db.close()

if __name__ == "__main__":
    asyncio.run(run_sync())
