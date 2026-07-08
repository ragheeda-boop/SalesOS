import json
import csv
import os
import time
import asyncio
from openpyxl import Workbook
from config import (
    CSV_PATH, XLSX_PATH, JSON_PATH, STATE_PATH,
    FIELD_NAMES, FIELD_LABELS,
    TEMP_SUFFIX, FILE_RETRY_DELAYS,
)


def _tmp_path(path):
    parent = os.path.dirname(path) or "."
    name = os.path.basename(path) + TEMP_SUFFIX
    return os.path.join(parent, name)


def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _write_with_retry(path, write_fn):
    for attempt, delay in enumerate(FILE_RETRY_DELAYS):
        try:
            write_fn()
            return
        except OSError as e:
            if attempt == len(FILE_RETRY_DELAYS) - 1:
                raise
            time.sleep(delay)


def _atomic_write(path, write_fn):
    tmp = _tmp_path(path)
    _ensure_dir(tmp)
    _ensure_dir(path)

    def do_write():
        write_fn(tmp)
        if os.path.exists(path):
            os.replace(tmp, path)
        else:
            os.rename(tmp, path)

    _write_with_retry(path, do_write)


def _direct_write(path, write_fn):
    _ensure_dir(path)

    def do_write():
        write_fn(path)

    _write_with_retry(path, do_write)


def _write_json_to(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


class Storage:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._buffer = []
        self._seen = set()
        self._total_flushed = 0
        self._labels = [FIELD_LABELS.get(k, k) for k in FIELD_NAMES]
        self._dirty = False

    @property
    def count(self):
        return self._total_flushed + len(self._buffer)

    def add(self, record: dict):
        sid = record.get("licenseNumber", "")
        if sid and sid in self._seen:
            return False
        if sid:
            self._seen.add(sid)
        self._buffer.append(record)
        self._dirty = True
        return True

    async def flush(self):
        if not self._dirty and not self._buffer:
            return
        async with self._lock:
            if not self._buffer:
                self._dirty = False
                return
            to_flush = self._buffer
            self._buffer = []
            self._dirty = False

            self._append_csv(to_flush)
            self._rebuild_json()
            self._rebuild_xlsx()

            self._total_flushed += len(to_flush)

    def get_unprocessed_pages(self, total_pages: int) -> set:
        state = self._load_state()
        csv_pages = state.get("processed_pages", [])
        csv_row_count = self._count_csv_rows()

        if csv_row_count < len(csv_pages):
            csv_pages = csv_pages[:csv_row_count]

        processed = set(csv_pages)
        if len(processed) >= total_pages:
            return set()
        return {p for p in range(1, total_pages + 1) if p not in processed}

    async def save_state(self, page: int, total_pages: int, processed_set: set):
        state = {
            "processed_pages": sorted(processed_set),
            "total_records": len(processed_set),
            "total_pages": total_pages,
        }
        _atomic_write(STATE_PATH, lambda p: _write_json_to(p, state))

    def rebuild_dedup_from_csv(self):
        seen = set()
        try:
            with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    lic = row.get("license_number", "") or row.get("licenseNumber", "")
                    if lic:
                        seen.add(lic)
        except (FileNotFoundError, csv.Error):
            pass
        self._seen = seen

    def _append_csv(self, rows):
        flat = [self._flatten(r) for r in rows]
        _direct_write(
            CSV_PATH,
            lambda _p: self._write_csv_append(flat),
        )

    def _write_csv_append(self, flat_rows):
        file_exists = os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0
        mode = "a" if file_exists else "w"
        with open(CSV_PATH, mode, encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self._labels)
            if not file_exists:
                w.writeheader()
            w.writerows(flat_rows)

    def _rebuild_json(self):
        all_rows = self._read_all_csv_rows()
        _atomic_write(JSON_PATH, lambda p: _write_json_to(p, all_rows))

    def _rebuild_xlsx(self):
        all_rows = self._read_all_csv_rows()
        _atomic_write(XLSX_PATH, lambda p: self._write_xlsx_to(p, all_rows))

    def _read_all_csv_rows(self):
        try:
            with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))
        except (FileNotFoundError, csv.Error):
            return []

    def _write_xlsx_to(self, path, rows):
        wb = Workbook()
        ws = wb.active
        ws.title = "Lawyers"
        ws.append(self._labels)
        for r in rows:
            ws.append([r.get(l, "") for l in self._labels])
        wb.save(path)

    def _count_csv_rows(self):
        try:
            with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
                for i, _ in enumerate(f):
                    pass
            return max(0, i)
        except (FileNotFoundError, NameError):
            return 0

    def _flatten(self, record: dict) -> dict:
        return {FIELD_LABELS.get(k, k): record.get(k, "") for k in FIELD_NAMES}

    def _load_state(self) -> dict:
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"processed_pages": [], "total_records": 0, "total_pages": 0}
