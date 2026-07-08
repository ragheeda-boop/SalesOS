"""
Phase 2: Deep investigation of Taqeem directory.
- Discover ALL sector options
- Check count per sector
- Find true total across all sectors
- Look for API/hidden data
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def investigate():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="en-US")

        # --- STEP 1: Get all sector options ---
        print("=" * 70)
        print("STEP 1: Discover sector options")
        print("=" * 70)
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load", timeout=60000)
        await page.wait_for_timeout(5000)

        # Get sector dropdown options
        sectors = await page.evaluate("""
            () => {
                const select = document.querySelector('select[name="sector"]');
                if (!select) return 'NO SECTOR SELECT';
                return Array.from(select.options).map(o => ({
                    value: o.value,
                    text: o.textContent.trim()
                }));
            }
        """)
        print(f"Sector options: {json.dumps(sectors, ensure_ascii=False, indent=2)}")

        # Get region options
        regions = await page.evaluate("""
            () => {
                const select = document.querySelector('select[name="region"]');
                if (!select) return 'NO REGION SELECT';
                return Array.from(select.options).map(o => ({
                    value: o.value,
                    text: o.textContent.trim()
                }));
            }
        """)
        print(f"\nRegion options: {json.dumps(regions, ensure_ascii=False, indent=2)[:2000]}")

        # Get classification options
        classifications = await page.evaluate("""
            () => {
                const select = document.querySelector('select[name="classification"]');
                if (!select) return 'NO CLASSIFICATION SELECT';
                return Array.from(select.options).map(o => ({
                    value: o.value,
                    text: o.textContent.trim()
                }));
            }
        """)
        print(f"\nClassification options: {json.dumps(classifications, ensure_ascii=False, indent=2)}")

        # --- STEP 2: Check total count per sector ---
        print("\n" + "=" * 70)
        print("STEP 2: Count per sector")
        print("=" * 70)
        for sec in sectors:
            if sec["value"] == "all":
                continue
            await page.goto(
                f"https://www.taqeem.gov.sa/en/facilities?classification=all&sector={sec['value']}&region=all&search_in=all&step=9",
                wait_until="load", timeout=60000)
            await page.wait_for_timeout(3000)
            count = await page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span.my-auto');
                    for (const sp of spans) {
                        const m = sp.textContent.match(/from\\s+(\\d+)/i);
                        if (m) return parseInt(m[1], 10);
                    }
                    return 0;
                }
            """)
            cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
            print(f"  Sector '{sec['text']}' (id={sec['value']}): count={count}, cards_on_page={len(cards)}")

        # --- STEP 3: Try to search with empty search_in (not all) ---
        print("\n" + "=" * 70)
        print("STEP 3: Try different URL combinations")
        print("=" * 70)

        # Try without search_in parameter
        urls_to_test = [
            ("sector=all, no search_in", "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&step=9"),
            ("no params", "https://www.taqeem.gov.sa/en/facilities?step=9"),
            ("with empty search", "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=4&region=all&search_in=&step=9"),
        ]
        for label, url in urls_to_test:
            await page.goto(url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(3000)
            count = await page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span.my-auto');
                    for (const sp of spans) {
                        const m = sp.textContent.match(/from\\s+(\\d+)/i);
                        if (m) return parseInt(m[1], 10);
                    }
                    return 0;
                }
            """)
            cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
            print(f"  {label}: count={count}, cards={len(cards)}")

        # --- STEP 4: Check the Arabic version for each sector ---
        print("\n" + "=" * 70)
        print("STEP 4: Arabic version counts per sector")
        print("=" * 70)
        for sec in sectors[:4]:
            await page.goto(
                f"https://www.taqeem.gov.sa/ar/facilities?classification=all&sector={sec['value']}&region=all&search_in=all&step=9",
                wait_until="load", timeout=60000)
            await page.wait_for_timeout(3000)
            count = await page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span.my-auto');
                    for (const sp of spans) {
                        const m = sp.textContent.match(/from\\s+(\\d+)/i);
                        if (m) return parseInt(m[1], 10);
                    }
                    return 0;
                }
            """)
            cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
            print(f"  AR Sector {sec['value']} '{sec['text']}': count={count}, cards={len(cards)}")

        # --- STEP 5: Try the form POST approach ---
        print("\n" + "=" * 70)
        print("STEP 5: Check what happens when you submit the search form")
        print("=" * 70)

        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities",
            wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)

        # Look at the search form
        form_info = await page.evaluate("""
            () => {
                const form = document.querySelector('form[action*=\"/en/facilities\"]');
                if (!form) return 'NO FORM';
                const inputs = form.querySelectorAll('input, select');
                return Array.from(inputs).map(i => ({
                    name: i.name,
                    value: i.value,
                    type: i.tagName.toLowerCase(),
                    options: i.options ? Array.from(i.options).map(o => ({v: o.value, t: o.textContent.trim()})) : null
                }));
            }
        """)
        print(f"Form inputs: {json.dumps(form_info, ensure_ascii=False, indent=2)[:3000]}")

        # --- STEP 6: Try to get a higher step ---
        print("\n" + "=" * 70)
        print("STEP 6: Try different step sizes to find max")
        print("=" * 70)
        for step in [50, 100, 200, 500]:
            await page.goto(
                f"https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step={step}",
                wait_until="load", timeout=60000)
            await page.wait_for_timeout(3000)
            cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
            print(f"  step={step}: cards={len(cards)}")

        # --- STEP 7: Check for hidden total in page source ---
        print("\n" + "=" * 70)
        print("STEP 7: Look for hidden total/JSON/data in page")
        print("=" * 70)
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)

        hidden = await page.evaluate("""
            () => {
                const results = [];
                // Check all meta tags
                document.querySelectorAll('meta').forEach(m => results.push({tag: 'meta', name: m.getAttribute('name'), content: m.getAttribute('content')}));
                // Check script tags for JSON data
                document.querySelectorAll('script').forEach(s => {
                    const txt = s.textContent || '';
                    if (txt.includes('total') || txt.includes('count') || txt.includes('facility') || txt.includes('records')) {
                        results.push({tag: 'script', id: s.id, src: s.src || 'inline', text: txt.substring(0, 1000)});
                    }
                });
                // Check for hidden inputs with totals
                document.querySelectorAll('input[type=\"hidden\"]').forEach(i => {
                    if (/\\d{3,}/.test(i.value)) results.push({tag: 'input', name: i.name, value: i.value.substring(0, 200)});
                });
                return results;
            }
        """)
        for h in hidden:
            print(f"  {h.get('tag','?')}: {json.dumps(h, ensure_ascii=False)[:500]}")

        # --- STEP 8: Look at the Odoo backend - try to find actual model name ---
        print("\n" + "=" * 70)
        print("STEP 8: Check for XHR/fetch calls to facility data")
        print("=" * 70)

        # Set up request monitoring
        requests_log = []
        async def on_response(response):
            url = response.url
            if any(k in url for k in ['/website/', '/web/image', '.js', '.css', '.png', '.ico', '.woff', '.ttf', 'google', 'cloudflare', 'gstatic', 'userway', 'fontawesome']):
                return
            ct = response.headers.get('content-type', '')
            if 'json' in ct or 'text' in ct:
                try:
                    body = await response.text()
                    if body and ('"result"' in body or '"count"' in body or '"total"' in body or 'facility' in body.lower()):
                        requests_log.append({
                            'url': url[:200],
                            'status': response.status,
                            'length': len(body),
                            'body': body[:5000]
                        })
                except:
                    pass

        page.on('response', on_response)

        # Re-navigate to trigger API calls
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)

        print("\n  Potentially relevant API responses:")
        for r in requests_log:
            print(f"  [{r['status']}] {r['url']}")
            print(f"    Body: {r['body'][:1000]}")

        # --- STEP 9: Check if there's a search API endpoint ---
        print("\n" + "=" * 70)
        print("STEP 9: Try to find API endpoints via common Odoo patterns")
        print("=" * 70)

        api_endpoints = [
            "/web/dataset/search_read",
            "/web/dataset/call",
            "/web/dataset/call_kw",
            "/web/dataset/search",
            "/website/search",
            "/api/v1/facilities",
            "/api/facilities",
            "/facilities/search",
            "/en/facilities/get_facilities",
        ]
        from playwright.async_api import expect
        for ep in api_endpoints[:5]:
            try:
                resp = await page.request.get(f"https://www.taqeem.gov.sa{ep}", timeout=10000)
                print(f"  {ep}: status={resp.status}")
                if resp.status == 200:
                    body = await resp.text()
                    print(f"    Body: {body[:500]}")
            except Exception as e:
                print(f"  {ep}: error={e}")

        print("\n" + "=" * 70)
        print("INVESTIGATION COMPLETE")
        print("=" * 70)
        await browser.close()


asyncio.run(investigate())
