import csv
months = set()
with open(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\rega_scraper\REGA_Qualified_Companies.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        for field in ['Qualification Start', 'Qualification End']:
            val = row.get(field, '').strip()
            if val and val != '-':
                parts = val.split()
                if len(parts) == 3:
                    months.add(parts[1])
print(sorted(months))
print(f'Total unique month names: {len(months)}')
