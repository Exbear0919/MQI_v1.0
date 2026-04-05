"""
读取JSON，生成干净的指标数据，然后构建HTML应用
"""
import json
import re

with open(r'C:\Users\Bear\WorkBuddy\20260402212518\indicators_data.json', 'r', encoding='utf-8') as f:
    indicators = json.load(f)

# 章节名称规范化映射
CATEGORY_MAP = {
    '医疗质量控制指标（2021 年版）': '心血管系统疾病相关专业医疗质量控制指标（2021年版）',
    '医疗质量控制指标（2022 年版）': '超声诊断专业医疗质量控制指标（2022年版）',
    '医疗质量控制指标（2019 年版）': '产科专业医疗质量控制指标（2019年版）',
    '医疗质量控制指标（2024 年版）': '急诊医学专业医疗质量控制指标（2024年版）',
    '医疗质量控制指标（2025 年版）': '药事管理专业医疗质量控制指标（2025年版）',
    '医疗质量控制指标（2020 年版）': '神经系统疾病医疗质量控制指标（2020年版）',
    '质量控制指标（2023 年版）': '肿瘤专业质量控制指标（2023年版）',
    '临床应用质量控制指标（2022 年版）': '异基因造血干细胞移植技术临床应用质量控制指标（2022年版）',
    '质量控制指标（2022 年版）': '消化内镜诊疗技术医疗质量控制指标（2022年版）',
    '质量控制指标（2019 年版）': '临床用血质量控制指标（2019年版）',
}

# 需要删除的无意义章节（重复、残缺）
REMOVE_PATTERNS = [
    r'^\d+',  # 纯数字开头
    r'^[nN]/\d+',
    r'^＞',
    r'^【',
    r'^医疗质量管理与控制指标汇编$',
]

cleaned = []
for ind in indicators:
    cat = ind.get('category', '').strip()
    
    # 检查是否需要删除
    skip = False
    for pat in REMOVE_PATTERNS:
        if re.match(pat, cat):
            skip = True
            break
    if skip:
        continue
    
    # 应用映射
    if cat in CATEGORY_MAP:
        ind['category'] = CATEGORY_MAP[cat]
    
    # 清理category中的页码数字（如"003"）
    ind['category'] = re.sub(r'\s+\d{3}$', '', ind['category']).strip()
    
    # 清理指标名称
    name = ind.get('name', '').strip()
    # 去除名称中的乱码和括号中的编码
    name = re.sub(r'（[A-Z]{2,10}-\d{2,3}(?:-\d{2})?）', '', name).strip()
    ind['name'] = name
    
    if name and len(name) >= 3:
        cleaned.append(ind)

# 重新编号
for i, ind in enumerate(cleaned):
    ind['id'] = i + 1

print(f"清洗后: {len(cleaned)} 个指标")

# 统计各专业
from collections import Counter
cats = Counter(ind['category'] for ind in cleaned)
print("\n各专业（前20）:")
for cat, cnt in sorted(cats.items(), key=lambda x: -x[1])[:20]:
    print(f"  {cat[:40]}: {cnt}个")

with open(r'C:\Users\Bear\WorkBuddy\20260402212518\indicators_clean.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)
print("\n清洗数据已保存")
