"""
screenshot_script.py
====================
Credit Card Screenshot Automation for GitHub Actions.
Sites are defined in config.py — edit URLs there, not here.
"""

import asyncio
import os
from datetime import datetime

import pandas as pd
from playwright.async_api import async_playwright

from config import CARD_OFFER_SITES as sites


async def take_screenshots_bulk(sites):
    timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'screenshots_{timestamp}'
    os.makedirs(output_dir, exist_ok=True)

    print(f"Output directory: {output_dir}\n")
    print("=" * 80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page    = await context.new_page()
        results = []

        for idx, site in enumerate(sites, 1):
            try:
                print(f"\n[{idx}/{len(sites)}] Capturing: {site['name']}")
                print(f"URL: {site['url']}")

                await page.goto(site['url'], wait_until='domcontentloaded', timeout=60000)

                wait_time = site.get('wait_time', 8)
                print(f"  Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)

                # Remove cookie/privacy banners
                for selector in [
                    '[class*="cookie"]', '[id*="cookie"]',
                    '[class*="privacy"]', '[id*="privacy"]',
                    '[class*="consent"]', '[id*="consent"]',
                    '#onetrust-banner-sdk', '.cookie-banner', '[role="dialog"]',
                ]:
                    try:
                        for el in await page.locator(selector).all():
                            try:
                                if await el.is_visible():
                                    await el.evaluate('el => el.style.display = "none"')
                            except:
                                pass
                    except:
                        pass

                await asyncio.sleep(1)

                safe_name = site['name'].replace(' ', '_').replace('/', '_')
                full_path = f"{output_dir}/{safe_name}_full.png"
                await page.screenshot(path=full_path, full_page=True)
                print(f"  ✅ {full_path}")

                results.append({
                    'name': site['name'], 'url': site['url'],
                    'status': 'Success', 'screenshot_file': full_path,
                    'timestamp': timestamp,
                })

            except Exception as e:
                print(f"  ❌ {str(e)[:150]}")
                results.append({
                    'name': site['name'], 'url': site['url'],
                    'status': f'Failed: {str(e)[:100]}', 'screenshot_file': None,
                    'timestamp': timestamp,
                })

        await browser.close()

    print("\n" + "=" * 80)
    success = sum(1 for r in results if r['status'] == 'Success')
    print(f"Total: {len(sites)}  |  Success: {success}  |  Failed: {len(sites)-success}")

    df = pd.DataFrame(results)
    summary = f"{output_dir}/summary.csv"
    df.to_csv(summary, index=False)
    print(f"\n✅ Summary: {summary}")
    print(df.to_string(index=False))

    return output_dir, results


if __name__ == "__main__":
    print(f"Starting Screenshot Automation — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sites: {len(sites)}")
    print("=" * 80)
    try:
        output_folder, results = asyncio.run(take_screenshots_bulk(sites))
        print("\n✅ Done!")
        exit(0)
    except Exception as e:
        import traceback
        print(f"\n❌ Failed: {e}")
        traceback.print_exc()
        exit(1)
