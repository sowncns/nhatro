import asyncio
from app.database.session import AsyncSessionLocal
from app.schemas.schemas import LoginRequest
from app.api.v1.endpoints.auth import login
from fastapi import Request

async def main():
    class DummyRequest:
        def __init__(self):
            self.headers = {'user-agent': 'test'}
            self.client = type('Client', (), {'host': '127.0.0.1'})()
    
    async with AsyncSessionLocal() as db:
        req = LoginRequest(email='ngocson877469@gmail.com', password='1', device_id='test')
        try:
            await login(req, DummyRequest(), db)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
