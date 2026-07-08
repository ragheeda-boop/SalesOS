"""
Phase 2b: Find actual page structure and filter options
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def investigate():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="en-US")

        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load", timeout=60000)
        await page.wait_for_timeout(5000)

        # Find ALL selects on the page
        all_selects = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('select').forEach(s => {
                    results.push({
                        id: s.id,
                        name: s.name,
                        class: s.className,
                        options: Array.from(s.options).map(o => ({
                            value: o.value,
                            text: o.textContent.trim()
                        }))
                    });
                });
                return results;
            }
        """)
        print("ALL SELECT elements:")
        for s in all_selects:
            print(f"  name={s['name']}, id={s['id']}")
            for o in s['options']:
                print(f"    {o['value']}: {o['text']}")

        # Find the form and its structure
        form_html = await page.evaluate("""
            () => {
                const forms = document.querySelectorAll('form');
                return Array.from(forms).map(f => ({
                    action: f.action,
                    method: f.method,
                    id: f.id,
                    class: f.className,
                    inner: f.innerHTML.substring(0, 3000)
                }));
            }
        """)
        print("\n\nFORM structure:")
        for f in form_html:
            print(f"  action={f['action']}, method={f['method']}, id={f['id']}")
            print(f"  innerHTML: {f['inner']}")

        # Find the pagination area structure
        pagination_area = await page.evaluate("""
            () => {
                const pag = document.querySelector('.pagination');
                if (!pag) return 'NO PAGINATION';
                // Find the surrounding container
                let el = pag;
                for (let i = 0; i < 5; i++) {
                    el = el.parentElement;
                    if (!el) break;
                }
                return el ? el.outerHTML.substring(0, 3000) : 'no parent';
            }
        """)
        print(f"\n\nPagination area:\n{pagination_area}")

        # Find ALL elements with "from" and number for total count
        all_froms = await page.evaluate("""
            () => {
                const results = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                let node;
                while (node = walker.nextNode()) {
                    const t = node.textContent.trim();
                    if (/from\\s+\\d/.test(t)) {
                        results.push({
                            text: t.substring(0, 100),
                            parent: node.parentElement.className,
                            parent_html: node.parentElement.outerHTML.substring(0, 500)
                        });
                    }
                }
                return results;
            }
        """)
        print(f"\n\nAll 'from N' elements:")
        for r in all_froms:
            print(f"  Text: \"{r['text']}\"")
            print(f"  Class: {r['parent']}")
            print(f"  HTML: {r['parent_html']}")
            print()

        await browser.close()


asyncio.run(investigate())
