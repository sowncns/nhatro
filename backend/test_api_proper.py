import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Proper JSON login
        login_res = await client.post('http://localhost:8000/api/v1/auth/login', json={'email': 'ngocson877469@gmail.com', 'password': '1', 'device_id': 'test1'})
        if login_res.status_code != 200:
            print("Login failed", login_res.text)
            return
        
        token = login_res.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get draft invoice
        inv_res = await client.get('http://localhost:8000/api/v1/invoices?status=DRAFT', headers=headers)
        if inv_res.status_code != 200:
            print("Failed to get invoices", inv_res.text)
            return
        
        items = inv_res.json()['items']
        if not items:
            print("No draft invoices")
            return
            
        inv_id = items[0]['id']
        print(f"Confirming invoice {inv_id}")
        
        # Confirm
        conf_res = await client.post(f'http://localhost:8000/api/v1/invoices/{inv_id}/confirm', headers=headers)
        print("Status:", conf_res.status_code)
        print("Response:", conf_res.text)

asyncio.run(main())
