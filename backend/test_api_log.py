import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # First login to get token
        login_res = await client.post('http://localhost:8000/api/v1/auth/login', data={'username': 'ngocson877469@gmail.com', 'password': '1'})
        print(login_res.text)

asyncio.run(main())
