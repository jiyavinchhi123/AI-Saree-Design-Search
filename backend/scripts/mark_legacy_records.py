import json
import sqlite3

def mark_legacy(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        items = json.load(f)
    for it in items:
        if it.get('object_id') is None or it.get('source_type') == 'onenote_app_sync':
            it['source_type'] = 'legacy_local_backup'
            it['is_verified_graph'] = False
        else:
            it['is_verified_graph'] = True
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2)
    print(f'Updated {len(items)} in {filepath}')

import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
mark_legacy(os.path.join(backend_dir, 'data/indexes/users/b6ecec459b998637/saree_meta.json'))
mark_legacy(os.path.join(backend_dir, 'data/indexes/saree_meta.json'))

conn = sqlite3.connect(os.path.join(backend_dir, 'data/saree_search.db'))
cursor = conn.cursor()
cursor.execute("UPDATE designs SET source_type = 'legacy_local_backup' WHERE object_id IS NULL OR source_type = 'onenote_app_sync'")
conn.commit()
print(f'Updated SQLite designs: {cursor.rowcount} rows marked legacy_local_backup')
conn.close()
