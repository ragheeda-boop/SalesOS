import os
import platform

BASE_URL = "https://najiz.sa"
API_ENDPOINT = "/applications/lawyers/api/Lawyers/GetLawyersByPageCount"
FULL_API_URL = f"{BASE_URL}{API_ENDPOINT}"

# Output files
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(OUTPUT_DIR, "lawyers.csv")
XLSX_PATH = os.path.join(OUTPUT_DIR, "lawyers.xlsx")
JSON_PATH = os.path.join(OUTPUT_DIR, "lawyers.json")
STATE_PATH = os.path.join(OUTPUT_DIR, "state.json")

# Temp suffixes for atomic writes
TEMP_SUFFIX = ".tmp"

# Scraping tuning
MAX_CONCURRENT = 30
MAX_RETRIES = 5
TIMEOUT = 30
SAVE_INTERVAL = 100
REQUEST_DELAY = 0.05

# File write retry
FILE_RETRY_DELAYS = [1, 2, 5, 10]

FIELD_NAMES = [
    "fullName",
    "mobile",
    "iqamaCity",
    "officeName",
    "officeCity",
    "officeRegion",
    "officeStreet",
    "status",
    "licenseNumber",
    "licenceEndDateHijri",
    "certificateName",
    "facultyName",
    "degreeSpecial",
    "nationality",
    "email",
]

FIELD_LABELS = {
    "fullName": "full_name",
    "mobile": "mobile_number",
    "iqamaCity": "city",
    "officeName": "office_name",
    "officeCity": "office_city",
    "officeRegion": "office_region",
    "officeStreet": "office_street",
    "status": "license_status",
    "licenseNumber": "license_number",
    "licenceEndDateHijri": "license_expiry_date_hijri",
    "certificateName": "certificate",
    "facultyName": "faculty",
    "degreeSpecial": "specialty",
    "nationality": "nationality",
    "email": "email",
}

# Headers to mimic a real browser
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Referer": f"{BASE_URL}/applications/lawyers/LawyersInquire",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}

IS_WINDOWS = platform.system() == "Windows"
IS_ONE_DRIVE = "OneDrive" in OUTPUT_DIR
