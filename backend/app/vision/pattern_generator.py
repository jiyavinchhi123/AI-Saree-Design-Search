"""
Authentic Saree Design Pattern Generator.

Generates high-resolution, realistic saree design images with authentic Indian motifs:
- Banarasi Floral Jaal (Brocade vines, rosettes, Shalu border)
- Kanjeevaram Temple (Spire triangles, Peacock/Mayil buttas, Korvai border)
- Paithani Muniya (Stylized parrot & peacock border, Asavali flower)
- Bandhani Gharchola (Zari square grid with tie-dye speckles)
- Chanderi Boota (Delicate gold coin motifs and sheer borders)
- Patola Double Ikat (Stepped geometric symmetry)
- Contemporary Minimalist (Negative control for "No strong match found")

Crucially, each core design is synthesized in MULTIPLE DISTINCT COLORWAYS
to prove color-invariant search capabilities.
"""

import os
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def create_fabric_texture(width: int, height: int, base_color: tuple, weave_intensity: float = 0.08) -> np.ndarray:
    """Creates a base silk/zari fabric texture with microscopic weave noise."""
    base = np.zeros((height, width, 3), dtype=np.float32)
    base[:, :] = base_color

    # Jacquard weave thread pattern
    y, x = np.ogrid[:height, :width]
    warp_weft = (np.sin(x * 1.5) * np.cos(y * 1.5)) * (weave_intensity * 255.0)
    
    # Add subtle random silk sheen
    noise = np.random.normal(0, 4.0, (height, width, 1))
    fabric = base + warp_weft[:, :, np.newaxis] + noise
    return np.clip(fabric, 0, 255).astype(np.uint8)

