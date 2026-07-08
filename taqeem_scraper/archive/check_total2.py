import asyncio
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9', wait_until='load', timeout=60000)
        await page.wait_for_timeout(5000)
        info = await page.evaluate('''
            () => {
                const spans = document.querySelectorAll('span.my-auto');
                let results = [];
                spans.forEach(sp => {
                    results.push({
                        text: sp.textContent.trim(),
                        prev_sibling: sp.previousSibling ? (sp.previousSibling.textContent || '').trim() : null,
                        parent_html: sp.parentElement.outerHTML.substring(0, 500)
                    });
                });
                return results;
            }
        ''')
        for r in info:
            print(f'Text: "{r["text"]}"')
            print(f'  Prev sibling: "{r["prev_sibling"]}"')
            print(f'  Parent: {r["parent_html"]}')
            print()
        await browser.close()
asyncio.run(check())
