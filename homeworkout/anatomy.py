"""
Muscle Anatomy Diagram Generator for FitPulse.
Produces dynamic front (anterior) and back (posterior) human body diagrams
with targeted muscle groups highlighted in electric blue (#0863F2) and sky blue (#64AFFF),
matching the exact faceted polygon silhouette style of REF/jumpingjack.jpg.
"""

import os
from pathlib import Path
from typing import List, Optional
from PIL import Image
import numpy as np

# Base paths
MODULE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = MODULE_DIR.parent
BASE_IMG_PATH = PROJECT_DIR / "workout_data" / "images" / "anatomy_base.png"

# Color constants matching REF/jumpingjack.jpg
BASE_GRAY = np.array([204, 204, 206], dtype=np.uint8)         # #CCCCCC neutral body
PRIMARY_BLUE = np.array([8, 99, 242], dtype=np.uint8)        # #0863F2 vibrant electric blue
SECONDARY_BLUE = np.array([100, 175, 255], dtype=np.uint8)    # #64AFFF sky blue accent

_CACHED_BASE_ARR: Optional[np.ndarray] = None


def _get_base_array() -> np.ndarray:
    """Loads and caches the neutral polygon anatomy silhouette array."""
    global _CACHED_BASE_ARR
    if _CACHED_BASE_ARR is not None:
        return _CACHED_BASE_ARR.copy()

    if BASE_IMG_PATH.exists():
        im = Image.open(BASE_IMG_PATH).convert("RGB")
        _CACHED_BASE_ARR = np.array(im)
        return _CACHED_BASE_ARR.copy()

    # Fallback: check REF/jumpingjack.jpg if base is not yet generated
    ref_path = PROJECT_DIR / "REF" / "jumpingjack.jpg"
    if ref_path.exists():
        im = Image.open(ref_path).convert("RGB")
        arr = np.array(im)
        is_body = ~((arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240))
        is_orig_blue = (arr[:, :, 2] > arr[:, :, 0] + 30) & is_body
        arr[is_orig_blue] = BASE_GRAY
        _CACHED_BASE_ARR = arr
        return _CACHED_BASE_ARR.copy()

    # Synthetic fallback: 673x548 blank white canvas with body placeholder
    canvas = np.full((548, 673, 3), 255, dtype=np.uint8)
    _CACHED_BASE_ARR = canvas
    return _CACHED_BASE_ARR.copy()


