"""Debug card info extraction from listing page."""
import asyncio
from playwright.async_api import async_playwright


async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9"
        await page.goto(url, wait_until="load", timeout=30000)
        await page.wait_for_timeout(3000)
        await page.wait_for_selector("div.border.rounded.p-3.h-100", timeout=15000)

        card_infos = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('div.col-lg-4.col-md-6.col-12');
                const results = [];
                cards.forEach((card, idx) => {
                    const body = card.querySelector('div.border.rounded.p-3.h-100');
                    if (!body) return;
                    const getText = (sel) => {
                        const el = body.querySelector(sel);
                        return el ? el.textContent.trim() : '';
                    };
                    const name = getText('span.text-lg-bold.text-gray-800');
                    
                    // Classification
                    const classEl = body.querySelector('span.ot-rec-active');
                    const classification = classEl ? classEl.textContent.trim().split('\\n')[0].trim() : 'EMPTY';
                    
                    // Check status too
                    const statusEl = body.querySelector('div.text-medium.text-dark.ms-2 span.ot-rec-active, div.text-medium.text-dark.ms-2 span.text-s-medium');
                    const status = statusEl ? statusEl.textContent.trim() : 'NO-STATUS';
                    
                    // All ot-rec-active texts
                    const allOtRec = [];
                    body.querySelectorAll('span.ot-rec-active').forEach(s => {
                        allOtRec.push(s.textContent.trim().split('\\n')[0].trim());
                    });
                    
                    results.push({ idx: idx+1, name: name.substring(0, 50), classification, status, 
                                  allOtRec: allOtRec.join(' | '),
                                  classElExists: classEl ? 'YES' : 'NO' });
                });
                return results;
            }
        """)

        print("Card info extraction results:")
        for c in card_infos:
            print(f"\n  Card {c['idx']}: {c['name']}")
            print(f"    classification='{c['classification']}' status='{c['status']}'")
            print(f"    all ot-rec-active: {c['allOtRec']}")
            print(f"    classEl exists: {c['classElExists']}")

        await browser.close()


asyncio.run(check())
