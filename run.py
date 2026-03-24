import asyncio
import run

async def start_app():

    is_verified = await run.verify_activation()
    if is_verified:
        try:

            await run.main_engine()
        except KeyboardInterrupt:
            print("\nStopped by User.")

if __name__ == "__main__":
    asyncio.run(start_app())