def generate_muscle_anatomy_image(
    target_muscle: str,
    focus_areas: Optional[List[str]] = None,
    width: Optional[int] = 360,
    height: Optional[int] = 220
) -> Image.Image:
    """
    Generates a PIL Image depicting front and back body anatomy
    with targeted muscle groups highlighted matching REF/jumpingjack.jpg.
    """
    if focus_areas is None:
        focus_areas = []

    canvas = _get_base_array()
    h, w, _ = canvas.shape
    Y, X = np.ogrid[:h, :w]

    # Non-white body mask (preserves white borders and facet separation lines)
    is_body = ~((canvas[:, :, 0] > 240) & (canvas[:, :, 1] > 240) & (canvas[:, :, 2] > 240))

    # Anatomic Polygon Coordinates (Front: X < 340, Back: X >= 340)
    chest_mask = is_body & (X < 340) & (Y >= 135) & (Y <= 185) & (X >= 185) & (X <= 250)
    delts_front = is_body & (X < 340) & (Y >= 135) & (Y <= 180) & (((X >= 148) & (X <= 188)) | ((X >= 248) & (X <= 288)))
    delts_rear = is_body & (X >= 340) & (Y >= 135) & (Y <= 180) & (((X >= 398) & (X <= 438)) | ((X >= 498) & (X <= 538)))
    arms_front = is_body & (X < 340) & (Y >= 180) & (Y <= 285) & (((X >= 115) & (X <= 175)) | ((X >= 260) & (X <= 320)))
    arms_back = is_body & (X >= 340) & (Y >= 175) & (Y <= 285) & (((X >= 365) & (X <= 425)) | ((X >= 510) & (X <= 570)))
    abs_mask = is_body & (X < 340) & (Y >= 185) & (Y <= 260) & (X >= 170) & (X <= 265)
    traps_mask = is_body & (X >= 340) & (Y >= 120) & (Y <= 175) & (X >= 430) & (X <= 505)
    lats_mask = is_body & (X >= 340) & (Y >= 175) & (Y <= 245) & (X >= 418) & (X <= 518)
    glutes_mask = is_body & (X >= 340) & (Y >= 235) & (Y <= 290) & (X >= 420) & (X <= 515)
    quads_mask = is_body & (X < 340) & (Y >= 260) & (Y <= 385) & (X >= 165) & (X <= 270)
    hamstrings_mask = is_body & (X >= 340) & (Y >= 290) & (Y <= 385) & (X >= 415) & (X <= 520)
    calves_front = is_body & (X < 340) & (Y >= 385) & (Y <= 485) & (X >= 175) & (X <= 260)
    calves_back = is_body & (X >= 340) & (Y >= 385) & (Y <= 485) & (X >= 425) & (X <= 510)

    # Determine muscle target context
    tm = str(target_muscle).lower()
    focus_text = (" ".join(focus_areas)).lower()

    # Highlight mapping based on primary target muscle and specific focus areas
    if "chest" in tm or "dada" in tm:
        canvas[chest_mask] = PRIMARY_BLUE
        if "tricep" in focus_text or "lengan" in focus_text:
            canvas[arms_back] = PRIMARY_BLUE
        else:
            canvas[arms_back] = SECONDARY_BLUE
        if "shoulder" in focus_text or "deltoid" in focus_text or "bahu" in focus_text:
            canvas[delts_front] = PRIMARY_BLUE
        else:
            canvas[delts_front] = SECONDARY_BLUE

    elif "abs" in tm or "core" in tm or "perut" in tm:
        canvas[abs_mask] = PRIMARY_BLUE
        if "oblique" in focus_text:
            canvas[abs_mask] = PRIMARY_BLUE
        if "hip" in focus_text or "leg" in focus_text or "kaki" in focus_text:
            canvas[quads_mask] = SECONDARY_BLUE
        if "back" in focus_text or "erector" in focus_text:
            canvas[lats_mask] = SECONDARY_BLUE

    elif "arm" in tm or "lengan" in tm or "bahu" in tm:
        if "tricep" in focus_text:
            canvas[arms_back] = PRIMARY_BLUE
            canvas[delts_front] = SECONDARY_BLUE
            canvas[chest_mask] = SECONDARY_BLUE
        elif "deltoid" in focus_text or "shoulder" in focus_text or "pike" in focus_text:
            canvas[delts_front] = PRIMARY_BLUE
            canvas[delts_rear] = PRIMARY_BLUE
            canvas[arms_back] = SECONDARY_BLUE
            canvas[traps_mask] = SECONDARY_BLUE
        else:
            canvas[delts_front] = PRIMARY_BLUE
            canvas[delts_rear] = PRIMARY_BLUE
            canvas[arms_front] = PRIMARY_BLUE
            canvas[arms_back] = SECONDARY_BLUE

    elif "leg" in tm or "kaki" in tm:
        canvas[quads_mask] = PRIMARY_BLUE
        if "glute" in focus_text or "bokong" in focus_text:
            canvas[glutes_mask] = PRIMARY_BLUE
            canvas[hamstrings_mask] = PRIMARY_BLUE
        else:
            canvas[glutes_mask] = SECONDARY_BLUE
            canvas[hamstrings_mask] = SECONDARY_BLUE

        if "calf" in focus_text or "calves" in focus_text or "betis" in focus_text:
            canvas[calves_front] = PRIMARY_BLUE
            canvas[calves_back] = PRIMARY_BLUE
        else:
            canvas[calves_front] = SECONDARY_BLUE
            canvas[calves_back] = SECONDARY_BLUE

    elif "back" in tm or "punggung" in tm:
        canvas[traps_mask] = PRIMARY_BLUE
        canvas[lats_mask] = PRIMARY_BLUE
        if "glute" in focus_text:
            canvas[glutes_mask] = PRIMARY_BLUE
        else:
            canvas[glutes_mask] = SECONDARY_BLUE
        if "core" in focus_text:
            canvas[abs_mask] = SECONDARY_BLUE

    elif "full body" in tm:
        # Full body: e.g. Jumping Jacks, Burpees, Mountain Climbers
        if "jumping" in focus_text or "jack" in focus_text or "cardio" in focus_text:
            canvas[delts_front] = PRIMARY_BLUE
            canvas[delts_rear] = PRIMARY_BLUE
            canvas[quads_mask] = PRIMARY_BLUE
            canvas[glutes_mask] = SECONDARY_BLUE
            canvas[calves_front] = SECONDARY_BLUE
            canvas[calves_back] = SECONDARY_BLUE
        elif "burpee" in focus_text or "dada" in focus_text:
            canvas[chest_mask] = PRIMARY_BLUE
            canvas[quads_mask] = PRIMARY_BLUE
            canvas[delts_front] = PRIMARY_BLUE
            canvas[abs_mask] = SECONDARY_BLUE
            canvas[calves_back] = SECONDARY_BLUE
        else:
            canvas[quads_mask] = PRIMARY_BLUE
            canvas[abs_mask] = PRIMARY_BLUE
            canvas[delts_front] = SECONDARY_BLUE
            canvas[delts_rear] = SECONDARY_BLUE
            canvas[calves_front] = SECONDARY_BLUE

    img = Image.fromarray(canvas)

    # If width and height are provided, fit cleanly on a white canvas
    if width is not None and height is not None:
        orig_w, orig_h = img.size
        scale = min(width / orig_w, height / orig_h)
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))

        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        final_canvas = Image.new("RGB", (width, height), (255, 255, 255))
        paste_x = (width - new_w) // 2
        paste_y = (height - new_h) // 2
        final_canvas.paste(resized, (paste_x, paste_y))
        return final_canvas

    return img
