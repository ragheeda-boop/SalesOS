import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\companies.json'
companies = json.load(open(path, encoding='utf-8'))

out = open(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\batch_list.txt', 'w', encoding='utf-8')
def o(s):
    out.write(s + '\n')
print(f'Total companies: {len(companies)}')
print()
print('=== BATCH 1 (first 30) ===')
for c in companies[:30]:
    print(f'{c["mid"]}: {c["std_name"]} | email={c["email"]} | phone={c["phone"]} | contact={c["contact"]}')
print()
print('=== BATCH 2 (next 70) ===')
for c in companies[30:100]:
    print(f'{c["mid"]}: {c["std_name"]}')
print()
print(f'Remaining: {len(companies)} - 100 = {len(companies) - 100}')
