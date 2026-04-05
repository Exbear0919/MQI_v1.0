#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度质量检查 + 修复"""
import json, re

data = json.load(open('indicators_clean.json', 'r', encoding='utf-8'))
print(f'总数: {len(data)}')

# === 1. 无定义无公式 ===
no_content = [d for d in data if not d['definition'] and not d['formula'] and not d.get('sub_indicators')]
print(f'\n无定义无公式（且无子指标）: {len(no_content)}')
for d in no_content[:15]:
    print(f'  [{d["category"][:20]}] {d["name"][:60]}')

# === 2. 名称含异常字符 ===
print('\n名称异常检查:')
bad = []
for d in data:
    name = d['name']
    if re.search(r'[=×÷]', name) or '计算公式' in name or '定义' in name or '意义' in name:
        bad.append(d)
    elif re.search(r'\d{3}\s+[^\s]', name):
        bad.append(d)
print(f'  名称含异常字符: {len(bad)}')
for d in bad[:5]:
    print(f'    {d["name"][:80]}')

# === 3. 名称过长（可能混入正文）===
long_names = [d for d in data if len(d['name']) > 50]
print(f'\n名称超50字: {len(long_names)}')
for d in long_names[:5]:
    print(f'  {d["name"][:100]}')

# === 4. 含子指标的 ===
with_sub = [d for d in data if d.get('sub_indicators')]
print(f'\n含子指标指标: {len(with_sub)}')
for d in with_sub[:5]:
    print(f'  {d["name"][:50]} → {len(d["sub_indicators"])}个子指标')
    for sub in d['sub_indicators'][:2]:
        print(f'    - {sub["name"][:50]}')

# === 5. 含表格的 ===
with_table = [d for d in data if d.get('tables_html')]
print(f'\n含表格指标: {len(with_table)}')
for d in with_table:
    print(f'  {d["name"][:50]} | {len(d["tables_html"])}个表格')

# === 6. 各章节指标数 vs 期望 ===
from collections import Counter
cat_counts = Counter(d['category'] for d in data)
print('\n各章节指标数:')
expected_ranges = {
    '住院病案首页数据质量管理与控制指标（2016年版）': (8,12),
    '产科专业医疗质量控制指标（2019年版）': (6,10),
    '呼吸内科专业医疗质量控制指标（2019年版）': (15,25),
    '神经系统疾病医疗质量控制指标（2020年版）': (55,85),
    '心血管系统疾病相关专业医疗质量控制指标（2021年版）': (100,140),
    '肿瘤专业质量控制指标（2023年版）': (90,130),
}
for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
    rng = expected_ranges.get(cat)
    flag = ''
    if rng and not (rng[0] <= cnt <= rng[1]):
        flag = ' ⚠️'
    print(f'  {cnt:3d}条  {cat[:45]}{flag}')

# === 7. 检查产科指标（已知应有6-9个）===
print('\n产科指标详情:')
ob = [d for d in data if '产科' in d['category']]
for d in ob:
    print(f'  {d["name"]} | def:{bool(d["definition"])} | formula:{bool(d["formula"])}')
