"""
FitPulse - Modern Home Workout Application (HCI Edition)
Modeled faithfully after the Home Workout mobile app experience.

Key Features & Usability Highlights:
1. Navigation: Main nav consists strictly of [⏱️ Training | 📊 Report | ⚙️ Settings] (No Discovery tab).
2. Training Hub:
   - Flame streak counter & user profile status
   - Search bar across routines and exercises
   - Weekly Goal card with 7-day strip highlighting today
   - Featured 28-Day Challenge card
   - Body Focus filter pills (Semua, Abs, Lengan, Dada, Kaki, Punggung, Full Body)
   - Workout Routine Cards displaying 1:1 thumbnails, duration, exercise counts, and difficulty lightning bolts
3. Routine Overview Screen (Frame 40):
   - Detailed list of exercises with 1:1 thumbnails, names, and reps/duration
   - Clicking ANY exercise in the routine opens the Exercise Detail Modal
   - 'Edit Plan' (Frame 45) to adjust reps/durations on the fly
   - Prominent START button
4. Exercise Detail Modal (Frame 65, 70, 75):
   - Dedicated 1:1 Image Container with instant image loading
   - '📷 Unggah / Ganti Foto Gerakan (Area 1:1)' button to insert custom photos
   - Target Muscles badges + Anatomical Muscle Body Diagram (front & back highlighting trained regions)
   - Step-by-step instructions
   - Common Mistakes (numbered items with clear title & risk explanation)
   - Breathing Tips (inhale & exhale guidance)
5. Active Workout Session (Frame 50, 55, 60, 85):
   - Top 1:1 Image Area directly replacing the movement video
   - Interactive 'ℹ️ Detail' button opening the Exercise Detail Modal anytime during workout
   - Support for both Time-Based exercises (timer countdown) and Rep-Based exercises (reps counter + big '✓ Selesai Repetisi' button)
   - Rest Interval Screen (Frame 60) with next exercise 1:1 preview, +20s and Skip buttons
   - Accidental cancellation protection (explicit confirmation token)
   - Celebration & Adaptive Post-Workout Feedback
6. Report Hub (Frame 12):
   - Day Streak & Personal Best records
   - Weight Tracker with current, heaviest, lightest, and 'Log Weight' dialog
   - BMI Calculator with color-coded gauge bar and height editor
   - Lifetime workout statistics and history logs
7. Settings Hub (Frame 7):
   - Biometric profile, rest duration, sound/TTS cues, weekly schedule manager, and custom builder
"""

import sys
import os
import shutil
import threading
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from PIL import Image
import customtkinter as ctk
from tkinter import messagebox, filedialog

from homeworkout.service import WorkoutAppService
from homeworkout.models import (
    MuscleGroup, DifficultyLevel, StepType, SessionState, WorkoutRoutine, Exercise,
    DailySchedule, WeeklySchedule, DayOfWeek, WorkoutStep, UserProfile
)
from homeworkout.engine import WorkoutEngine
from homeworkout.anatomy import generate_muscle_anatomy_image


# Color palette & styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "workout_data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Muscle group icon and color mappings
MUSCLE_META = {
    "Semua": ("🌐", "#3B82F6"),
    "Full Body": ("⚡", "#38BDF8"),
    "Abs & Core": ("🔥", "#10B981"),
    "Abs": ("🔥", "#10B981"),
    "Arms": ("🦾", "#60A5FA"),
    "Lengan": ("🦾", "#60A5FA"),
    "Chest": ("💪", "#F97316"),
    "Dada": ("💪", "#F97316"),
    "Legs": ("🦵", "#8B5CF6"),
    "Kaki": ("🦵", "#8B5CF6"),
    "Back": ("🧘", "#EC4899"),
    "Punggung": ("🧘", "#EC4899")
}


class AudioFeedback:
    """Manages audio cues for Accessibility and UX feedback."""
    @staticmethod
    def play_beep(freq: int = 1000, duration_ms: int = 200):
        if not HAS_WINSOUND:
            return
        def _run():
            try:
                winsound.Beep(freq, duration_ms)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    @staticmethod
    def play_countdown():
        AudioFeedback.play_beep(800, 140)

    @staticmethod
    def play_go():
        AudioFeedback.play_beep(1200, 300)

    @staticmethod
    def play_celebration():
        if not HAS_WINSOUND:
            return
        def _run():
            try:
                for f in [523, 659, 784, 1046]:
                    winsound.Beep(f, 140)
                    time.sleep(0.04)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()


def load_ctk_image(image_path: Optional[str], size: Tuple[int, int] = (260, 260)) -> Optional[ctk.CTkImage]:
    """Helper to safely load a PIL image and return a CTkImage for 1:1 display."""
    if not image_path:
        return None
    p = Path(image_path)
    if not p.is_absolute():
        p = BASE_DIR / image_path
    if not p.exists():
        return None
    try:
        with Image.open(p) as img:
            img = img.copy()
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception as e:
        print(f"Error loading image from {p}: {e}")
        return None


