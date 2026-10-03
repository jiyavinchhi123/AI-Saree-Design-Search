import json
from app.onenote.link_builder import get_exact_image_hyperlinks

# Image #223 metadata
item_223 = {
  "id": "ONENOTE-b6ecec-8C424B",
  "design_id": "ONENOTE-b6ecec-8C424B",
  "user_id": "b6ecec459b998637",
  "title": "Saree designs",
  "notebook_name": "My Notebook",
  "section_name": "New Section 2",
  "page_title": "Saree designs",
  "onenote_web_url": "https://onedrive.live.com/redir.aspx?cid=b6ecec459b998637&page=edit&resid=B6ECEC459B998637!1012&wd=target%28New%20Section%202.one%2FSaree%20designs%2F%29",
  "onenote_client_url": None,
  "image_url": "/api/storage/users/b6ecec459b998637/ONENOTE-b6ecec-8C424B.jpg",
  "image_order": 223,
  "resource_id": "ONENOTE-b6ecec-8C424B",
  "page_id": None,
  "object_id": None,
}

res = get_exact_image_hyperlinks(item_223)
print("=== EXACT IMAGE HYPERLINKS FOR IMAGE #223 ===")
for k, v in res.items():
    print(f"{k}: {v}")
