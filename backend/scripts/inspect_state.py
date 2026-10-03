import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.database import SessionLocal, DesignRecord, UserRecord
from app.main import vector_index_mgr

db = SessionLocal()
print('Total DesignRecords in DB:', db.query(DesignRecord).count())
for d in db.query(DesignRecord).all():
    print(f'DB row: id={d.id}, user_id={d.user_id}, title={d.title}, object_id={d.object_id}')

print('\nDefault index count:', vector_index_mgr._default_index.count())
u = db.query(UserRecord).first()
if u:
    u_idx = vector_index_mgr.get_index(u.id)
    print(f'User index count ({u.id}):', u_idx.count())
    for m in u_idx.metadata_store:
        print(f'User index item: {m.get("design_id")} -> obj_id: {m.get("object_id")} on page "{m.get("page_title")}"')
db.close()
