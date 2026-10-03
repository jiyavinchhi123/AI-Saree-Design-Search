"""
Color-Invariant Feature Extraction Module for Saree Designs.

Powered by Meta's DINOv2 (Self-Supervised Vision Transformer) backbone with:
- Contrast-normalized CLAHE luminance input (100% color-invariant)
- Deep semantic motif embeddings (CLS token)
- 4-Zone Spatial Motif & Border Pooling:
    * Zone 1: Top Zari / Temple border
    * Zone 2: Saree Body Field (repeating Jaal, Buttis, Geometric Weaves)
    * Zone 3: Bottom Border & Pallu
- Visual Structural Tensor Generation for UI Inspection

Hue and saturation are completely eliminated so the identical design
in different colors (e.g., Pink vs Yellow vs Peacock Blue) matches with high fidelity,
while differing motifs (e.g., Ikat geometric weave vs Bandhani tie-dye dots) are cleanly separated.
"""

import os
import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
from typing import Tuple, List, Union

class ColorInvariantFeatureExtractor:
    def __init__(self, device: str = None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        torch.set_grad_enabled(False)
        if self.device.type == "cpu":
            try:
                torch.set_num_threads(1)
            except Exception:
                pass

        self._model = None

        # ImageNet normalization for DINOv2
        self.normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        self.to_tensor = transforms.ToTensor()
        # CLAHE for luminance contrast normalization (eliminates shadows and colorcast)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    @property
    def model(self):
        """Lazy load DINOv2 model on first search request to prevent boot-time OOM on low-memory servers"""
        if self._model is None:
            import gc
            torch.set_grad_enabled(False)
            if self.device.type == "cpu":
                try:
                    torch.set_num_threads(1)
                except Exception:
                    pass
            print("[AI Saree Search] Initializing DINOv2 vision model on demand...")
            self._model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')
            self._model.to(self.device)
            self._model.eval()
            gc.collect()
            print("[AI Saree Search] DINOv2 vision model loaded successfully.")
        return self._model

    def preprocess_to_structural_tensor(self, image_np: np.ndarray) -> np.ndarray:
        """
        Converts any RGB/BGR image into a 3-channel structural visualization map:
        Channel 0: CLAHE normalized grayscale luminance
        Channel 1: Sobel gradient magnitude (sharp motif contours & border lines)
        Channel 2: Multi-scale Adaptive threshold / Laplacian (fine jacquard weave texture)
        
        Returns:
            structural_bgr: 3-channel image for visualization/inspection (0-255)
        """
        if len(image_np.shape) == 2:
            gray = image_np
        else:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

        gray_resized = cv2.resize(gray, (224, 224), interpolation=cv2.INTER_AREA)

        # 1. CLAHE Luminance Normalization
        luma = self.clahe.apply(gray_resized)

        # 2. Gradient Magnitude (Sobel X and Y) - captures motif borders & layout
        sobel_x = cv2.Sobel(luma, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(luma, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = cv2.magnitude(sobel_x, sobel_y)
        grad_mag = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 3. Fine jacquard texture & edge details
        blurred = cv2.GaussianBlur(luma, (3, 3), 0)
        edges = cv2.Canny(blurred, 40, 120)
        adaptive = cv2.adaptiveThreshold(
            luma, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        texture_channel = cv2.addWeighted(edges, 0.6, 255 - adaptive, 0.4, 0)

        # Stack into 3-channel purely structural representation
        structural_map = np.stack([luma, grad_mag, texture_channel], axis=-1)
        return structural_map

    def _prepare_dinov2_tensor(self, img_bgr: np.ndarray) -> torch.Tensor:
        """Prepares a color-invariant CLAHE luminance tensor ready for DINOv2."""
        if len(img_bgr.shape) == 2:
            gray = img_bgr
        else:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        luma = self.clahe.apply(gray)
        # Duplicate contrast-normalized luma into 3 channels (pure color-invariance)
        rgb = cv2.cvtColor(luma, cv2.COLOR_GRAY2RGB)
        pil_img = Image.fromarray(rgb).resize((224, 224), Image.BICUBIC)
        tensor = self.normalize(self.to_tensor(pil_img)).unsqueeze(0).to(self.device)
        return tensor

    def extract_features_from_image(self, image_input: Union[str, Image.Image, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts the unified color-invariant 1536-dimensional feature vector.
        
        Args:
            image_input: Can be a file path (str), PIL.Image, or numpy.ndarray (BGR)
            
        Returns:
            embedding: 1D numpy array (L2-normalized, ready for FAISS cosine similarity)
            structural_map: 3-channel numpy array showing the AI vision structural map
        """
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image not found: {image_input}")
            img_bgr = cv2.imread(image_input)
            if img_bgr is None:
                raise ValueError(f"Could not read image: {image_input}")
        elif isinstance(image_input, Image.Image):
            img_rgb = np.array(image_input)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            img_bgr = image_input
        else:
            raise TypeError("Unsupported image input type")

        # 1. Structural tensor representation for inspection
        structural_map = self.preprocess_to_structural_tensor(img_bgr)

        # 2. Deep DINOv2 feature extraction with 4-zone spatial pooling
        tensor = self._prepare_dinov2_tensor(img_bgr)
        with torch.no_grad():
            feat = self.model.forward_features(tensor)
            cls_tok = feat['x_norm_clstoken'].squeeze(0)          # [384]
            patch_tok = feat['x_norm_patchtokens'].squeeze(0)      # [256, 384]

            # 16x16 patch grid decomposition for saree vertical layout
            grid = patch_tok.reshape(16, 16, 384)
            top_border = grid[:4, :, :].reshape(-1, 384).mean(dim=0)      # Top 25% (border)
            body_field = grid[4:12, :, :].reshape(-1, 384).mean(dim=0)    # Middle 50% (jaal / motifs)
            bottom_border = grid[12:, :, :].reshape(-1, 384).mean(dim=0)  # Bottom 25% (border / pallu)

        cls_np = cls_tok.cpu().numpy()
        body_np = body_field.cpu().numpy()
        top_np = top_border.cpu().numpy()
        bottom_np = bottom_border.cpu().numpy()

        # Zone-wise L2 normalization before weighted composition
        cls_np /= (np.linalg.norm(cls_np) + 1e-7)
        body_np /= (np.linalg.norm(body_np) + 1e-7)
        top_np /= (np.linalg.norm(top_np) + 1e-7)
        bottom_np /= (np.linalg.norm(bottom_np) + 1e-7)

        # Weighted combination: Global Motif (0.50), Body Weave/Jaal (0.30), Borders (0.10 each)
        combined = np.concatenate([
            cls_np * 0.50,
            body_np * 0.30,
            top_np * 0.10,
            bottom_np * 0.10
        ]).astype(np.float32)

        # Global L2 Normalization (dot product == cosine similarity)
        norm = np.linalg.norm(combined)
        if norm > 1e-7:
            normalized_embedding = combined / norm
        else:
            normalized_embedding = combined

        return normalized_embedding, structural_map
