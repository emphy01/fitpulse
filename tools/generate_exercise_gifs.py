"""
FitPulse Exercise GIF Animation Generator
Generates lightweight, smooth, looping demonstration GIFs for all exercises in FitPulse.
"""

import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageEnhance

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "workout_data" / "images"
GIFS_DIR = IMAGES_DIR / "gifs"
GIFS_DIR.mkdir(parents=True, exist_ok=True)

def get_bg_color(im):
    """Samples corner pixels to find dominant background color."""
    corners = [
        im.getpixel((0, 0)),
        im.getpixel((im.width - 1, 0)),
        im.getpixel((0, im.height - 1)),
        im.getpixel((im.width - 1, im.height - 1)),
    ]
    # Default to white if not uniform
    r = int(np.median([c[0] for c in corners]))
    g = int(np.median([c[1] for c in corners]))
    b = int(np.median([c[2] for c in corners]))
    return (r, g, b)

def get_subject_bbox(im, bg_color):
    """Detects bounding box of the subject by thresholding against background color."""
    arr = np.array(im.convert("RGB"), dtype=int)
    bg = np.array(bg_color, dtype=int)
    diff = np.abs(arr - bg).sum(axis=2)
    mask = diff > 30 # Threshold for non-background pixels
    if not mask.any():
        return (0, 0, im.width, im.height)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    return (int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1]))

def center_crop_on_canvas(sub_im, target_w=500, target_h=400, bg_color=(255, 255, 255)):
    """Scales and centers a cropped pose onto a target canvas."""
    bbox = get_subject_bbox(sub_im, bg_color)
    sub_w = bbox[2] - bbox[0]
    sub_h = bbox[3] - bbox[1]
    
    if sub_w <= 10 or sub_h <= 10:
        cropped = sub_im
    else:
        # Add a little margin
        pad_x = int(sub_w * 0.05)
        pad_y = int(sub_h * 0.05)
        x0 = max(0, bbox[0] - pad_x)
        y0 = max(0, bbox[1] - pad_y)
        x1 = min(sub_im.width, bbox[2] + pad_x)
        y1 = min(sub_im.height, bbox[3] + pad_y)
        cropped = sub_im.crop((x0, y0, x1, y1))

    # Scale to fit comfortably inside target_w x target_h
    avail_w = int(target_w * 0.88)
    avail_h = int(target_h * 0.88)
    scale = min(avail_w / cropped.width, avail_h / cropped.height)
    new_w = max(1, int(cropped.width * scale))
    new_h = max(1, int(cropped.height * scale))
    scaled = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (target_w, target_h), bg_color)
    pos_x = (target_w - new_w) // 2
    pos_y = (target_h - new_h) // 2
    canvas.paste(scaled, (pos_x, pos_y))
    return canvas

def generate_2pose_gif(im, out_path, target_w=500, target_h=400):
    bg_color = get_bg_color(im)
    w, h = im.size
    p1_raw = im.crop((0, 0, w // 2, h))
    p2_raw = im.crop((w // 2, 0, w, h))
    
    p1 = center_crop_on_canvas(p1_raw, target_w, target_h, bg_color)
    p2 = center_crop_on_canvas(p2_raw, target_w, target_h, bg_color)
    
    frames = []
    durations = []
    
    # Hold Pose 1 (starting position)
    frames.append(p1)
    durations.append(500)
    
    # Transition Pose 1 -> Pose 2
    for alpha in [0.25, 0.50, 0.75]:
        frames.append(Image.blend(p1, p2, alpha))
        durations.append(90)
        
    # Hold Pose 2 (peak contraction)
    frames.append(p2)
    durations.append(500)
    
    # Transition Pose 2 -> Pose 1
    for alpha in [0.75, 0.50, 0.25]:
        frames.append(Image.blend(p1, p2, alpha))
        durations.append(90)
        
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )

def generate_3pose_gif(im, out_path, target_w=500, target_h=400):
    bg_color = get_bg_color(im)
    w, h = im.size
    p_w = w // 3
    poses = [
        center_crop_on_canvas(im.crop((i * p_w, 0, (i + 1) * p_w, h)), target_w, target_h, bg_color)
        for i in range(3)
    ]
    p1, p2, p3 = poses[0], poses[1], poses[2]
    
    frames = []
    durations = []
    
    # Pose 1
    frames.append(p1)
    durations.append(400)
    for a in [0.33, 0.67]:
        frames.append(Image.blend(p1, p2, a))
        durations.append(80)
        
    # Pose 2
    frames.append(p2)
    durations.append(400)
    for a in [0.5]:
        frames.append(Image.blend(p2, p1, a))
        durations.append(80)
        
    # Pose 1 (transit)
    frames.append(p1)
    durations.append(250)
    for a in [0.33, 0.67]:
        frames.append(Image.blend(p1, p3, a))
        durations.append(80)
        
    # Pose 3 (Jump up)
    frames.append(p3)
    durations.append(450)
    for a in [0.67, 0.33]:
        frames.append(Image.blend(p1, p3, a))
        durations.append(80)
        
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )

def generate_isometric_pulse_gif(im, out_path, target_w=500, target_h=400):
    """Generates breathing/tension pulse loop for static isometric holds (like Wall Sit)."""
    bg_color = get_bg_color(im)
    base = center_crop_on_canvas(im, target_w, target_h, bg_color)
    
    frames = []
    durations = []
    
    # Generate 6 breathing steps
    scales = [1.0, 1.015, 1.03, 1.015]
    for s in scales:
        if s == 1.0:
            frame = base
        else:
            w = int(target_w * s)
            h = int(target_h * s)
            zoomed = base.resize((w, h), Image.Resampling.LANCZOS)
            x0 = (w - target_w) // 2
            y0 = (h - target_h) // 2
            frame = zoomed.crop((x0, y0, x0 + target_w, y0 + target_h))
        frames.append(frame)
        durations.append(400)
        
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )

def process_all_exercises():
    print("🚀 Starting Exercise GIF generation...")
    count = 0
    for filename in sorted(os.listdir(IMAGES_DIR)):
        if not (filename.startswith("ex_") and filename.endswith(".png")):
            continue
            
        src_path = IMAGES_DIR / filename
        gif_name = filename.replace(".png", ".gif")
        out_path = GIFS_DIR / gif_name
        
        im = Image.open(src_path).convert("RGB")
        w, h = im.size
        ratio = w / h
        
        if "burpees" in filename:
            generate_3pose_gif(im, out_path)
        elif "wall_sit" in filename:
            generate_isometric_pulse_gif(im, out_path)
        else:
            # All other exercises have 2 distinct poses side-by-side
            generate_2pose_gif(im, out_path)
            
        file_size_kb = os.path.getsize(out_path) / 1024
        print(f"  ✓ {gif_name:24} -> {file_size_kb:.1f} KB")
        count += 1
        
    print(f"\n🎉 Successfully generated {count} exercise GIFs in '{GIFS_DIR}'!")

if __name__ == "__main__":
    process_all_exercises()

