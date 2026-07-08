import json, openpyxl
from datetime import datetime

# Load companies
companies = json.load(open(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\companies.json', encoding='utf-8'))
today = datetime.now().strftime('%Y-%m-%d')

# Batch 1 enrichment data compiled from web research
enriched = {}

enriched['COMP-000001'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Facebook: Basma Zad بصمة زاد للدعايا والاعلان',
    'source2': 'dlilsa.com directory listing',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': False,
    'reason': ''
}

enriched['COMP-000002'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Search returned no direct match',
    'source2': 'Name is generic (means "Arab Flowers")',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': False,
    'reason': ''
}

enriched['COMP-000003'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Facebook: معمل الفاخر للأصناف الحارة و الوجبات الشعبية',
    'source2': 'Possible: mlhamet-alfakher.com',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': False,
    'reason': ''
}

enriched['COMP-000004'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Search returned مخابز بدر (Badr Bakeries) - name variant',
    'source2': 'badr.com.sa - likely different entity',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': False,
    'reason': ''
}

enriched['COMP-000005'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'No direct results found',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'No web presence found'
}

enriched['COMP-000006'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'No direct match (generic name)',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'No web presence found'
}

enriched['COMP-000007'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Instagram: marja_juices (المرجع | مرجع العصيرات)',
    'source2': 'Al Qatif juice restaurant',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': False,
    'reason': ''
}

enriched['COMP-000008'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': 'https://www.linkedin.com/in/مؤسسة-محمص-للتجارة-والتجزئه-a93b97377',
    'li_conf': 50,
    'source1': 'LinkedIn profile found',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'Yes',
    'failed': False,
    'reason': ''
}

enriched['COMP-000009'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': 'https://www.linkedin.com/company/bahasan-trading',
    'li_conf': 70,
    'source1': 'LinkedIn: شركة باحسن التجارية',
    'source2': 'directoryksa.com listing',
    'has_ws': 'No',
    'has_li': 'Yes',
    'failed': False,
    'reason': ''
}

enriched['COMP-000010'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000011'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000012'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Search returned generic hypermarket results',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Name too generic for direct match'
}

enriched['COMP-000013'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000014'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000015'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000016'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000017'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000018'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000019'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000020'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000021'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000022'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000023'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000024'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': '',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000025'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Has email: yhaddad@alnahdico.com',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000026'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Has email: yasseralghamdi.for.ceramics@gmail.com',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000027'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Has email: yasser@almarwani.com',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000028'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Has email: waterfishsa@gmail.com - brand name "Waterfish"',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

enriched['COMP-000029'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Has email: waqas.anwar@sedres.com - domain: sedres.com',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': False,
    'reason': ''
}

enriched['COMP-000030'] = {
    'website': '',
    'ws_conf': 0,
    'linkedin': '',
    'li_conf': 0,
    'source1': 'Has email: wael_almogy@hotmail.com',
    'source2': '',
    'has_ws': 'No',
    'has_li': 'No',
    'failed': True,
    'reason': 'Pending further research'
}

# Open workbook and populate
wb = openpyxl.load_workbook(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\CRM_Enriched_Final.xlsx')
ws1 = wb['ENRICHED_COMPANIES']
ws2 = wb['FAILED_LOOKUPS']

row1 = 2
row2 = 2

for c in companies:
    mid = c['mid']
    name = c['std_name']
    e = enriched.get(mid, {})
    if not e:
        e = {'website': '', 'ws_conf': 0, 'linkedin': '', 'li_conf': 0,
             'source1': '', 'source2': '', 'has_ws': 'No', 'has_li': 'No',
             'failed': True, 'reason': 'Pending research'}

    if e.get('failed') and e.get('ws_conf', 0) < 70 and e.get('li_conf', 0) < 70:
        ws2.cell(row=row2, column=1, value=mid)
        ws2.cell(row=row2, column=2, value=name)
        ws2.cell(row=row2, column=3, value='Yes' if e['website'] else 'No')
        ws2.cell(row=row2, column=4, value='Yes' if e['linkedin'] else 'No')
        ws2.cell(row=row2, column=5, value=e.get('reason', 'No web presence found'))
        ws2.cell(row=row2, column=6, value=today)
        row2 += 1
    else:
        ws1.cell(row=row1, column=1, value=mid)
        ws1.cell(row=row1, column=2, value=name)
        ws1.cell(row=row1, column=3, value=e['website'])
        ws1.cell(row=row1, column=4, value=e['ws_conf'])
        ws1.cell(row=row1, column=5, value=e['linkedin'])
        ws1.cell(row=row1, column=6, value=e['li_conf'])
        ws1.cell(row=row1, column=7, value=e.get('source1', ''))
        ws1.cell(row=row1, column=8, value=e.get('source2', ''))
        ws1.cell(row=row1, column=9, value=e['has_ws'])
        ws1.cell(row=row1, column=10, value=e['has_li'])
        ws1.cell(row=row1, column=11, value=today)
        row1 += 1

wb.save(r'C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\CRM_Enriched_Final.xlsx')
print(f'ENRICHED_COMPANIES: {row1-2} rows')
print(f'FAILED_LOOKUPS: {row2-2} rows')
print(f'Total: {row1+row2-4}')
