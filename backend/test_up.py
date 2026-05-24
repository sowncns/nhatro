import httpx
import asyncio

async def main():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get('http://localhost:8000/docs')
            print("Status:", res.status_code)
    except Exception as e:
        print("Failed:", e)

asyncio.run(main())
