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
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                let results = [];
                let node;
                while (node = walker.nextNode()) {
                    const t = node.textContent.trim();
                    if (/from\\s+\\d/.test(t)) {
                        results.push({
                            text: t.substring(0, 100),
                            parent_tag: node.parentElement.tagName,
                            parent_class: node.parentElement.className,
                            parent_html: node.parentElement.outerHTML.substring(0, 500)
                        });
                    }
                }
                return results;
            }
        ''')
        for r in info:
            print(f'Found: "{r["text"]}"')
            print(f'  Tag: {r["parent_tag"]}, Class: {r["parent_class"]}')
            print(f'  HTML: {r["parent_html"]}')
            print()
        await browser.close()
asyncio.run(check())
