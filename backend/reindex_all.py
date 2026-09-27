"""
Batch Re-Indexing Script for AI Saree Design Search.
Re-indexes all catalog designs using the DINOv2 Vision Transformer with 4-zone spatial motif pooling.
"""

import os
import json
import time
import shutil
import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
import faiss
from PIL import Image

def main():
    index_file = os.path.join("data", "indexes", "saree_faiss.index")
    meta_file = os.path.join("data", "indexes", "saree_meta.json")
    backup_file = os.path.join("data", "indexes", "saree_faiss_mobilenet_backup.index")

    if not os.path.exists(meta_file):
        print(f"Error: {meta_file} not found.")
        return

    # 1. Backup old index
    if os.path.exists(index_file) and not os.path.exists(backup_file):
        print(f"Backing up old FAISS index to {backup_file}...")
        shutil.copy2(index_file, backup_file)

    with open(meta_file, "r", encoding="utf-8") as f:
        meta_items = json.load(f)

    total_items = len(meta_items)
    print(f"Found {total_items} items in metadata catalog.")

    # 2. Setup DINOv2 model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading DINOv2 backbone on {device}...")
    torch.set_num_threads(8)
    model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14').to(device).eval()

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    norm_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dimension = 1536
    new_index = faiss.IndexFlatIP(dimension)
    updated_meta = []

    batch_size = 64
    batch_tensors = []
    batch_meta = []
    
    t_start = time.time()
    processed_count = 0
    missing_count = 0

    def process_batch(tensors, metas):
        if not tensors:
            return
        batch = torch.stack(tensors).to(device)
        with torch.no_grad():
            feat = model.forward_features(batch)
            cls_toks = feat['x_norm_clstoken'] # [B, 384]
            patch_toks = feat['x_norm_patchtokens'] # [B, 256, 384]
            grid = patch_toks.reshape(-1, 16, 16, 384)
            top_b = grid[:, :4, :, :].reshape(-1, 64, 384).mean(dim=1)
            body_f = grid[:, 4:12, :, :].reshape(-1, 128, 384).mean(dim=1)
            bot_b = grid[:, 12:, :, :].reshape(-1, 64, 384).mean(dim=1)

        cls_np = cls_toks.cpu().numpy()
        body_np = body_f.cpu().numpy()
        top_np = top_b.cpu().numpy()
        bot_np = bot_b.cpu().numpy()

        # Normalize per zone
        cls_np /= (np.linalg.norm(cls_np, axis=1, keepdims=True) + 1e-7)
        body_np /= (np.linalg.norm(body_np, axis=1, keepdims=True) + 1e-7)
        top_np /= (np.linalg.norm(top_np, axis=1, keepdims=True) + 1e-7)
        bot_np /= (np.linalg.norm(bot_np, axis=1, keepdims=True) + 1e-7)

        vecs = np.concatenate([
            cls_np * 0.50,
            body_np * 0.30,
            top_np * 0.10,
            bot_np * 0.10
        ], axis=1).astype(np.float32)

        vecs /= (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-7)

        # Add to FAISS index
        start_idx = new_index.ntotal
        new_index.add(vecs)

        for i, m in enumerate(metas):
            m["index_id"] = start_idx + i
            updated_meta.append(m)

    print("Beginning batch feature extraction...")
    for idx, item in enumerate(meta_items):
        img_rel = item['image_url'].replace('/api/storage/', 'data/storage/')
        if not os.path.exists(img_rel):
            missing_count += 1
            continue

        bgr = cv2.imread(img_rel)
        if bgr is None:
            missing_count += 1
            continue

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        luma = clahe.apply(gray)
        rgb = cv2.cvtColor(luma, cv2.COLOR_GRAY2RGB)
        pil = Image.fromarray(rgb).resize((224, 224), Image.BICUBIC)
        batch_tensors.append(norm_transform(pil))
        batch_meta.append(item)

        if len(batch_tensors) >= batch_size:
            process_batch(batch_tensors, batch_meta)
            processed_count += len(batch_tensors)
            elapsed = time.time() - t_start
            rate = processed_count / elapsed
            remaining = (total_items - processed_count) / max(rate, 0.01)
            print(f"Indexed {processed_count}/{total_items} designs ({rate:.1f} img/s, ~{remaining:.0f}s remaining)...")
            batch_tensors = []
            batch_meta = []

    # Final batch
    if batch_tensors:
        process_batch(batch_tensors, batch_meta)
        processed_count += len(batch_tensors)

    # Save new index and meta
    print(f"Indexing completed: {new_index.ntotal} total vectors indexed ({missing_count} missing).")
    faiss.write_index(new_index, index_file)
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(updated_meta, f, indent=2)

    total_time = time.time() - t_start
    print(f"Saved new index to {index_file} ({total_time:.1f}s elapsed).")

    # 3. Verification search on query_6ea36b12.jpg (pink Ikat saree from user screenshot)
    query_path = "data/storage/query_6ea36b12.jpg"
    if os.path.exists(query_path):
        print("\n--- RUNNING ACCURACY VERIFICATION ON USER'S PINK IKAT QUERY ---")
        from app.vision.feature_extractor import ColorInvariantFeatureExtractor
        extractor = ColorInvariantFeatureExtractor()
        q_emb, _ = extractor.extract_features_from_image(query_path)
        
        scores, indices = new_index.search(np.expand_dims(q_emb, axis=0), 10)
        print("Top 10 Predictions:")
        for r, (score, i) in enumerate(zip(scores[0], indices[0])):
            m = updated_meta[i]
            print(f"{r+1}. [{m.get('section_name')}] {m.get('title')[:35]} | Score: {score:.4f} ({score*100:.1f}%) | URL: {m.get('image_url')}")

if __name__ == "__main__":
    main()
