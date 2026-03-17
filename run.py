import run  # compile လုပ်ထားသော run.so ဖိုင်ကို import လုပ်ခြင်း
import sys
import time

def main():
    try:
        # run.so ထဲတွင် ပါဝင်သော start_process function ကို ခေါ်ယူခြင်း
        # ဤ function သည် internal အနေဖြင့် verify_activation နှင့် 
        # check_time_integrity တို့ကို အလိုအလျောက် စစ်ဆေးသွားမည် ဖြစ်သည်။
        
        run.start_process()
        
    except AttributeError:
        print("\n[X] Error: 'run.so' ဖိုင်ထဲတွင် start_process ကို ရှာမတွေ့ပါ။")
    except KeyboardInterrupt:
        print("\n[!] Script ကို ရပ်တန့်လိုက်ပါပြီ။")
    except Exception as e:
        print(f"\n[!] Error ဖြစ်ပွားခဲ့သည်: {e}")

if __name__ == "__main__":
    main()
  