def draw_temple_spires(draw: ImageDraw.ImageDraw, y_base: int, spire_h: int, w: int, spire_w: int, color: tuple):
    """Draws traditional Kanjeevaram temple spires (triangular spires) along border."""
    x = 0
    while x < w:
        pts = [(x, y_base), (x + spire_w // 2, y_base - spire_h), (x + spire_w, y_base)]
        draw.polygon(pts, fill=color)
        # Inner accent spire
        inner_pts = [(x + 4, y_base), (x + spire_w // 2, y_base - spire_h + 6), (x + spire_w - 4, y_base)]
        draw.polygon(inner_pts, outline=(255, 230, 150), width=1)
        x += spire_w

def draw_paisley_kalka(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color: tuple, angle: float = 0):
    """Draws an authentic Indian Paisley / Mango / Kalka motif."""
    # Approximate a teardrop with curved tip
    r = size // 2
    # Outer circle for bottom
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    # Curved hook tip
    pts = [
        (cx - r // 2, cy - r // 4),
        (cx + r // 2, cy - r),
        (cx + r, cy - r * 1.5),
        (cx + r * 1.3, cy - r * 1.2),
        (cx + r * 0.7, cy - r * 0.4),
        (cx + r // 2, cy)
    ]
    draw.polygon(pts, fill=color)
    # Inner paisley core
    draw.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2], outline=(255, 240, 180), width=2)
    # Center dot
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 240, 180))

def draw_peacock_motif(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color: tuple):
    """Draws a traditional Mayil (Peacock) butta motif."""
    r = size // 3
    # Body
    draw.ellipse([cx - r, cy, cx + r, cy + r * 1.5], fill=color)
    # Neck and head
    draw.line([(cx, cy + r // 2), (cx - r // 2, cy - r // 2)], fill=color, width=r // 2)
    draw.ellipse([cx - r, cy - r - 4, cx, cy - r + 8], fill=color)
    # Beak
    draw.polygon([(cx - r, cy - r + 2), (cx - r - 6, cy - r + 4), (cx - r, cy - r + 6)], fill=(255, 220, 130))
    # Crest (crown feathers)
    draw.line([(cx - r // 2, cy - r - 2), (cx - r // 2 - 4, cy - r - 10)], fill=(255, 220, 130), width=2)
    draw.line([(cx - r // 2 + 2, cy - r - 2), (cx - r // 2 + 2, cy - r - 10)], fill=(255, 220, 130), width=2)
    # Fan feathers (tail)
    for ang in range(-60, 70, 20):
        rad = math.radians(ang)
        ex = int(cx + math.sin(rad) * (size * 0.9))
        ey = int(cy + r + math.cos(rad) * (size * 0.6))
        draw.line([(cx, cy + r), (ex, ey)], fill=color, width=3)
        draw.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=(255, 235, 160))

def draw_floral_jaal_network(draw: ImageDraw.ImageDraw, top: int, bottom: int, w: int, spacing: int, color: tuple):
    """Draws diagonal floral vine network (Jaal) typical of Banarasi brocades."""
    # Diagonal vines
    for offset in range(-w, w * 2, spacing):
        # Sine wave vine 1
        pts1 = []
        pts2 = []
        for y in range(top, bottom, 10):
            x1 = offset + int((y - top) * 0.8 + math.sin(y * 0.05) * 12)
            x2 = offset - int((y - top) * 0.8 + math.cos(y * 0.05) * 12) + w
            pts1.append((x1, y))
            pts2.append((x2, y))
        if len(pts1) > 1:
            draw.line(pts1, fill=color, width=2)
        if len(pts2) > 1:
            draw.line(pts2, fill=color, width=2)

    # Rosette blossoms at vine intersections
    for y in range(top + spacing // 2, bottom - spacing // 2, spacing):
        for x in range(spacing // 2, w, spacing):
            # Center flower
            draw.ellipse([x - 8, y - 8, x + 8, y + 8], fill=color)
            # Petals
            for p_ang in range(0, 360, 45):
                prad = math.radians(p_ang)
                px = int(x + math.cos(prad) * 12)
                py = int(y + math.sin(prad) * 12)
                draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 235, 170))

def generate_saree_image(design_type: str, colorway: dict, width: int = 600, height: int = 600) -> Image.Image:
    """
    Synthesizes a high-fidelity saree image for a specified design pattern and colorway.
    """
    # 1. Base fabric
    body_bg = colorway["body_bg"]
    border_bg = colorway["border_bg"]
    zari_color = colorway["zari"]
    accent_color = colorway.get("accent", zari_color)

    # Create fabric background
    fabric_np = create_fabric_texture(width, height, body_bg)
    img = Image.fromarray(fabric_np)
    draw = ImageDraw.Draw(img)

    border_height = int(height * 0.22)
    top_border_y = border_height
    bottom_border_y = height - border_height

    # 2. Draw border backgrounds
    draw.rectangle([0, 0, width, top_border_y], fill=border_bg)
    draw.rectangle([0, bottom_border_y, width, height], fill=border_bg)

    # Decorative zari piping separating border and body
    draw.line([(0, top_border_y), (width, top_border_y)], fill=zari_color, width=4)
    draw.line([(0, top_border_y - 8), (width, top_border_y - 8)], fill=accent_color, width=2)
    draw.line([(0, bottom_border_y), (width, bottom_border_y)], fill=zari_color, width=4)
    draw.line([(0, bottom_border_y + 8), (width, bottom_border_y + 8)], fill=accent_color, width=2)

    if design_type == "banarasi_jaal":
        # Banarasi Shalu border pattern: ornate diagonal chevrons & floral creeper
        for y_off in [top_border_y - 45, bottom_border_y + 25]:
            for x in range(20, width, 40):
                draw_paisley_kalka(draw, x, y_off, 24, zari_color)
        # Continuous floral jaal across field
        draw_floral_jaal_network(draw, top_border_y + 10, bottom_border_y - 10, width, 70, zari_color)

    elif design_type == "kanjeevaram_temple":
        # Temple spires pointing into body from both borders
        spire_h = 28
        draw_temple_spires(draw, top_border_y + spire_h, spire_h, width, 32, border_bg)
        # Inverted spires on bottom
        for x in range(0, width, 32):
            pts = [(x, bottom_border_y), (x + 16, bottom_border_y - spire_h), (x + 32, bottom_border_y)]
            draw.polygon(pts, fill=border_bg)
        
        # Border internal zari bands
        for b_y in [top_border_y // 2, height - border_height // 2]:
            draw.line([(0, b_y), (width, b_y)], fill=zari_color, width=6)
            for x in range(15, width, 30):
                draw.rectangle([x - 5, b_y - 5, x + 5, b_y + 5], fill=(255, 240, 180))

        # Peacock (Mayil) buttas scattered across body in alternating grid
        row = 0
        for y in range(top_border_y + 50, bottom_border_y - 40, 75):
            offset_x = 35 if row % 2 == 1 else 0
            for x in range(40 + offset_x, width - 20, 80):
                draw_peacock_motif(draw, x, y, 32, zari_color)
            row += 1

    elif design_type == "paithani_muniya":
        # Paithani signature Muniya (parrot) border
        for b_y in [top_border_y - 35, bottom_border_y + 35]:
            for x in range(25, width, 45):
                # Stylized oblique parrot/muniya
                draw.polygon([(x, b_y - 12), (x + 18, b_y), (x, b_y + 12), (x - 6, b_y)], fill=zari_color)
                draw.ellipse([x - 4, b_y - 4, x + 4, b_y + 4], fill=accent_color)
        
        # Body: Classic Asavali rosettes & coin buttas
        for y in range(top_border_y + 40, bottom_border_y - 30, 60):
            for x in range(35, width, 70):
                # Star / coin butta
                draw.ellipse([x - 10, y - 10, x + 10, y + 10], fill=zari_color)
                draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=accent_color)

    elif design_type == "bandhani_gharchola":
        # Gharchola golden zari square grid
        grid_step = 55
        for x in range(0, width, grid_step):
            draw.line([(x, 0), (x, height)], fill=zari_color, width=3)
        for y in range(0, height, grid_step):
            draw.line([(0, y), (width, y)], fill=zari_color, width=3)

        # Traditional Bandhani tie-dye speckled dots inside each square
        for gx in range(grid_step // 2, width, grid_step):
            for gy in range(grid_step // 2, height, grid_step):
                # Central flower of 5 white dots
                draw.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], fill=(255, 255, 255))
                for dang in range(0, 360, 60):
                    drad = math.radians(dang)
                    dx = int(gx + math.cos(drad) * 12)
                    dy = int(gy + math.sin(drad) * 12)
                    draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(255, 255, 255))

    elif design_type == "patola_ikat":
        # Double ikat stepped geometry
        step = 50
        for y in range(top_border_y + 20, bottom_border_y - 20, step):
            for x in range(step // 2, width, step):
                # Diamond with stepped edges
                pts = [
                    (x, y - 20), (x + 8, y - 12), (x + 20, y), 
                    (x + 8, y + 12), (x, y + 20), (x - 8, y + 12), 
                    (x - 20, y), (x - 8, y - 12)
                ]
                draw.polygon(pts, outline=zari_color, fill=accent_color)
                draw.rectangle([x - 4, y - 4, x + 4, y + 4], fill=(255, 255, 255))

    elif design_type == "modern_minimalist":
        # Contemporary plain linen: no motifs, simple thin accent line
        # Used as a negative test to show "No strong match found"
        draw.line([(0, height - 40), (width, height - 40)], fill=accent_color, width=2)
        draw.line([(0, height - 35), (width, height - 35)], fill=(180, 180, 180), width=1)

    return img
