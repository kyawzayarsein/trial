import asyncio
import aiohttp
import re
import time
import hashlib
import os
import datetime
from urllib.parse import urlparse, parse_qs, urljoin

# --- CONFIGURATION ---
SECRET_SALT = "ohmygod@123"
CONCURRENT_PINGS = 10   
PING_INTERVAL = 0.1     
FAST_TIMEOUT = aiohttp.ClientTimeout(total=2)

def get_stable_id():
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
            serial = os.popen("getprop ro.build.display.id").read().strip()
        if not serial:
            import platform
            serial = platform.node() + platform.processor()
    except:
        serial = "DEFAULT_NODE"
    fixed_hash = hashlib.md5(serial.encode()).hexdigest()[:10].upper()
    return f"TRB-{fixed_hash}"

def check_time_manipulation():
    """ဖုန်းအချိန်ကို နောက်ပြန်ဆုတ်ပြီး သက်တမ်းတိုးတာမျိုးကို Offline စစ်ဆေးခြင်း"""
    time_file = os.path.join(os.path.expanduser("~"), ".turbo_runtime")
    current_now = datetime.datetime.now()
    
    if os.path.exists(time_file):
        with open(time_file, "r") as f:
            try:
                last_run_str = f.read().strip()
                last_run = datetime.datetime.fromisoformat(last_run_str)
                # လက်ရှိအချိန်က နောက်ဆုံး run ခဲ့တဲ့အချိန်ထက် ငယ်နေရင် (အချိန်လိမ်ထားရင်)
                if current_now < last_run:
                    return False
            except:
                pass
    
    # လက်ရှိအချိန်ကို မှတ်ထားမယ်
    with open(time_file, "w") as f:
        f.write(current_now.isoformat())
    return True

async def verify_activation():
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    
    # အချိန်လိမ်ထားရင် ပိတ်မယ်
    if not check_time_manipulation():
        print(f"DEVICE ID: {device_id}")
        print("\n[!] Error: System time has been manipulated!")
        print("[!] ကျေးဇူးပြု၍ ဖုန်းအချိန်ကို အမှန်ပြန်ပြင်ပေးပါ။")
        return False

    def check_key(key_input):
        try:
            # Hash(12) + Timestamp(12) = 24 characters
            if len(key_input) < 24: return False
            provided_hash = key_input[:12]
            expiry_str = key_input[12:]
            
            # Key မှန်မမှန် ပြန်စစ်ခြင်း
            expected_hash = hashlib.sha256(f"{device_id}{expiry_str}{SECRET_SALT}".encode()).hexdigest()[:12].upper()
            
            if provided_hash == expected_hash:
                # အချိန်သက်တမ်းကို စစ်ဆေးခြင်း
                expiry_date = datetime.datetime.strptime(expiry_str, "%Y%m%d%H%M")
                if datetime.datetime.now() < expiry_date:
                    return expiry_date
            return False
        except:
            return False

    saved_key = None
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            saved_key = f.read().strip()

    expiry_info = check_key(saved_key)
    if expiry_info:
        print(f"DEVICE ID: {device_id}")
        print(f"Status: Verified ✔ (Expires: {expiry_info.strftime('%Y-%m-%d %H:%M')})")
        return True
    else:
        print(f"DEVICE ID: {device_id}")
        print(f"\n[!] License Expired or Invalid Key.")
        input_key = input("Enter Activation Key: ").strip().upper()
        
        expiry_info = check_key(input_key)
        if expiry_info:
            with open(key_file, "w") as f:
                f.write(input_key)
            print(f"Activation Successful! Valid until: {expiry_info.strftime('%Y-%m-%d %H:%M')}")
            return True
        else:
            print("Invalid Activation Key!")
            return False

async def high_speed_ping(session, auth_link, sid):
    while True:
        try:
            if session.closed: break
            async with session.get(auth_link, timeout=aiohttp.ClientTimeout(total=1)) as response:
                if response.status == 200:
                    print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (DNS Cached) ", end='\r')
                await asyncio.sleep(PING_INTERVAL)
        except:
            break

async def start_process():
    if not await verify_activation():
        return

    print(f"[{time.strftime('%H:%M:%S')}] Turbo Async + DNS Cache Active...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    resolver = aiohttp.ThreadedResolver()
    
    while True:
        connector = aiohttp.TCPConnector(resolver=resolver, use_dns_cache=True, ttl_dns_cache=300)
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            try:
                while not session.closed:
                    try:
                        async with session.get("http://connectivitycheck.gstatic.com/generate_204", 
                                               allow_redirects=True, 
                                               timeout=FAST_TIMEOUT) as r:
                            
                            if r.status == 204:
                                print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Monitoring... ", end='\r')
                                await asyncio.sleep(0.5) 
                                continue
                            
                            portal_url = str(r.url)
                            print(f"\n[!] Internet Dropped! Reconnecting: {portal_url}")
                            
                            async with session.get(portal_url, timeout=FAST_TIMEOUT) as r1:
                                text = await r1.text()
                                path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", text)
                                next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
                                
                                async with session.get(next_url, timeout=FAST_TIMEOUT) as r2:
                                    final_url = str(r2.url)
                                    sid = parse_qs(urlparse(final_url).query).get('sessionId', [None])[0]
                                    
                                    if sid:
                                        print(f"[*] SID Found: {sid}")
                                        parsed_portal = urlparse(portal_url)
                                        gw_addr = parse_qs(parsed_portal.query).get('gw_address', ['192.168.60.1'])[0]
                                        gw_port = parse_qs(parsed_portal.query).get('gw_port', ['2060'])[0]
                                        auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}"

                                        tasks = [high_speed_ping(session, auth_link, sid) for _ in range(CONCURRENT_PINGS)]
                                        await asyncio.gather(*tasks)

                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        break
            except Exception:
                pass
            
            if not session.closed:
                await session.close()
        
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(start_process())
    except KeyboardInterrupt:
        print("\n\n[!] Script Stopped.")
