"""Configuration for Balady Engineering Offices Scraper"""

BASE_URL = "https://apps.balady.gov.sa"
ENDPOINTS = {
    "load_data": "/Eservices/Inquiries/InquiryEngOffices/LoadData",
    "get_cards": "/Eservices/Inquiries/InquiryEngOffices/GetCardsPagged",
    "get_cities": "/Eservices/Inquiries/InquiryEngOffices/GetCities",
    "details": "/Eservices/Inquiries/InquiryEngOffices/Details",
    "download_file": "/Eservices/Inquiries/InquiryEngOffices/DownloadFile",
}

AJAX_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://apps.balady.gov.sa/Eservices/Inquiries/InquiryEngOffices",
}

HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

PAGINATION = {
    "batch_size": 2000,
    "max_batch_size": 2000,
    "card_page_size": 1000,
}

DETAILS = {
    "timeout": 30,
    "retries": 5,
    "concurrent_workers": 2,
    "worker_delay": 0.5,
    "max_retry_delay": 60,
    "rate_limit_backoff": 30,
}

OUTPUT = {
    "csv": "engineering_offices.csv",
    "xlsx": "engineering_offices.xlsx",
    "json": "engineering_offices.json",
}

LOGS = {
    "success": "success.log",
    "failed": "failed.log",
    "progress": "progress.log",
}
