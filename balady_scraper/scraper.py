"""Main scraper orchestrator for Balady Engineering Offices"""

import os
import time
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from config import DETAILS
from api import BaladyAPI
from parser import parse_load_data_response, parse_details_page
from utils import ProgressTracker, setup_logging


class BaladyScraper:
    def __init__(self, log_dir="."):
        self.api = BaladyAPI()
        self.log_dir = log_dir
        self.success_logger, self.failed_logger, self.progress_logger = setup_logging(log_dir)
        self.tracker = None
        self.list_offices = []
        self.detailed_offices = {}
        self._lock = Lock()
        self._failures = 0

    def scrape(self):
        self.progress_logger.info("=" * 60)
        self.progress_logger.info("Balady Engineering Offices Scraper — FULL DETAILS")
        self.progress_logger.info("=" * 60)

        self._phase1_collect_list()
        self._phase2_scrape_details()
        self._phase3_save()
        return self.detailed_offices

    def _phase1_collect_list(self):
        self.progress_logger.info("\n--- Phase 1: Collecting office list from LoadData API ---")
        total = self.api.get_total_records()
        self.progress_logger.info(f"Total records to process: {total}")
        def cb(processed, total, batch):
            for item in parse_load_data_response({"data": batch}):
                self.list_offices.append(item)
            self.progress_logger.info(f"  [{processed}/{total}] {processed/total*100:.1f}%")
        self.api.fetch_all_offices(progress_callback=cb)
        self.progress_logger.info(f"  Done. {len(self.list_offices)} offices in list.")

    def _phase2_scrape_details(self):
        self.progress_logger.info("\n--- Phase 2: Scraping Details pages ---")
        total = len(self.list_offices)
        self.tracker = ProgressTracker(total, self.log_dir)
        processed = [0]

        resume_file = os.path.join(self.log_dir, "detailed_offices_partial.json")
        if os.path.exists(resume_file):
            try:
                with open(resume_file, "r", encoding="utf-8") as f:
                    self.detailed_offices = json.load(f)
                processed[0] = len(self.detailed_offices)
                self.progress_logger.info(f"  Resuming: {processed[0]} offices already scraped")
            except Exception:
                self.detailed_offices = {}

        offices_to_scrape = [o for o in self.list_offices if o["office_id"] not in self.detailed_offices]
        self.progress_logger.info(f"  Offices to scrape: {len(offices_to_scrape)}")

        def scrape_one(office):
            time.sleep(DETAILS["worker_delay"])
            office_id = office["office_id"]
            hashed = office.get("hashed_office_id", "")
            if not hashed:
                return office_id, None, "no_hashed_id"
            try:
                html = self.api.fetch_details_page(hashed)
                if "ssoapp" in html.lower() or "login" in html[:1000].lower():
                    return office_id, None, "sso_redirect"
                details = parse_details_page(html, office_id, hashed)
                for k, v in office.items():
                    if k not in details and v is not None:
                        details[k] = v
                return office_id, details, None
            except Exception as e:
                return office_id, None, str(e)

        with ThreadPoolExecutor(max_workers=DETAILS["concurrent_workers"]) as executor:
            futures = {executor.submit(scrape_one, o): o for o in offices_to_scrape}
            for future in as_completed(futures):
                office_id, details, error = future.result()
                with self._lock:
                    processed[0] += 1
                    if error:
                        self._failures += 1
                        self.failed_logger.warning(f"FAIL | {office_id} | {error}")
                    elif details:
                        self.detailed_offices[office_id] = details
                        self.success_logger.info(f"OK   | {office_id} | {str(details.get('office_name', ''))[:40]}")
                    self.tracker.update(processed[0])
                    if processed[0] % 100 == 0 or processed[0] == total:
                        line = self.tracker.get_progress_line()
                        self.progress_logger.info(f"  {line}")
                        # Atomic partial save for resume
                        tmp = resume_file + ".tmp"
                        with open(tmp, "w", encoding="utf-8") as f:
                            json.dump(self.detailed_offices, f, ensure_ascii=False)
                        os.replace(tmp, resume_file)

        if os.path.exists(resume_file):
            os.remove(resume_file)

        self.progress_logger.info(f"\n  Details complete: {len(self.detailed_offices)} success, {self._failures} failed")

    def _phase3_save(self):
        self.progress_logger.info("\n--- Phase 3: Validation & Export ---")
        offices_list = list(self.detailed_offices.values())
        total = len(self.list_offices)
        with_details = len(offices_list)

        ids_in_details = {o.get("office_id") for o in offices_list}
        ids_in_list = {o.get("office_id") for o in self.list_offices}
        missing_ids = ids_in_list - ids_in_details

        self.progress_logger.info(f"  Total: {total} | With details: {with_details} | Missing: {len(missing_ids)}")
        for mid in sorted(missing_ids):
            self.failed_logger.warning(f"MISSING | {mid}")

        all_ids = [o["office_id"] for o in offices_list if o.get("office_id")]
        if len(all_ids) == len(set(all_ids)):
            self.progress_logger.info("  Duplicates: NONE")
        else:
            self.progress_logger.warning(f"  Duplicates: {len(all_ids) - len(set(all_ids))}")

        all_fields = set()
        for o in offices_list:
            all_fields.update(o.keys())
        self.progress_logger.info(f"  Unique fields: {len(all_fields)}")
        for f in sorted(all_fields):
            non_null = sum(1 for o in offices_list if o.get(f) not in (None, "", [], {}))
            self.progress_logger.info(f"    {f}: {non_null}/{with_details}")

        from export import export_all
        results = export_all(offices_list, full=True)
        self.progress_logger.info("\n--- Output Files ---")
        for fmt, path in results.items():
            if path:
                self.progress_logger.info(f"  {fmt.upper()}: {os.path.abspath(path)}")
