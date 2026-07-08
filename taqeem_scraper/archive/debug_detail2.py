"""Debug multiple detail pages to find the classification badge."""
import asyncio
from playwright.async_api import async_playwright

urls = [
    "https://www.taqeem.gov.sa/en/authority-partner/2122240",  # Record 1 - VFR3 OK
    "https://www.taqeem.gov.sa/en/authority-partner/2122242",  # Record 2 - had Active
    "https://www.taqeem.gov.sa/en/authority-partner/2122243",  # Record 3 - had Active
    "https://www.taqeem.gov.sa/en/authority-partner/2122244",  # Record 4
]

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in urls:
            print(f"\n{'='*60}")
            print(f"URL: {url}")
            await page.goto(url, wait_until="load", timeout=30000)
            await page.wait_for_timeout(3000)

            # Find all span.ot-rec-active
            data = await page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span.ot-rec-active');
                    const result = [];
                    spans.forEach(s => {
                        result.push({
                            text: s.textContent.trim().substring(0, 80),
                            cls: s.className,
                            parentText: (s.parentElement ? s.parentElement.textContent.trim().substring(0, 100) : ''),
                        });
                    });
                    return result;
                }
            """)
            print(f"  ot-rec-active spans: {len(data)}")
            for d in data:
                print(f"    text='{d['text']}' class='{d['cls']}'")

            # Also look for VFR classification in the entire page
            vfr = await page.evaluate("""
                () => {
                    const body = document.body.innerText;
                    const match = body.match(/VFR\\d/);
                    return match ? match[0] : 'NOT FOUND';
                }
            """)
            print(f"  VFR badge text on page: {vfr}")

            # Check if there's a section with both "Basic information" and the VFR badge
            structure = await page.evaluate("""
                () => {
                    // Find the Basic information section
                    const headings = document.querySelectorAll('.text-xs-semibold.text-dark');
                    let result = [];
                    headings.forEach(h => {
                        const text = h.textContent.trim();
                        const row = h.closest('.row');
                        let spans = [];
                        if (row) {
                            row.querySelectorAll('span.ot-rec-active').forEach(s => {
                                spans.push(s.textContent.trim().substring(0, 50));
                            });
                        }
                        if (spans.length > 0) {
                            result.push({ heading: text, spans: spans });
                        }
                    });
                    // Also check the card listing structure
                    return result;
                }
            """)
            for s in structure:
                print(f"  Section '{s['heading']}' has ot-rec-active: {s['spans']}")

        await browser.close()

asyncio.run(check())
