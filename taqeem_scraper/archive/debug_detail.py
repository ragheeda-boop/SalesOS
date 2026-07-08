"""Debug detail page structure."""
import asyncio
from playwright.async_api import async_playwright


async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Check page 2, item 2 (which had Classification=Active)
        url = "https://www.taqeem.gov.sa/en/authority-partner/2122242"
        print(f"Checking: {url}")
        await page.goto(url, wait_until="load", timeout=30000)
        await page.wait_for_timeout(3000)

        spans = await page.evaluate("""
            () => {
                const spans = document.querySelectorAll('span.ot-rec-active');
                return Array.from(spans).map(s => ({
                    text: s.textContent.trim().substring(0, 100),
                    cls: s.className,
                }));
            }
        """)
        print("\nAll ot-rec-active spans:")
        for s in spans:
            print(f"  Text: '{s['text']}'  Class: {s['cls']}")

        # Check what extract_detail_page does
        pairs = await page.evaluate("""
            () => {
                const results = [];
                const containers = document.querySelectorAll(
                    '.col-lg-6.col-md-6.col-12.d-flex, .col-12.d-lg-flex.d-md-flex.d-block'
                );
                containers.forEach(container => {
                    const labelEl = container.querySelector('.text-md-regular.text-dark');
                    if (!labelEl) return;
                    let label = labelEl.textContent.replace(/:\\s*$/, '').trim();
                    let value = '';
                    if (container.classList.contains('d-lg-flex')) {
                        const allText = container.textContent.trim();
                        const lbl = labelEl.textContent.trim();
                        let rest = allText.substring(lbl.length).replace(/^:/, '').trim();
                        value = rest.split('\\n').map(s => s.trim()).filter(Boolean).join(', ');
                    } else {
                        const valueEl = container.querySelector('.text-md-semibold');
                        if (valueEl) value = valueEl.textContent.trim();
                    }
                    if (label && value) results.push({ label, value });
                });
                return results;
            }
        """)
        print("\nLabel-value pairs found:")
        for p in pairs:
            print(f"  Label: '{p['label']}' -> Value: '{p['value']}'")

        # Check status section on card
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all",
            wait_until="load", timeout=30000,
        )
        await page.wait_for_timeout(3000)
        card_html = await page.evaluate("""
            () => {
                const card = document.querySelector('div.col-lg-4.col-md-6.col-12:nth-child(2)');
                if (!card) return 'NO CARD 2';
                const body = card.querySelector('div.border.rounded.p-3.h-100');
                return body ? body.innerHTML.substring(0, 2000) : 'NO BODY';
            }
        """)
        print("\n\nSecond card HTML:")
        print(card_html)

        await browser.close()


asyncio.run(check())
