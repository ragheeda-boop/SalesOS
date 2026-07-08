import os, httpx, json

token = os.environ.get('NOTION_TOKEN') or os.environ.get('NOTION_API_KEY') or os.environ.get('NOTION_SECRET')
print('Token found:', bool(token))

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Notion-Version': '2022-06-28'} if token else {}
if token:
    r = httpx.get('https://api.notion.com/v1/users/me', headers=headers)
    print(f'Notion API status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Bot name: {data.get("name", "N/A")}')
        # Also search for a parent page to create database under
        search_r = httpx.post('https://api.notion.com/v1/search', headers=headers, json={})
        print(f'Search status: {search_r.status_code}')
        if search_r.status_code == 200:
            results = search_r.json().get('results', [])
            for item in results[:10]:
                obj_type = item['object']
                parent_info = item.get('parent', {})
                print(f"  - {item['id']} | {obj_type} | title: {item.get('title', [{}])[0].get('plain_text', '') if obj_type == 'database' else item.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '') if obj_type == 'page' else 'N/A'}")
