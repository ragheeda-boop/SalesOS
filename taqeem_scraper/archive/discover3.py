"""Explore the Taqeem detail page structure."""
import asyncio
from playwright.async_api import async_playwright


async def discover():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()

        # Go to a detail page directly
        print("Navigating to a facility detail page...")
        await page.goto(
            "https://www.taqeem.gov.sa/en/authority-partner/2122240",
            wait_until="load",
            timeout=60000,
        )
        await page.wait_for_timeout(3000)

        # Save HTML
        html = await page.content()
        with open("taqeem_scraper/detail_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved detail page HTML")

        # Look for the content structure
        info = await page.evaluate("""
            () => {
                const wrap = document.querySelector('#wrap') || document.querySelector('main');
                if (!wrap) return 'NO WRAP';
                return wrap.innerHTML.substring(0, 15000);
            }
        """)
        with open("taqeem_scraper/detail_inner.html", "w", encoding="utf-8") as f:
            f.write(info)
        print("Saved detail inner HTML")

        # Find all key labels and values
        labels = await page.evaluate("""
            () => {
                const wrap = document.querySelector('.ow-facility-detail, #wrap') || document.querySelector('main');
                if (!wrap) return 'NO CONTENT';
                const allText = wrap.innerText;
                return allText;
            }
        """)
        # Write to file due to encoding
        with open("taqeem_scraper/detail_text.txt", "w", encoding="utf-8") as f:
            f.write(labels)
        print("Saved detail text")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(discover())
