import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file if present

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

DB_IDS = {
    "sfda": "35969edd-f301-8135-9baf-eed1ef4e717b",
    "engineering_offices": "b85c24be-6aa9-41a3-95dc-33fd1c5f566a",
    "contractors": "25384c7f-9128-462b-8737-773004e7d1bd",
    "suppliers": "a4daa26b-89ca-4ef9-89e4-c24f33e5b765",
    "companies": "331e04a6-2da7-4afe-9ab6-b0efead39200",
    "contacts": "9ca842d2-0aa9-460b-bdd9-58d0aa940d9c"
}

SHEET_ID = ""

DB_NAMES = {
    "sfda": "SFDA",
    "engineering_offices": "Engineering Offices",
    "contractors": "Contractors",
    "suppliers": "Suppliers",
    "companies": "Companies",
    "contacts": "Contacts"
}

DB_NAMES_AR = {
    "sfda": "الهيئة العامة للغذاء والدواء",
    "engineering_offices": "المكاتب الهندسية",
    "contractors": "المقاولون",
    "suppliers": "الموردون",
    "companies": "الشركات",
    "contacts": "جهات الاتصال"
}
