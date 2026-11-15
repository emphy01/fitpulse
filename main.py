"""
Interactive CLI Runner for Home Workout Application.
Provides an interactive terminal interface to test and operate all backend features,
including multi-tier templates, difficulty engines, and weekly routine scheduler.
"""

import sys
import time
import os
from typing import Optional

from homeworkout.service import WorkoutAppService
from homeworkout.models import (
    MuscleGroup, DifficultyLevel, StepType, SessionState, WorkoutStep, DayOfWeek
)


class WorkoutCLI:
    def __init__(self):
        self.service = WorkoutAppService()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, subtitle: str = ""):
        profile = self.service.get_profile()
        today_name = self.service.get_today_day_name()
        print("=" * 65)
        print("   🏋️  FITPULSE - HOME WORKOUT COMPANION (HCI EDITION)")
        print(f"   👤 User: {profile.name} | ⚖️ {profile.weight_kg} kg | 📅 Hari Ini: {today_name}")
        if subtitle:
            print(f"   📌 {subtitle}")
        print("=" * 65)

    def print_menu(self):
        self.clear_screen()
        today_sched = self.service.get_today_schedule()
        today_name = self.service.get_today_day_name()

        self.print_header("Menu Utama")
        if today_sched.is_rest_day:
            print(f" 🍃 Jadwal Hari Ini ({today_name}): HARI ISTIRAHAT & PEMULIHAN")
        else:
            print(f" 🎯 Jadwal Hari Ini ({today_name} @ {today_sched.scheduled_time}): {today_sched.routine_title or 'Latihan'}")
        print("-" * 65)

        print(" [1] ⚡ Quick Start: 7-Minute Full Body (Efficiency)")
        print(" [2] 📅 Rencana & Jadwal Rutin Mingguan (Habit Building)")
        print(" [3] 🔍 Jelajahi Template Workout (Berdasarkan Otot & Tingkat Kesulitan)")
        print(" [4] 📖 Katalog Gerakan & Panduan Aksesibilitas (Accessible)")
        print(" [5] 🛠️  Buat Custom Workout Sendiri (Valuable)")
        print(" [6] 📊 Dashboard Progres, Streak & Riwayat (Credible)")
        print(" [7] ⚙️  Pengaturan Profil & Aksesibilitas (Learnability)")
        print(" [0] 🚪 Keluar")
        print("-" * 65)

    def run(self):
        while True:
            self.print_menu()
            choice = input("Pilih menu (0-7): ").strip()

            if choice == "1":
                self.handle_quick_start()
            elif choice == "2":
                self.handle_weekly_schedule()
            elif choice == "3":
                self.handle_browse_routines()
            elif choice == "4":
                self.handle_exercise_catalog()
            elif choice == "5":
                self.handle_create_custom_routine()
            elif choice == "6":
                self.handle_dashboard()
            elif choice == "7":
                self.handle_settings()
            elif choice == "0":
                print("\nTerima kasih telah berolahraga hari ini! Tetap aktif & sehat! 💪\n")
                break
            else:
                input("\n⚠️ Pilihan tidak valid. Tekan Enter untuk mengulang...")

    # ---- 1. Quick Start ----
    def handle_quick_start(self):
        self.clear_screen()
        self.print_header("Quick Start Workout")
        print("Menyiapkan 'Scientific 7-Minute Full Body'...")
        engine = self.service.quick_start()
        self.run_workout_session(engine)

    # ---- 2. Weekly Schedule Planner (Habit Building) ----
    def handle_weekly_schedule(self):
        day_order = [
            DayOfWeek.SENIN.value, DayOfWeek.SELASA.value, DayOfWeek.RABU.value,
            DayOfWeek.KAMIS.value, DayOfWeek.JUMAT.value, DayOfWeek.SABTU.value,
            DayOfWeek.MINGGU.value
        ]

        while True:
            self.clear_screen()
            self.print_header("Jadwal Rutin Mingguan (Senin - Minggu)")
            schedule = self.service.get_weekly_schedule()
            today_name = self.service.get_today_day_name()

            print("Rencana Latihan Anda:")
            for idx, day in enumerate(day_order, 1):
                daily = schedule.days.get(day)
                is_today = " 👈 [HARI INI]" if day == today_name else ""
                if not daily or daily.is_rest_day:
                    print(f" [{idx}] {day:<8}: 🍃 Hari Istirahat & Pemulihan{is_today}")
                else:
                    print(f" [{idx}] {day:<8}: 🏋️ {daily.routine_title} (⏰ {daily.scheduled_time}){is_today}")

            print("\nPilihan:")
            print(" [1-7] Ubah Jadwal untuk Hari Tertentu")
            print(" [M]   Mulai Workout Hari Ini Langsung 🚀")
            print(" [0]   Kembali ke Menu Utama")
            print("-" * 65)

            c = input("Pilihan: ").strip().lower()
            if c == "0":
                break
            elif c == "m":
                today_sched = self.service.get_today_schedule()
                if today_sched.is_rest_day or not today_sched.routine_id:
                    input("Hari ini dijadwalkan sebagai hari istirahat. Tekan Enter...")
                else:
                    engine = self.service.start_workout(today_sched.routine_id)
                    self.run_workout_session(engine)
            elif c.isdigit() and 1 <= int(c) <= 7:
                selected_day = day_order[int(c) - 1]
                self._edit_single_day_schedule(selected_day)

    def _edit_single_day_schedule(self, day: str):
        self.clear_screen()
        self.print_header(f"Atur Jadwal: {day}")

        print("Pilih tipe hari:")
        print(" [1] 🏋️ Jadwalkan Latihan Rutin")
        print(" [2] 🍃 Jadwalkan Hari Istirahat (Rest Day)")
        t_pick = input("Pilihan (1/2): ").strip()

        if t_pick == "2":
            self.service.update_daily_schedule(day=day, is_rest_day=True)
            input(f"✅ Hari {day} berhasil diubah menjadi Hari Istirahat. Tekan Enter...")
            return

        routines = self.service.list_routines()
        print("\nPilih Template Workout:")
        for idx, r in enumerate(routines, 1):
            dur_mins = round(r.total_duration_seconds / 60, 1)
            print(f" [{idx}] {r.title} ({r.difficulty.value} - ~{dur_mins} min)")

        r_pick = input(f"Nomor Workout (1-{len(routines)}): ").strip()
        if not (r_pick.isdigit() and 1 <= int(r_pick) <= len(routines)):
            input("Pilihan workout tidak valid. Pembatalan dilakukan. Tekan Enter...")
            return

        selected_routine = routines[int(r_pick) - 1]
        time_str = input("Jam Latihan Target (Format HH:MM, default 07:00): ").strip() or "07:00"

        self.service.update_daily_schedule(
            day=day,
            is_rest_day=False,
            routine_id=selected_routine.id,
            scheduled_time=time_str,
            reminder_enabled=True
        )
        input(f"✅ Berhasil menjadwalkan '{selected_routine.title}' untuk hari {day}! Tekan Enter...")

    # ---- 3. Browse & Search Routines (Findable) ----
    def handle_browse_routines(self):
        while True:
            self.clear_screen()
            self.print_header("Koleksi Template Workout")
            print("Filter & Pencarian:")
            print(" [1] Tampilkan Semua Template")
            print(" [2] Filter berdasarkan Otot Target (Full Body, Abs, Legs, Arms, Back)")
            print(" [3] Filter berdasarkan Tingkat Kesulitan (Beginner, Intermediate, Advanced)")
            print(" [4] Cari berdasarkan Kata Kunci")
            print(" [0] Kembali ke Menu Utama")
            print("-" * 65)

            c = input("Pilihan (0-4): ").strip()
            if c == "0":
                break
            elif c == "1":
                routines = self.service.list_routines()
            elif c == "2":
                print("\nPilih Otot:")
                print("1. Full Body | 2. Abs & Core | 3. Legs | 4. Arms | 5. Back")
                m_pick = input("Nomor: ").strip()
                muscle_map = {
                    "1": MuscleGroup.FULL_BODY,
                    "2": MuscleGroup.ABS_CORE,
                    "3": MuscleGroup.LEGS,
                    "4": MuscleGroup.ARMS,
                    "5": MuscleGroup.BACK
                }
                target_m = muscle_map.get(m_pick)
                if not target_m:
                    continue
                routines = self.service.search_routines(target_muscle=target_m)
            elif c == "3":
                print("\nPilih Tingkat Kesulitan:")
                print("1. Beginner (20s kerja / 20s istirahat, 4-5 gerakan)")
                print("2. Intermediate (30s kerja / 15s istirahat, 6-8 gerakan)")
                print("3. Advanced (45s kerja / 10s istirahat, 8-10 gerakan)")
                d_pick = input("Nomor: ").strip()
                diff_map = {
                    "1": DifficultyLevel.BEGINNER,
                    "2": DifficultyLevel.INTERMEDIATE,
                    "3": DifficultyLevel.ADVANCED
                }
                target_d = diff_map.get(d_pick)
                if not target_d:
                    continue
                routines = self.service.search_routines(difficulty=target_d)
            elif c == "4":
                kw = input("Ketik kata kunci: ").strip()
                routines = self.service.search_routines(keyword=kw)
            else:
                continue

            self._display_routine_list(routines)

    def _display_routine_list(self, routines):
        self.clear_screen()
        self.print_header("Hasil Koleksi Workout")
        if not routines:
            print("❌ Tidak ada workout yang cocok.")
            input("\nTekan Enter untuk kembali...")
            return

        for idx, r in enumerate(routines, 1):
            dur_min = round(r.total_duration_seconds / 60, 1)
            print(f"[{idx}] {r.title}")
            print(f"    Target: {r.target_muscle.value} | Tingkat: {r.difficulty.value} | Durasi: ~{dur_min} menit")
            if r.difficulty == DifficultyLevel.BEGINNER:
                print(f"    ⚡ Spesifikasi: 20s kerja / 20s istirahat per gerakan")
            elif r.difficulty == DifficultyLevel.INTERMEDIATE:
                print(f"    ⚡ Spesifikasi: 30s kerja / 15s istirahat per gerakan")
            else:
                print(f"    ⚡ Spesifikasi: 45s kerja / 10s istirahat per gerakan (Tinggi)")
            print(f"    Deskripsi: {r.description}")
            ex_names = [s.exercise.name for s in r.steps if s.exercise]
            print(f"    Latihan ({r.exercise_count} gerakan): " + ", ".join(ex_names[:4]) + "...")
            print("-" * 65)

        choice = input(f"Pilih nomor workout untuk mulai (1-{len(routines)}) atau 'B' untuk batal: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(routines):
            selected = routines[int(choice) - 1]
            engine = self.service.start_workout(selected.id)
            self.run_workout_session(engine)

    # ---- 4. Exercise Catalog & Accessible Instructions ----
    def handle_exercise_catalog(self):
        while True:
            self.clear_screen()
            self.print_header("Katalog Gerakan & Panduan Audio/Teks Aksesibel")
            exercises = self.service.list_exercises()

            for idx, ex in enumerate(exercises, 1):
                print(f"[{idx}] {ex.name} ({ex.target_muscle.value} - {ex.difficulty.value})")

            print("[0] Kembali")
            c = input("\nPilih nomor gerakan untuk melihat detail lengkap (0 untuk kembali): ").strip()
            if c == "0":
                break
            if c.isdigit() and 1 <= int(c) <= len(exercises):
                ex = exercises[int(c) - 1]
                self.clear_screen()
                self.print_header(f"Detail Gerakan: {ex.name}")
                print(f"Target Otot   : {ex.target_muscle.value}")
                print(f"Tingkat       : {ex.difficulty.value}")
                print(f"Alat          : {ex.equipment_needed}")
                print(f"Estimasi MET  : {ex.met_value} (Scientific Calorie Constant)")
                print("\n📋 Instruksi Langkah demi Langkah:")
                for step_no, step in enumerate(ex.instructions, 1):
                    print(f"   {step_no}. {step}")

                print("\n♿ Panduan Aksesibilitas (Deskripsi Teks / Screen-Reader):")
                print(f"   \"{ex.accessible_description}\"")

                print("\n🔊 Audio Cue / Suara Panduan:")
                print(f"   \"{ex.audio_cue}\"")

                input("\nTekan Enter untuk kembali ke katalog...")

    # ---- 5. Custom Routine Builder ----
    # ---- 5. Custom Routine Builder & Editor ----
    def handle_create_custom_routine(self):
        self.clear_screen()
        self.print_header("Buat / Edit Template Workout")
        print("Pilih Mode Pembuatan:")
        print(" [1] 🛠️  Custom dari Nol (Mulai Kosong)")
        print(" [2] 📋 Pilih Template yang Ada untuk Dimodifikasi / Diedit")
        mode = input("Pilihan (1/2, default 1): ").strip()

        preset_routine = None
        if mode == "2":
            routines = self.service.list_routines()
            print("\nPilih Template yang Ingin Dimuat:")
            for idx, r in enumerate(routines, 1):
                print(f" [{idx}] {r.title} ({r.difficulty.value})")
            p_pick = input(f"Nomor Template (1-{len(routines)}): ").strip()
            if p_pick.isdigit() and 1 <= int(p_pick) <= len(routines):
                preset_routine = routines[int(p_pick) - 1]

        self.clear_screen()
        self.print_header("Detail Template Workout")

        default_title = preset_routine.title if preset_routine else ""
        prompt_title = f"Judul Workout (default '{default_title}'): " if default_title else "Judul Workout: "
        title = input(prompt_title).strip() or default_title
        if not title:
            input("❌ Judul tidak boleh kosong! Tekan Enter...")
            return

        default_desc = preset_routine.description if preset_routine else "Latihan mandiri pribadi."
        desc = input(f"Deskripsi (default '{default_desc}'): ").strip() or default_desc

        print("\nPilih Filter Fokus Otot untuk Menampilkan Gerakan:")
        print(" [1] Semua Otot  [2] Dada (Chest)  [3] Kaki (Legs)  [4] Perut (Abs)  [5] Lengan (Arms)  [6] Punggung (Back)")
        m_choice = input("Pilihan filter (1-6, default 1): ").strip()
        m_filter_map = {
            "2": MuscleGroup.CHEST,
            "3": MuscleGroup.LEGS,
            "4": MuscleGroup.ABS_CORE,
            "5": MuscleGroup.ARMS,
            "6": MuscleGroup.BACK
        }
        target_muscle_filter = m_filter_map.get(m_choice)

        if target_muscle_filter:
            catalog_to_show = self.service.search_exercises(target_muscle=target_muscle_filter)
        else:
            catalog_to_show = self.service.list_exercises()

        print(f"\nDaftar Gerakan Tersedia ({len(catalog_to_show)} gerakan):")
        for idx, ex in enumerate(catalog_to_show, 1):
            print(f"  [{idx}] {ex.name:<25} ({ex.target_muscle.value} - {ex.difficulty.value})")

        selected_pairs = []
        if preset_routine:
            print("\nGerakan bawaan dari template yang dipilih:")
            for s in preset_routine.steps:
                if s.step_type == StepType.EXERCISE and s.exercise:
                    selected_pairs.append((s.exercise.id, s.duration_seconds))
                    print(f"  • {s.exercise.name} ({s.duration_seconds}s)")
            add_more = input("\nIngin mereset dan memilih ulang gerakan? (y/N): ").strip().lower()
            if add_more == "y":
                selected_pairs = []

        if not selected_pairs:
            print("\nMasukkan nomor gerakan satu per satu. Ketik 'selesai' jika sudah cukup.")
            while True:
                pick = input(f"Gerakan #{len(selected_pairs)+1} (Nomor/selesai): ").strip()
                if pick.lower() in ("selesai", "done", "s", "q"):
                    break
                if pick.isdigit() and 1 <= int(pick) <= len(catalog_to_show):
                    ex = catalog_to_show[int(pick) - 1]
                    dur_str = input(f"  Durasi untuk '{ex.name}' dalam detik (default 30): ").strip()
                    dur = int(dur_str) if dur_str.isdigit() and int(dur_str) > 0 else 30
                    selected_pairs.append((ex.id, dur))
                    print(f"  ✅ '{ex.name}' ({dur}s) ditambahkan!")
                else:
                    print("  Nomor tidak valid.")

        if not selected_pairs:
            input("\n❌ Minimal harus ada 1 gerakan. Pembuatan dibatalkan. Tekan Enter...")
            return

        rest_str = input("\nDurasi istirahat antar gerakan dalam detik (default 15): ").strip()
        rest_sec = int(rest_str) if rest_str.isdigit() else 15

        try:
            r_id = preset_routine.id if preset_routine else None
            routine = self.service.create_custom_routine(
                title=title,
                description=desc,
                target_muscle=target_muscle_filter if target_muscle_filter else MuscleGroup.FULL_BODY,
                difficulty=DifficultyLevel.BEGINNER,
                exercise_ids_and_durations=selected_pairs,
                rest_seconds=rest_sec,
                routine_id=r_id
            )
            print(f"\n🎉 Berhasil menyimpan template workout: '{routine.title}'!")
            print(f"   Total {routine.exercise_count} gerakan, perkiraan durasi {round(routine.total_duration_seconds/60, 1)} menit.")
            input("\nTekan Enter untuk kembali...")
        except Exception as e:
            input(f"\n❌ Terjadi kesalahan: {e}. Tekan Enter...")

    # ---- 6. Dashboard & Analytics ----
    def handle_dashboard(self):
        self.clear_screen()
        self.print_header("Dashboard Progres & Riwayat Latihan")
        stats = self.service.get_user_dashboard_stats()

        print("📈 STATISTIK AKTIVITAS:")
        print(f"   🔥 Current Streak  : {stats['current_streak_days']} Hari berturut-turut")
        print(f"   🏆 Total Sesi      : {stats['total_workouts']} Workout Selesai")
        print(f"   ⏱️  Total Durasi    : {stats['total_minutes']} Menit")
        print(f"   ⚡ Total Kalori    : {stats['total_calories']} kkal terbakar (ACSM MET)")
        print("-" * 65)

        logs = self.service.get_history()
        print("📜 5 RIWAYAT TERAKHIR:")
        if not logs:
            print("   Belum ada riwayat workout. Mulai latihan pertamamu sekarang! 🚀")
        else:
            for l in reversed(logs[-5:]):
                status_icon = "✅" if l.status == "COMPLETED" else "⚠️"
                ts = l.timestamp.split("T")[0]
                mins = round(l.duration_spent_seconds / 60, 1)
                print(f"   {status_icon} [{ts}] {l.routine_title} - {mins} min | {l.calories_burned} kkal ({l.completion_percentage}% selesai)")

        print("-" * 65)
        input("Tekan Enter untuk kembali ke menu...")

    # ---- 7. Settings & Profile ----
    def handle_settings(self):
        self.clear_screen()
        self.print_header("Pengaturan Profil & Aksesibilitas")
        prof = self.service.get_profile()

        print(f" [1] Nama Pengguna        : {prof.name}")
        print(f" [2] Berat Badan          : {prof.weight_kg} kg (mempengaruhi hitungan kalori)")
        print(f" [3] Tinggi Badan         : {prof.height_cm} cm")
        print(f" [4] Default Istirahat    : {prof.default_rest_seconds} detik")
        print(f" [5] Suara & Beep         : {'Aktif' if prof.sound_enabled else 'Nonaktif'}")
        print(f" [6] Voice Cues / Text    : {'Aktif' if prof.voice_cues_enabled else 'Nonaktif'}")
        print(f" [7] High Contrast Mode   : {'Aktif' if prof.high_contrast_mode else 'Nonaktif'}")
        print(" [0] Kembali")
        print("-" * 65)

        c = input("Pilih pengaturan yang ingin diubah (0-7): ").strip()
        try:
            if c == "1":
                val = input("Masukkan nama baru: ").strip()
                self.service.update_profile(name=val)
            elif c == "2":
                val = float(input("Masukkan berat badan (kg): ").strip())
                self.service.update_profile(weight_kg=val)
            elif c == "3":
                val = float(input("Masukkan tinggi badan (cm): ").strip())
                self.service.update_profile(height_cm=val)
            elif c == "4":
                val = int(input("Durasi istirahat default (detik): ").strip())
                self.service.update_profile(default_rest_seconds=val)
            elif c == "5":
                self.service.update_profile(sound_enabled=not prof.sound_enabled)
            elif c == "6":
                self.service.update_profile(voice_cues_enabled=not prof.voice_cues_enabled)
            elif c == "7":
                self.service.update_profile(high_contrast_mode=not prof.high_contrast_mode)
        except Exception as e:
            input(f"\n❌ Error: {e}. Tekan Enter...")

    # ---- Live Workout Execution Screen ----
    def run_workout_session(self, engine):
        cue_cache = [""]

        def audio_listener(cue):
            cue_cache[0] = cue

        engine.on_audio_cue_callbacks.append(audio_listener)

        while engine.state not in (SessionState.COMPLETED, SessionState.ABORTED):
            self.clear_screen()
            snap = engine.get_snapshot()

            print("=" * 65)
            print(f"   ⏱️  SESI WORKOUT: {snap['routine_title'].upper()}")
            print(f"   STATUS: {snap['state']} | PROGRESS: [{self._progress_bar(snap['progress_percentage'])}] {snap['progress_percentage']}%")
            print("=" * 65)

            step_type = snap['step_type']
            if step_type == StepType.REST.value:
                print("\n   🍃 ISTIRAHAT & AMBIL NAFAS 🍃")
                print(f"   Sisa Waktu : ⏳ {snap['step_remaining_seconds']} detik")
                print(f"   Berikutnya : 👉 {snap['next_exercise']}")
            else:
                print(f"\n   💪 GERAKAN #{snap['step_index']}/{snap['total_steps']}: {snap['exercise_name'].upper()}")
                print(f"   Sisa Waktu : ⏳ {snap['step_remaining_seconds']} detik")
                print(f"   Kalori     : 🔥 {snap['calories_burned']} kkal")
                print(f"   Berikutnya : 👉 {snap['next_exercise']}")
                if snap['audio_cue']:
                    print(f"\n   🗣️ Voice Cue: \"{snap['audio_cue']}\"")
                print("\n   ♿ Deskripsi Panduan:")
                print(f"   \"{snap['accessible_description']}\"")

            print("\n" + "-" * 65)
            print(" KONTROL SESI (Ketik perintah lalu tekan Enter):")
            print(" [Enter] Lanjutkan timer 5 detik  |  [T] Maju 10 detik")
            print(" [P] Pause / Resume               |  [S] Lewati (Skip) step")
            print(" [B] Kembali ke step sebelumnya   |  [+] Tambah 10 detik")
            print(" [Q] Akhiri / Batalkan Workout")
            print("-" * 65)

            cmd = input("Perintah: ").strip().lower()

            if cmd == "p":
                if engine.state == SessionState.PAUSED:
                    engine.resume()
                else:
                    engine.pause()
            elif cmd == "s":
                engine.skip_step()
            elif cmd == "b":
                engine.previous_step()
            elif cmd == "+":
                engine.adjust_time(10)
            elif cmd == "t":
                engine.tick(delta_seconds=10)
            elif cmd == "q":
                confirm = input("⚠️ Apakah Anda yakin ingin membatalkan sesi workout ini? (y/N): ").strip().lower()
                if confirm == "y":
                    engine.abort(confirmed=True)
                    print("\nWorkout dibatalkan. Progres parsial telah dicatat.")
                    input("Tekan Enter untuk kembali...")
                    return
                else:
                    print("Pembatalan dibatalkan. Melanjutkan workout...")
            else:
                engine.tick(delta_seconds=5)

        # Finished Screen
        self.clear_screen()
        print("=" * 65)
        print("   🎉 WORKOUT SELESAI! KERJA BAGUS! 🔥")
        print("=" * 65)
        snap = engine.get_snapshot()
        print(f"   🏆 Routine        : {snap['routine_title']}")
        print(f"   ⏱️  Total Durasi   : {round(snap['total_elapsed_seconds'] / 60, 1)} Menit")
        print(f"   🔥 Total Kalori   : {snap['calories_burned']} kkal")
        print(f"   ✅ Latihan tuntas : {snap['total_steps']} dari {snap['total_steps']} gerakan")
        print("-" * 65)

        # HCI Post-Workout Feedback (User Request)
        print("\n 💬 BAGAIMANA KONDISI TUBUH ANDA SETELAH LATIHAN INI?")
        print(" [1] 🥵 Terlalu Berat / Sangat Lelah")
        print(" [2] 😮‍💨 Agak Berat tapi Mampu")
        print(" [3] 😊 Pas & Nyaman")
        print(" [4] ⚡ Terlalu Ringan / Kurang Berasa")
        print(" [S] ⏩ Lewati Sesi Feedback (Skip)")
        print("-" * 65)

        fb_choice = input("Pilihan respon tubuh (1-4 atau 'S' untuk lewati): ").strip().lower()
        fb_map = {
            "1": "TOO_HEAVY",
            "2": "SLIGHTLY_HEAVY",
            "3": "BALANCED",
            "4": "TOO_LIGHT"
        }

        if fb_choice in fb_map:
            rec = self.service.record_session_feedback(fb_map[fb_choice])
            print("\n" + "=" * 65)
            print(f" 📋 Umpan Balik: {rec['title']}")
            print(f" {rec['advice']}")
            print("=" * 65)
        else:
            print("\n Feedback dilewati. Data sesi tetap tersimpan ke riwayat.")

        input("\nTekan Enter untuk kembali ke Menu Utama...")

    def _progress_bar(self, percentage: float, length: int = 15) -> str:
        filled = int(length * (percentage / 100.0))
        return "█" * filled + "░" * (length - filled)


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--web' in args or '-w' in args:
        import run_web
        run_web.main()
    elif '--gui' in args or '-g' in args:
        import gui_app
        gui_app.main()
    elif '--cli' in args or '-c' in args:
        cli = WorkoutCLI()
        cli.run()
    else:
        print("=" * 65)
        print("   🏋️ FITPULSE - HOME WORKOUT COMPANION (HCI EDITION)")
        print("=" * 65)
        print(" Pilih antarmuka yang ingin Anda jalankan:")
        print(" [1] 🌐 Web Application (Responsif Mobile, Tablet & Desktop - Rekomendasi)")
        print(" [2] 🖥️ Desktop GUI (CustomTkinter)")
        print(" [3] ⌨️ Terminal Interactive CLI")
        print("-" * 65)
        choice = input("Pilihan (1/2/3, default [1]): ").strip()
        if choice == "2":
            import gui_app
            gui_app.main()
        elif choice == "3":
            cli = WorkoutCLI()
            cli.run()
        else:
            import run_web
            run_web.main()

