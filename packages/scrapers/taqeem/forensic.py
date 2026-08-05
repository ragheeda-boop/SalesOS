"""
Forensic investigation of Taqeem facilities directory.
Captures ALL network traffic, detects API endpoints, and determines the true total count.
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def investigate():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-US")

        page = await context.new_page()

        # Capture ALL network requests
        requests_log = []
        responses_log = []

        async def on_request(request):
            url = request.url
            if any(k in url for k in ['.js', '.css', '.png', '.svg', '.ico', '.woff', 'google', 'userway',
                                       'cloudflare', 'gstatic']):
                return
            requests_log.append({
                'url': url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data,
            })

        async def on_response(response):
            url = response.url
            if any(k in url for k in ['.js', '.css', '.png', '.svg', '.ico', '.woff', 'google', 'userway',
                                       'cloudflare', 'gstatic']):
                return
            ct = response.headers.get('content-type', '')
            try:
                body = await response.text()
            except Exception:
                body = None
            responses_log.append({
                'url': url,
                'status': response.status,
                'content_type': ct,
                'body_length': len(body) if body else 0,
                'body': (body[:5000] if body and ('json' in ct or 'text' in ct) else None),
            })

        page.on('request', on_request)
        page.on('response', on_response)

        # Step 1: Load the main page
        print("=" * 70)
        print("STEP 1: Loading main facilities page")
        print("=" * 70)
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?sector=all",
            wait_until="load",
            timeout=60000,
        )
        await page.wait_for_timeout(5000)

        # Extract all text and search for total count
        body_text = await page.evaluate("() => document.body.innerText")
        print(f"\n--- Body text (first 3000 chars) ---")
        print(body_text[:3000])

        # Check for total count in various forms
        import re
        count_matches = re.findall(r'(\d[\d,]*)\s*(?:result|facilit|record|facility)', body_text, re.IGNORECASE)
        print(f"\n--- Count matches in text: {count_matches}")

        # Check for total in HTML
        html = await page.content()
        count_in_html = re.findall(r'(\d[\d,]*)\s*(?:result|facilit|record)', html, re.IGNORECASE)
        print(f"Count matches in HTML: {count_in_html}")

        print("\n--- All non-static requests ---")
        for r in requests_log:
            print(f"  {r['method']} {r['url'][:120]}")

        print("\n--- All non-static responses with JSON ---")
        for r in responses_log:
            if 'json' in r['content_type']:
                print(f"  [{r['status']}] {r['url'][:120]} (len={r['body_length']})")
                if r['body']:
                    # Check if it contains facility data
                    if 'facilit' in r['body'].lower() or 'result' in r['body'].lower() or 'count' in r['body'].lower():
                        print(f"    --> Contains relevant data!")
                        print(f"    Body: {r['body'][:2000]}")

        # Step 2: Try different page sizes
        print("\n" + "=" * 70)
        print("STEP 2: Trying different URL patterns")
        print("=" * 70)

        # Try page 6 (beyond the detected 5 pages)
        print("\n--- Trying page 6 ---")
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities/page/6?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(3000)

        cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
        print(f"  Cards found on page 6: {len(cards)}")

        pagination = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('.pagination a');
                return Array.from(links).map(a => ({
                    href: a.getAttribute('href'),
                    text: a.textContent.trim(),
                }));
            }
        """)
        print(f"  Pagination links: {json.dumps(pagination, ensure_ascii=False)}")

        # Step 3: Try with step=100 to get more per page
        print("\n--- Trying step=100 ---")
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=100",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(5000)
        cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
        print(f"  Cards found with step=100: {len(cards)}")
        pagination = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('.pagination a');
                return Array.from(links).map(a => ({
                    href: a.getAttribute('href'),
                    text: a.textContent.trim(),
                }));
            }
        """)
        print(f"  Pagination links: {json.dumps(pagination, ensure_ascii=False)}")

        # Check page count with step=100
        page_count = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('.pagination .page-item a[href*=\"/en/facilities/page/\"]');
                let max = 1;
                links.forEach(a => {
                    const m = a.getAttribute('href').match(/\\/page\\/(\\d+)/);
                    if (m) { const n = parseInt(m[1]); if (n > max) max = n; }
                });
                return max;
            }
        """)
        print(f"  Max page detected with step=100: {page_count}")

        # Step 3.5: Go to page 49 to see if it exists
        print("\n--- Trying page 49 (step=9) ---")
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities/page/49?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(3000)
        cards_p49 = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
        print(f"  Cards found on page 49: {len(cards_p49)}")
        pagination_p49 = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('.pagination a');
                return Array.from(links).map(a => ({
                    href: a.getAttribute('href'),
                    text: a.textContent.trim(),
                }));
            }
        """)
        print(f"  Pagination links: {json.dumps(pagination_p49, ensure_ascii=False)}")

        print("\n--- Trying page 50 (step=9) should be invalid ---")
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities/page/50?classification=all&sector=all&region=all&search_in=all&step=9",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(3000)
        cards_p50 = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
        print(f"  Cards found on page 50: {len(cards_p50)}")
        body_p50 = await page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"  Body: {body_p50}")

        # Step 4: Try without sector filter but with all params
        print("\n--- Trying explicit all params ---")
        await page.goto(
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(5000)
        cards = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
        print(f"  Cards found: {len(cards)}")
        body_text2 = await page.evaluate("() => document.body.innerText")
        count_matches2 = re.findall(r'(\d[\d,]*)\s*(?:result|facilit|record)', body_text2, re.IGNORECASE)
        print(f"  Count matches: {count_matches2}")
        # Look for total count
        show_text = await page.evaluate("""
            () => {
                const pages = document.querySelectorAll('.pagination');
                if (!pages.length) return 'NO PAGINATION';
                // Get text around pagination
                const parent = pages[0].parentElement?.parentElement;
                return parent ? parent.textContent.trim() : pages[0].textContent.trim();
            }
        """)
        print(f"  Pagination area text: {show_text[:500]}")

        # Step 5: Look at the XHR responses more carefully for API
        print("\n" + "=" * 70)
        print("STEP 3: Looking for hidden facility data in page")
        print("=" * 70)

        # Check if facilities are embedded in a script tag
        scripts = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                return Array.from(scripts).map(s => ({
                    src: s.src || 'inline',
                    type: s.type,
                    length: (s.textContent || '').length,
                    text: (s.textContent || '').substring(0, 2000),
                })).filter(s => s.length > 100);
            }
        """)
        for s in scripts:
            txt = s['text'].lower()
            if 'facilit' in txt or 'record' in txt or 'total' in txt or 'count' in txt or 'paginat' in txt or 'odoo' in txt:
                print(f"\n  Script [{s['src'][:60]}]: len={s['length']}")
                print(f"  Content preview: {s['text'][:1000]}")

        # Step 6: Check for API in the page source
        print("\n" + "=" * 70)
        print("STEP 4: Checking for API endpoints in HTML")
        print("=" * 70)
        apis = re.findall(r'(/api/[\w/]+|/web/[\w/]+|/facilities/[\w/]+|controller[\w/]+)', html, re.IGNORECASE)
        print(f"  API-like paths: {list(set(apis))[:20]}")

        # Step 7: Try to access an Odoo JSON-RPC endpoint if it exists
        print("\n" + "=" * 70)
        print("STEP 5: Trying Odoo JSON-RPC API")
        print("=" * 70)
        from playwright.async_api import expect

        # Odoo often has /web/dataset/search_read or similar
        api_urls = [
            "https://www.taqeem.gov.sa/web/dataset/search_read",
            "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9",
        ]

        # Look in the page for any JSON-RPC calls
        print("\n  Checking responses for JSON-RPC (Odoo API calls)...")
        for r in responses_log:
            body = r.get('body')
            if body and ('jsonrpc' in body or 'json-rpc' in body):
                print(f"  JSON-RPC endpoint: {r['url']}")
                print(f"  Body: {body[:3000]}")

        # Step 8: Look for any form/API submission
        print("\n" + "=" * 70)
        print("STEP 6: Checking page elements for forms and AJAX")
        print("=" * 70)

        elements = await page.evaluate("""
            () => {
                const forms = document.querySelectorAll('form');
                const inputs = document.querySelectorAll('input[type=\"hidden\"]');
                const data_attrs = [];
                document.querySelectorAll('[data-*]').forEach(el => {
                    const attrs = el.getAttributeNames().filter(a => a.startsWith('data-'));
                    attrs.forEach(a => data_attrs.push({ tag: el.tagName, attr: a, val: el.getAttribute(a).substring(0, 100) }));
                });
                return {
                    forms: Array.from(forms).map(f => ({ action: f.action, method: f.method, id: f.id })),
                    inputs: Array.from(inputs).map(i => ({ name: i.name, value: i.value?.substring(0, 200) })),
                    data_attrs: data_attrs.slice(0, 20),
                };
            }
        """)
        print(f"  Forms: {json.dumps(elements['forms'], ensure_ascii=False)}")
        print(f"  Hidden inputs: {json.dumps(elements['inputs'], ensure_ascii=False)}")

        # Step 9: Try to find total count on page 1 with all filters
        print("\n" + "=" * 70)
        print("STEP 7: Looking for total count in pagination element")
        print("=" * 70)

        pagination_html = await page.evaluate("""
            () => {
                const pag = document.querySelector('.pagination');
                if (!pag) return 'NO PAGINATION';
                return pag.parentElement ? pag.parentElement.parentElement.innerHTML : pag.outerHTML;
            }
        """)
        print(f"  Pagination area HTML: {pagination_html[:2000]}")

        # Check for any "Showing X-Y of Z" text
        showing = await page.evaluate("""
            () => {
                const els = document.querySelectorAll('[class*=\"showing\"], [class*=\"info\"], [class*=\"count\"], [class*=\"total\"]');
                return Array.from(els).map(e => ({ class: e.className, text: e.textContent.trim() }));
            }
        """)
        print(f"  Showing/count elements: {json.dumps(showing, ensure_ascii=False)}")

        # Look for the total count in any element
        all_elements_text = await page.evaluate("""
            () => {
                const results = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (/\\d+/.test(text) && text.length < 100 && text.length > 3) {
                        results.push(text);
                    }
                }
                // Find texts containing numbers
                return results.filter(t => /\\b\\d{2,}\\b/.test(t)).slice(0, 50);
            }
        """)
        print(f"  All text nodes with numbers: {all_elements_text}")

        # Step 10: Check the URL for Arabic version - maybe more data there?
        print("\n" + "=" * 70)
        print("STEP 8: Checking Arabic version")
        print("=" * 70)
        await page.goto(
            "https://www.taqeem.gov.sa/ar/facilities?sector=all",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(5000)
        body_text_ar = await page.evaluate("() => document.body.innerText")
        count_matches_ar = re.findall(r'(\d[\d,]*)\s*(?:نتيجة|منشأة|مرفق|صفحة)', body_text_ar, re.IGNORECASE)
        print(f"  Arabic count matches: {count_matches_ar}")
        cards_ar = await page.query_selector_all("div.col-lg-4.col-md-6.col-12")
        print(f"  Cards in Arabic: {len(cards_ar)}")

        pagination_ar = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('.pagination a');
                return Array.from(links).map(a => ({
                    href: a.getAttribute('href'),
                    text: a.textContent.trim(),
                }));
            }
        """)
        print(f"  Arabic pagination: {json.dumps(pagination_ar, ensure_ascii=False)}")

        print("\n" + "=" * 70)
        print("FORENSIC COMPLETE")
        print("=" * 70)

        await browser.close()


asyncio.run(investigate())
