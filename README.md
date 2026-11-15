# 🏋️ FitPulse - Home Workout Companion (HCI Web & Multi-Platform Edition)

Aplikasi latihan fisik mandiri yang dirancang khusus untuk memenuhi standar mata kuliah **Interaksi Manusia dan Komputer (HCI / Human-Computer Interaction)**. Kini hadir dalam format **Web Application modern responsif** (didukung FastAPI, Tailwind CSS, Lucide icons, dan Web Audio API), serta tetap menyediakan antarmuka Desktop GUI (CustomTkinter) dan CLI interaktif.

---

## 🚀 Cara Menjalankan Aplikasi

### 1. 🌐 Web Application (Rekomendasi - Responsif Mobile, Tablet & Desktop)
```bash
# Cara tercepat:
python run_web.py

# Atau lewat main.py:
python main.py --web
```
Server web akan otomatis berjalan pada **`http://localhost:8000`** dan langsung membuka browser bawaan Anda.

> [!TIP]
> **Fitur Simulasi Device di Web:** Di pojok kanan atas terdapat tombol **"Mode Device"** yang memungkinkan penguji / dosen menguji tampilan dalam ukuran **📱 Mobile (420px)**, **📱 Tablet (768px)**, dan **💻 Desktop Penuh (Fluid)** langsung dalam satu browser!

### 2. 🖥️ Desktop GUI (CustomTkinter)
```bash
python main.py --gui
```

### 3. ⌨️ Terminal Interactive CLI
```bash
python main.py --cli
```

