# -*- coding: utf-8 -*-
"""把 indicators_clean.json 中的弯引号替换为直引号"""
import json

data = json.load(open('indicators_clean.json', 'r', encoding='utf-8'))

# 弯引号 -> 直引号映射
replace_map = {
    '\u201c': '"',   # "  左双弯引号
    '\u201d': '"',   # "  右双弯引号
    '\u2018': "'",   # '  左单弯引号
    '\u2019': "'",   # '  右单弯引号
    '\u300c': '"',   # 「 左书名号
    '\u300d': '"',   # 」 右书名号
}

def clean_str(s):
    if not s:
        return s
    for k, v in replace_map.items():
        s = s.replace(k, v)
    return s

def clean_obj(obj):
    if isinstance(obj, str):
        return clean_str(obj)
    elif isinstance(obj, list):
        return [clean_obj(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    return obj

cleaned = clean_obj(data)
json.dump(cleaned, open('indicators_clean.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'完成，共处理 {len(cleaned)} 条指标，弯引号已全部替换为直引号')
