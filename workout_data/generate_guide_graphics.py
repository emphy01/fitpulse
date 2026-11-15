import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Font definitions
FONT_BOLD_PATH = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_REG_PATH = r'C:\Windows\Fonts\segoeui.ttf'

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_badge(draw, text, xy, font, bg_color, text_color, pad_x=14, pad_y=5, radius=999):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x, y = xy
    rect = [x, y, x + tw + pad_x * 2, y + th + pad_y * 2]
    draw.rounded_rectangle(rect, radius=radius, fill=bg_color)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=text_color)
    return rect[2], rect[3]

def draw_pin(draw, number_str, xy, size=32, bg_color=(2, 132, 199), text_color=(255, 255, 255)):
    x, y = xy
    r = size // 2
    # Outer glow
    draw.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=(14, 165, 233, 120), outline=(56, 189, 248), width=2)
    draw.ellipse([x - r, y - r, x + r, y + r], fill=bg_color)
    font = get_font(FONT_BOLD_PATH, size - 12)
    bbox = font.getbbox(number_str)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw // 2 - bbox[0], y - th // 2 - bbox[1]), number_str, font=font, fill=text_color)

def round_corners(im, radius):
    mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, im.size[0], im.size[1]], radius=radius, fill=255)
    result = im.copy()
    result.putalpha(mask)
    return result

def create_window_mockup(inner_im, title="FitPulse Home Workout", width=1280, height=720, corner_radius=16):
    inner_resized = inner_im.resize((width, height - 38), Image.Resampling.LANCZOS)
    win = Image.new('RGBA', (width, height), (15, 23, 42, 255))
    draw = ImageDraw.Draw(win)

    # Titlebar background
    draw.rounded_rectangle([0, 0, width, height], radius=corner_radius, fill=(15, 23, 42, 255))
    draw.rectangle([0, 24, width, height], fill=(2, 6, 23, 255))

    # Window dots
    draw.ellipse([16, 12, 26, 22], fill=(239, 68, 68)) # red
    draw.ellipse([34, 12, 44, 22], fill=(245, 158, 11)) # yellow
    draw.ellipse([52, 12, 62, 22], fill=(34, 197, 94)) # green

    # Title / URL bar
    url_box = [80, 7, width - 24, 30]
    draw.rounded_rectangle(url_box, radius=6, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255), width=1)
    title_font = get_font(FONT_REG_PATH, 12)
    draw.text((92, 11), title, font=title_font, fill=(148, 163, 184))

    # Screen with bottom corners rounded
    screen_im = round_corners(inner_resized.convert('RGBA'), corner_radius - 4)
    win.paste(screen_im, (0, 38), screen_im)

    # Outer border
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=corner_radius, outline=(71, 85, 105, 255), width=2)
    return win

def create_phone_mockup(inner_im, width=440, height=920, corner_radius=36):
    inner_resized = inner_im.resize((width - 16, height - 28), Image.Resampling.LANCZOS)
    phone = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(phone)

    # Phone chassis
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=corner_radius, fill=(15, 23, 42, 255), outline=(71, 85, 105, 255), width=2)
    draw.rounded_rectangle([6, 6, width - 7, height - 7], radius=corner_radius - 6, fill=(2, 6, 23, 255))

    # Screen with rounded corners
    screen_im = round_corners(inner_resized.convert('RGBA'), corner_radius - 12)
    phone.paste(screen_im, (8, 14), screen_im)

    # Dynamic Island / Notch
    notch_w = 110
    notch_h = 18
    notch_x = (width - notch_w) // 2
    draw.rounded_rectangle([notch_x, 18, notch_x + notch_w, 18 + notch_h], radius=9, fill=(0, 0, 0, 240))
    draw.ellipse([notch_x + notch_w - 24, 22, notch_x + notch_w - 14, 32], fill=(20, 30, 50))

    return phone