### 4. ☁️ Hosting & Cloud Database (GitHub + TiDB Cloud + Vercel)
Aplikasi ini sudah **100% siap deploy** ke cloud secara gratis!
- **Panduan Lengkap:** Baca [DEPLOY_GUIDE.md](file:///x:/campus/matkul/HCI/DEPLOY_GUIDE.md).
- **Database:** Mendukung TiDB Cloud Serverless (MySQL) otomatis via variabel `DATABASE_URL`.
- **Hosting Vercel:** Serverless API otomatis via `api/index.py` dan konfigurasi `vercel.json`.

### 5. 🧪 Menjalankan Unit Tests (21/21 Tests)
```bash
python -m unittest discover tests -v
```

---

## 📱 Keunggulan Web Edition (HCI & Usability Principles)

1. **Learnability Maksimal:**
   - **Hirarki Visual Jelas:** Elemen navigasi terstruktur dengan baik. Pada smartphone (<768px) tersedia *Bottom Navigation Bar* standar mobile OS, sedangkan pada tablet & desktop tersedia *Top Nav Bar*.
   - **Affordance & Signifier Terang:** Tombol aksi utama (Start, Selesai Repetisi, Panduan) memiliki kontras warna tinggi, ikon pendukung, dan label eksplisit.
   - **Panduan Gerakan 1:1 Terintegrasi:** Tombol **"📖 Panduan Gerakan"** dapat diakses kapan saja (baik saat browsing routine maupun saat workout aktif) untuk membuka modal lengkap berisi:
     - Foto ilustrasi 1:1.
     - **Diagram Anatomi Otot Tubuh (Tampak Depan & Belakang)** yang otomatis menyorot kelompok otot aktif dengan warna *electric blue*.
     - Daftar bernomor **Kesalahan Umum (*Common Mistakes*)** dengan mitigasi biomekanik cedera.
     - **Teknik Pernapasan (*Breathing Tips*)**.
     - Instruksi langkah demi langkah.

2. **Ultra-Responsive Multi-Device Layout:**
   - **Mobile (360px – 480px):** Tata letak satu kolom yang dioptimalkan untuk sentuhan satu tangan (*thumb zone*), tombol kontrol sesi workout diposisikan dengan aman sehingga **tidak akan pernah terpotong** oleh tinggi layar.
   - **Tablet (768px – 1024px):** Grid 2 kolom kartu latihan, kartu ringkasan biometrik seimbang.
   - **Desktop (1080px+):** Grid 3 kolom kartu latihan terpusat rapi dengan `max-w-6xl`, nyaman dipandang tanpa elemen yang terlalu renggang.

3. **Interaktivitas Real-Time & Web Audio API:**
   - Hitung mundur timer halus di browser tanpa lag jaringan.
   - Sintesis audio bawaan untuk hitung mundur (*beep* pada 3, 2, 1), nada mulai, dan akord perayaan kemenangan (*fanfare*).
   - Efek konfeti visual (*Canvas Confetti*) saat latihan berhasil dituntaskan.

4. **Laporan Konsistensi & Riwayat Latihan Lengkap:**
   - Kartu persentase **Konsistensi Penyelesaian Latihan** dengan indikator progress bar adaptif (hijau $\ge 70\%$, kuning $\ge 40\%$, merah $< 40\%$).
   - Riwayat latihan lengkap dengan tanggal, status badge (✅ Tuntas / ⚠️ Dibatalkan), durasi, dan kalori yang terbakar.
   - Kalkulator BMI interaktif dengan *gauge bar* warna standar WHO.

---

## 📑 Pemetaan Aspek Usability (Jakob Nielsen)

| No | Aspek Usability | Implementasi pada Backend / Logika | Lokasi Kode |
|---|---|---|---|
| 1 | **Learnability** *(Mudah dipelajari)* | Menu bernomor terstruktur, status state yang konsisten, instruksi gerakan yang dibagi per langkah, dan panduan cue suara. | [`main.py`](file:///x:/campus/matkul/HCI/main.py), [`data.py`](file:///x:/campus/matkul/HCI/homeworkout/data.py) |
| 2 | **Efficiency** *(Cepat & efisien)* | Fitur **`quick_start()`** untuk langsung memulai latihan 7-menit dalam 1 klik tanpa harus memilih dari awal; shortcut timer (+10s, skip). | [`service.py`](file:///x:/campus/matkul/HCI/homeworkout/service.py#L182-L191) |
| 3 | **Memorability** *(Mudah diingat)* | Preferensi pengguna (berat badan, durasi istirahat, mode aksesibilitas) tersimpan otomatis di JSON storage sehingga tidak perlu diatur ulang setiap sesi. | [`storage.py`](file:///x:/campus/matkul/HCI/homeworkout/storage.py), [`models.py`](file:///x:/campus/matkul/HCI/homeworkout/models.py) |
| 4 | **Errors** *(Toleransi & Pencegahan Kesalahan)* | Validasi input ketat (misal: berat badan harus rasional 20–300 kg), serta **Accidental Cancellation Protection** (membatalkan workout wajib ada konfirmasi eksplisit). | [`engine.py`](file:///x:/campus/matkul/HCI/homeworkout/engine.py#L210-L218), [`service.py`](file:///x:/campus/matkul/HCI/homeworkout/service.py#L30-L65) |
| 5 | **Satisfaction** *(Kepuasan Pengguna)* | Progress bar visual `[████████░░]`, umpan balik apresiasi saat workout tuntas, pelacak streak harian, dan statistik kalori terbakar. | [`main.py`](file:///x:/campus/matkul/HCI/main.py#L303-L318), [`storage.py`](file:///x:/campus/matkul/HCI/homeworkout/storage.py#L106-L148) |

---

## 🍯 Pemetaan 7 Prinsip UX (Peter Morville's Honeycomb)

1. **Useful (Bermanfaat):**
   * Menyediakan program latihan berbasis sains (*Scientific 7-Minute Workout*, *Abs & Core Sculptor*, *Leg Power*) dengan jeda waktu istirahat terukur.
2. **Usable (Mudah Digunakan):**
   * State machine yang prediktif: `IDLE` ➔ `RUNNING` ➔ `RESTING` ➔ `PAUSED` ➔ `COMPLETED`. Pengguna dapat melakukan jeda (pause), resume, lewati gerakan (skip), atau kembali ke gerakan sebelumnya (previous).
3. **Desirable (Menarik & Memikat):**
   * Antarmuka visual rapi dengan tema gelap (*Sport Dark Mode*), kartu beranimasi, audio cue countdown (*3, 2, 1, Go!*), dan fleksibilitas membuat *Custom Workout Routine* sendiri.
4. **Findable (Mudah Ditemukan):**
   * Fitur pencarian multi-kriteria: cari template berdasarkan kata kunci, otot target (*Full Body, Abs, Legs, Arms, Back*), dan **tingkat kesulitan** (*Beginner, Intermediate, Advanced*).
5. **Accessible (Inklusif & Ramah Disabilitas):**
   * Setiap gerakan dilengkapi teks deskripsi aksesibilitas untuk screen-reader / Tuna Netra ([`accessible_description`](file:///x:/campus/matkul/HCI/homeworkout/models.py#L56)), teks cue audio, dan pengaturan *High Contrast Mode*.
6. **Credible (Dapat Dipercaya):**
   * Penghitungan kalori menggunakan standar ilmiah kedokteran olahraga **ACSM (American College of Sports Medicine)** berbasis **MET (Metabolic Equivalent of Task)**:
     $$\text{Kalori/menit} = \frac{\text{MET} \times 3.5 \times \text{Berat Badan (kg)}}{200}$$
7. **Valuable (Bernilai Nyata & Habit Building):**
   * **Jadwal Rutin Mingguan (Senin - Minggu):** Terintegrasi tombol **"Create Template"** untuk menyusun rutinitas baru atau mengedit rutinitas yang ada.
   * **Adaptive Post-Workout Feedback:** Sesi umpan balik kondisi fisik adaptif di akhir latihan yang memberikan saran penyesuaian beban serta opsi lewati (*Skip*).

---

## ⚡ Pengaruh Tingkat Kesulitan (*Difficulty Engine*)

Tingkat kesulitan dirancang secara sistematis mempengaruhi **durasi per sesi**, **durasi istirahat**, **kuantitas gerakan**, dan **jenis gerakan**:

| Parameter | 🟢 **Beginner (Pemula)** | 🔵 **Intermediate (Menengah)** | 🔴 **Advanced (Lanjutan)** |
|---|---|---|---|
| **Durasi per Gerakan** | **20 detik** | **30 detik** | **45 detik** |
| **Durasi Istirahat** | **20 detik** *(pemulihan lebih santai)* | **15 detik** | **10 detik** *(intensitas tinggi)* |
| **Kuantitas Gerakan** | **4 – 5 gerakan** | **6 – 8 gerakan** | **8 – 10 gerakan** |
| **Karakter & Jenis Gerakan** | Ramah sendi, *low-impact* (Knee Push-ups, Wall Sit, Crunches, Bird Dog) | Gerakan beban tubuh standar (Push-ups, Walking Lunges, Plank, Russian Twists) | Eksplosif & plyometrics (Burpees, Jump Squats, Diamond Push-ups, Bicycle Crunches, Pike Push-ups) |
| **Contoh Template** | *Full Body Pemula*, *Perut Rata*, *Lengan Kencang*, *Koreksi Postur* | *7-Minute HIIT*, *Six-Pack Sculptor*, *Upper Body Push*, *Quad Power* | *Spartan Beast*, *Iron Core*, *Pike Arm Destroyer*, *Explosive Leg Blast* |

---

## 🛠️ Sistem Pembuatan & Pengeditan Template (*Template Builder*)

1. **Akses Cepat dari Jadwal Mingguan:**
   * Terdapat tombol **"➕ Buat / Edit Template (Create Template)"** langsung di halaman jadwal mingguan.
2. **Pilihan Mode Pembuatan:**
   * **🛠️ Custom dari Nol:** Mulai dengan formulir kosong dan tentukan sendiri seluruh gerakan serta durasinya.
   * **📋 Pilih Template Bawaan (Duplikat & Edit):** Muat salah satu template yang sudah ada (misal: *Six-Pack Sculptor* atau *7-Minute HIIT*) untuk dimodifikasi sebagian atau disesuaikan durasinya.
3. **Filter Fokus Otot:**
   * Filter gerakan berdasarkan kelompok otot spesifik: **Chest (Dada)**, **Legs (Kaki)**, **Abs & Core (Perut)**, **Arms (Lengan)**, **Back (Punggung)**, atau **Full Body**.
4. **Pengeditan Granular per Sesi Gerakan:**
   * Setiap gerakan memiliki tombol penyesuaian durasi cepat (`-5s` / `+5s`) dan input angka langsung, sehingga pengguna dapat mengedit durasi gerakan tertentu secara spesifik.

---

## 💬 Sesi Feedback Fisik Adaptif (*Post-Workout Feedback*)

Di akhir setiap sesi latihan, aplikasi menampilkan dialog evaluasi kondisi fisik:
* 🥵 **Terlalu Berat / Sangat Lelah:** Memberikan saran untuk menurunkan durasi gerakan 5–10 detik atau menambah waktu istirahat.
* 😮‍💨 **Agak Berat tapi Mampu:** Memberikan konfirmasi bahwa intensitas sudah ideal untuk stimulasi otot.
* 😊 **Pas & Nyaman:** Memberikan apresiasi atas kestabilan kebugaran dan dorongan konsistensi.
* ⚡ **Terlalu Ringan / Kurang Berasa:** Memberikan saran untuk menambah durasi (+10s), memotong waktu istirahat, atau beralih ke level lanjutan.
* ⏩ **Tombol Lewati (Skip):** Pengguna yang tidak ingin mengisi umpan balik dapat langsung melewati sesi ini menuju ringkasan/dashboard.

---

---

## 📱 Transformasi Fitur Mobile "Home Workout" (HCI Visual Edition)

Berdasarkan analisis *screen recording* aplikasi mobile "Home Workout", antarmuka [`gui_app.py`](file:///x:/campus/matkul/HCI/gui_app.py) telah ditingkatkan dengan fitur-fitur berikut:

1. **Struktur Navigasi Utama (Tanpa Fitur Discovery):**
   * Navigasi utama disederhanakan menjadi 3 pilar:
     * ⏱️ **Latihan (Training):** Hub utama berisi target mingguan (7-day strip), banner tantangan 28 hari, filter kategori fokus otot (*Body Focus*: Semua, Abs, Lengan, Dada, Kaki, Punggung, Full Body), dan kartu rutinitas latihan dengan thumbnail rasio 1:1.
     * 📊 **Laporan (Report):** Pelacak *Day Streak*, rekor pribadi, *Weight Tracker* (catat berat badan, terberat, teringan), dan kalkulator **BMI interaktif dengan gauge bar warna-warni** (Underweight, Normal, Overweight, Obese) serta pengatur tinggi badan.
     * ⚙️ **Pengaturan (Settings):** Personalisasi profil atlet (nama, berat, tinggi, fitness level), durasi istirahat bawaan, toggle audio cue & TTS, pintasan jadwal mingguan, dan template builder.

2. **Layar Tinjauan Rencana Gerakan (*Routine Overview Screen*):**
   * Menampilkan daftar gerakan dalam latihan dengan nomor urut, durasi/repetisi, dan thumbnail gambar 1:1.
   * **Interaksi Inti HCI:** Mengklik nama gerakan atau thumbnail manapun akan langsung membuka **Modal Detail Gerakan**.
   * Tersedia tombol **"✏️ Sesuaikan Rencana"** untuk menaikkan/menurunkan repetisi atau durasi tiap gerakan (`-` dan `+`).
   * Tombol biru besar **"▶ MULAI LATIHAN SEKARANG"** di bagian bawah.

3. **Modal Dialog Detail Gerakan (*Exercise Detail Modal*):**
   * **Area Foto 1:1:** Wadah visual berbentuk persegi (rasio 1:1) yang menampilkan foto gerakan. Dilengkapi tombol interaktif **"📷 Unggah / Ganti Foto Gerakan (Area 1:1)"** agar pengguna dapat memasukkan foto kustom kapan saja dari komputernya.
   * **Otot yang Dilatih & Diagram Anatomi:** Badge target otot disertai **diagram anatomi tubuh manusia (tampak depan & tampak belakang)** yang menyorot kelompok otot target dengan warna biru terang (*electric blue*).
   * **Kesalahan Umum (*Common Mistakes*):** Daftar bernomor berisi kesalahan-kesalahan umum gerakan, penjelasan biomekanika mengapa hal itu berbahaya, dan cara memperbaikinya.
   * **Panduan Pernapasan (*Breathing Tips*):** Petunjuk kapan harus menarik napas (*inhale*) dan membuang napas (*exhale*) untuk menjaga stabilitas postur tubuh.

4. **Layar Latihan Aktif (*Active Workout Screen*):**
   * **Area Foto 1:1 Pengganti Video:** Posisi video gerakan aplikasi Home Workout digantikan oleh area foto 1:1 yang menampilkan gambar gerakan secara jelas.
   * **Tombol Akses Form Cepat:** Terdapat tombol **"ℹ️ Panduan & Kesalahan"** di samping nama gerakan yang membuka Modal Detail Gerakan kapan saja tanpa menghilangkan status workout.
   * **Dukungan Berbasis Durasi & Repetisi:**
     * Latihan durasi: Timer digital besar, kontrol Previous, Pause/Resume, Next, dan shortcut `+10s`.
     * Latihan repetisi: Penghitung repetisi besar (`×12`) dan tombol centang besar **"✓ SELESAI REPETISI"** untuk lanjut ke gerakan berikutnya.
   * **Layar Istirahat (*Rest Screen*):** Menampilkan preview foto 1:1 gerakan berikutnya, countdown istirahat, tombol `+20 Detik`, dan tombol `LEWATI ISTIRAHAT ▶`.
   * **Toleransi Kesalahan:** Konfirmasi dialog jika pengguna menekan tombol kembali atau selesai lebih awal untuk mencegah ketidaksengajaan kehilangan progres.

---

## 📁 Struktur Proyek

```text
x:\campus\matkul\HCI\
├── homeworkout\
│   ├── __init__.py      # Package export
│   ├── models.py        # Model data (Exercise, WorkoutRoutine, UserProfile, WorkoutLog, Schedules)
│   ├── data.py          # Katalog latihan bawaan & template program multi-tier
│   ├── storage.py       # Persistence layer (JSON storage, riwayat, schedule, feedback)
│   ├── engine.py        # State machine & controller sesi latihan (Timer & MET Calorie)
│   ├── anatomy.py       # Generator diagram visual anatomi tubuh (Tampak Depan & Belakang)
│   └── service.py       # Facade API pusat (Search, Builder, Scheduler, Adaptive Feedback)
├── tests\
│   └── test_workout.py  # Unit testing otomatis (12 skenario pengujian)
├── workout_data\        # Direktori persistensi JSON & aset foto
│   ├── exercises.json   # 22 katalog latihan lengkap dengan focus_areas, common_mistakes, breathing
│   ├── routines.json    # 14 template latihan multi-tier
│   ├── images\          # Penyimpanan foto 1:1 untuk setiap gerakan
│   └── ...
├── gui_app.py           # GUI Desktop Modern (CustomTkinter) versi Home Workout Edition
├── main.py              # CLI Runner interaktif untuk uji coba terminal
└── README.md            # Dokumentasi & panduan laporan HCI
```

---

## 🚀 Cara Menjalankan

### 1. Menjalankan Versi Modern GUI Desktop (Rekomendasi Utama)
Buka PowerShell atau terminal di folder `x:\campus\matkul\HCI\` lalu jalankan:
```powershell
python gui_app.py
```
*Antarmuka visual modern (Dark Mode sporty) berbasis CustomTkinter akan muncul lengkap dengan timer animasi, navigasi sidebar, Fitts's Law button layout, form builder, dan audio cue countdown.*

### 2. Menjalankan Versi CLI Terminal (Console Mode)
Jika ingin menguji lewat teks murni di terminal PowerShell:
```powershell
python main.py
```

### 3. Menjalankan Unit Testing Otomatis
Untuk memvalidasi logika, state machine, dan validasi error:
```powershell
python -m unittest discover tests
```
*(Hasil: `Ran 8 tests ... OK`)*

---

## 🎨 Langkah Selanjutnya (Pengembangan UI)
Arsitektur backend ini sepenuhnya terpisah (*decoupled*) dari UI melalui fungsi callback pada [`WorkoutEngine`](file:///x:/campus/matkul/HCI/homeworkout/engine.py):
* `on_tick_callbacks`
* `on_step_change_callbacks`
* `on_state_change_callbacks`
* `on_audio_cue_callbacks`
* `on_complete_callbacks`

Ketika nanti ingin membuat UI visual (misalnya menggunakan **CustomTkinter/PyQt** untuk GUI Desktop, atau **Flask/FastAPI + HTML/CSS modern** untuk Web), Anda cukup menghubungkan antarmuka tersebut ke [`WorkoutAppService`](file:///x:/campus/matkul/HCI/homeworkout/service.py) tanpa perlu mengubah logika backend yang sudah ada.
