#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后处理：清理数据，修复问题
1. 移除纯分组标题（无内容的占位指标）
2. 修复名称异常
3. 确保子指标内容完整
4. 最终输出 indicators_clean.json
"""
import json, re

data = json.load(open('indicators_clean.json', 'r', encoding='utf-8'))
print(f'处理前: {len(data)} 条')

cleaned = []
removed = []

for ind in data:
    name = ind.get('name', '').strip()
    definition = ind.get('definition', '').strip()
    formula = ind.get('formula', '').strip()
    significance = ind.get('significance', '').strip()
    notes = ind.get('notes', '').strip()
    sub_indicators = ind.get('sub_indicators', [])
    tables_html = ind.get('tables_html', [])
    
    # === 修复名称异常 ===
    # 去掉名称中包含"= ×100%"等公式残留
    if re.search(r'[=×÷]', name) and len(name) > 30:
        # 截取到第一个公式符号前
        name = re.split(r'[=×÷]', name)[0].strip()
        name = re.sub(r'\s+', ' ', name).strip()
        ind['name'] = name
    
    # 去掉名称中表格残留（如"24 离院方式 住院信息"）
    if re.search(r'\s+\d+\s+[^\s]{2,}\s+[^\s]{2,}', name):
        name = re.split(r'\s+\d+\s+', name)[0].strip()
        ind['name'] = name
    
    # === 过滤规则 ===
    has_content = bool(definition or formula or significance or sub_indicators or tables_html)
    
    # 明确是子章节分组标题的情况：
    # 1. 纯疾病名称（如"急性肺血栓栓塞症"、"癫痫与惊厥性癫痫持续状态"）
    # 2. 技术名称（如"血液净化技术"）
    # 3. 指标分组（如"人力资源配置指标"、"病历书写时效性指标"）
    # 判断：无内容 且 名称符合分组标题特征
    group_title_patterns = [
        r'^[^（(]+（\d+项指标）$',  # "XXX（16项指标）"
        r'^[一二三四五六七八九十]+、.{2,10}$',  # "一、急诊医学..."
    ]
    is_group_title = not has_content
    
    if is_group_title:
        # 记录移除
        removed.append(ind)
        continue
    
    # 名称过短（<3字）
    if len(name) < 3:
        removed.append(ind)
        continue
    
    # 更新id（后面重新编号）
    cleaned.append(ind)

# 清理子指标中的空条目
for ind in cleaned:
    if ind.get('sub_indicators'):
        ind['sub_indicators'] = [
            sub for sub in ind['sub_indicators']
            if sub.get('name') and len(sub['name']) >= 3
        ]

# 重新编号
for i, ind in enumerate(cleaned):
    ind['id'] = i + 1
    # 重建full_text
    parts = [ind['name']]
    if ind.get('definition'):
        parts.append('定义：' + ind['definition'])
    if ind.get('formula'):
        parts.append('计算公式：' + ind['formula'])
    if ind.get('significance'):
        parts.append('意义：' + ind['significance'])
    if ind.get('notes'):
        parts.append('说明：' + ind['notes'])
    if ind.get('sub_indicators'):
        for sub in ind['sub_indicators']:
            sub_parts = [f"（子指标）{sub['name']}"]
            if sub.get('definition'):
                sub_parts.append('定义：' + sub['definition'])
            if sub.get('formula'):
                sub_parts.append('计算公式：' + sub['formula'])
            parts.extend(sub_parts)
    ind['full_text'] = '\n'.join(parts)

print(f'移除: {len(removed)} 条（分组标题/空内容）')
print('移除列表:')
for d in removed[:20]:
    print(f'  [{d["category"][:20]}] {d["name"]}')

print(f'\n处理后: {len(cleaned)} 条')

# 保存
with open('indicators_clean.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

import os
size_kb = os.path.getsize('indicators_clean.json') / 1024
print(f'文件大小: {size_kb:.1f} KB')

# 最终统计
from collections import Counter
type_counts = Counter(d['type'] for d in cleaned)
cat_counts = Counter(d['category'] for d in cleaned)
has_sub = sum(1 for d in cleaned if d.get('sub_indicators'))
has_table = sum(1 for d in cleaned if d.get('tables_html'))
no_def = sum(1 for d in cleaned if not d['definition'] and not d['formula'])

print('\n最终类型分布:')
for t, c in sorted(type_counts.items()):
    print(f'  {t}: {c}')
print(f'分类数: {len(cat_counts)}')
print(f'含子指标: {has_sub}')
print(f'含表格: {has_table}')
print(f'无定义公式: {no_def}（正常，部分为纯意义型指标）')
