"""
FitPulse Web App Launcher.
Starts the FastAPI web server on http://localhost:8000 and automatically opens the browser.
"""

import sys
import time
import webbrowser
import threading
import uvicorn


def open_browser():
    time.sleep(1.2)
    url = "http://localhost:8000"
    print(f"\n🚀 Membuka FitPulse Web App di browser: {url}")
    webbrowser.open(url)


def main():
    print("=" * 68)
    print("   ⚡ FITPULSE - HOME WORKOUT COMPANION (WEB EDITION)")
    print("   HCI Usability & Responsive Multi-Device Edition")
    print("=" * 68)
    print("   🌐 Server berjalan di: http://localhost:8000")
    print("   📱 Responsif: Mobile (420px), Tablet (768px), Desktop (1080px+)")
    print("   📖 Fitur: Panduan Gerakan 1:1, Anatomi Otot, Kesalahan Umum,")
    print("             Laporan Konsistensi, Riwayat Latihan, Jadwal Mingguan")
    print("   Tekan Ctrl+C untuk menghentikan server.")
    print("=" * 68)

    # Launch browser in separate thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Uvicorn server with auto-reload enabled
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    main()