# =============================================================================
# EXERCISE DETAIL MODAL (Frame 65, 70, 75)
# Pops up when any exercise is clicked:
# - Strict 1:1 image display area
# - Button to insert/upload image
# - Target muscles & anatomical muscle diagram
# - Step-by-step instructions
# - Common mistakes (numbered with explanations)
# - Breathing tips
# =============================================================================
class ExerciseDetailModal(ctk.CTkToplevel):
    def __init__(self, parent, exercise: Exercise, service: WorkoutAppService, on_image_updated=None):
        super().__init__(parent)
        self.exercise = exercise
        self.service = service
        self.on_image_updated = on_image_updated

        self.title(f"Detail Gerakan: {exercise.name}")
        self.geometry("400x780")
        self.minsize(360, 580)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = max(20, px + (pw - 400) // 2)
            y = max(20, py + (ph - 780) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color=("gray95", "#0F172A"))
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Header Title
        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(12, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=self.exercise.name.upper(),
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w"
        )
        title_lbl.pack(side="left")

        diff_badge = ctk.CTkLabel(
            header_frame,
            text=f"Level: {self.exercise.difficulty.value}",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3B82F6",
            text_color="white",
            corner_radius=12,
            padx=10,
            pady=3
        )
        diff_badge.pack(side="right")

        # =====================================================================
        # 1:1 IMAGE CONTAINER & INSERT IMAGE BUTTON
        # =====================================================================
        img_container = ctk.CTkFrame(scroll, fg_color=("gray85", "#1E293B"), corner_radius=16)
        img_container.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            img_container,
            text="📷 AREA FOTO GERAKAN (ASPEK RASIO 1:1)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94A3B8"
        ).pack(pady=(12, 6))

        # 1:1 Display Box (260x260 px)
        self.photo_box = ctk.CTkFrame(img_container, width=260, height=260, fg_color="#0F172A", corner_radius=12)
        self.photo_box.pack(pady=4)
        self.photo_box.pack_propagate(False)

        self.photo_lbl = ctk.CTkLabel(self.photo_box, text="")
        self.photo_lbl.pack(expand=True, fill="both", padx=6, pady=6)
        self._refresh_photo_display()

        # Insert / Replace Image Button
        btn_upload = ctk.CTkButton(
            img_container,
            text="📷 Unggah / Ganti Foto Gerakan (Area 1:1)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            command=self._handle_pick_image
        )
        btn_upload.pack(pady=(10, 14), padx=20, fill="x")

        # =====================================================================
        # TARGET MUSCLE & ANATOMICAL BODY DIAGRAM (Frame 70, 75)
        # =====================================================================
        muscle_card = ctk.CTkFrame(scroll, fg_color=("gray90", "#1E293B"), corner_radius=14)
        muscle_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            muscle_card,
            text="🎯 BAGIAN OTOT YANG DILATIH (TARGET MUSCLES)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38BDF8"
        ).pack(padx=16, pady=(12, 6), anchor="w")

        # Muscle badges
        tags_row = ctk.CTkFrame(muscle_card, fg_color="transparent")
        tags_row.pack(fill="x", padx=16, pady=(0, 10))

        main_badge = ctk.CTkLabel(
            tags_row,
            text=f"🔵 {self.exercise.target_muscle.value}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            text_color="white",
            corner_radius=10,
            padx=10,
            pady=3
        )
        main_badge.pack(side="left", padx=(0, 6))

        for fa in self.exercise.focus_areas:
            chip = ctk.CTkLabel(
                tags_row,
                text=fa,
                font=ctk.CTkFont(size=11),
                fg_color=("#E2E8F0", "#334155"),
                text_color=("black", "#F1F5F9"),
                corner_radius=10,
                padx=8,
                pady=3
            )
            chip.pack(side="left", padx=3)

        # Anatomical Diagram
        anatomy_img = generate_muscle_anatomy_image(
            target_muscle=self.exercise.target_muscle.value,
            focus_areas=self.exercise.focus_areas,
            width=300,
            height=180
        )
        self.anatomy_ctk = ctk.CTkImage(light_image=anatomy_img, dark_image=anatomy_img, size=(300, 180))
        anatomy_lbl = ctk.CTkLabel(muscle_card, image=self.anatomy_ctk, text="")
        anatomy_lbl.pack(pady=(4, 12))

        # =====================================================================
        # COMMON MISTAKES (Frame 70)
        # =====================================================================
        mistakes_card = ctk.CTkFrame(scroll, fg_color=("gray90", "#1E293B"), corner_radius=14)
        mistakes_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            mistakes_card,
            text="⚠️ KESALAHAN YANG BIASANYA DILAKUKAN (COMMON MISTAKES)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F87171"
        ).pack(padx=16, pady=(12, 8), anchor="w")

        mistakes = self.exercise.common_mistakes or [
            {"title": "Postur Tubuh Kurang Tegak", "desc": "Hindari membungkuk agar tidak membebani tulang punggung."},
            {"title": "Menahan Napas", "desc": "Pertahankan pola pernapasan stabil sepanjang repetisi."}
        ]

        for idx, m in enumerate(mistakes, 1):
            item_box = ctk.CTkFrame(mistakes_card, fg_color=("white", "#0F172A"), corner_radius=10)
            item_box.pack(fill="x", padx=16, pady=4)

            top_row = ctk.CTkFrame(item_box, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                top_row,
                text=str(idx),
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#EF4444",
                text_color="white",
                corner_radius=10,
                width=22,
                height=22
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(
                top_row,
                text=m.get("title", ""),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#B91C1C", "#FCA5A5")
            ).pack(side="left")

            ctk.CTkLabel(
                item_box,
                text=m.get("desc", ""),
                font=ctk.CTkFont(size=12),
                text_color=("gray20", "#CBD5E1"),
                wraplength=320,
                justify="left"
            ).pack(fill="x", padx=10, pady=(2, 8), anchor="w")

        ctk.CTkLabel(mistakes_card, text="").pack(pady=2)

        # =====================================================================
        # INSTRUCTIONS / CARA MELAKUKAN
        # =====================================================================
        inst_card = ctk.CTkFrame(scroll, fg_color=("gray90", "#1E293B"), corner_radius=14)
        inst_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            inst_card,
            text="📋 PANDUAN LANGKAH GERAKAN (INSTRUCTIONS)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#10B981"
        ).pack(padx=16, pady=(12, 6), anchor="w")

        for s_idx, step in enumerate(self.exercise.instructions, 1):
            s_row = ctk.CTkFrame(inst_card, fg_color="transparent")
            s_row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                s_row,
                text=f"{s_idx}.",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#10B981",
                width=20
            ).pack(side="left", anchor="n")
            ctk.CTkLabel(
                s_row,
                text=step,
                font=ctk.CTkFont(size=12),
                wraplength=320,
                justify="left"
            ).pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkLabel(inst_card, text="").pack(pady=4)

        # =====================================================================
        # BREATHING TIPS (Frame 70)
        # =====================================================================
        if self.exercise.breathing_tips:
            b_card = ctk.CTkFrame(scroll, fg_color=("gray90", "#1E293B"), corner_radius=14)
            b_card.pack(fill="x", padx=16, pady=(0, 14))

            ctk.CTkLabel(
                b_card,
                text="🫁 PANDUAN PERNAPASAN (BREATHING TIPS)",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#F59E0B"
            ).pack(padx=16, pady=(12, 6), anchor="w")

            for b in self.exercise.breathing_tips:
                b_row = ctk.CTkFrame(b_card, fg_color="transparent")
                b_row.pack(fill="x", padx=16, pady=2)
                ctk.CTkLabel(b_row, text="•", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F59E0B").pack(side="left", padx=(0, 6), anchor="n")
                ctk.CTkLabel(b_row, text=b, font=ctk.CTkFont(size=12), wraplength=320, justify="left").pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(b_card, text="").pack(pady=4)

        # Bottom Close Button
        btn_close = ctk.CTkButton(
            scroll,
            text="TUTUP (CLOSE)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=44,
            corner_radius=22,
            command=self.destroy
        )
        btn_close.pack(fill="x", padx=16, pady=(8, 20))

    def _refresh_photo_display(self):
        img_ctk = load_ctk_image(self.exercise.image_path, size=(240, 240))
        if img_ctk:
            self.photo_lbl.configure(image=img_ctk, text="")
            self.photo_lbl.image = img_ctk
        else:
            self.photo_lbl.configure(
                image="",
                text="Area Foto 1:1\n(Belum ada foto dimasukkan)\n\nKlik tombol di bawah\nuntuk memilih gambar.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )

    def _handle_pick_image(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Pilih Foto Gerakan (Area 1:1)",
            filetypes=[
                ("File Gambar", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("Semua File", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            dest_file = IMAGES_DIR / f"{self.exercise.id}.png"
            with Image.open(file_path) as src:
                w, h = src.size
                min_dim = min(w, h)
                left = (w - min_dim) // 2
                top = (h - min_dim) // 2
                cropped = src.crop((left, top, left + min_dim, top + min_dim))
                resized = cropped.resize((400, 400), Image.Resampling.LANCZOS)
                resized.convert("RGB").save(dest_file, "PNG")

            rel_path = f"workout_data/images/{self.exercise.id}.png"
            self.service.update_exercise_image(self.exercise.id, rel_path)
            self.exercise.image_path = rel_path
            self._refresh_photo_display()

            if self.on_image_updated:
                self.on_image_updated(self.exercise)

            messagebox.showinfo(
                "Berhasil",
                f"Foto gerakan '{self.exercise.name}' berhasil diperbarui ke area 1:1!",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Gagal", f"Gagal memuat foto: {e}", parent=self)


# =============================================================================
# ROUTINE PLAN EDITOR MODAL (Frame 45)
# Allows users to adjust durations and reps: [-] and [+]
# =============================================================================
class RoutinePlanEditorModal(ctk.CTkToplevel):
    def __init__(self, parent, routine: WorkoutRoutine, service: WorkoutAppService, on_saved=None):
        super().__init__(parent)
        self.routine = routine
        self.service = service
        self.on_saved = on_saved

        self.title(f"Sesuaikan Rencana: {routine.title}")
        self.geometry("400x700")
        self.minsize(360, 520)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color=("gray95", "#0F172A"))
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            header,
            text="EDIT RENCANA LATIHAN",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        self.step_vars: List[Tuple[WorkoutStep, ctk.IntVar]] = []

        for idx, step in enumerate(self.routine.steps):
            if step.step_type != StepType.EXERCISE or not step.exercise:
                continue

            card = ctk.CTkFrame(scroll, fg_color=("gray90", "#1E293B"), corner_radius=10)
            card.pack(fill="x", padx=16, pady=6)

            left_box = ctk.CTkFrame(card, fg_color="transparent")
            left_box.pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(
                left_box,
                text=step.exercise.name,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w")

            is_rep = bool(step.target_reps or step.exercise.is_reps_based)
            unit_text = "Repetisi" if is_rep else "Detik"
            val = step.target_reps if is_rep else step.duration_seconds
            var = ctk.IntVar(value=val or 12)
            self.step_vars.append((step, var))

            right_box = ctk.CTkFrame(card, fg_color="transparent")
            right_box.pack(side="right", padx=12, pady=10)

            # [-] button
            def _sub(v=var, r=is_rep):
                delta = 2 if r else 5
                v.set(max(1, v.get() - delta))

            def _add(v=var, r=is_rep):
                delta = 2 if r else 5
                v.set(v.get() + delta)

            ctk.CTkButton(
                right_box, text="-", width=32, height=32, font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=("#CBD5E1", "#334155"), text_color=("black", "white"), command=_sub
            ).pack(side="left", padx=4)

            val_lbl = ctk.CTkLabel(
                right_box,
                textvariable=var,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=50
            )
            val_lbl.pack(side="left", padx=2)

            ctk.CTkButton(
                right_box, text="+", width=32, height=32, font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=("#CBD5E1", "#334155"), text_color=("black", "white"), command=_add
            ).pack(side="left", padx=4)

            ctk.CTkLabel(
                right_box, text=unit_text, font=ctk.CTkFont(size=11), text_color="gray", width=55
            ).pack(side="left", padx=(4, 0))

        # Bottom buttons (Cancel & Save)
        btn_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=20)

        ctk.CTkButton(
            btn_bar,
            text="Batal",
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            width=120,
            height=40,
            command=self.destroy
        ).pack(side="left", padx=(0, 8), expand=True, fill="x")

        ctk.CTkButton(
            btn_bar,
            text="Simpan Perubahan",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=160,
            height=40,
            command=self._handle_save
        ).pack(side="right", padx=(8, 0), expand=True, fill="x")

    def _handle_save(self):
        for step, var in self.step_vars:
            val = var.get()
            if step.target_reps or (step.exercise and step.exercise.is_reps_based):
                step.target_reps = val
            else:
                step.duration_seconds = val

        self.service.save_or_update_routine(self.routine)
        messagebox.showinfo("Berhasil", "Rencana latihan berhasil diperbarui!", parent=self)
        if self.on_saved:
            self.on_saved()
        self.destroy()


# =============================================================================
# =============================================================================
# MODAL: ONBOARDING USER GUIDE OVERLAY (PANDUAN PENGGUNA)
# =============================================================================
class UserGuideModal(ctk.CTkToplevel):
    def __init__(self, parent, service: WorkoutAppService, on_close=None):
        super().__init__(parent)
        self.service = service
        self.on_close = on_close
        self.current_step = 1

        self.title("Panduan Pengguna FitPulse")
        self.geometry("780x640")
        self.minsize(520, 480)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = max(20, px + (pw - 780) // 2)
            y = max(20, py + (ph - 640) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top Bar
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        self.lbl_title = ctk.CTkLabel(
            top_frame,
            text="📖 PANDUAN PENGGUNA FITPULSE",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38BDF8"
        )
        self.lbl_title.pack(side="left")

        self.lbl_step = ctk.CTkLabel(
            top_frame,
            text="Langkah 1/2",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E293B",
            corner_radius=8,
            padx=10,
            pady=3
        )
        self.lbl_step.pack(side="left", padx=10)

        btn_close = ctk.CTkButton(
            top_frame,
            text="✕ Lewati",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            width=80,
            height=30,
            command=self.destroy
        )
        btn_close.pack(side="right")

        # Center Clickable Area (Advancing on click anywhere)
        self.center_frame = ctk.CTkFrame(self, fg_color="#020617", corner_radius=14)
        self.center_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        self.img_label = ctk.CTkLabel(self.center_frame, text="")
        self.img_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Instruction overlay text ("tap anywhere to continue")
        self.lbl_tap_instruction = ctk.CTkLabel(
            self.center_frame,
            text="👆 Ketuk di mana saja untuk lanjut • Tap anywhere to continue",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38BDF8",
            fg_color=("#0F172A", "#0F172A"),
            corner_radius=12,
            padx=14,
            pady=6
        )
        self.lbl_tap_instruction.grid(row=1, column=0, pady=(0, 10))

        # Bind click anywhere on image and center_frame to advance
        self.center_frame.bind("<Button-1>", lambda e: self.advance_step())
        self.img_label.bind("<Button-1>", lambda e: self.advance_step())
        self.lbl_tap_instruction.bind("<Button-1>", lambda e: self.advance_step())

        # Bottom Bar: Checkbox & Next Button
        bottom_frame = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=12)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 12))

        profile = self.service.get_profile()
        self.var_dont_show = ctk.BooleanVar(value=not profile.show_onboarding_guide)

        self.chk_dont_show = ctk.CTkCheckBox(
            bottom_frame,
            text="Jangan tampilkan panduan ini lagi saat dibuka",
            variable=self.var_dont_show,
            font=ctk.CTkFont(size=12),
            command=self._on_toggle_dont_show
        )
        self.chk_dont_show.pack(side="left", padx=16, pady=10)

        self.btn_next = ctk.CTkButton(
            bottom_frame,
            text="Lanjut ➔",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            width=110,
            height=34,
            command=self.advance_step
        )
        self.btn_next.pack(side="right", padx=16, pady=10)

        self._render_step_image()

    def _render_step_image(self):
        img_filename = "panduan1.png" if self.current_step == 1 else "panduan2.png"
        img_path = Path("workout_data/images") / img_filename
        if not img_path.exists():
            img_path = Path(img_filename)

        if img_path.exists():
            try:
                pil_img = Image.open(img_path)
                # Scale nicely to fit inside ~740x440
                max_w, max_h = 740, 440
                pil_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.img_label.configure(image=ctk_img)
                self.img_label.image = ctk_img
            except Exception:
                self.img_label.configure(text=f"Panduan {self.current_step}")
        else:
            self.img_label.configure(text=f"Panduan {self.current_step}")

        self.lbl_step.configure(text=f"Langkah {self.current_step}/2")
        if self.current_step == 1:
            self.btn_next.configure(text="Lanjut ➔")
        else:
            self.btn_next.configure(text="Mulai Aplikasi ✓")

    def advance_step(self):
        if self.current_step == 1:
            self.current_step = 2
            self._render_step_image()
        else:
            self.destroy()

    def _on_toggle_dont_show(self):
        dont_show = self.var_dont_show.get()
        profile = self.service.get_profile()
        profile.show_onboarding_guide = not dont_show
        self.service.save_profile(profile)


# =============================================================================
# MAIN APPLICATION WINDOW
# =============================================================================
class FitPulseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.service = WorkoutAppService()
        self.active_engine: Optional[WorkoutEngine] = None
        self.timer_running = False

        # State filters
        self.current_focus_filter = "Semua"
        self.search_keyword = ""

        # Viewport Mode (Default: Smartphone 420x860, with Desktop toggle)
        self.is_mobile_view = True
        self.title("FitPulse - Home Workout (Mobile Edition)")
        self.geometry("420x860")
        self.minsize(380, 680)

        # Apply user profile preference
        profile = self.service.get_profile()
        if profile.high_contrast_mode:
            ctk.set_appearance_mode("Dark")

        # Layout: Grid with Top Header, Main Content Area, and Main Nav Bar
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_top_header()
        self._build_main_container()
        self._build_main_nav_bar()

        # Start on Training View
        self.show_training_view()

        # Check and show onboarding guide if enabled
        profile = self.service.get_profile()
        if getattr(profile, 'show_onboarding_guide', True):
            self.after(450, self.show_user_guide_modal)

    def toggle_view_mode(self):
        """Allows toggling between Smartphone Mobile (420x860) and Desktop (1080x820) mode."""
        self.is_mobile_view = not self.is_mobile_view
        if self.is_mobile_view:
            self.geometry("420x860")
            self.minsize(380, 680)
            self.title("FitPulse - Home Workout (Mobile Edition)")
            if hasattr(self, 'btn_mode_toggle'):
                self.btn_mode_toggle.configure(text="💻 Desktop")
        else:
            self.geometry("1080x820")
            self.minsize(800, 680)
            self.title("FitPulse - Home Workout (Desktop Edition)")
            if hasattr(self, 'btn_mode_toggle'):
                self.btn_mode_toggle.configure(text="📱 Mobile")

    # =========================================================================
    # TOP HEADER & MAIN NAVIGATION (Strictly: Training, Report, Settings - NO Discovery)
    # =========================================================================
    def _build_top_header(self):
        self.top_header = ctk.CTkFrame(self, height=56, corner_radius=0, fg_color=("#F1F5F9", "#0F172A"))
        self.top_header.grid(row=0, column=0, sticky="ew")
        self.top_header.grid_columnconfigure(1, weight=1)

        # Brand / Logo
        brand_lbl = ctk.CTkLabel(
            self.top_header,
            text="⚡ FITPULSE",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=("#0F172A", "#38BDF8")
        )
        brand_lbl.grid(row=0, column=0, padx=(14, 6), pady=12, sticky="w")

        # Center Status info / streak
        stats = self.service.get_user_dashboard_stats()
        streak_val = stats.get('current_streak_days', stats.get('streak_days', 0))
        self.streak_badge = ctk.CTkLabel(
            self.top_header,
            text=f"🔥 {streak_val}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#FEE2E2", "#450A0A"),
            text_color="#EF4444",
            corner_radius=12,
            padx=8,
            pady=3
        )
        self.streak_badge.grid(row=0, column=1, padx=4, pady=12, sticky="e")

        # Mobile / Desktop Mode Toggle Button
        self.btn_mode_toggle = ctk.CTkButton(
            self.top_header,
            text="💻 Desktop" if self.is_mobile_view else "📱 Mobile",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color=("black", "white"),
            width=78,
            height=28,
            corner_radius=10,
            command=self.toggle_view_mode
        )
        self.btn_mode_toggle.grid(row=0, column=2, padx=4, pady=12, sticky="e")

        # User profile button
        self.profile_btn = ctk.CTkButton(
            self.top_header,
            text="👤",
            font=ctk.CTkFont(size=13),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color=("black", "white"),
            width=32,
            height=28,
            corner_radius=10,
            command=self.show_settings_view
        )
        self.profile_btn.grid(row=0, column=3, padx=(4, 14), pady=12, sticky="e")

    def _build_main_container(self):
        self.main_container = ctk.CTkFrame(self, fg_color=("gray95", "#020617"), corner_radius=0)
        self.main_container.grid(row=1, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

    def _build_main_nav_bar(self):
        """
        Bottom Main Navigation Bar modeled after Home Workout app.
        Contains STRICTLY:
        - ⏱️ Training (Latihan)
        - 📊 Report (Laporan)
        - ⚙️ Settings (Pengaturan)
        (Explicit requirement: No Discovery feature!)
        """
        self.nav_bar = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=("#F8FAFC", "#0F172A"))
        self.nav_bar.grid(row=2, column=0, sticky="ew")
        self.nav_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_nav_training = ctk.CTkButton(
            self.nav_bar,
            text="⏱️ Latihan",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6",
            text_color="white",
            height=42,
            corner_radius=10,
            command=self.show_training_view
        )
        self.btn_nav_training.grid(row=0, column=0, padx=6, pady=8, sticky="ew")

        self.btn_nav_report = ctk.CTkButton(
            self.nav_bar,
            text="📊 Laporan",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent",
            text_color=("gray30", "gray80"),
            hover_color=("#E2E8F0", "#1E293B"),
            height=42,
            corner_radius=10,
            command=self.show_report_view
        )
        self.btn_nav_report.grid(row=0, column=1, padx=6, pady=8, sticky="ew")

        self.btn_nav_settings = ctk.CTkButton(
            self.nav_bar,
            text="⚙️ Pengaturan",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent",
            text_color=("gray30", "gray80"),
            hover_color=("#E2E8F0", "#1E293B"),
            height=42,
            corner_radius=10,
            command=self.show_settings_view
        )
        self.btn_nav_settings.grid(row=0, column=2, padx=6, pady=8, sticky="ew")

    def _set_active_nav(self, active_tab: str):
        tabs = {
            "training": self.btn_nav_training,
            "report": self.btn_nav_report,
            "settings": self.btn_nav_settings
        }
        for name, btn in tabs.items():
            if name == active_tab:
                btn.configure(fg_color="#3B82F6", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray30", "gray80"))

    def _clear_main(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # =========================================================================
    # VIEW 1: TRAINING HUB (HOME SCREEN)
    # - Search bar
    # - Weekly Goal card (7-day strip)
    # - Challenge Banner
    # - Body Focus horizontal filter pills
    # - Workout cards with 1:1 image thumbnails
    # =========================================================================
    def show_user_guide_modal(self):
        """Displays the interactive visual user guide popup overlay."""
        UserGuideModal(self, self.service)

    def show_training_view(self):
        self._set_active_nav("training")
        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        # 1. Search Bar
        search_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        search_card.pack(fill="x", pady=(0, 16))

        self.search_entry = ctk.CTkEntry(
            search_card,
            placeholder_text="🔍 Cari latihan, nama gerakan, atau target otot...",
            font=ctk.CTkFont(size=13),
            height=42,
            border_width=0,
            fg_color="transparent"
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=16, pady=6)
        if self.search_keyword:
            self.search_entry.insert(0, self.search_keyword)

        btn_search = ctk.CTkButton(
            search_card,
            text="Cari",
            width=80,
            height=34,
            command=self._handle_search
        )
        btn_search.pack(side="right", padx=10, pady=6)

        # 2. Weekly Goal Card (Frame 00)
        self._build_weekly_goal_card(scroll)

        # 3. Challenge Banner (Frame 00, 35)
        self._build_challenge_banner(scroll)

        # 4. Body Focus Filters (Pills)
        focus_title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        focus_title_row.pack(fill="x", pady=(10, 6))

        ctk.CTkLabel(
            focus_title_row,
            text="Fokus Otot (Body Focus)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        # Pills Row (Horizontal Scrollable like Frame 00 in the mobile app!)
        pills_scroll = ctk.CTkScrollableFrame(scroll, orientation="horizontal", height=46, fg_color="transparent")
        pills_scroll.pack(fill="x", pady=(0, 10))

        filters = [
            ("Semua", "🌐 Semua"),
            ("Abs & Core", "🔥 Abs"),
            ("Arms", "🦾 Lengan"),
            ("Chest", "💪 Dada"),
            ("Legs", "🦵 Kaki"),
            ("Back", "🧘 Punggung"),
            ("Full Body", "⚡ Full Body")
        ]

        for val, label in filters:
            is_active = (self.current_focus_filter == val)
            fg = "#3B82F6" if is_active else ("gray85", "#1E293B")
            txt_color = "white" if is_active else ("gray20", "gray80")

            b = ctk.CTkButton(
                pills_scroll,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                fg_color=fg,
                text_color=txt_color,
                height=32,
                corner_radius=16,
                command=lambda f=val: self._handle_focus_filter(f)
            )
            b.pack(side="left", padx=3)

        # Quick Shortcuts row (clean 2 buttons side by side)
        shortcuts_row = ctk.CTkFrame(scroll, fg_color="transparent")
        shortcuts_row.pack(fill="x", pady=(0, 10))
        shortcuts_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            shortcuts_row,
            text="📅 Jadwal Mingguan",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#CBD5E1", "#1E293B"),
            text_color=("black", "white"),
            height=34,
            corner_radius=10,
            command=self.show_schedule_view
        ).grid(row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(
            shortcuts_row,
            text="🛠️ Buat Template",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#059669", "#065F46"),
            hover_color="#047857",
            height=34,
            corner_radius=10,
            command=self.show_custom_builder_view
        ).grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # 5. Routine Cards Grid / List
        self._build_routines_list(scroll)

    def _handle_search(self):
        self.search_keyword = self.search_entry.get().strip()
        self.show_training_view()

    def _handle_focus_filter(self, focus_name: str):
        self.current_focus_filter = focus_name
        self.show_training_view()

    def _build_weekly_goal_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"), corner_radius=16)
        card.pack(fill="x", pady=(0, 14))

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(14, 8))

        ctk.CTkLabel(
            top_row,
            text="Target Mingguan (Weekly Goal)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        consistency = self.service.storage.compute_weekly_consistency()
        completed_week = consistency.get('completed_this_week', 0)
        total_target = consistency.get('total_scheduled_week', 0)
        ctk.CTkLabel(
            top_row,
            text=f"{completed_week}/{total_target} Sesi",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B82F6"
        ).pack(side="right")

        # 7-day strip
        days_row = ctk.CTkFrame(card, fg_color="transparent")
        days_row.pack(fill="x", padx=16, pady=(0, 14))
        days_row.grid_columnconfigure(tuple(range(7)), weight=1)

        days_labels = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
        today_idx = datetime.now().weekday()  # 0 is Monday

        for idx, d_name in enumerate(days_labels):
            is_today = (idx == today_idx)
            f = ctk.CTkFrame(
                days_row,
                corner_radius=20,
                fg_color="#3B82F6" if is_today else ("gray90", "#0F172A")
            )
            f.grid(row=0, column=idx, padx=4, sticky="ew")

            ctk.CTkLabel(
                f,
                text=d_name,
                font=ctk.CTkFont(size=11),
                text_color="white" if is_today else "gray"
            ).pack(pady=(6, 1))

            ctk.CTkLabel(
                f,
                text=str(24 + idx),  # realistic date numbers
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="white" if is_today else ("gray10", "gray90")
            ).pack(pady=(0, 6))

    def _build_challenge_banner(self, parent):
        banner = ctk.CTkFrame(parent, fg_color="#1E3A8A", corner_radius=16)
        banner.pack(fill="x", pady=(0, 14))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            inner,
            text="🔥 TANTANGAN 28 HARI (MASSIVE BODY CHALLENGE)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93C5FD"
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text="HARI 7: INTENSIF PEMBAKARAN LEMAK",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(anchor="w", pady=(2, 6))

        progress = ctk.CTkProgressBar(inner, height=8, progress_color="#38BDF8")
        progress.set(7 / 28.0)
        progress.pack(fill="x", pady=(2, 10))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text="MULAI HARI 7 ▶",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#38BDF8",
            hover_color="#0284C7",
            text_color="#0F172A",
            height=36,
            corner_radius=18,
            command=self.handle_quick_start
        ).pack(side="left")

        ctk.CTkLabel(
            btn_row,
            text="Progres: 7 dari 28 hari selesai",
            font=ctk.CTkFont(size=12),
            text_color="#BFDBFE"
        ).pack(side="right")

    def _build_routines_list(self, parent):
        routines = self.service.list_routines()

        # Apply Focus Filter
        if self.current_focus_filter != "Semua":
            routines = [r for r in routines if r.target_muscle.value == self.current_focus_filter]

        # Apply Search Filter
        if self.search_keyword:
            kw = self.search_keyword.lower()
            routines = [r for r in routines if kw in r.title.lower() or kw in r.description.lower() or kw in r.target_muscle.value.lower()]

        if not routines:
            empty_frame = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"), corner_radius=14)
            empty_frame.pack(fill="x", pady=20)
            ctk.CTkLabel(
                empty_frame,
                text="Tidak ada latihan yang cocok dengan kriteria filter.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=30)
            return

        for routine in routines:
            self._create_routine_card(parent, routine)

    def _create_routine_card(self, parent, routine: WorkoutRoutine):
        card = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"), corner_radius=14)
        card.pack(fill="x", pady=6)

        # Make entire card clickable
        card.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        # 1:1 Thumbnail preview (first exercise image)
        cover_path = getattr(routine, 'cover_image', None) or f"workout_data/images/covers/cover_{routine.id}.png"
        first_ex_img = cover_path if (BASE_DIR / cover_path).exists() else None
        for step in routine.steps:
            if step.exercise and step.exercise.image_path:
                first_ex_img = step.exercise.image_path
                break

        thumb_ctk = load_ctk_image(first_ex_img, size=(68, 68))
        thumb_box = ctk.CTkFrame(inner, width=68, height=68, fg_color="#0F172A", corner_radius=10)
        thumb_box.pack(side="left", padx=(0, 14))
        thumb_box.pack_propagate(False)
        thumb_box.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        thumb_lbl = ctk.CTkLabel(thumb_box, image=thumb_ctk, text="" if thumb_ctk else "🏋️")
        thumb_lbl.pack(expand=True, fill="both")
        thumb_lbl.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        # Center Info
        center_box = ctk.CTkFrame(inner, fg_color="transparent")
        center_box.pack(side="left", fill="x", expand=True)
        center_box.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        title_lbl = ctk.CTkLabel(
            center_box,
            text=routine.title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_lbl.pack(fill="x")
        title_lbl.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        dur_mins = max(1, routine.total_duration_seconds // 60)
        details_text = f"{dur_mins} Menit • {routine.exercise_count} Gerakan • {routine.target_muscle.value}"
        sub_lbl = ctk.CTkLabel(
            center_box,
            text=details_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        sub_lbl.pack(fill="x", pady=(2, 0))
        sub_lbl.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        # Lightning intensity icons
        diff_bolts = {"Beginner": "⚡", "Intermediate": "⚡⚡", "Advanced": "⚡⚡⚡"}
        bolts = diff_bolts.get(routine.difficulty.value, "⚡")
        bolt_lbl = ctk.CTkLabel(
            center_box,
            text=f"Intensitas: {bolts} ({routine.difficulty.value})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38BDF8",
            anchor="w"
        )
        bolt_lbl.pack(fill="x", pady=(2, 0))
        bolt_lbl.bind("<Button-1>", lambda e, r=routine: self.show_routine_overview_view(r.id))

        # Chevron arrow — subtle, clean, no redundant button
        ctk.CTkLabel(
            inner,
            text="›",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#94A3B8", "#475569")
        ).pack(side="right", padx=(10, 0))

    # =========================================================================
    # VIEW 2: ROUTINE OVERVIEW SCREEN (Frame 40)
    # - Top bar with Back button '<'
    # - Summary info
    # - Exercise list where clicking ANY exercise row opens ExerciseDetailModal!
    # - 'Edit Plan' button (Frame 45)
    # - Big 'START' button
    # =========================================================================
    def show_routine_overview_view(self, routine_id: str):
        routine = self.service.get_routine_by_id(routine_id)
        if not routine:
            messagebox.showerror("Error", "Program latihan tidak ditemukan.")
            return

        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        # Top Navigation Bar
        top_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(
            top_bar,
            text="◀ Kembali",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("gray85", "#1E293B"),
            text_color=("black", "white"),
            hover_color=("gray75", "#334155"),
            width=90,
            height=34,
            command=self.show_training_view
        ).pack(side="left")

        ctk.CTkLabel(
            top_bar,
            text=routine.title.upper(),
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=16)

        # Edit Plan Button (Frame 45)
        ctk.CTkButton(
            top_bar,
            text="✏️ Sesuaikan Rencana",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#CBD5E1", "#334155"),
            text_color=("black", "white"),
            height=34,
            command=lambda: RoutinePlanEditorModal(self, routine, self.service, on_saved=lambda: self.show_routine_overview_view(routine.id))
        ).pack(side="right")

        # Routine Cover Banner
        cov_p = getattr(routine, 'cover_image', None) or f"workout_data/images/covers/cover_{routine.id}.png"
        cov_ctk = load_ctk_image(cov_p, size=(520, 190))
        if cov_ctk:
            cov_lbl = ctk.CTkLabel(scroll, image=cov_ctk, text="")
            cov_lbl.pack(fill="x", pady=(0, 14))

        # Summary strip
        dur_mins = max(1, routine.total_duration_seconds // 60)
        summary_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        summary_card.pack(fill="x", pady=(0, 16))

        s_inner = ctk.CTkFrame(summary_card, fg_color="transparent")
        s_inner.pack(fill="x", padx=20, pady=12)
        s_inner.grid_columnconfigure((0, 1, 2, 3), weight=1)

        items = [
            ("⏱️ Durasi", f"{dur_mins} Menit"),
            ("🎯 Gerakan", f"{routine.exercise_count} Gerakan"),
            ("⚡ Level", routine.difficulty.value),
            ("💪 Otot Target", routine.target_muscle.value)
        ]
        for idx, (label, val) in enumerate(items):
            f = ctk.CTkFrame(s_inner, fg_color="transparent")
            f.grid(row=0, column=idx)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color="gray").pack()
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=14, weight="bold")).pack()

        # Instruction note: Clicking exercise shows form & common mistakes
        info_pill = ctk.CTkLabel(
            scroll,
            text="💡 TIPS: Klik pada nama gerakan manapun untuk melihat detail otot & kesalahan umum (Area 1:1)",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#38BDF8"
        )
        info_pill.pack(pady=(0, 10))

        # Exercise List (Frame 40)
        ex_container = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        ex_container.pack(fill="x", pady=(0, 20))

        step_num = 1
        for step in routine.steps:
            if step.step_type != StepType.EXERCISE or not step.exercise:
                continue

            ex = step.exercise
            row = ctk.CTkFrame(ex_container, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)

            # Row click handler
            row.bind("<Button-1>", lambda e, x=ex: self.show_exercise_detail_modal(x.id))

            # Drag/order icon
            ctk.CTkLabel(row, text="≡", font=ctk.CTkFont(size=18, weight="bold"), text_color="gray").pack(side="left", padx=(0, 8))

            # 1:1 Thumbnail (54x54)
            thumb_box = ctk.CTkFrame(row, width=54, height=54, fg_color="#0F172A", corner_radius=8)
            thumb_box.pack(side="left", padx=(0, 12))
            thumb_box.pack_propagate(False)
            thumb_box.bind("<Button-1>", lambda e, x=ex: self.show_exercise_detail_modal(x.id))

            thumb_ctk = load_ctk_image(getattr(ex, 'icon_path', None) or ex.image_path, size=(54, 54))
            t_lbl = ctk.CTkLabel(thumb_box, image=thumb_ctk, text="" if thumb_ctk else "🏋️")
            t_lbl.pack(expand=True, fill="both")
            t_lbl.bind("<Button-1>", lambda e, x=ex: self.show_exercise_detail_modal(x.id))

            # Title & Muscle
            mid_box = ctk.CTkFrame(row, fg_color="transparent")
            mid_box.pack(side="left", fill="x", expand=True)
            mid_box.bind("<Button-1>", lambda e, x=ex: self.show_exercise_detail_modal(x.id))

            e_lbl = ctk.CTkLabel(
                mid_box,
                text=f"{step_num}. {ex.name}",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            e_lbl.pack(fill="x")
            e_lbl.bind("<Button-1>", lambda e, x=ex: self.show_exercise_detail_modal(x.id))

            focus_str = ", ".join(ex.focus_areas[:2]) if ex.focus_areas else ex.target_muscle.value
            m_lbl = ctk.CTkLabel(
                mid_box,
                text=f"Fokus: {focus_str}",
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            m_lbl.pack(fill="x")
            m_lbl.bind("<Button-1>", lambda e, x=ex: self.show_exercise_detail_modal(x.id))

            # Reps or Duration Badge
            is_rep = bool(step.target_reps or ex.is_reps_based)
            badge_text = f"×{step.target_reps or ex.default_reps}" if is_rep else f"{step.duration_seconds}s"

            ctk.CTkLabel(
                row,
                text=badge_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=("#E2E8F0", "#334155"),
                corner_radius=8,
                padx=10,
                pady=4
            ).pack(side="right", padx=(8, 0))

            # Detail Info button
            ctk.CTkButton(
                row,
                text="ℹ️ Detail",
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                hover_color=("#E2E8F0", "#334155"),
                text_color="#38BDF8",
                width=65,
                height=28,
                command=lambda x=ex: self.show_exercise_detail_modal(x.id)
            ).pack(side="right")

            step_num += 1

        # Big Blue START Button (Bottom fixed)
        btn_start = ctk.CTkButton(
            scroll,
            text="▶ MULAI LATIHAN SEKARANG (START)",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=52,
            corner_radius=26,
            command=lambda: self.start_workout_session(routine.id)
        )
        btn_start.pack(fill="x", padx=16, pady=(10, 30))

    # =========================================================================
    # OPEN EXERCISE DETAIL MODAL
    # =========================================================================
    def show_exercise_detail_modal(self, exercise_id: str):
        ex = self.service.get_exercise_by_id(exercise_id)
        if not ex:
            messagebox.showerror("Error", "Gerakan tidak ditemukan.")
            return

        def _on_updated(updated_ex):
            # If in workout or list, refresh
            if self.active_engine and hasattr(self, '_refresh_workout_ui'):
                self._refresh_workout_ui(self.active_engine.get_snapshot())

        ExerciseDetailModal(self, ex, self.service, on_image_updated=_on_updated)

    # =========================================================================
    # VIEW 3: ACTIVE WORKOUT SESSION (Frame 50, 55, 60, 85)
    # - Top Area: 1:1 image area replacing the movement video
    # - (?) button to view exercise details anytime
    # - Time-based vs Rep-based support (Checkmark button ✓)
    # - Rest interval with next exercise preview
    # - Accidental cancellation protection
    # =========================================================================
    def start_workout_session(self, routine_id: str):
        if self.active_engine and self.active_engine.state in (SessionState.RUNNING, SessionState.RESTING, SessionState.PAUSED):
            confirm = messagebox.askyesno(
                "Workout Sedang Berjalan",
                "Ada sesi workout yang sedang berlangsung. Apakah Anda ingin mengakhiri sesi lama dan memulai yang baru?"
            )
            if not confirm:
                return

        self.active_engine = self.service.start_workout(routine_id)
        self._build_active_workout_view()

        self.timer_running = True
        self._start_timer_thread()

    def _build_active_workout_view(self):
        self._clear_main()
        snap = self.active_engine.get_snapshot()

        # Outer: grid-based so controls are ALWAYS pinned at bottom / visible
        outer = ctk.CTkFrame(self.main_container, corner_radius=16, fg_color=("white", "#0F172A"))
        outer.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        outer.grid_rowconfigure(0, weight=0)   # header
        outer.grid_rowconfigure(1, weight=0)   # progress bar
        outer.grid_rowconfigure(2, weight=1)   # image — fills remaining height
        outer.grid_rowconfigure(3, weight=0)   # title + info btn
        outer.grid_rowconfigure(4, weight=0)   # status pill
        outer.grid_rowconfigure(5, weight=0)   # large timer
        outer.grid_rowconfigure(6, weight=0)   # cals + next
        outer.grid_rowconfigure(7, weight=0)   # controls — ALWAYS VISIBLE
        outer.grid_columnconfigure(0, weight=1)
        self.session_frame = outer  # alias so other methods still work

        # ── ROW 0: Header ───────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(outer, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 6))

        ctk.CTkButton(
            top_bar,
            text="◀ Keluar",
            width=80,
            height=32,
            fg_color=("gray80", "#1E293B"),
            text_color=("black", "white"),
            hover_color=("#FEE2E2", "#7F1D1D"),
            corner_radius=16,
            command=self._handle_abort_session
        ).pack(side="left")

        self.live_routine_lbl = ctk.CTkLabel(
            top_bar,
            text=snap['routine_title'].upper(),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.live_routine_lbl.pack(side="left", padx=10)

        self.live_step_badge = ctk.CTkLabel(
            top_bar,
            text=f"Langkah {snap['step_index']}/{snap['total_steps']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E2E8F0", "#334155"),
            corner_radius=8,
            padx=10,
            pady=4
        )
        self.live_step_badge.pack(side="right")

        # ── ROW 1: Progress bar ──────────────────────────────────────────────
        self.progress_bar = ctk.CTkProgressBar(outer, height=8, progress_color="#3B82F6")
        self.progress_bar.set(snap['progress_percentage'] / 100.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 6))

        # ── ROW 2: 1:1 Image area — expands to fill remaining vertical space ─
        img_holder = ctk.CTkFrame(outer, fg_color="transparent")
        img_holder.grid(row=2, column=0, sticky="nsew", padx=20, pady=4)
        img_holder.grid_rowconfigure(0, weight=1)
        img_holder.grid_columnconfigure(0, weight=1)

        self.media_container = ctk.CTkFrame(img_holder, fg_color="#020617", corner_radius=16)
        self.media_container.grid(row=0, column=0, sticky="nsew")

        self.live_image_lbl = ctk.CTkLabel(self.media_container, text="")
        self.live_image_lbl.pack(expand=True, fill="both", padx=8, pady=8)

        # ── ROW 3: Exercise title + 📖 Panduan Gerakan button ───────────────
        title_row = ctk.CTkFrame(outer, fg_color="transparent")
        title_row.grid(row=3, column=0, sticky="ew", padx=20, pady=(6, 2))

        # Exercise Icon Badge (Live Workout)
        self.live_icon_lbl = ctk.CTkLabel(title_row, text="", width=36, height=36)
        self.live_icon_lbl.pack(side="left", padx=(0, 8))

        self.live_exercise_lbl = ctk.CTkLabel(
            title_row,
            text=snap['exercise_name'],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.live_exercise_lbl.pack(side="left", padx=(0, 8))

        self.btn_info = ctk.CTkButton(
            title_row,
            text="📖 Panduan Gerakan",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E2E8F0", "#1E293B"),
            hover_color=("#CBD5E1", "#334155"),
            text_color="#38BDF8",
            height=30,
            corner_radius=15,
            command=self._handle_current_exercise_info
        )
        self.btn_info.pack(side="left")

        # ── ROW 4: Status pill ───────────────────────────────────────────────
        self.status_pill = ctk.CTkLabel(
            outer,
            text="💪 LATIHAN AKTIF",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10B981",
            text_color="white",
            corner_radius=14,
            padx=16,
            pady=3
        )
        self.status_pill.grid(row=4, column=0, pady=(2, 2))

        # ── ROW 5: Large timer / reps display ────────────────────────────────
        self.live_timer_lbl = ctk.CTkLabel(
            outer,
            text=f"{snap['step_remaining_seconds']}s",
            font=ctk.CTkFont(size=52, weight="bold"),
            text_color="#38BDF8"
        )
        self.live_timer_lbl.grid(row=5, column=0, pady=(0, 2))

        # ── ROW 6: Cals + Next exercise ──────────────────────────────────────
        badge_row = ctk.CTkFrame(outer, fg_color="transparent")
        badge_row.grid(row=6, column=0, sticky="ew", padx=30, pady=(0, 4))

        self.live_cals_lbl = ctk.CTkLabel(
            badge_row,
            text=f"🔥 {snap['calories_burned']} kkal",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F59E0B"
        )
        self.live_cals_lbl.pack(side="left")

        self.live_next_lbl = ctk.CTkLabel(
            badge_row,
            text=f"👉 Selanjutnya: {snap['next_exercise']}",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.live_next_lbl.pack(side="right")

        # ── ROW 7: Controls — ALWAYS VISIBLE ────────────────────────────────
        self.controls_box = ctk.CTkFrame(outer, fg_color="transparent")
        self.controls_box.grid(row=7, column=0, pady=(4, 14))

        self._build_workout_controls(snap)

    def _build_workout_controls(self, snap: Dict[str, Any]):
        for w in self.controls_box.winfo_children():
            w.destroy()

        is_rest = (snap['step_type'] == StepType.REST.value)
        is_reps = snap.get('is_reps_based', False) and not is_rest

        if is_rest:
            # REST SCREEN (Frame 60)
            btn_row = ctk.CTkFrame(self.controls_box, fg_color="transparent")
            btn_row.pack()

            ctk.CTkButton(
                btn_row,
                text="+20 Detik",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=110,
                height=44,
                corner_radius=22,
                fg_color=("#CBD5E1", "#334155"),
                text_color=("black", "white"),
                command=self._handle_plus_20
            ).pack(side="left", padx=8)

            ctk.CTkButton(
                btn_row,
                text="LEWATI ISTIRAHAT ▶",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=160,
                height=44,
                corner_radius=22,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                text_color="white",
                command=self._handle_step_skip
            ).pack(side="left", padx=8)

        elif is_reps:
            # REP-BASED EXERCISE (Frame 85)
            btn_row = ctk.CTkFrame(self.controls_box, fg_color="transparent")
            btn_row.pack()

            ctk.CTkButton(
                btn_row,
                text="⏮",
                width=48,
                height=46,
                corner_radius=23,
                fg_color=("gray80", "#1E293B"),
                command=self._handle_step_prev
            ).pack(side="left", padx=6)

            # Big Checkmark Button
            ctk.CTkButton(
                btn_row,
                text="✓ SELESAI REPETISI",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=180,
                height=46,
                corner_radius=23,
                fg_color="#10B981",
                hover_color="#059669",
                command=self._handle_step_skip
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                btn_row,
                text="⏭",
                width=48,
                height=46,
                corner_radius=23,
                fg_color=("gray80", "#1E293B"),
                command=self._handle_step_skip
            ).pack(side="left", padx=6)

        else:
            # TIME-BASED EXERCISE (Frame 55)
            btn_row = ctk.CTkFrame(self.controls_box, fg_color="transparent")
            btn_row.pack()

            ctk.CTkButton(
                btn_row,
                text="⏮",
                width=48,
                height=44,
                corner_radius=22,
                fg_color=("gray80", "#1E293B"),
                command=self._handle_step_prev
            ).pack(side="left", padx=4)

            self.btn_pause = ctk.CTkButton(
                btn_row,
                text="⏸ Pause",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                height=44,
                corner_radius=22,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                command=self._handle_pause_resume
            )
            self.btn_pause.pack(side="left", padx=4)

            ctk.CTkButton(
                btn_row,
                text="⏭",
                width=48,
                height=44,
                corner_radius=22,
                fg_color=("gray80", "#1E293B"),
                command=self._handle_step_skip
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                btn_row,
                text="+10s",
                width=65,
                height=44,
                corner_radius=22,
                fg_color=("gray80", "#1E293B"),
                command=self._handle_plus_10
            ).pack(side="left", padx=4)

        # Refresh images and text
        self._refresh_workout_ui(snap)

    def _handle_current_exercise_info(self):
        if not self.active_engine:
            return
        snap = self.active_engine.get_snapshot()
        ex_id = snap.get('exercise_id')
        if ex_id:
            self.show_exercise_detail_modal(ex_id)

    # Timer Loop
    def _start_timer_thread(self):
        def _loop():
            while self.timer_running and self.active_engine:
                if self.active_engine.state in (SessionState.RUNNING, SessionState.RESTING):
                    time.sleep(1)
                    self.after(0, self._on_timer_tick)
                else:
                    time.sleep(0.3)

        threading.Thread(target=_loop, daemon=True).start()

    def _on_timer_tick(self):
        if not self.active_engine:
            return

        snap = self.active_engine.tick(delta_seconds=1)

        prof = self.service.get_profile()
        if prof.sound_enabled:
            rem = snap['step_remaining_seconds']
            if rem in (3, 2, 1):
                AudioFeedback.play_countdown()
            elif rem == 0:
                AudioFeedback.play_go()

        if snap['state'] == SessionState.COMPLETED.value:
            self.timer_running = False
            AudioFeedback.play_celebration()
            self._show_workout_celebration(snap)
            return

        self._refresh_workout_ui(snap)

    def _refresh_workout_ui(self, snap: Dict[str, Any]):
        if not hasattr(self, 'live_timer_lbl'):
            return

        is_rest = (snap['step_type'] == StepType.REST.value)
        is_reps = snap.get('is_reps_based', False) and not is_rest

        # Update 1:1 image
        img_to_show = snap.get('next_image_path') if is_rest else snap.get('image_path')

        # Update live exercise icon
        icon_to_show = "workout_data/images/icons/icon_rest.png" if is_rest else snap.get('icon_path')
        if not icon_to_show and not is_rest and snap.get('exercise_id'):
            icon_to_show = f"workout_data/images/icons/icon_{snap['exercise_id']}.png"
        icon_ctk = load_ctk_image(icon_to_show, size=(36, 36))
        if hasattr(self, 'live_icon_lbl'):
            if icon_ctk:
                self.live_icon_lbl.configure(image=icon_ctk, text="")
                self.live_icon_lbl.image = icon_ctk
            else:
                self.live_icon_lbl.configure(image="", text="⚡")
        ctk_img = load_ctk_image(img_to_show, size=(260, 260))
        if ctk_img:
            self.live_image_lbl.configure(image=ctk_img, text="")
            self.live_image_lbl.image = ctk_img
        else:
            self.live_image_lbl.configure(
                image="",
                text="Area Foto 1:1\n(Posisi Menggantikan Video Gerakan)",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )

        # Status & title
        if is_rest:
            self.status_pill.configure(text="🍃 ISTIRAHAT & PEMULIHAN", fg_color="#0284C7")
            self.live_exercise_lbl.configure(text="ISTIRAHAT (REST)")
            self.live_timer_lbl.configure(text=f"{snap['step_remaining_seconds']}s")
            self.btn_info.configure(text="📖 Panduan Gerakan Selanjutnya")
        elif is_reps:
            self.status_pill.configure(text="💪 LATIHAN REPETISI", fg_color="#10B981")
            self.live_exercise_lbl.configure(text=snap['exercise_name'])
            self.live_timer_lbl.configure(text=f"×{snap.get('target_reps') or 12}")
            self.btn_info.configure(text="📖 Panduan Gerakan")
        else:
            self.status_pill.configure(text="💪 LATIHAN AKTIF", fg_color="#10B981")
            self.live_exercise_lbl.configure(text=snap['exercise_name'])
            self.live_timer_lbl.configure(text=f"{snap['step_remaining_seconds']}s")
            self.btn_info.configure(text="📖 Panduan Gerakan")

        if hasattr(self, 'btn_pause'):
            if snap['state'] == SessionState.PAUSED.value:
                self.btn_pause.configure(text="▶ Lanjut", fg_color="#10B981")
            else:
                self.btn_pause.configure(text="⏸ Pause", fg_color="#3B82F6")

        self.live_step_badge.configure(text=f"Langkah {snap['step_index']}/{snap['total_steps']}")
        self.progress_bar.set(snap['progress_percentage'] / 100.0)
        self.live_cals_lbl.configure(text=f"🔥 {snap['calories_burned']} kkal")
        self.live_next_lbl.configure(text=f"👉 Selanjutnya: {snap['next_exercise']}")

    def _handle_pause_resume(self):
        if not self.active_engine:
            return
        if self.active_engine.state == SessionState.PAUSED:
            self.active_engine.resume()
        else:
            self.active_engine.pause()
        self._refresh_workout_ui(self.active_engine.get_snapshot())

    def _handle_step_skip(self):
        if self.active_engine:
            self.active_engine.skip_step()
            snap = self.active_engine.get_snapshot()
            self._build_workout_controls(snap)

    def _handle_step_prev(self):
        if self.active_engine:
            self.active_engine.previous_step()
            snap = self.active_engine.get_snapshot()
            self._build_workout_controls(snap)

    def _handle_plus_10(self):
        if self.active_engine:
            self.active_engine.adjust_time(10)
            self._refresh_workout_ui(self.active_engine.get_snapshot())

    def _handle_plus_20(self):
        if self.active_engine:
            self.active_engine.adjust_time(20)
            self._refresh_workout_ui(self.active_engine.get_snapshot())

    def _handle_abort_session(self):
        confirm = messagebox.askyesno(
            "Konfirmasi Pembatalan",
            "Apakah Anda yakin ingin mengakhiri sesi workout ini lebih awal?\nProgres latihan yang sudah dijalani tetap akan dicatat ke riwayat."
        )
        if confirm:
            self.timer_running = False
            log = self.active_engine.abort(confirmed=True)
            messagebox.showinfo("Workout Selesai Sebagian", f"Total kalori terbakar: {log.calories_burned} kkal.")
            self.show_training_view()

    # Celebration & Adaptive Feedback
    def _show_workout_celebration(self, snap: Dict[str, Any]):
        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        card = ctk.CTkFrame(scroll, corner_radius=18, fg_color=("white", "#1E293B"))
        card.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(card, text="🎉", font=ctk.CTkFont(size=56)).pack(pady=(24, 6))
        ctk.CTkLabel(card, text="WORKOUT SELESAI! LUAR BIASA!", font=ctk.CTkFont(size=24, weight="bold"), text_color="#10B981").pack(pady=(0, 4))
        ctk.CTkLabel(card, text=f"Anda baru saja menyelesaikan \"{snap['routine_title']}\"", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(0, 16))

        # Stats summary row
        stats_row = ctk.CTkFrame(card, fg_color="transparent")
        stats_row.pack(fill="x", padx=30, pady=(0, 20))
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)

        dur_mins = round(snap['total_elapsed_seconds'] / 60.0, 1)
        res_data = [
            ("⏱️ Total Durasi", f"{dur_mins} Menit"),
            ("🔥 Kalori Terbakar", f"{snap['calories_burned']} kkal"),
            ("✅ Gerakan Tuntas", f"{snap['total_steps']}/{snap['total_steps']}")
        ]
        for idx, (label, val) in enumerate(res_data):
            f = ctk.CTkFrame(stats_row, corner_radius=10, fg_color=("#F1F5F9", "#0F172A"))
            f.grid(row=0, column=idx, padx=6, sticky="nsew")
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(10, 2))
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        # Adaptive Post-Workout Feedback Card
        fb_card = ctk.CTkFrame(card, fg_color=("#F8FAFC", "#0F172A"), corner_radius=14)
        fb_card.pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkLabel(
            fb_card,
            text="💬 Bagaimana Kondisi Tubuh Anda Setelah Sesi Latihan Ini?",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(padx=20, pady=(16, 4), anchor="w")

        ctk.CTkLabel(
            fb_card,
            text="Pilih kondisi yang paling Anda rasakan untuk saran latihan adaptif berikutnya:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(padx=20, pady=(0, 12), anchor="w")

        btn_grid = ctk.CTkFrame(fb_card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=20, pady=(0, 12))
        btn_grid.grid_columnconfigure((0, 1), weight=1)

        fb_options = [
            ("TOO_HEAVY", "🥵 Terlalu Berat / Sangat Lelah", "#EF4444", 0, 0),
            ("SLIGHTLY_HEAVY", "😮‍💨 Agak Berat tapi Mampu", "#F59E0B", 0, 1),
            ("BALANCED", "😊 Pas & Nyaman", "#10B981", 1, 0),
            ("TOO_LIGHT", "⚡ Terlalu Ringan / Kurang Berasa", "#3B82F6", 1, 1),
        ]

        for code, text_val, col, r, c in fb_options:
            b = ctk.CTkButton(
                btn_grid,
                text=text_val,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=col,
                height=38,
                corner_radius=10,
                command=lambda cd=code: self._handle_feedback_choice(cd)
            )
            b.grid(row=r, column=c, padx=6, pady=6, sticky="ew")

        # Skip button
        ctk.CTkButton(
            card,
            text="Lewati Umpan Balik & Kembali ke Menu Latihan ⏩",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color="gray",
            hover_color=("#E2E8F0", "#334155"),
            command=self.show_training_view
        ).pack(pady=(0, 20))

    def _handle_feedback_choice(self, code: str):
        result = self.service.record_session_feedback(code)
        messagebox.showinfo(
            "Rekomendasi Adaptif FitPulse",
            f"{result['message']}\n\n💡 Saran Pelatih:\n{result['recommendation']}"
        )
        self.show_training_view()

    # =========================================================================
    # VIEW 4: REPORT HUB (Frame 12)
    # - Day Streak & Personal Best
    # - Weight Tracker (Current, Heaviest, Lightest, Log button)
    # - BMI Calculator with color-coded bar gauge & height editor
    # - Lifetime stats & Workout History
    # =========================================================================
    def show_report_view(self):
        self._set_active_nav("report")
        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        ctk.CTkLabel(
            scroll,
            text="LAPORAN KEBUGARAN (REPORT)",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 14))

        stats = self.service.get_user_dashboard_stats()
        profile = self.service.get_profile()

        # 1. Streak Card (Frame 12)
        streak_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        streak_card.pack(fill="x", pady=(0, 14))

        s_grid = ctk.CTkFrame(streak_card, fg_color="transparent")
        s_grid.pack(fill="x", padx=24, pady=16)
        s_grid.grid_columnconfigure((0, 1), weight=1)

        f1 = ctk.CTkFrame(s_grid, fg_color="transparent")
        f1.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(f1, text="Day Streak", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        current_streak = stats.get('current_streak_days', stats.get('streak_days', 0))
        ctk.CTkLabel(f1, text=f"🔥 {current_streak}", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")

        f2 = ctk.CTkFrame(s_grid, fg_color="transparent")
        f2.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(f2, text="Personal Best", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="e")
        pb_streak = stats.get('personal_best_streak', current_streak)
        ctk.CTkLabel(f2, text=f"🏆 {pb_streak} Hari", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="e")

        # 2. Weight Tracker Card (Frame 12)
        weight_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        weight_card.pack(fill="x", pady=(0, 14))

        w_top = ctk.CTkFrame(weight_card, fg_color="transparent")
        w_top.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(w_top, text="Berat Badan (Weight)", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(
            w_top,
            text="Catat (Log)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            width=90,
            height=32,
            corner_radius=16,
            command=self._prompt_log_weight
        ).pack(side="right")

        w_stats = ctk.CTkFrame(weight_card, fg_color="transparent")
        w_stats.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            w_stats,
            text=f"{profile.weight_kg:.1f} kg",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#38BDF8"
        ).pack(side="left")

        w_sub = ctk.CTkFrame(w_stats, fg_color="transparent")
        w_sub.pack(side="right")
        ctk.CTkLabel(w_sub, text=f"Terberat: {profile.weight_kg:.0f} kg", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="e")
        ctk.CTkLabel(w_sub, text=f"Teringan: {profile.weight_kg:.0f} kg", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="e")

        # 3. BMI Gauge Card (Frame 12)
        bmi_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        bmi_card.pack(fill="x", pady=(0, 14))

        b_top = ctk.CTkFrame(bmi_card, fg_color="transparent")
        b_top.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(b_top, text="BMI (Body Mass Index)", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(
            b_top,
            text="Ubah Tinggi",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#CBD5E1", "#334155"),
            text_color=("black", "white"),
            width=95,
            height=32,
            corner_radius=16,
            command=self._prompt_edit_height
        ).pack(side="right")

        # BMI Calculation
        height_m = profile.height_cm / 100.0
        bmi_val = profile.weight_kg / (height_m * height_m) if height_m > 0 else 22.0

        if bmi_val < 18.5:
            cat_name = "Kekurangan Berat Badan (Underweight)"
            cat_color = "#3B82F6"
        elif bmi_val < 25.0:
            cat_name = "Berat Badan Sehat / Ideal (Healthy weight)"
            cat_color = "#10B981"
        elif bmi_val < 30.0:
            cat_name = "Kelebihan Berat Badan (Overweight)"
            cat_color = "#F59E0B"
        else:
            cat_name = "Obesitas (Obese)"
            cat_color = "#EF4444"

        b_val_row = ctk.CTkFrame(bmi_card, fg_color="transparent")
        b_val_row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            b_val_row,
            text=f"{bmi_val:.1f}",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            b_val_row,
            text=f"● {cat_name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=cat_color
        ).pack(side="left")

        # Color-coded Bar Gauge (Frame 12)
        gauge_frame = ctk.CTkFrame(bmi_card, fg_color="transparent")
        gauge_frame.pack(fill="x", padx=20, pady=(4, 6))
        gauge_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkFrame(gauge_frame, height=12, fg_color="#3B82F6", corner_radius=6).grid(row=0, column=0, padx=2, sticky="ew")
        ctk.CTkFrame(gauge_frame, height=12, fg_color="#10B981", corner_radius=6).grid(row=0, column=1, padx=2, sticky="ew")
        ctk.CTkFrame(gauge_frame, height=12, fg_color="#F59E0B", corner_radius=6).grid(row=0, column=2, padx=2, sticky="ew")
        ctk.CTkFrame(gauge_frame, height=12, fg_color="#EF4444", corner_radius=6).grid(row=0, column=3, padx=2, sticky="ew")

        labels_frame = ctk.CTkFrame(bmi_card, fg_color="transparent")
        labels_frame.pack(fill="x", padx=20, pady=(0, 12))
        labels_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(labels_frame, text="< 18.5", font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=0)
        ctk.CTkLabel(labels_frame, text="18.5 - 24.9", font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=1)
        ctk.CTkLabel(labels_frame, text="25 - 29.9", font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=2)
        ctk.CTkLabel(labels_frame, text="≥ 30", font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=3)

        ctk.CTkLabel(
            bmi_card,
            text=f"Tinggi Badan Pengguna: {profile.height_cm:.0f} cm",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 14))

        # 4. Lifetime Stats Summary
        life_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        life_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            life_card,
            text="Statistik Menyeluruh (Lifetime Records)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=20, pady=(14, 10))

        life_grid = ctk.CTkFrame(life_card, fg_color="transparent")
        life_grid.pack(fill="x", padx=20, pady=(0, 16))
        life_grid.grid_columnconfigure((0, 1, 2), weight=1)

        stat_boxes = [
            ("✅ Total Latihan Tuntas", f"{stats.get('total_workouts', 0)} Sesi"),
            ("🔥 Total Kalori Terbakar", f"{stats.get('total_calories', 0):.0f} kkal"),
            ("⏱️ Total Menit Latihan", f"{stats.get('total_minutes', 0):.0f} Menit")
        ]
        for idx, (title, val) in enumerate(stat_boxes):
            b = ctk.CTkFrame(life_grid, corner_radius=10, fg_color=("#F1F5F9", "#0F172A"))
            b.grid(row=0, column=idx, padx=4, sticky="nsew")
            ctk.CTkLabel(b, text=title, font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(10, 2))
            ctk.CTkLabel(b, text=val, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        # ─────────────────────────────────────────────────────────────────────
        # 5. RIWAYAT LATIHAN + KONSISTENSI PENYELESAIAN
        # ─────────────────────────────────────────────────────────────────────
        try:
            all_logs = self.service.storage.load_logs()
        except Exception:
            all_logs = []

        total_logs = len(all_logs)
        completed_logs = [lg for lg in all_logs if getattr(lg, 'status', '') == 'COMPLETED']
        consistency_pct = (len(completed_logs) / total_logs * 100) if total_logs > 0 else 0

        # Consistency Card
        consist_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        consist_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            consist_card,
            text="Konsistensi Penyelesaian Latihan",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=20, pady=(14, 6))

        bar_color = "#10B981" if consistency_pct >= 70 else ("#F59E0B" if consistency_pct >= 40 else "#EF4444")
        bar_fill_w = max(0.01, consistency_pct / 100.0)
        consist_bar = ctk.CTkProgressBar(consist_card, height=14, progress_color=bar_color, corner_radius=7)
        consist_bar.set(bar_fill_w)
        consist_bar.pack(fill="x", padx=20, pady=(0, 8))

        c_stats = ctk.CTkFrame(consist_card, fg_color="transparent")
        c_stats.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            c_stats,
            text=f"Selesai: {len(completed_logs)}   Dibatalkan: {total_logs - len(completed_logs)}   Total: {total_logs} Sesi",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side="left")

        ctk.CTkLabel(
            c_stats,
            text=f"{consistency_pct:.0f}%",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=bar_color
        ).pack(side="right")

        # History Log List
        hist_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        hist_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            hist_card,
            text="Riwayat Latihan",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=20, pady=(14, 6))

        if not all_logs:
            ctk.CTkLabel(
                hist_card,
                text="Belum ada riwayat latihan. Yuk mulai latihan pertama kamu!",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            ).pack(pady=(0, 20))
        else:
            import datetime as _dt
            # Show most recent 15 entries (reversed = newest first)
            for lg in list(reversed(all_logs))[:15]:
                status_ok = getattr(lg, 'status', '') == 'COMPLETED'
                status_icon = "[OK]" if status_ok else "[!]"
                status_color = "#10B981" if status_ok else "#F59E0B"
                try:
                    ts = _dt.datetime.fromisoformat(str(lg.timestamp))
                    date_str = ts.strftime("%d %b %Y, %H:%M")
                except Exception:
                    date_str = str(lg.timestamp)[:16]

                comp_pct = 0.0
                try:
                    comp_pct = float(getattr(lg, 'completion_percentage', 0))
                except Exception:
                    pass

                dur_min = max(0, int(getattr(lg, 'duration_spent_seconds', 0) // 60))
                cals = getattr(lg, 'calories_burned', 0)

                row_f = ctk.CTkFrame(hist_card, fg_color=("gray95", "#0F172A"), corner_radius=10)
                row_f.pack(fill="x", padx=16, pady=(0, 6))

                top_f = ctk.CTkFrame(row_f, fg_color="transparent")
                top_f.pack(fill="x", padx=14, pady=(10, 4))

                ctk.CTkLabel(
                    top_f,
                    text=f"{status_icon}  {getattr(lg, 'routine_title', 'Latihan')}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=status_color
                ).pack(side="left")

                ctk.CTkLabel(
                    top_f,
                    text=date_str,
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                ).pack(side="right")

                prog = ctk.CTkProgressBar(row_f, height=6, corner_radius=3,
                                          progress_color=status_color,
                                          fg_color=("gray80", "#1E293B"))
                prog.set(max(0.0, min(1.0, comp_pct / 100.0)))
                prog.pack(fill="x", padx=14, pady=(0, 4))

                bot_f = ctk.CTkFrame(row_f, fg_color="transparent")
                bot_f.pack(fill="x", padx=14, pady=(0, 10))

                ctk.CTkLabel(
                    bot_f,
                    text=f"Selesai: {comp_pct:.0f}%  |  {dur_min} menit  |  {cals:.0f} kkal",
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                ).pack(side="left")


    def _prompt_log_weight(self):
        dialog = ctk.CTkInputDialog(text="Masukkan berat badan baru Anda (kg):", title="Catat Berat Badan")
        val = dialog.get_input()
        if val:
            try:
                num = float(val)
                self.service.update_profile(weight_kg=num)
                self.profile_btn.configure(text=f"👤 {self.service.get_profile().name} ({num:.0f}kg)")
                self.show_report_view()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def _prompt_edit_height(self):
        dialog = ctk.CTkInputDialog(text="Masukkan tinggi badan Anda (cm):", title="Ubah Tinggi Badan")
        val = dialog.get_input()
        if val:
            try:
                num = float(val)
                self.service.update_profile(height_cm=num)
                self.show_report_view()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    # =========================================================================
    # VIEW 5: SETTINGS HUB (Frame 7)
    # - Profile Settings
    # - Workout Settings
    # - Sound & TTS options
    # - Weekly Routine schedule link
    # =========================================================================
    def show_settings_view(self):
        self._set_active_nav("settings")
        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        ctk.CTkLabel(
            scroll,
            text="PENGATURAN & PROFIL (SETTINGS)",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 14))

        profile = self.service.get_profile()

        # 1. Profile Form Card
        prof_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        prof_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(prof_card, text="👤 Profil Pengguna", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 10))

        # Inputs
        form = ctk.CTkFrame(prof_card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=(0, 16))
        form.grid_columnconfigure((0, 1), weight=1)

        # Name
        ctk.CTkLabel(form, text="Nama Atlet:", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=0, sticky="w", pady=(4, 2))
        self.entry_name = ctk.CTkEntry(form, height=36)
        self.entry_name.insert(0, profile.name)
        self.entry_name.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        # Fitness Level
        ctk.CTkLabel(form, text="Tingkat Kebugaran:", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=1, sticky="w", pady=(4, 2))
        self.opt_level = ctk.CTkOptionMenu(
            form,
            values=["Beginner", "Intermediate", "Advanced"],
            height=36
        )
        self.opt_level.set(profile.fitness_level.value)
        self.opt_level.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        # Weight
        ctk.CTkLabel(form, text="Berat Badan (kg):", font=ctk.CTkFont(size=12), text_color="gray").grid(row=2, column=0, sticky="w", pady=(4, 2))
        self.entry_weight = ctk.CTkEntry(form, height=36)
        self.entry_weight.insert(0, str(profile.weight_kg))
        self.entry_weight.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        # Height
        ctk.CTkLabel(form, text="Tinggi Badan (cm):", font=ctk.CTkFont(size=12), text_color="gray").grid(row=2, column=1, sticky="w", pady=(4, 2))
        self.entry_height = ctk.CTkEntry(form, height=36)
        self.entry_height.insert(0, str(profile.height_cm))
        self.entry_height.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        btn_save_prof = ctk.CTkButton(
            prof_card,
            text="Simpan Profil",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=38,
            command=self._handle_save_profile
        )
        btn_save_prof.pack(padx=20, pady=(0, 16), anchor="e")

        # 2. Workout & Voice Options (Frame 7)
        workout_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        workout_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(workout_card, text="⚙️ Pengaturan Latihan & Suara (Audio)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 10))

        # Rest duration
        rest_row = ctk.CTkFrame(workout_card, fg_color="transparent")
        rest_row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(rest_row, text="Durasi Istirahat Bawaan:").pack(side="left")

        self.rest_slider = ctk.CTkSlider(rest_row, from_=10, to=45, number_of_steps=7, command=self._on_rest_slider)
        self.rest_slider.set(profile.default_rest_seconds)
        self.rest_slider.pack(side="left", fill="x", expand=True, padx=16)

        self.rest_lbl = ctk.CTkLabel(rest_row, text=f"{profile.default_rest_seconds}s", width=40)
        self.rest_lbl.pack(side="right")

        # Sound switch
        self.sw_sound = ctk.CTkSwitch(workout_card, text="Bunyi Beep / Hitungan Mundur (Countdown Sound)", command=self._on_toggle_sound)
        if profile.sound_enabled:
            self.sw_sound.select()
        self.sw_sound.pack(padx=20, pady=10, anchor="w")

        # Voice cues switch
        self.sw_voice = ctk.CTkSwitch(workout_card, text="Panduan Suara / Voice Cues (TTS)", command=self._on_toggle_voice)
        if profile.voice_cues_enabled:
            self.sw_voice.select()
        self.sw_voice.pack(padx=20, pady=(0, 16), anchor="w")

        # 3. Quick Navigation Links
        # 3. User Guide Card (Panduan Pengguna)
        guide_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        guide_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(guide_card, text="📖 Panduan Pengguna (User Guide)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 6))
        ctk.CTkLabel(
            guide_card,
            text="Pelajari cara penggunaan aplikasi, navigasi, dan pemilihan program latihan.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        sw_guide_frame = ctk.CTkFrame(guide_card, fg_color="transparent")
        sw_guide_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.sw_guide = ctk.CTkSwitch(
            sw_guide_frame,
            text="Tampilkan panduan saat aplikasi dibuka",
            command=self._on_toggle_guide_startup
        )
        if getattr(profile, 'show_onboarding_guide', True):
            self.sw_guide.select()
        else:
            self.sw_guide.deselect()
        self.sw_guide.pack(side="left")

        ctk.CTkButton(
            guide_card,
            text="📖 Buka Panduan Pengguna Sekarang",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=38,
            command=self.show_user_guide_modal
        ).pack(fill="x", padx=20, pady=(0, 16))

        links_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        links_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(links_card, text="🔗 Akses Fitur Manajemen", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 10))

        ctk.CTkButton(
            links_card,
            text="📅 Kelola Jadwal Rutin Mingguan (Senin - Minggu)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#CBD5E1", "#334155"),
            text_color=("black", "white"),
            height=40,
            command=self.show_schedule_view
        ).pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(
            links_card,
            text="🛠️ Template Builder (Buat & Duplikat Template)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#CBD5E1", "#334155"),
            text_color=("black", "white"),
            height=40,
            command=self.show_custom_builder_view
        ).pack(fill="x", padx=20, pady=(0, 16))

    def _on_toggle_guide_startup(self):
        is_on = bool(self.sw_guide.get())
        self.service.update_profile(show_onboarding_guide=is_on)

    def _on_rest_slider(self, val):
        self.rest_lbl.configure(text=f"{int(val)}s")
        self.service.update_profile(default_rest_seconds=int(val))

    def _on_toggle_sound(self):
        self.service.update_profile(sound_enabled=bool(self.sw_sound.get()))

    def _on_toggle_voice(self):
        self.service.update_profile(voice_cues_enabled=bool(self.sw_voice.get()))

    def _handle_save_profile(self):
        try:
            name = self.entry_name.get().strip()
            w = float(self.entry_weight.get().strip())
            h = float(self.entry_height.get().strip())
            lvl = self.opt_level.get()

            self.service.update_profile(name=name, weight_kg=w, height_cm=h, fitness_level=lvl)
            self.profile_btn.configure(text=f"👤 {name} ({w:.0f}kg)")
            messagebox.showinfo("Berhasil", "Profil pengguna berhasil disimpan!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memperbarui profil: {e}")

    # =========================================================================
    # VIEW 6: WEEKLY SCHEDULE MANAGER
    # =========================================================================
    def show_schedule_view(self):
        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        top_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(
            top_row,
            text="◀ Kembali",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=90,
            height=34,
            command=self.show_training_view
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="JADWAL RUTIN MINGGUAN (HABIT BUILDER)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=16)

        schedule = self.service.get_weekly_schedule()
        routines = self.service.list_routines()
        routine_options = ["🍃 Hari Istirahat (Rest Day)"] + [f"{r.title} ({r.id})" for r in routines]

        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

        for d in days:
            daily = schedule.days.get(d, DailySchedule(day=d))
            card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=12)
            card.pack(fill="x", pady=5)

            c_inner = ctk.CTkFrame(card, fg_color="transparent")
            c_inner.pack(fill="x", padx=16, pady=12)

            # Day name & current status
            ctk.CTkLabel(
                c_inner,
                text=d.upper(),
                font=ctk.CTkFont(size=14, weight="bold"),
                width=80,
                anchor="w"
            ).pack(side="left")

            current_text = "🍃 Hari Istirahat" if daily.is_rest_day else (daily.routine_title or "Belum Diatur")
            ctk.CTkLabel(
                c_inner,
                text=f"Saat Ini: {current_text}",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10)

            # Quick assign option menu
            def _on_assign(choice, day_name=d):
                if "Istirahat" in choice:
                    self.service.update_daily_schedule(day_name, is_rest_day=True, routine_id=None, routine_title="Hari Istirahat")
                else:
                    r_id = choice.split("(")[-1].replace(")", "").strip()
                    r_obj = self.service.get_routine_by_id(r_id)
                    title = r_obj.title if r_obj else choice
                    self.service.update_daily_schedule(day_name, is_rest_day=False, routine_id=r_id, routine_title=title)
                self.show_schedule_view()

            menu = ctk.CTkOptionMenu(
                c_inner,
                values=routine_options,
                width=240,
                height=34,
                command=_on_assign
            )
            menu.set("Ganti Latihan...")
            menu.pack(side="right")

    # =========================================================================
    # VIEW 7: TEMPLATE BUILDER (Custom & Clone Routine)
    # =========================================================================
    def show_custom_builder_view(self, base_routine_id: Optional[str] = None):
        self._clear_main()

        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        top_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(
            top_row,
            text="◀ Kembali",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=90,
            height=34,
            command=self.show_training_view
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="TEMPLATE BUILDER (BUAT & MODIFIKASI)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=16)

        # Form card
        f_card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=14)
        f_card.pack(fill="x", pady=(0, 14))

        f_inner = ctk.CTkFrame(f_card, fg_color="transparent")
        f_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(f_inner, text="Nama Template Baru:", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        self.entry_b_title = ctk.CTkEntry(f_inner, placeholder_text="Misal: Tantangan Perut 10 Menit", height=36)
        self.entry_b_title.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(f_inner, text="Target Otot Utama:", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        self.opt_b_muscle = ctk.CTkOptionMenu(
            f_inner,
            values=["Full Body", "Abs & Core", "Arms", "Chest", "Legs", "Back"],
            height=36
        )
        self.opt_b_muscle.pack(fill="x", pady=(4, 14))

        # Exercise Selection Checklist
        ctk.CTkLabel(
            scroll,
            text="Pilih Gerakan untuk Dimasukkan ke Rencana:",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", pady=(6, 8))

        exercises = self.service.list_exercises()
        self.builder_checks: List[Tuple[Exercise, ctk.BooleanVar, ctk.IntVar]] = []

        for ex in exercises:
            c_row = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=10)
            c_row.pack(fill="x", pady=3)

            b_var = ctk.BooleanVar(value=False)
            val_var = ctk.IntVar(value=ex.default_reps if ex.is_reps_based else 30)

            sw = ctk.CTkCheckBox(c_row, text=f"{ex.name} ({ex.target_muscle.value})", variable=b_var, font=ctk.CTkFont(size=13, weight="bold"))
            sw.pack(side="left", padx=14, pady=10)

            unit = "reps" if ex.is_reps_based else "detik"
            ctk.CTkLabel(c_row, text=unit, font=ctk.CTkFont(size=11), text_color="gray").pack(side="right", padx=(2, 14))
            ctk.CTkEntry(c_row, textvariable=val_var, width=55, height=28).pack(side="right", padx=4)

            self.builder_checks.append((ex, b_var, val_var))

        btn_save = ctk.CTkButton(
            scroll,
            text="SIMPAN TEMPLATE WORKOUT BARU",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=46,
            corner_radius=23,
            command=self._handle_save_new_template
        )
        btn_save.pack(fill="x", pady=(16, 30))

    def _handle_save_new_template(self):
        title = self.entry_b_title.get().strip()
        if not title:
            messagebox.showerror("Error", "Nama template wajib diisi.")
            return

        selected = [(ex, val.get()) for ex, b, val in self.builder_checks if b.get()]
        if not selected:
            messagebox.showerror("Error", "Pilih minimal 1 gerakan untuk membuat template.")
            return

        muscle = MuscleGroup(self.opt_b_muscle.get())
        steps = []
        for s_idx, (ex, dur) in enumerate(selected, 1):
            target_reps = dur if ex.is_reps_based else None
            dur_sec = 30 if ex.is_reps_based else dur
            steps.append(WorkoutStep(
                step_id=f"step_{s_idx}",
                step_type=StepType.EXERCISE,
                duration_seconds=dur_sec,
                exercise=ex,
                target_reps=target_reps
            ))
            # add rest interval
            if s_idx < len(selected):
                steps.append(WorkoutStep(
                    step_id=f"rest_{s_idx}",
                    step_type=StepType.REST,
                    duration_seconds=15
                ))

        new_r = WorkoutRoutine(
            id=f"custom_{int(time.time()) % 100000}",
            title=title,
            description="Kustom rancangan pengguna FitPulse.",
            target_muscle=muscle,
            difficulty=DifficultyLevel.BEGINNER,
            steps=steps,
            tags=["Custom", muscle.value]
        )
        self.service.save_or_update_routine(new_r)
        messagebox.showinfo("Berhasil", f"Template '{title}' berhasil dibuat!")
        self.show_training_view()

    # =========================================================================
    # QUICK START
    # =========================================================================
    def handle_quick_start(self):
        today_sched = self.service.get_today_schedule()
        if today_sched and today_sched.routine_id:
            self.show_routine_overview_view(today_sched.routine_id)
        else:
            routines = self.service.list_routines()
            if routines:
                self.show_routine_overview_view(routines[0].id)


if __name__ == "__main__":
    app = FitPulseApp()
    app.mainloop()
