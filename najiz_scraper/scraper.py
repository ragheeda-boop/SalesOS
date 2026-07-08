import asyncio
import time
import logging
from api import NajizAPI
from storage import Storage
from config import SAVE_INTERVAL, MAX_CONCURRENT

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self):
        self._api = NajizAPI()
        self._storage = Storage()
        self._processed_set = set()
        self._last_save_count = 0
        self._batch_size = MAX_CONCURRENT * 4

    async def run(self):
        print("Connecting to Najiz API...", flush=True)

        total_pages = await self._api.get_total_pages()
        if total_pages == 0:
            print("ERROR: Could not determine total pages.")
            await self._api.close()
            return

        self._storage.rebuild_dedup_from_csv()

        pending = self._storage.get_unprocessed_pages(total_pages)
        if not pending:
            print(f"All {total_pages} records already scraped.")
            await self._flush_and_state(total_pages)
            await self._api.close()
            return

        self._processed_set = {
            p for p in range(1, total_pages + 1) if p not in pending
        }

        print(f"Total records: {total_pages}")
        print(f"Resuming from record {len(self._processed_set) + 1}")
        print()

        sorted_pending = sorted(pending)
        idx = 0
        last_progress_time = 0

        while idx < len(sorted_pending):
            batch = sorted_pending[idx : idx + self._batch_size]
            idx += self._batch_size

            results = await self._api.fetch_batch(batch)

            for page, data in results:
                self._processed_set.add(page)
                if data and data.get("data"):
                    for record in data["data"]:
                        self._storage.add(record)

            if self._storage.count - self._last_save_count >= SAVE_INTERVAL:
                await self._flush_and_state(total_pages)

            now = time.time()
            if now - last_progress_time >= 1.0:
                print(
                    f"Page {min(batch)}-{max(batch)} / {total_pages}  |  "
                    f"Record {self._storage.count} / {total_pages}",
                    flush=True,
                )
                last_progress_time = now

        await self._flush_and_state(total_pages)
        print(
            f"\nDone! {self._storage.count} records -> data/lawyers.(csv|xlsx|json)",
            flush=True,
        )
        await self._api.close()

    async def _flush_and_state(self, total_pages):
        await self._storage.flush()
        self._last_save_count = self._storage.count
        last_processed = max(self._processed_set) if self._processed_set else 0
        await self._storage.save_state(
            last_processed, total_pages, self._processed_set
        )
