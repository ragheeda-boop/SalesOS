"""Explore the Taqeem page structure in detail."""
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

        print("Navigating to facilities page...")
        await page.goto(
            "https://www.taqeem.gov.sa/facilities?sector=all",
            wait_until="load",
            timeout=60000,
        )

        # Wait a bit for dynamic content
        await page.wait_for_timeout(5000)

        # Save full HTML
        html = await page.content()
        with open("taqeem_scraper/page_full.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved full HTML to taqeem_scraper/page_full.html")

        # Find the main facility content area
        main_content = await page.evaluate("""
            () => {
                const el = document.querySelector('#facilities_content, #wrap, .ow-facility');
                if (!el) return 'NO MAIN CONTENT FOUND';
                return el.innerHTML.substring(0, 10000);
            }
        """)
        with open("taqeem_scraper/main_content.html", "w", encoding="utf-8") as f:
            f.write(main_content)
        print("Saved main content to taqeem_scraper/main_content.html")

        # List all class names in the main content
        classes = await page.evaluate("""
            () => {
                const el = document.querySelector('#facilities_content') || document.querySelector('#wrap');
                if (!el) return [];
                const all = el.querySelectorAll('*');
                const cs = new Set();
                all.forEach(e => {
                    if (e.className && typeof e.className === 'string') {
                        e.className.split(/\\s+/).forEach(c => { if (c) cs.add(c); });
                    }
                });
                return Array.from(cs).sort();
            }
        """)
        print(f"\nAll CSS classes in main content ({len(classes)}):")
        for c in classes:
            print(f"  {c}")

        # Get the facility cards structure
        cards = await page.evaluate("""
            () => {
                const container = document.querySelector('#facilities_content') || document.querySelector('#wrap');
                if (!container) return 'NO CONTAINER';
                
                // Find all elements that look like cards
                const candidates = container.querySelectorAll('[class*="card"], [class*="facility"], [class*="item"], [class*="list"], article, .row > div');
                const results = [];
                candidates.forEach((el, idx) => {
                    const text = (el.textContent || '').trim().substring(0, 300);
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 100 && rect.height > 50 && text.length > 20) {
                        results.push({
                            idx,
                            tag: el.tagName,
                            class: el.className,
                            rect: `${rect.width}x${rect.height}`,
                            text: text.substring(0, 200),
                            children: el.children.length,
                        });
                    }
                });
                return results;
            }
        """)

        print(f"\nFound {len(cards)} card-like elements:")
        for c in cards[:30]:
            print(f"\n  [{c['idx']}] <{c['tag']}> class={c['class'][:80]}")
            print(f"      size={c['rect']} children={c['children']}")
            print(f"      text={c['text']}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(discover())
