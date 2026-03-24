import run
import asyncio

async def main():
    try:
        # Module ထဲမှာ ပါဝင်တဲ့ start_process ကို ခေါ်ယူခြင်း
        # မှတ်ချက် - function အတွက် လိုအပ်တဲ့ arguments တွေကို ထည့်သွင်းပေးရန် လိုအပ်နိုင်ပါတယ်
        print("Starting process...")
        await run.start_process()
        
        # အခြား function များကိုလည်း လိုအပ်သလို ခေါ်ယူနိုင်ပါတယ်
        # ဥပမာ - run.high_speed_ping()
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    # ဤ module သည် coroutine များ (async) အသုံးပြုထားသဖြင့် asyncio နှင့် ပတ်ရပါသည်
    asyncio.run(main())
