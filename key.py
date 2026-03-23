import hashlib
import datetime

SECRET_SALT = "ohmygod@123"

def generate_key(device_id, hours):
    # အခုအချိန်ကနေ နာရီအရေအတွက်ကို ပေါင်းပြီး သက်တမ်းကုန်မယ့်အချိန် တွက်တယ်
    expiry_time = datetime.datetime.now() + datetime.timedelta(hours=hours)
    expiry_str = expiry_time.strftime("%Y%m%d%H%M") 
    
    # Hash ထုတ်ခြင်း
    raw_data = f"{device_id}{expiry_str}{SECRET_SALT}"
    key_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:12].upper()
    
    # Key = Hash(12) + Expiry(12)
    return f"{key_hash}{expiry_str}"

if __name__ == "__main__":
    print("--- Turbo Activation Key Generator ---")
    dev_id = input("Enter Device ID (e.g., TRB-XXXX): ").strip().upper()
    try:
        hrs = float(input("Enter Duration in Hours (e.g., 24 for 1 day, 0.5 for 30 mins): "))
        key = generate_key(dev_id, hrs)
        
        print("\n" + "="*30)
        print(f"DEVICE ID: {dev_id}")
        print(f"KEY      : {key}")
        print(f"EXPIRES  : {(datetime.datetime.now() + datetime.timedelta(hours=hrs)).strftime('%Y-%m-%d %H:%M')}")
        print("="*30)
    except ValueError:
        print("Invalid input! Please enter a number.")
      
