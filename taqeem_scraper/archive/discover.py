"""Discover the Taqeem API by monitoring network traffic."""
import asyncio
from playwright.async_api import async_playwright


async def discover():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="en-US",
            timezone_id="Asia/Riyadh",
        )
        page = await context.new_page()

        # Track XHR/fetch requests
        api_responses = []

        async def on_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "json" in ct or url.endswith((".json", "/search", "/list")):
                try:
                    body = await response.text()
                    api_responses.append({
                        "url": url,
                        "status": response.status,
                        "content_type": ct,
                        "body": body[:3000],
                    })
                except Exception:
                    pass

        page.on("response", on_response)

        print("Navigating to facilities page...")
        await page.goto(
            "https://www.taqeem.gov.sa/facilities?sector=all",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        # Wait for content to load
        await page.wait_for_selector('[class*="facility"]', timeout=15000)
        await page.wait_for_timeout(3000)

        print(f"\nCaptured {len(api_responses)} API responses:")
        for i, r in enumerate(api_responses[:10]):
            print(f"\n--- Response {i+1} ---")
            print(f"URL: {r['url']}")
            print(f"Status: {r['status']}")
            print(f"Content-Type: {r['content_type']}")
            print(f"Body: {r['body'][:600]}...")

        # Check page structure
        cards = await page.query_selector_all('.facility-card, [class*="facility"], article, .card')
        print(f"\nFound {len(cards)} potential cards")

        # Get all element classes
        classes = await page.evaluate("""
            () => {
                const els = document.querySelectorAll('*');
                const classSet = new Set();
                els.forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        el.className.split(/\\s+/).forEach(c => {
                            if (c) classSet.add(c);
                        });
                    }
                });
                return Array.from(classSet).filter(c => 
                    c.includes('card') || c.includes('facility') || c.includes('item')
                );
            }
        """)
        print(f"\nRelevant CSS classes: {classes}")

        # Get page title and visible text
        title = await page.title()
        print(f"\nPage title: {title}")

        # Try to find where facility data is rendered
        scripts = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                return Array.from(scripts).map(s => ({
                    type: s.type || 'text/javascript',
                    src: s.src || 'inline',
                    length: (s.textContent || '').length,
                }));
            }
        """)
        for s in scripts:
            print(f"Script: type={s['type']}, src={s['src'][:80]}, length={s['length']}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(discover())
