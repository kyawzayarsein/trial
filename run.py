import asyncio
import run

if __name__ == "__main__":
    try:
        asyncio.run(run.start_process())
    except KeyboardInterrupt:
        pass
    
