import hashlib
import time
from datetime import datetime, timedelta

# --- SETTINGS (run.py ထဲကအတိုင်း တူညီရပါမည်) ---
SECRET_SALT = "FIXED_SALT_999"

def generate_license_key(device_id, days=0, hours=0, minutes=0):
    """
    Device ID နှင့် သက်တမ်းကို အခြေခံပြီး Activation Key ထုတ်ပေးရန်
    """
    # လက်ရှိအချိန်ကို အခြေခံပြီး သက်တမ်းကုန်မည့်အချိန် (Expiry) ကို တွက်ချက်ခြင်း
    now = datetime.now()
    expiry_date = now + timedelta(days=days, hours=hours, minutes=minutes)
    expiry_ts = str(int(expiry_date.timestamp()))

    # Security Hash ပြုလုပ်ခြင်း (Device ID + Salt + Timestamp)
    # ဒါမှ User က Timestamp ကို ကိုယ်တိုင်ပြင်ရင် Hash နဲ့ မကိုက်တော့ဘဲ Invalid ဖြစ်မှာပါ
    check_str = f"{device_id.upper()}{SECRET_SALT}{expiry_ts}"
    auth_hash = hashlib.sha256(check_str.encode()).hexdigest()[:16].upper()

    # နောက်ဆုံးထွက်လာမည့် Key Format: HASH-TIMESTAMP
    full_key = f"{auth_hash}-{expiry_ts}"
    
    return full_key, expiry_date

def main():
    print("--- RUIJIE TURBO KEY GENERATOR ---")
    
    # User ဆီက Device ID တောင်းခြင်း
    device_id = input("Enter User's Device ID: ").strip().upper()
    if not device_id:
        print("Device ID cannot be empty!")
        return

    print("\nSelect Validity Period:")
    print("1. 1 Hour (Test)")
    print("2. 1 Day")
    print("3. 7 Days (1 Week)")
    print("4. 30 Days (1 Month)")
    print("5. Custom (ရက်ပေါင်း စိတ်ကြိုက်ရိုက်ထည့်ရန်)")
    
    choice = input("Choice (1-5): ")

    d, h = 0, 0
    if choice == '1': h = 1
    elif choice == '2': d = 1
    elif choice == '3': d = 7
    elif choice == '4': d = 30
    elif choice == '5':
        d = int(input("Enter number of days: "))
        h = int(input("Enter additional hours (optional): "))
    else:
        print("Invalid Choice!")
        return

    key, expiry = generate_license_key(device_id, days=d, hours=h)

    print("\n" + "="*40)
    print(f"DEVICE ID : {device_id}")
    print(f"EXPIRES ON: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"KEY       : {key}")
    print("="*40)
    print("\nCopy the KEY and send it to the user.")

if __name__ == "__main__":
    main()
