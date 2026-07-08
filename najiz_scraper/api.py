import asyncio
import httpx
from config import FULL_API_URL, MAX_CONCURRENT, MAX_RETRIES, TIMEOUT, HEADERS, REQUEST_DELAY

class NajizAPI:
    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(TIMEOUT),
            headers=HEADERS,
            follow_redirects=True,
        )
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def fetch_page(self, page: int):
        url = f"{FULL_API_URL}?pageNumber={page}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with self._sem:
                    resp = await self._client.get(url)
                    await asyncio.sleep(REQUEST_DELAY)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("httpCode") == 200 and data.get("data"):
                        return data["data"]
                return None
            except (httpx.TimeoutException, httpx.RequestError) as e:
                if attempt < MAX_RETRIES:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                return None

    async def fetch_batch(self, pages: list[int]):
        tasks = [self.fetch_page(p) for p in pages]
        results = await asyncio.gather(*tasks)
        return list(zip(pages, results))

    async def get_total_pages(self) -> int:
        data = await self.fetch_page(1)
        if data:
            return data.get("totalPages", 0)
        return 0

    async def close(self):
        await self._client.aclose()
