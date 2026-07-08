#!/usr/bin/env python3
import asyncio
import sys
from scraper import Scraper

async def main():
    scraper = Scraper()
    await scraper.run()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
