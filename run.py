import requests
import re
import time
import threading
import hashlib
import os
import uuid
import urllib3
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SETTINGS ---
PING_THREADS = 10
PING_INTERVAL = 0.1 
SECRET_SALT = "FIXED_SALT_999"
LICENSE_FILE = "license.txt"

def get_device_id():
    try:
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                return hashlib.md5(f.read().encode()).hexdigest()[:12].upper()
        return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:12].upper()
    except: return "DEV-FIXED-ID"

def get_online_unix_time():
    """အင်တာနက်ရပြီဆိုမှ တကယ့်အချိန်ကို လှမ်းစစ်ရန်"""
    try:
        # WorldTimeAPI သုံးထားပါတယ် (Myanmar Time အတွက်)
        r = requests.get("http://worldtimeapi.org/api/timezone/Asia/Yangon", timeout=5)
        if r.status_code == 200:
            return int(r.json()['unixtime'])
    except:
        try:
            # API အဆင်မပြေရင် Google Header က အချိန်ကို ယူမယ်
            r = requests.head("https://www.google.com", timeout=5)
            date_str = r.headers['Date'] # e.g. "Mon, 01 Jan 2024 12:00:00 GMT"
            # GMT ကို Unix Timestamp ပြောင်းရန်
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            return int(dt.timestamp())
        except:
            return None

def verify_license(device_id, full_key, online_ts=None):
    try:
        if "-" not in full_key: return False, "Format Error"
        user_hash, expiry_ts = full_key.split("-")
        
        # အချိန်စစ်ဆေးခြင်း (Online Time ရှိရင် အဲဒါနဲ့စစ်၊ မရှိရင် စက်အချိန်နဲ့စစ်)
        current_ts = online_ts if online_ts else int(time.time())
        
        if current_ts > int(expiry_ts):
            return False, "Expired"

        # Integrity Check
        check_str = f"{device_id}{SECRET_SALT}{expiry_ts}"
        valid_hash = hashlib.sha256(check_str.encode()).hexdigest()[:16].upper()
        
        if user_hash == valid_hash:
            return True, datetime.fromtimestamp(int(expiry_ts)).strftime('%Y-%m-%d %H:%M:%S')
        return False, "Invalid Key"
    except: return False, "Check Failed"

def start_process():
    device_id = get_device_id()
    print(f"\n[ RUIJIE TURBO BYPASS v2.1 ]")
    print(f"DEVICE ID: {device_id}")

    saved_key = None
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            saved_key = f.read().strip()

    if not saved_key:
        saved_key = input("Enter Activation Key: ").strip()

    # အစပိုင်းမှာ Offline အနေနဲ့ အရင်စစ်မယ်
    is_valid, msg = verify_license(device_id, saved_key)
    if not is_valid:
        print(f"[!] {msg}")
        if os.path.exists(LICENSE_FILE): os.remove(LICENSE_FILE)
        return
    
    # ပထမအကြိမ် အောင်မြင်ရင် သိမ်းထားမယ်
    with open(LICENSE_FILE, "w") as f: f.write(saved_key)
    print(f"[+] Initial Validation Success. Monitoring...")

    session = requests.Session()
    online_verified = False

    while True:
        is_up, status, ping = check_internet_status() # (ဒီ Function က မူလအတိုင်းထားပါ)
        
        if is_up:
            # အင်တာနက်ရပြီဆိုတာနဲ့ Online Time ကို တစ်ခါပဲ (သို့) အခါအားလျော်စွာ စစ်မယ်
            if not online_verified:
                print("[*] Internet Detected. Syncing with Network Time...")
                online_ts = get_online_unix_time()
                
                if online_ts:
                    is_still_valid, expire_date = verify_license(device_id, saved_key, online_ts)
                    if not is_still_valid:
                        print(f"\n[!!!] SECURITY ALERT: License Expired on {expire_date}")
                        print("[!] System blocking access...")
                        # ချက်ချင်း ရပ်ပစ်ခြင်း (သို့မဟုတ် bypass threads တွေကို သတ်ပစ်ခြင်း)
                        sys.exit()
                    else:
                        print(f"[+] Online Verification Passed. (Valid until: {expire_date})")
                        online_verified = True
                else:
                    print("[?] Could not sync time. Retrying later...")

            # ကျန်တဲ့ normal logs...
            log_status(status, ping, True)
        else:
            # အင်တာနက်ပြတ်သွားရင် ပြန်စစ်ဖို့ reset လုပ်မယ်
            online_verified = False 
            # ... (Bypass logic: sid ယူတာတွေ၊ threads run တာတွေ ဒီမှာ ဆက်ရေးပါ) ...
            
        time.sleep(1)

if __name__ == "__main__":
    start_process()
