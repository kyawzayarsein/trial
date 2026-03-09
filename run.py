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

# SSL Warning များ မပြစေရန်
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
                data = f.read()
                return hashlib.md5(data.encode()).hexdigest()[:12].upper()
        return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:12].upper()
    except:
        return "DEV-FIXED-ID"

def get_online_unix_time():
    """အင်တာနက်ရပြီဆိုမှ တကယ့်အချိန်ကို လှမ်းစစ်ရန်"""
    try:
        r = requests.get("http://worldtimeapi.org/api/timezone/Asia/Yangon", timeout=5)
        if r.status_code == 200:
            return int(r.json()['unixtime'])
    except:
        try:
            r = requests.head("https://www.google.com", timeout=5)
            date_str = r.headers['Date']
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            return int(dt.timestamp())
        except:
            return None

def verify_license(device_id, full_key, online_ts=None):
    try:
        if "-" not in full_key: return False, "Format Error"
        user_hash, expiry_ts = full_key.split("-")
        current_ts = online_ts if online_ts else int(time.time())
        
        if current_ts > int(expiry_ts):
            return False, "Expired"

        check_str = f"{device_id}{SECRET_SALT}{expiry_ts}"
        valid_hash = hashlib.sha256(check_str.encode()).hexdigest()[:16].upper()
        
        if user_hash == valid_hash:
            return True, datetime.fromtimestamp(int(expiry_ts)).strftime('%Y-%m-%d %H:%M:%S')
        return False, "Invalid Key"
    except: return False, "Check Failed"

def check_internet_status():
    """အင်တာနက် အခြေအနေကို စစ်ဆေးသည်"""
    url = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        start_time = time.time()
        response = requests.get(url, timeout=2, allow_redirects=False)
        end_time = time.time()
        ping_ms = int((end_time - start_time) * 1000)
        if response.status_code == 204:
            return True, response.status_code, ping_ms
        return False, response.status_code, ping_ms
    except:
        return False, 0, 0

def log_status(status_code, ping, is_access):
    current_time = time.strftime('%H-%M-%S')
    print(f"Log: {{time: {current_time}, status: {status_code}, ping: {ping}ms, Access: {is_access}}}")

def high_speed_ping(auth_link, session):
    while True:
        try:
            session.get(auth_link, timeout=2)
            time.sleep(PING_INTERVAL)
        except:
            break

def start_process():
    device_id = get_device_id()
    print(f"\n==============================")
    print(f"   RUIJIE TURBO BYPASS v2.1")
    print(f"==============================")
    print(f"DEVICE ID: {device_id}")

    saved_key = None
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            saved_key = f.read().strip()

    if not saved_key:
        saved_key = input("Enter Activation Key: ").strip()

    # အစပိုင်း Offline စစ်ဆေးခြင်း
    is_valid, msg = verify_license(device_id, saved_key)
    if not is_valid:
        print(f"[!] {msg}")
        if os.path.exists(LICENSE_FILE): os.remove(LICENSE_FILE)
        return
    
    with open(LICENSE_FILE, "w") as f: f.write(saved_key)
    print(f"[+] Initial Validation Success. Monitoring...")

    session = requests.Session()
    online_verified = False

    while True:
        is_up, status, ping = check_internet_status()
        
        if is_up:
            if not online_verified:
                online_ts = get_online_unix_time()
                if online_ts:
                    is_still_valid, expire_date = verify_license(device_id, saved_key, online_ts)
                    if not is_still_valid:
                        print(f"\n[!!!] EXPIRED ON ONLINE CHECK: {expire_date}")
                        sys.exit()
                    else:
                        print(f"[+] Online Verify Passed. Exp: {expire_date}")
                        online_verified = True
            log_status(status, ping, "ONLINE")
        else:
            online_verified = False
            log_status(status, ping, "RECONNECTING...")
            try:
                r = session.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=3)
                if r.status_code != 204:
                    portal_url = r.url
                    r1 = session.get(portal_url, verify=False, timeout=5)
                    sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r1.text)
                    
                    if not sid_match:
                        path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
                        if path_match:
                            next_url = urljoin(portal_url, path_match.group(1))
                            r2 = session.get(next_url, verify=False, timeout=5)
                            sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.url)
                    
                    if sid_match:
                        sid = sid_match.group(1)
                        parsed_portal = urlparse(portal_url)
                        params = parse_qs(parsed_portal.query)
                        gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                        gw_port = params.get('gw_port', ['2060'])[0]
                        auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"
                        
                        for _ in range(PING_THREADS):
                            threading.Thread(target=high_speed_ping, args=(auth_link, session), daemon=True).start()
                        print(f"[*] Reconnected! SID: {sid}")
            except:
                pass
        
        time.sleep(1)

if __name__ == "__main__":
    start_process()
