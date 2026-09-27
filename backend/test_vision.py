import os
import cv2
import numpy as np
from app.vision.feature_extractor import ColorInvariantFeatureExtractor
from app.vision.pattern_generator import generate_saree_image

def main():
    print("Testing Saree Design Feature Extractor & Color-Invariance...")
    extractor = ColorInvariantFeatureExtractor()

    # 1. Synthesize Design 1: Banarasi Floral Jaal in Colorway A (Peacock Blue & Gold)
    colorway_blue = {
        "body_bg": (15, 45, 110),      # Deep Royal Blue
        "border_bg": (10, 25, 75),     # Navy
        "zari": (235, 195, 80),        # Antique Gold
        "accent": (255, 220, 120)
    }
    img_banarasi_blue = generate_saree_image("banarasi_jaal", colorway_blue)
    
    # 2. Synthesize Design 1: Banarasi Floral Jaal in Colorway B (Crimson Red & Gold)
    # COMPLETELY DIFFERENT RGB PIXELS, SAME MOTIFS/BORDER/LAYOUT!
    colorway_red = {
        "body_bg": (140, 15, 30),      # Crimson Red
        "border_bg": (95, 10, 20),     # Maroon
        "zari": (235, 195, 80),        # Antique Gold
        "accent": (255, 220, 120)
    }
    img_banarasi_red = generate_saree_image("banarasi_jaal", colorway_red)

    # 3. Synthesize Design 2: Kanjeevaram Temple & Peacock in Yellow & Maroon
    colorway_yellow = {
        "body_bg": (220, 170, 25),     # Mustard Yellow
        "border_bg": (120, 20, 30),    # Maroon
        "zari": (240, 205, 90),
        "accent": (255, 120, 50)
    }
    img_kanjeevaram = generate_saree_image("kanjeevaram_temple", colorway_yellow)

    # 4. Synthesize Design 3: Minimalist Linen (Negative control)
    colorway_linen = {
        "body_bg": (225, 220, 210),
        "border_bg": (210, 205, 195),
        "zari": (150, 150, 150),
        "accent": (100, 100, 100)
    }
    img_minimalist = generate_saree_image("modern_minimalist", colorway_linen)

    # Extract vectors
    v_blue, _ = extractor.extract_features_from_image(img_banarasi_blue)
    v_red, _ = extractor.extract_features_from_image(img_banarasi_red)
    v_kanjeevaram, _ = extractor.extract_features_from_image(img_kanjeevaram)
    v_minimalist, _ = extractor.extract_features_from_image(img_minimalist)

    # Compute cosine similarities (dot product of L2 normalized vectors)
    sim_same_design_diff_color = float(np.dot(v_blue, v_red))
    sim_diff_design_kanjee = float(np.dot(v_blue, v_kanjeevaram))
    sim_diff_design_minimal = float(np.dot(v_blue, v_minimalist))

    print("\n--- RESULTS ---")
    print(f"Same Design (Banarasi Jaal), Different Colors (Blue vs Red): {sim_same_design_diff_color * 100:.2f}% Match")
    print(f"Different Design (Banarasi Jaal vs Kanjeevaram Temple):       {sim_diff_design_kanjee * 100:.2f}% Match")
    print(f"Different Design (Banarasi Jaal vs Modern Linen):            {sim_diff_design_minimal * 100:.2f}% Match")

    if sim_same_design_diff_color > 0.80 and sim_same_design_diff_color > sim_diff_design_kanjee + 0.15:
        print("\nSUCCESS: Color-invariant design matching verified!")
    else:
        print("\nNote: Tuning may be adjusted.")

if __name__ == "__main__":
    main()
