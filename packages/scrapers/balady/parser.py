"""Parse Balady API responses and Details HTML pages"""

from bs4 import BeautifulSoup


def parse_load_data_response(response_json):
    offices = response_json.get("data", [])
    parsed = []
    for item in offices:
        office = {
            "office_id": item.get("OfficeId", ""),
            "office_name": item.get("OfficeName", ""),
            "classification_grade": item.get("ClassificationGrade"),
            "classification_status": item.get("ClassificationStatus"),
            "mobile_no": item.get("MobileNo"),
            "latitude": item.get("Y"),
            "longitude": item.get("X"),
            "hashed_office_id": item.get("HashedOfficeId", ""),
            "logo_url": item.get("LogoUrl", ""),
        }
        parsed.append(office)
    return parsed


def parse_details_page(html, office_id, hashed_office_id):
    """Dynamically extract all fields from the Details page HTML"""
    soup = BeautifulSoup(html, "lxml")
    data = {
        "office_id": office_id,
        "hashed_office_id": hashed_office_id,
    }

    # --- Method 1: Extract all label/value pairs from item-content-details divs ---
    detail_items = soup.find_all("div", class_="item-content-details")
    seen_labels = set()
    for item in detail_items:
        title_el = item.find("div", class_="title")
        desc_el = item.find("div", class_="description")
        if title_el and desc_el:
            label = title_el.get_text(strip=True)
            value = desc_el.get_text(strip=True)
            if label and value and label not in seen_labels:
                seen_labels.add(label)
                field = _label_to_field_name(label)
                # Keep existing value if duplicate (first occurrence wins)
                if field not in data:
                    data[field] = value

    # --- Method 2: Extract working hours table ---
    tables = soup.find_all("table")
    for table_idx, table in enumerate(tables):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = []
        header_row = rows[0]
        header_cells = header_row.find_all(["td", "th"])
        for cell in header_cells:
            cell_text = cell.get_text(strip=True)
            if cell_text:
                headers.append(cell_text)

        # Check if this is the working hours table
        row_text = " ".join(h.get_text(strip=True) for h in header_cells)
        if any(kw in row_text for kw in ["ايام العمل", "أيام العمل", "days", "ساعة", "دوام"]):
            working_hours = []
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                day_data = {}
                for idx, cell in enumerate(cells):
                    if idx < len(headers):
                        day_data[_label_to_field_name(headers[idx])] = cell.get_text(strip=True)
                if day_data:
                    working_hours.append(day_data)
            if working_hours:
                data["working_hours"] = working_hours
        else:
            # Could be activities/classification table
            activities = []
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                row_data = {}
                for idx, cell in enumerate(cells):
                    if idx < len(headers):
                        key = _label_to_field_name(headers[idx]) if headers[idx] else f"col_{idx}"
                        row_data[key] = cell.get_text(strip=True)
                if row_data:
                    activities.append(row_data)
            if activities:
                table_key = "activities" if any(kw in row_text for kw in ["نشاط", "النشاط", "activity"]) else f"table_{table_idx}"
                data[table_key] = activities

    return data


def _label_to_field_name(label):
    """Convert Arabic label to English field name"""
    mapping = {
        "اسم المنشأة": "office_name",
        "رقم ترخيص المكتب": "license_number",
        "رقم الترخيص": "license_number",
        "المنطقة \\ المدينة": "region_city",
        "المنطقة \u200f\\u200f المدينة": "region_city",
        "المنطقة \\u200f\\\\u200f المدينة": "region_city",
        "المنطقة": "region",
        "المدينة": "city",
        "حالة تصنيف المنشأة": "classification_status",
        "درجة تصنيف المنشأة": "classification_grade",
        "رقم الجوال": "mobile",
        "رقم الهاتف": "phone",
        "الموقع الالكتروني": "website",
        "البريد الالكتروني": "email",
        "رقم الفاكس": "fax",
        "العنوان": "address",
        "الاسم": "contact_name",
        "الرمز البريدي": "postal_code",
        "صندوق البريد": "pobox",
        "رقم السجل التجاري": "commercial_registration",
        "السجل التجاري": "commercial_registration",
        "تاريخ الترخيص": "license_date",
        "تاريخ الاصدار": "license_date",
        "تاريخ الانتهاء": "expiry_date",
        "تاريخ النهاية": "expiry_date",
        "حالة الترخيص": "license_status",
        "حالة المكتب": "office_status",
        "المدير": "manager",
        "مدير المكتب": "manager",
        "تصنيف المنشأة": "classification",
        "فئات التصنيف": "classification_categories",
        "الانشطة": "activities_text",
        "الموقع": "location",
        "الاحداثيات": "coordinates",
        "خط الطول": "longitude",
        "خط العرض": "latitude",
        "المنطقة \\ المدينة": "region_city",
        "المنطقة / المدينة": "region_city",
        "حي": "district",
        "الحي": "district",
        "الشارع": "street",
        "طريق": "street",
        "المملكة": "country",
    }
    if label in mapping:
        return mapping[label]

    # Fallback: generate snake_case from Arabic
    return f"field_{label[:30]}"
