#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 indicators_clean.json 转换为微信小程序可用的数据文件（分块处理）
"""
import json, os, re

SRC = r'C:\Users\Bear\WorkBuddy\20260402212518\indicators_clean.json'
OUT_DIR = r'C:\Users\Bear\WorkBuddy\20260402212518\miniprogram\utils'

with open(SRC, 'r', encoding='utf-8') as f:
    raw = json.load(f)

# 清洗：去除换行/多余空格，保留必要字段
data = []
for i, d in enumerate(raw):
    name = d.get('name', '').strip()
    if not name:
        continue
    definition = re.sub(r'\s+', ' ', d.get('definition', '')).strip()
    formula = re.sub(r'\s+', ' ', d.get('formula', '')).strip()
    significance = re.sub(r'\s+', ' ', d.get('significance', '')).strip()
    full_text = re.sub(r'\s+', ' ', d.get('full_text', '')).strip()
    category = d.get('category', '').strip()
    type_ = d.get('type', '').strip()

    data.append({
        'id': d.get('id', i + 1),
        'name': name,
        'code': d.get('code', '').strip(),
        'category': category,
        'type': type_,
        'definition': definition,
        'formula': formula,
        'significance': significance,
        'full_text': full_text,
    })

# 提取分类列表
cats = sorted(set(d['category'] for d in data if d['category']))
types = sorted(set(d['type'] for d in data if d['type']))

# 写出索引数据（只含搜索字段，减小体积）
index_data = [{'id': d['id'], 'name': d['name'], 'category': d['category'], 'type': d['type']} for d in data]

# 全量数据（小程序本地存储）
out_all = os.path.join(OUT_DIR, 'indicators.js')
with open(out_all, 'w', encoding='utf-8') as f:
    f.write('// AUTO GENERATED - DO NOT EDIT\n')
    f.write('const INDICATORS = ')
    f.write(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    f.write(';\n\n')
    f.write('const CATEGORIES = ')
    f.write(json.dumps(cats, ensure_ascii=False, separators=(',', ':')))
    f.write(';\n\n')
    f.write('const TYPES = ')
    f.write(json.dumps(types, ensure_ascii=False, separators=(',', ':')))
    f.write(';\n\n')
    f.write('module.exports = { INDICATORS, CATEGORIES, TYPES };\n')

size_kb = os.path.getsize(out_all) / 1024
print(f'✅ 已生成 indicators.js: {size_kb:.1f} KB，共 {len(data)} 条指标，{len(cats)} 个分类')