def draw_card(draw, xy, size, num_str, title, desc, tag="FITUR", accent=(2, 132, 199)):
    x, y = xy
    w, h = size
    # Card background (dark glassmorphism)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=(15, 23, 42, 240), outline=(51, 65, 85, 255), width=1)
    
    # Left accent bar
    draw.rounded_rectangle([x, y + 8, x + 4, y + h - 8], radius=2, fill=accent)

    # Number Pin Badge
    pin_r = 14
    px = x + 26
    py = y + 26
    draw.ellipse([px - pin_r, py - pin_r, px + pin_r, py + pin_r], fill=accent)
    pfont = get_font(FONT_BOLD_PATH, 14)
    bbox = pfont.getbbox(num_str)
    pw = bbox[2] - bbox[0]
    ph = bbox[3] - bbox[1]
    draw.text((px - pw // 2 - bbox[0], py - ph // 2 - bbox[1]), num_str, font=pfont, fill=(255, 255, 255))

    # Tag Badge
    tag_font = get_font(FONT_BOLD_PATH, 10)
    draw_badge(draw, tag, (x + 50, y + 16), tag_font, (30, 41, 59), (148, 163, 184), pad_x=8, pad_y=2, radius=4)

    # Title
    tfont = get_font(FONT_BOLD_PATH, 15)
    draw.text((x + 18, y + 50), title, font=tfont, fill=(241, 245, 249))

    # Description (wrapped)
    dfont = get_font(FONT_REG_PATH, 12)
    words = desc.split(' ')
    lines = []
    cur_line = []
    for w_word in words:
        test_line = ' '.join(cur_line + [w_word])
        w_box = dfont.getbbox(test_line)
        if (w_box[2] - w_box[0]) < (w - 36):
            cur_line.append(w_word)
        else:
            lines.append(' '.join(cur_line))
            cur_line = [w_word]
    if cur_line:
        lines.append(' '.join(cur_line))

    dy = y + 76
    for line in lines[:3]:
        draw.text((x + 18, dy), line, font=dfont, fill=(148, 163, 184))
        dy += 18

def build_all():
    os.makedirs('workout_data/images', exist_ok=True)

    # 1. Mobile Guide 1
    raw_home = Image.open('workout_data/guide_raw/mobile_home.png')
    c1 = Image.new('RGB', (828, 1470), (2, 6, 23))
    d1 = ImageDraw.Draw(c1)
    for y in range(1470):
        factor = min(1.0, y / 1470)
        d1.line([(0, y), (828, y)], fill=(int(2 + factor * 8), int(6 + factor * 14), int(23 + factor * 25)))

    draw_badge(d1, '⚡ FITPULSE MOBILE GUIDE', (30, 24), get_font(FONT_BOLD_PATH, 11), (12, 74, 110), (56, 189, 248), pad_x=12, pad_y=4)
    d1.text((30, 56), 'LANGKAH 1/2: NAVIGASI & BERANDA', font=get_font(FONT_BOLD_PATH, 25), fill=(255, 255, 255))
    d1.text((30, 96), 'Akses cepat jadwal mingguan, target latihan, dan filter kategori otot', font=get_font(FONT_REG_PATH, 14), fill=(148, 163, 184))
    draw_badge(d1, '1 / 2', (740, 36), get_font(FONT_BOLD_PATH, 12), (30, 41, 59), (226, 232, 240), pad_x=12, pad_y=4)

    phone1 = create_phone_mockup(raw_home, width=440, height=910)
    p1x = (828 - 440) // 2
    p1y = 135
    c1.paste(phone1, (p1x, p1y), phone1)

    # Highlight box around Muscle Category Pills on mobile
    d1.rounded_rectangle([p1x + 28, p1y + 492, p1x + 416, p1y + 532], radius=10, outline=(16, 185, 129), width=2)
    draw_badge(d1, 'KATEGORI OTOT', (p1x + 36, p1y + 476), get_font(FONT_BOLD_PATH, 8), (16, 185, 129), (255, 255, 255), pad_x=5, pad_y=2, radius=4)

    # Pins
    draw_pin(d1, '1', (p1x + 360, p1y + 55), size=30, bg_color=(2, 132, 199))
    draw_pin(d1, '2', (p1x + 90, p1y + 160), size=30, bg_color=(14, 165, 233))
    draw_pin(d1, '4', (p1x + 90, p1y + 310), size=30, bg_color=(245, 158, 11))
    draw_pin(d1, '3', (p1x + 24, p1y + 512), size=32, bg_color=(16, 185, 129))
    draw_pin(d1, '5', (p1x + 220, p1y + 865), size=30, bg_color=(168, 85, 247))

    draw_card(d1, (30, 1065), (374, 175), '1', 'Profil & Streak Harian', 'Pantau hari beruntun, berat badan, serta status sinkronisasi akun pengguna aktif.', tag='AKUN', accent=(2, 132, 199))
    draw_card(d1, (424, 1065), (374, 175), '2', 'Jadwal & Buat Kustom', 'Atur hari latihan vs rehat mingguan, atau rancang urutan gerakan kustom sendiri.', tag='JADWAL', accent=(14, 165, 233))
    draw_card(d1, (30, 1260), (374, 175), '3', 'Kategori Target Otot', 'Saring latihan spesifik: Full Body, Dada (Chest), Perut (Abs), Lengan, Kaki, Punggung.', tag='KATEGORI', accent=(16, 185, 129))
    draw_card(d1, (424, 1260), (374, 175), '4', 'Target & Navigasi Bawah', 'Cek progres target mingguan, tantangan 28 hari, dan akses cepat menu Laporan.', tag='TARGET', accent=(245, 158, 11))
    c1.save('workout_data/images/panduan_mobile_1.png', 'PNG', optimize=True)

    # 2. Mobile Guide 2
    raw_workout = Image.open('workout_data/guide_raw/mobile_workout.png')
    raw_report = Image.open('workout_data/guide_raw/mobile_report.png')
    c2 = Image.new('RGB', (828, 1470), (2, 6, 23))
    d2 = ImageDraw.Draw(c2)
    for y in range(1470):
        factor = min(1.0, y / 1470)
        d2.line([(0, y), (828, y)], fill=(int(2 + factor * 8), int(6 + factor * 14), int(23 + factor * 25)))

    draw_badge(d2, '⚡ FITPULSE MOBILE GUIDE', (30, 24), get_font(FONT_BOLD_PATH, 11), (12, 74, 110), (56, 189, 248), pad_x=12, pad_y=4)
    d2.text((30, 56), 'LANGKAH 2/2: SESI LATIHAN & EVALUASI', font=get_font(FONT_BOLD_PATH, 25), fill=(255, 255, 255))
    d2.text((30, 96), 'Latihan dipandu timer audio visual & pantau ringkasan performa kebugaran', font=get_font(FONT_REG_PATH, 14), fill=(148, 163, 184))
    draw_badge(d2, '2 / 2', (740, 36), get_font(FONT_BOLD_PATH, 12), (30, 41, 59), (226, 232, 240), pad_x=12, pad_y=4)

    phone_w, phone_h = 384, 880
    p2y = 140
    p_left = create_phone_mockup(raw_workout, width=phone_w, height=phone_h)
    lx = 24
    c2.paste(p_left, (lx, p2y), p_left)

    p_right = create_phone_mockup(raw_report, width=phone_w, height=phone_h)
    rx = 420
    c2.paste(p_right, (rx, p2y), p_right)

    draw_badge(d2, 'STUDIO LATIHAN AKTIF', (lx + 10, p2y - 18), get_font(FONT_BOLD_PATH, 10), (15, 23, 42), (56, 189, 248), pad_x=8, pad_y=2, radius=4)
    draw_badge(d2, 'DASHBOARD LAPORAN', (rx + 10, p2y - 18), get_font(FONT_BOLD_PATH, 10), (15, 23, 42), (16, 185, 129), pad_x=8, pad_y=2, radius=4)

    draw_pin(d2, '1', (lx + 192, p2y + 180), size=30, bg_color=(2, 132, 199))
    draw_pin(d2, '2', (lx + 192, p2y + 520), size=30, bg_color=(245, 158, 11))
    draw_pin(d2, '3', (lx + 192, p2y + 780), size=30, bg_color=(16, 185, 129))
    draw_pin(d2, '4', (rx + 192, p2y + 260), size=30, bg_color=(168, 85, 247))

    draw_card(d2, (30, 1060), (374, 180), '1', 'Visual Panduan Gerakan', 'GIF gerakan interaktif atau ilustrasi posisi statis (Plank) dengan panduan form tubuh.', tag='VISUAL', accent=(2, 132, 199))
    draw_card(d2, (424, 1060), (374, 180), '2', 'Smart Timer & Audio Cues', 'Hitung mundur otomatis dengan panduan suara synthesizer & jeda hidrasi rehat.', tag='TIMER', accent=(245, 158, 11))
    draw_card(d2, (30, 1255), (374, 180), '3', 'Kendali Tempo Bebas', 'Tombol Jeda, Lanjut, Lewati, serta penyesuaian durasi waktu sesuai kemampuan fisik.', tag='KONTROL', accent=(16, 185, 129))
    draw_card(d2, (424, 1255), (374, 180), '4', 'Laporan & Riwayat Sesi', 'Rekam otomatis total durasi, repetisi gerakan, dan riwayat evaluasi di perangkat Anda.', tag='EVALUASI', accent=(168, 85, 247))
    c2.save('workout_data/images/panduan_mobile_2.png', 'PNG', optimize=True)

    # 3. Desktop Guide 1
    raw_desk_home = Image.open('workout_data/guide_raw/desktop_home.png')
    c3 = Image.new('RGB', (1920, 1080), (2, 6, 23))
    d3 = ImageDraw.Draw(c3)
    for y in range(1080):
        factor = min(1.0, y / 1080)
        d3.line([(0, y), (1920, y)], fill=(int(2 + factor * 8), int(6 + factor * 14), int(23 + factor * 25)))

    draw_badge(d3, '⚡ FITPULSE DESKTOP EXPERIENCE', (50, 24), get_font(FONT_BOLD_PATH, 11), (12, 74, 110), (56, 189, 248), pad_x=14, pad_y=4)
    d3.text((50, 56), 'LANGKAH 1/2: EKSPLORASI PROGRAM & JADWAL MINGGUAN', font=get_font(FONT_BOLD_PATH, 27), fill=(255, 255, 255))
    d3.text((50, 96), 'Pusat kendali kebugaran layar lebar: navigasi intuitif, target mingguan, dan perancangan sesi kustom', font=get_font(FONT_REG_PATH, 15), fill=(148, 163, 184))
    draw_badge(d3, '1 / 2', (1820, 36), get_font(FONT_BOLD_PATH, 13), (30, 41, 59), (226, 232, 240), pad_x=14, pad_y=4)

    win1 = create_window_mockup(raw_desk_home, title='FitPulse App — Beranda & Jadwal (https://fitpulse.app)', width=1270, height=890)
    w1x, w1y = 50, 140
    c3.paste(win1, (w1x, w1y), win1)

    # Glowing highlight box around Muscle Filter Pills ([Semua], [Full Body], [Dada], [Perut], etc.)
    d3.rounded_rectangle([256, 630, 848, 696], radius=12, outline=(16, 185, 129), width=2)
    draw_badge(d3, 'FILTER KATEGORI OTOT AKTIF', (264, 614), get_font(FONT_BOLD_PATH, 9), (16, 185, 129), (255, 255, 255), pad_x=6, pad_y=2, radius=4)

    # Pin 1: Header / Profil Pengguna & Streak
    draw_pin(d3, '1', (1040, 215), size=34, bg_color=(2, 132, 199))

    # Pin 2: Tombol Jadwal Mingguan & Buat Kustom
    draw_pin(d3, '2', (348, 315), size=34, bg_color=(14, 165, 233))

    # Pin 4: Target Latihan Mingguan & Tantangan 28 Hari
    draw_pin(d3, '4', (348, 430), size=34, bg_color=(245, 158, 11))

    # Pin 3: Filter Kategori Otot (Tepat di baris tombol kategori otot)
    draw_pin(d3, '3', (240, 663), size=36, bg_color=(16, 185, 129))

    cx = 1350
    cw = 520
    ch = 205
    draw_card(d3, (cx, 140), (cw, ch), '1', 'Profil Pengguna & Status Harian', 'Pantau streak latihan beruntun, berat badan, serta status sinkronisasi akun. Tetap login otomatis tanpa repot memasukkan kredensial berulang kali.', tag='AKUN & PROFIL', accent=(2, 132, 199))
    draw_card(d3, (cx, 368), (cw, ch), '2', 'Manajemen Jadwal & Latihan Kustom', 'Atur pembagian hari aktif vs istirahat secara visual, atau buat program latihan kustom sendiri dengan memilih kombinasi gerakan dan durasi yang Anda inginkan.', tag='JADWAL MINGGUAN', accent=(14, 165, 233))
    draw_card(d3, (cx, 596), (cw, ch), '3', 'Filter Kategori Otot Seketika', 'Saring latihan spesifik dengan satu klik: Full Body, Dada (Chest), Perut (Abs), Lengan (Arms), Kaki (Legs), atau Punggung (Back).', tag='TARGET OTOT', accent=(16, 185, 129))
    draw_card(d3, (cx, 824), (cw, ch), '4', 'Target Mingguan & Program Sains', 'Pantau kepatuhan target mingguan (contoh: 0/5 hari) dan langsung mulai program terkurasi seperti Tantangan 28 Hari Transformasi Tubuh atau 7-Min Scientific Workout.', tag='PROGRAM UNGGULAN', accent=(245, 158, 11))
    c3.save('workout_data/images/panduan1.png', 'PNG', optimize=True)

    # 4. Desktop Guide 2
    raw_desk_workout = Image.open('workout_data/guide_raw/desktop_workout.png')
    raw_desk_report = Image.open('workout_data/guide_raw/desktop_report.png')
    c4 = Image.new('RGB', (1920, 1080), (2, 6, 23))
    d4 = ImageDraw.Draw(c4)
    for y in range(1080):
        factor = min(1.0, y / 1080)
        d4.line([(0, y), (1920, y)], fill=(int(2 + factor * 8), int(6 + factor * 14), int(23 + factor * 25)))

    draw_badge(d4, '⚡ FITPULSE WORKOUT STUDIO & ANALYTICS', (50, 24), get_font(FONT_BOLD_PATH, 11), (12, 74, 110), (56, 189, 248), pad_x=14, pad_y=4)
    d4.text((50, 56), 'LANGKAH 2/2: STUDIO LATIHAN & ANALITIK LENGKAP', font=get_font(FONT_BOLD_PATH, 27), fill=(255, 255, 255))
    d4.text((50, 96), 'Eksekusi sesi latihan interaktif dipandu timer audio visual & pantau evaluasi perkembangan kebugaran terperinci', font=get_font(FONT_REG_PATH, 15), fill=(148, 163, 184))
    draw_badge(d4, '2 / 2', (1820, 36), get_font(FONT_BOLD_PATH, 13), (30, 41, 59), (226, 232, 240), pad_x=14, pad_y=4)

    win2_1 = create_window_mockup(raw_desk_workout, title='FitPulse Runner — 7-Min Scientific Workout (Aktif)', width=950, height=640)
    win2_2 = create_window_mockup(raw_desk_report, title='FitPulse Laporan — Analitik & Riwayat Aktivitas', width=865, height=640)

    w2_1x, w2_1y = 50, 140
    w2_2x, w2_2y = 1005, 140

    c4.paste(win2_1, (w2_1x, w2_1y), win2_1)
    c4.paste(win2_2, (w2_2x, w2_2y), win2_2)

    draw_pin(d4, '1', (w2_1x + 230, w2_1y + 260), size=34, bg_color=(2, 132, 199))
    draw_pin(d4, '2', (w2_1x + 680, w2_1y + 260), size=34, bg_color=(245, 158, 11))
    draw_pin(d4, '3', (w2_1x + 475, w2_1y + 575), size=34, bg_color=(16, 185, 129))
    draw_pin(d4, '4', (w2_2x + 430, w2_2y + 260), size=34, bg_color=(168, 85, 247))

    cy = 805
    ch = 240
    draw_card(d4, (50, cy), (445, ch), '1', 'Panduan Visual & Posisi Statis', 'Animasi GIF ritmis memandu repetisi dinamis. Gerakan statis (seperti Plank) otomatis menampilkan ilustrasi postur tahanan dengan badge khusus tanpa ilusi repetisi.', tag='VISUAL FORM', accent=(2, 132, 199))
    draw_card(d4, (515, cy), (445, ch), '2', 'Smart Timer & Sesi Istirahat', 'Hitung mundur otomatis dengan peringatan audio dan panduan suara TTS. Interval rehat menyajikan visual hidrasi air minum sebelum gerakan berikutnya.', tag='AUDIO TIMER', accent=(245, 158, 11))
    draw_card(d4, (980, cy), (445, ch), '3', 'Kendali Tempo Fleksibel', 'Kendalikan sesi latihan sepenuhnya: jeda (pause) kapan saja, lewati gerakan, sesuaikan durasi istirahat, atau selesaikan sesi lebih awal dengan aman.', tag='KONTROL STUDIO', accent=(16, 185, 129))
    draw_card(d4, (1445, cy), (445, ch), '4', 'Dashboard Analitik & Riwayat', 'Visualisasi kepatuhan mingguan, total menit aktif, estimasi kalori terbakar, serta catatan log riwayat sesi lengkap yang tersimpan aman di akun Anda.', tag='EVALUASI PROGRES', accent=(168, 85, 247))
    c4.save('workout_data/images/panduan2.png', 'PNG', optimize=True)

    print("All 4 guides generated successfully!")

if __name__ == '__main__':
    build_all()
