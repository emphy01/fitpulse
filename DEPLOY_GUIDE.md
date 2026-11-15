# 🚀 Panduan Lengkap Hosting FitPulse: GitHub + TiDB Cloud + Vercel

Panduan ini memandu Anda langkah demi langkah untuk menghosting **FitPulse** secara online secara **100% Gratis** menggunakan arsitektur modern:
- **Database Cloud**: [TiDB Cloud Serverless](https://tidbcloud.com/) (MySQL-compatible, gratis selamanya, otomatis autoscaling).
- **Frontend & Serverless Backend**: [Vercel](https://vercel.com/) (FastAPI via `@vercel/python` + Single Page Application di Edge CDN).
- **Source Code Repository**: [GitHub](https://github.com/).

---

## 📑 Daftar Isi
1. [Langkah 1: Membuat Database di TiDB Cloud](#langkah-1-membuat-database-di-tidb-cloud)
2. [Langkah 2: Menyiapkan Repository GitHub](#langkah-2-menyiapkan-repository-github)
3. [Langkah 3: Deploy Project ke Vercel](#langkah-3-deploy-project-ke-vercel)
4. [Langkah 4: Verifikasi & Pengujian](#langkah-4-verifikasi--pengujian)
5. [Struktur File Deployment](#struktur-file-deployment)
6. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Langkah 1: Membuat Database di TiDB Cloud

TiDB Cloud Serverless menyediakan kuota gratis tanpa batas waktu (Free Forever) dengan kapasitas storage hingga 5 GiB dan 50 juta Request Unit per bulan.

1. Buka [https://tidbcloud.com/](https://tidbcloud.com/) dan login (bisa menggunakan akun GitHub atau Google).
2. Di dashboard TiDB Cloud, klik tombol **Create Cluster**.
3. Pilih opsi **Serverless** (gratis / $0).
4. Pilih Region terdekat, disarankan:
   - **AWS / Singapore (`ap-southeast-1`)** untuk akses cepat dengan latensi rendah dari Indonesia.
5. Beri nama cluster (misalnya: `fitpulse-db`), lalu klik **Create**.
6. Setelah cluster siap (sekitar 10–20 detik), Anda akan melihat popup informasi koneksi:
   - Buat/Salin **Root Password** yang diberikan. Simpan password ini baik-baik!
7. Klik tab **Connect** di pojok kanan atas:
   - Pilih bahasa / driver: **Python** atau **PyMySQL**.
   - Anda akan mendapatkan connection string dengan format:
     ```text
     mysql+pymysql://<user>:<password>@<host>:4000/<database>?ssl_verify_cert=true
     ```
   - Contoh nyata:
     ```text
     mysql+pymysql://3y7AbcDef.root:Rahasia12345@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test?ssl_verify_cert=true
     ```
   - *Tips:* Anda bisa mengganti nama database default `/test` menjadi `/fitpulse` (FitPulse akan otomatis membuat seluruh tabel saat aplikasi dijalankan pertama kali).

---

## Langkah 2: Menyiapkan Repository GitHub

Pastikan seluruh file project sudah siap dan file besar (seperti video `.mp4` 56MB) serta database lokal tidak ikut ter-upload. FitPulse sudah dilengkapi file `.gitignore` standar.

1. Buka terminal PowerShell di folder project (`x:\campus\matkul\HCI`):
   ```powershell
   # Inisialisasi git jika belum
   git init

   # Cek file yang akan di-commit (pastikan file .mp4 dan fitpulse.db tidak muncul)
   git status
   ```

2. Tambahkan semua file dan buat commit pertama:
   ```powershell
   git add .
   git commit -m "Siap deploy ke Vercel dan TiDB Cloud"
   git branch -M main
   ```

3. Buat repository baru di [GitHub](https://github.com/new):
   - Beri nama repository, misalnya: `fitpulse-app`.
   - Pilih jenis: **Public** atau **Private**.
   - *Jangan centang "Add a README file"* karena project Anda sudah memilikinya.
   - Klik **Create repository**.

4. Hubungkan remote repository GitHub dan push kode Anda:
   ```powershell
   git remote add origin https://github.com/<username-github-anda>/fitpulse-app.git
   git push -u origin main
   ```

---

## Langkah 3: Deploy Project ke Vercel

1. Buka [https://vercel.com/](https://vercel.com/) dan login menggunakan akun GitHub Anda.
2. Di dashboard Vercel, klik tombol **Add New...** -> **Project**.
3. Cari repository `fitpulse-app` yang baru saja Anda push, lalu klik **Import**.
4. Di halaman konfigurasi proyek:
   - **Framework Preset**: Biarkan `Other` (Vercel otomatis membaca konfigurasi `vercel.json`).
   - **Root Directory**: `./` (default).
5. Buka bagian **Environment Variables** dan tambahkan 2 variabel berikut:
   
   | Key | Value | Keterangan |
   | :--- | :--- | :--- |
   | `DATABASE_URL` | `mysql+pymysql://<user>:<password>@<host>:4000/fitpulse?ssl_verify_cert=true` | Connection string TiDB Cloud Anda |
   | `JWT_SECRET` | `string-acak-rahasia-minimal-32-karakter-contoh-1234567890` | Kunci keamanan token login |

6. Klik tombol **Deploy**.
7. Tunggu proses build selesai (sekitar 1–2 menit).
8. Vercel akan menampilkan ucapan selamat dan memberikan URL live Anda, misalnya:  
   `https://fitpulse-app.vercel.app` 🎉

---

## Langkah 4: Verifikasi & Pengujian

### 1. Cek Diagnostik Database
Buka URL aplikasi Anda ditambah `/api/health`, contoh:
`https://fitpulse-app.vercel.app/api/health`

Respon yang benar menandakan TiDB Cloud berhasil terhubung:
```json
{
  "status": "ok",
  "database_engine": "mysql",
  "database_status": "connected",
  "server_time": "2026-11-13T..."
}
```

### 2. Uji Fitur Registrasi & Login
1. Buka halaman utama web FitPulse.
2. Klik tombol **Masuk / Daftar** di kanan atas.
3. Pilih tab **Daftar Akun Baru**, masukkan Nama, Username unik, Email, dan Password.
4. Klik **Daftar Akun Baru**.
5. Setelah berhasil:
   - Header akan menampilkan nama Anda dan ikon profil `👤 [Nama]`.
   - Di tab **Pengaturan**, badge status akun akan berwarna hijau: **Terhubung Cloud**.
   - Atur jadwal mingguan, ubah profil, atau selesaikan sesi latihan. Semua data Anda kini tersimpan aman di TiDB Cloud dan tidak akan hilang meski Anda membersihkan cache browser!

---

## Struktur File Deployment

Proyek ini telah dikonfigurasi secara presisi untuk hosting Vercel & TiDB Cloud:

```text
├── api/
│   └── index.py            # Entry point Serverless Function (@vercel/python)
├── vercel.json             # Konfigurasi routing static files & API endpoint Vercel
├── web_app.py              # Backend FastAPI dengan dukungan multi-user & TiDB Cloud
├── web/
│   ├── index.html          # Frontend SPA (Single Page Application)
│   └── app.js              # State manager, logic latihan, auth interactor, dan timer
├── homeworkout/
│   ├── database.py         # SQLAlchemy 2.0 Engine & Schema (TiDB Cloud MySQL + SQLite fallback)
│   ├── auth.py             # Enkripsi bcrypt, verifikasi token JWT & session validator
│   ├── storage.py          # Data mapper multi-user ke database
│   └── service.py          # Business logic latihan, jadwal, dan progres pengguna
├── workout_data/
│   ├── images/             # Ilustrasi gerakan latihan (1:1 aspect ratio)
│   │   ├── icons/          # Ikon gerakan & status
│   │   └── covers/         # Cover program latihan
│   ├── exercises.json      # Katalog gerakan & target otot
│   └── routines.json       # Katalog program latihan bawaan
├── requirements.txt        # Dependencies Python untuk Vercel
├── .gitignore              # Memastikan file database lokal & video 56MB tidak ter-upload
└── .env.example            # Template konfigurasi environment variable
```

---

## Troubleshooting & FAQ

### Tanya: Bagaimana jika saya tidak mengatur `DATABASE_URL` di Vercel?
**Jawab:** Jika `DATABASE_URL` tidak diisi, FitPulse akan mencoba menggunakan database lokal SQLite. Namun, pada environment serverless Vercel, filesystem bersifat *read-only* atau *ephemeral* (reset setiap cold-start). Oleh karena itu, sangat disarankan menggunakan **TiDB Cloud** agar data login dan riwayat latihan tersimpan permanen.

### Tanya: Apakah aplikasi desktop offline (`gui_app.py`) masih bisa dipakai?
**Jawab:** Ya, 100% tetap bisa dipakai! FitPulse mendukung mode hybrid:
- Jika tidak ada koneksi TiDB Cloud, aplikasi otomatis menggunakan database lokal `workout_data/fitpulse.db`.
- Aplikasi desktop GUI `gui_app.py` dan mode tamu di web tetap berjalan lancar tanpa memerlukan koneksi internet.

### Tanya: Bagaimana cara menjalankan lokal dengan koneksi TiDB Cloud?
**Jawab:**
1. Salin `.env.example` menjadi `.env`.
2. Isi nilai `DATABASE_URL` dengan connection string TiDB Cloud Anda.
3. Jalankan server lokal:
   ```powershell
   python run_web.py
   ```
4. Buka `http://localhost:8000` di browser Anda.

