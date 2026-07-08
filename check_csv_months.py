import csv
from collections import Counter

month_counter = Counter()
date_samples = []
with open(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\rega_scraper\REGA_Qualified_Companies.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        for field in ['Qualification Start', 'Qualification End']:
            val = row.get(field, '').strip()
            if val and val != '-':
                parts = val.split()
                if len(parts) == 3:
                    month_counter[parts[1]] += 1
                    if len(date_samples) < 20:
                        date_samples.append((i+2, field, val))

print("Month name frequencies:")
for month, count in month_counter.most_common():
    print(f"  '{month}' ({month.encode('unicode_escape').decode()}): {count}")

print("\nDate samples:")
for row_num, field, val in date_samples:
    print(f"  Row {row_num}, {field}: '{val}'")
