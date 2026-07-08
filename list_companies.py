import json
data = json.load(open('companies.json', 'r', encoding='utf-8'))
with open('companies_list.txt', 'w', encoding='utf-8') as f:
    f.write(f'Total companies: {len(data)}\n\n')
    for i, c in enumerate(data[:30]):
        f.write(f'{c["mid"]} | {c["std_name"]}\n')
print('Written to companies_list.txt')
