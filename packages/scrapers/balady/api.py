"""API client for Balady Engineering Offices"""

import time
import random
import requests
from config import BASE_URL, ENDPOINTS, AJAX_HEADERS, HTML_HEADERS, DETAILS


class BaladyAPI:
    """Handles all HTTP communication with Balady API"""

    def __init__(self):
        self.ajax_session = requests.Session()
        self.ajax_session.headers.update(AJAX_HEADERS)
        self.html_session = requests.Session()
        self.html_session.headers.update(HTML_HEADERS)
        self._total_records = None
        self._detail_count = 0
        # Prime sessions with main page visit
        self.ajax_session.get(f"{BASE_URL}{ENDPOINTS['load_data'].replace('LoadData', '')}", timeout=15)

    def _ajax_request(self, method, endpoint, **kwargs):
        url = f"{BASE_URL}{endpoint}"
        kwargs.setdefault("timeout", 30)
        for attempt in range(3):
            try:
                resp = self.ajax_session.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                if attempt == 2:
                    raise
                time.sleep((attempt + 1) * 2)

    def fetch_details_page(self, hashed_office_id):
        url = f"{BASE_URL}{ENDPOINTS['details']}?OfficeId={hashed_office_id}"
        max_retries = DETAILS["retries"]
        for attempt in range(max_retries):
            try:
                resp = self.html_session.get(url, timeout=DETAILS["timeout"])
                if resp.status_code == 429:
                    wait = DETAILS["rate_limit_backoff"] * (attempt + 1) + random.uniform(0, 5)
                    if attempt < max_retries - 1:
                        time.sleep(wait)
                        continue
                resp.raise_for_status()
                self._detail_count += 1
                return resp.text
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait = (attempt + 1) * 3 + random.uniform(0, 2)
                time.sleep(wait)
        raise RuntimeError(f"Failed to fetch details for {hashed_office_id}")

    def get_total_records(self):
        if self._total_records is not None:
            return self._total_records
        data = {
            "draw": 1, "start": 0, "length": 1,
            "regionId": -1, "cityId": -1, "textSearch": "", "activity": "",
        }
        resp = self._ajax_request("POST", ENDPOINTS["load_data"], data=data)
        self._total_records = resp.json().get("recordsFiltered", 0)
        return self._total_records

    def fetch_batch(self, start, length=2000):
        data = {
            "draw": (start // length) + 1,
            "start": start,
            "length": length,
            "regionId": -1, "cityId": -1, "textSearch": "", "activity": "",
        }
        resp = self._ajax_request("POST", ENDPOINTS["load_data"], data=data)
        return resp.json()

    def fetch_all_offices(self, progress_callback=None):
        total = self.get_total_records()
        batch_size = 2000
        all_offices = []
        for start in range(0, total, batch_size):
            result = self.fetch_batch(start, batch_size)
            offices = result.get("data", [])
            all_offices.extend(offices)
            if progress_callback:
                progress_callback(len(all_offices), total, offices)
        return all_offices


