# -*- coding: utf-8 -*-
import json

data = json.load(open('indicators_clean.json', 'r', encoding='utf-8'))

has_notes = sum(1 for d in data if d.get('notes'))
has_code = sum(1 for d in data if d.get('code'))
has_subnotes = sum(1 for d in data if any(sub.get('notes') for sub in d.get('sub_indicators',[])))
has_subcode = sum(1 for d in data if any(sub.get('code') for sub in d.get('sub_indicators',[])))

print(f'含notes(注释)的主指标: {has_notes}')
print(f'含code(编码)的主指标: {has_code}')
print(f'含子指标notes: {has_subnotes}')
print(f'含子指标code: {has_subcode}')

# 看几条有notes/code的样例
for d in data[:20]:
    if d.get('notes') or d.get('code'):
        print()
        print(f'  name={d["name"][:30]}')
        print(f'  code={repr(d.get("code",""))}')
        print(f'  notes={repr(d.get("notes","")[:80])}')

# 也看看子指标
for d in data:
    for sub in d.get('sub_indicators', []):
        if sub.get('notes') or sub.get('code'):
            print()
            print(f'  SUB name={sub["name"][:30]}')
            print(f'  SUB code={repr(sub.get("code",""))}')
            print(f'  SUB notes={repr(sub.get("notes","")[:80])}')
            break
    else:
        continue
    break
