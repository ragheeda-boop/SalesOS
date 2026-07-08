"""Debug CR number extraction from listing cards."""
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

        card_info = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('div.col-lg-4.col-md-6.col-12');
                const results = [];
                cards.forEach((card, idx) => {
                    const body = card.querySelector('div.border.rounded.p-3.h-100');
                    if (!body) return;
                    const name = body.querySelector('span.text-lg-bold.text-gray-800');
                    const nameText = name ? name.textContent.trim().substring(0, 50) : 'N/A';
                    
                    // Debug CR extraction
                    const grayLabels = body.querySelectorAll('.text-gray-700');
                    const labelTexts = [];
                    grayLabels.forEach(l => labelTexts.push(l.textContent.trim()));
                    
                    // Find the specific CR label
                    const crLabel = Array.from(grayLabels)
                        .find(el => el.textContent.includes('Commercial number'));
                    
                    let crNumber = '';
                    let debugInfo = '';
                    if (crLabel) {
                        debugInfo = 'found crLabel: ' + crLabel.textContent.trim().substring(0, 60);
                        const crRow = crLabel.closest('div.d-flex');
                        if (crRow) {
                            debugInfo += ' | found d-flex: ' + crRow.className.substring(0, 80);
                            const crValEl = crRow.querySelector('.text-medium');
                            if (crValEl) {
                                const t = crValEl.textContent.trim();
                                const nums = t.match(/\\d+/g);
                                if (nums) crNumber = nums[0];
                                debugInfo += ' | val=' + t.substring(0, 30);
                            } else {
                                debugInfo += ' | NO .text-medium found';
                                // Check children
                                const children = crRow.querySelectorAll('*');
                                const childClasses = Array.from(children).slice(0, 5).map(c => c.className);
                                debugInfo += ' children: ' + childClasses.join(', ');
                            }
                        } else {
                            debugInfo += ' | NO d-flex parent';
                            debugInfo += ' parent=' + (crLabel.parentElement ? crLabel.parentElement.className : 'none');
                        }
                    } else {
                        debugInfo = 'NO crLabel found';
                    }
                    
                    results.push({ idx: idx+1, name: nameText, crNumber, labelTexts: labelTexts.join(' | '), debugInfo });
                });
                return results;
            }
        """)

        for c in card_info:
            print(f"\nCard {c['idx']}: {c['name']}")
            print(f"  Labels: {c['labelTexts']}")
            print(f"  CR: '{c['crNumber']}'")
            print(f"  Debug: {c['debugInfo']}")

        await browser.close()


asyncio.run(check())
