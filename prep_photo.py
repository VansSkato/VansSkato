#!/usr/bin/env python3
"""
Step 3a — Prep a photo for ASCII conversion.

1. Remove the background with OpenCV's GrabCut (no model download,
   works fully offline) so only the subject remains.
2. Boost local contrast with CLAHE so a flatly-lit face gets real
   highlights/shadows instead of converting into a dark blob.
3. Composite onto pure white so the background maps to the blank
   end of the ASCII density ramp (white -> space).

Usage:
    python scripts/prep_photo.py source-photo.jpg
Writes:
    source-prepped.png (grayscale, ready for make_ascii_svg.py)
"""
import sys
import numpy as np
import cv2
from PIL import Image


def remove_background_grabcut(bgr: np.ndarray) -> np.ndarray:
    """Return a 0/255 uint8 mask (255 = subject) using GrabCut,
    seeded with a rectangle inset from the frame edges."""
    h, w = bgr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Portrait framing assumption: subject fills most of the frame,
    # background is a thin border around it.
    margin_x, margin_top, margin_bottom = int(w * 0.06), int(h * 0.03), int(h * 0.02)
    rect = (margin_x, margin_top, w - 2 * margin_x, h - margin_top - margin_bottom)

    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")

    # Clean up small holes/specks
    kernel = np.ones((5, 5), np.uint8)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    return fg_mask


def prep(input_path: str, output_path: str = "source-prepped.png"):
    bgr = cv2.imread(input_path)
    if bgr is None:
        raise FileNotFoundError(f"could not read {input_path}")

    alpha = remove_background_grabcut(bgr)

    # 1+2. Composite onto pure white using the mask
    white_bg = np.full_like(bgr, 255)
    alpha_3c = cv2.merge([alpha, alpha, alpha]).astype(np.float32) / 255.0
    composited = (bgr.astype(np.float32) * alpha_3c + white_bg.astype(np.float32) * (1 - alpha_3c))
    composited = composited.astype(np.uint8)

    # 3. Grayscale + CLAHE local contrast boost
    gray = cv2.cvtColor(composited, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)

    # Re-flatten background to pure white (CLAHE can gray it slightly)
    boosted[alpha < 10] = 255

    # Smooth out fine texture (pinstripes, hair strands, skin pores)
    # BEFORE the huge downsample to a ~100x53 character grid — without
    # this, that texture aliases into dense noise across the whole
    # portrait instead of clean tonal blocks.
    h, w = boosted.shape[:2]
    target_cols = 60
    sigma = max(1.0, (w / target_cols) / 2.2)
    ksize = int(sigma * 6) | 1  # odd kernel size
    boosted = cv2.GaussianBlur(boosted, (ksize, ksize), sigma)

    # Push midtones toward the extremes so a handful of ASCII density
    # levels reads as a clear image instead of a flat gray smear.
    boosted = cv2.convertScaleAbs(boosted, alpha=1.35, beta=-25)
    boosted[alpha < 10] = 255

    Image.fromarray(boosted).save(output_path)
    print(f"wrote {output_path}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    prep(src)
