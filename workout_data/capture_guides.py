import subprocess
import os
import time

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NjkwNjIxYS0zNTM0LTQxOWUtODZmYi1lZDMyMmE0N2U4ZDAiLCJ1c2VybmFtZSI6InJlaGFuIiwiZXhwIjoxNzk3MzUzNTY3LCJpYXQiOjE3OTQ3NjE1Njd9.7KmvqeR34UG83t37U66469jLy-TovYylbMfTuEDKa5A'

targets = [
    ('mobile_home.png', '412,915', f'http://127.0.0.1:8008/?auth_token={token}&view=training&hide_guide=true'),
    ('mobile_workout.png', '412,915', f'http://127.0.0.1:8008/?auth_token={token}&view=active-workout&routine=rt_scientific_7min&hide_guide=true'),
    ('mobile_report.png', '412,915', f'http://127.0.0.1:8008/?auth_token={token}&view=report&hide_guide=true'),
    ('desktop_home.png', '1600,900', f'http://127.0.0.1:8008/?auth_token={token}&view=training&hide_guide=true'),
    ('desktop_workout.png', '1600,900', f'http://127.0.0.1:8008/?auth_token={token}&view=active-workout&routine=rt_scientific_7min&hide_guide=true'),
    ('desktop_report.png', '1600,900', f'http://127.0.0.1:8008/?auth_token={token}&view=report&hide_guide=true'),
]

os.makedirs('workout_data/guide_raw', exist_ok=True)

for fname, win_size, url in targets:
    out_p = os.path.abspath(os.path.join('workout_data', 'guide_raw', fname))
    base_n = fname.replace('.png', '')
    user_d = os.path.abspath(f'tmp_chrome_{base_n}')
    cmd = [
        chrome_path,
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        f'--window-size={win_size}',
        f'--user-data-dir={user_d}',
        f'--screenshot={out_p}',
        '--virtual-time-budget=6000',
        url
    ]
    print(f'Capturing {fname} ({win_size})...')
    res = subprocess.run(cmd, capture_output=True, timeout=25)
    print(f'Captured {fname}: exists={os.path.exists(out_p)}')
