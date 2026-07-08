import csv
with open(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\rega_scraper\REGA_Qualified_Companies.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ln = row.get('License Number', '').strip()
        if ln in ('E109', '2072', '1602'):
            qs = row.get('Qualification Start', '')
            qe = row.get('Qualification End', '')
            name = row.get('Company Name', '')[:40]
            print(f'LN={ln} | QS=[{qs}] | QE=[{qe}] | Name={name}')
