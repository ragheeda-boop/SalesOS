import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        t0 = asyncio.get_event_loop().time()
        resp = await client.post(
            'http://localhost:8000/api/v1/identity/register',
            json={'email': 'regtest@example.com', 'password': 'Test1234!', 'full_name': 'Test Reg', 'tenant_name': 'Reg Corp'}
        )
        t = asyncio.get_event_loop().time() - t0
        data = resp.json()
        print(f'Time: {t:.3f}s')
        print(f'Status: {resp.status_code}')
        print(f'Response: {data}')
        
        if resp.status_code == 200:
            print('--- REGISTRATION SUCCESSFUL ---')
            uid = data.get('user', {}).get('id', 'N/A')
            token = data.get('access_token', '')
            print(f'User ID: {uid}')
            print(f'Token: {token[:20]}...')
        else:
            print(f'Error detail: {data.get("detail", data)}')

asyncio.run(test())
