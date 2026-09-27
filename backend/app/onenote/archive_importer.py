"""
OneNote Archive & File Importer.

Allows importing saree design archives (.zip or directory) representing exported OneNote
notebooks and sections. Automatically maps folder structures to Notebook -> Section -> Page.
"""

import os
import zipfile
import shutil
import json
import uuid
import cv2
from typing import Dict, Any, List

class OneNoteArchiveImporter:
    def __init__(self, storage_dir: str = "data/storage"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def process_zip_archive(
        self, 
        zip_path: str, 
        extractor, 
        vector_index,
        default_notebook: str = "Imported OneNote Archive"
    ) -> Dict[str, Any]:
        """
        Extracts a zip file and indexes all saree design images with inferred OneNote hierarchy.
        Hierarchy can be:
        1. Zip root -> Notebook -> Section -> Page -> image.jpg
        2. Zip root -> Section -> Page.jpg
        3. Zip root -> image.jpg (uses defaults)
        4. manifest.json or metadata.json if present
        """
        extract_tmp = os.path.join(self.storage_dir, f"tmp_{uuid.uuid4().hex[:8]}")
        os.makedirs(extract_tmp, exist_ok=True)

        indexed_items = []
        errors = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_tmp)

            # Check if there is a metadata.json manifest
            manifest_path = os.path.join(extract_tmp, "metadata.json")
            manifest_map = {}
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest_data = json.load(mf)
                        if isinstance(manifest_data, list):
                            for entry in manifest_data:
                                if "filename" in entry:
                                    manifest_map[entry["filename"]] = entry
                except Exception as e:
                    print(f"Warning: Manifest parsing error: {e}")

            # Walk through all extracted files
            valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
            for root, dirs, files in os.walk(extract_tmp):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in valid_extensions:
                        continue

                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, extract_tmp)
                    parts = rel_path.split(os.sep)

                    # Infer hierarchy
                    if file in manifest_map:
                        meta = manifest_map[file]
                        notebook = meta.get("notebook", default_notebook)
                        section = meta.get("section", "General")
                        page = meta.get("page", os.path.splitext(file)[0])
                        web_url = meta.get("web_url", f"https://onenote.office.com/imported/{file}")
                        category = meta.get("category", "Traditional")
                    elif len(parts) >= 3:
                        notebook = parts[0]
                        section = parts[1]
                        page = os.path.splitext(parts[2])[0]
                        web_url = "https://www.onenote.com/notebooks"
                        category = "Imported"
                    elif len(parts) == 2:
                        notebook = default_notebook
                        section = parts[0]
                        page = os.path.splitext(parts[1])[0]
                        web_url = "https://www.onenote.com/notebooks"
                        category = "Imported"
                    else:
                        notebook = default_notebook
                        section = "Master Weaves"
                        page = os.path.splitext(file)[0].replace("_", " ").title()
                        web_url = "https://www.onenote.com/notebooks"
                        category = "Imported"

                    design_id = f"ARCH-{uuid.uuid4().hex[:6].upper()}"
                    dest_filename = f"{design_id}_{file}"
                    dest_path = os.path.join(self.storage_dir, dest_filename)
                    shutil.copy2(full_path, dest_path)

                    try:
                        # Extract color-invariant vector and structural map
                        embedding, structural_map = extractor.extract_features_from_image(dest_path)
                        
                        # Save structural preview map for AI vision inspection
                        preview_filename = f"struct_{design_id}.jpg"
                        preview_path = os.path.join(self.storage_dir, preview_filename)
                        cv2.imwrite(preview_path, structural_map)

                        item_meta = {
                            "id": design_id,
                            "design_id": design_id,
                            "title": page,
                            "clean_title": page,
                            "raw_title": file,
                            "notebook_name": notebook,
                            "section_name": section,
                            "page_title": page,
                            "onenote_web_url": f"/api/designs/{design_id}/open-onenote",
                            "onenote_client_url": f"onenote:?title={urllib.parse.quote(page)}",
                            "image_url": f"/api/storage/{dest_filename}",
                            "structural_preview_url": f"/api/storage/{preview_filename}",
                            "category": category,
                            "source_type": "archive_upload",
                            "colorway": "Archive Original"
                        }

                        vector_index.add_design(embedding, item_meta)
                        indexed_items.append(item_meta)
                    except Exception as err:
                        errors.append({"file": file, "error": str(err)})

            vector_index.save()

        finally:
            # Clean up temp folder
            if os.path.exists(extract_tmp):
                shutil.rmtree(extract_tmp, ignore_errors=True)

        return {
            "total_extracted": len(indexed_items),
            "indexed_designs": indexed_items,
            "errors": errors
        }
