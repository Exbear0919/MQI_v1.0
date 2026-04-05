#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 medical_quality_indicators.html 中的 RAW_DATA 数据块
同时同步更新统计数字
"""
import json, re, os

# 读取新数据
data = json.load(open('indicators_clean.json', 'r', encoding='utf-8'))
data_json = json.dumps(data, ensure_ascii=False)
total = len(data)
cats = sorted(set(d['category'] for d in data))
cat_count = len(cats)
spec = sum(1 for d in data if d['type']=='专业（专科）类')
tech = sum(1 for d in data if d['type']=='医疗技术类')
other = sum(1 for d in data if d['type']=='其他')

# 读取HTML
with open('medical_quality_indicators.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 替换 RAW_DATA = [...]
# 找到 "const RAW_DATA = [" 到下一个 ";\n\n// ===== State"
pattern = r'(const RAW_DATA = )(\[.*?\])(\s*\n\s*\n// =====\s*State)'
m = re.search(pattern, html, re.DOTALL)
if m:
    new_html = html[:m.start()] + f'const RAW_DATA = {data_json}' + m.group(3) + html[m.end():]
    print(f'RAW_DATA替换成功: {total}条')
else:
    # 手动找边界
    start_marker = 'const RAW_DATA = ['
    end_marker = '\n\n// ===== State'
    s = html.find(start_marker)
    e = html.find(end_marker, s)
    if s == -1 or e == -1:
        print('❌ 未找到 RAW_DATA 块，跳过替换')
        new_html = html
    else:
        new_html = html[:s] + f'const RAW_DATA = {data_json}' + html[e:]
        print(f'RAW_DATA替换成功（手动边界）: {total}条')

# 替换统计数字（title和subtitle中的数字）
new_html = re.sub(
    r'共\s*<strong>\d+</strong>\s*条指标',
    f'共 <strong>{total}</strong> 条指标',
    new_html
)
new_html = re.sub(
    r'(\d+)\s*条指标\s*[·•]\s*(\d+)\s*个专业',
    f'{total} 条指标 · {cat_count} 个专业',
    new_html
)
# 分类下拉 - 重建options
cats_options = '<option value="">全部分类（' + str(cat_count) + '个）</option>\n'
for c in cats:
    cats_options += f'<option value="{c}">{c}</option>\n'

# 找到 catFilter select 并替换options
old_sel_pattern = r'(<select[^>]*id=["\']catFilter["\'][^>]*>)(.*?)(</select>)'
sel_m = re.search(old_sel_pattern, new_html, re.DOTALL)
if sel_m:
    new_html = new_html[:sel_m.start(2)] + cats_options + new_html[sel_m.end(2):]
    print('分类下拉已更新')

with open('medical_quality_indicators.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

size_kb = os.path.getsize('medical_quality_indicators.html') / 1024
print(f'✅ medical_quality_indicators.html 更新完成 ({size_kb:.1f} KB)')
print(f'   指标数: {total}，分类: {cat_count}')
