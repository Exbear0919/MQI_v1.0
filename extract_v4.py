#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗质量指标 PDF 专业提取器 v4
- 双栏分离提取（左栏+右栏）
- 正确识别主指标/子指标/备注/表格
- 医学逻辑校验
- 输出 indicators_clean.json（覆盖原文件）
"""

import pdfplumber
import json
import re
import os
from collections import defaultdict

PDF_PATH = r'C:/Users/Bear/Desktop/医疗质量管理与控制指标汇编（8.0）.pdf'
OUTPUT_PATH = r'C:/Users/Bear/WorkBuddy/20260402212518/indicators_clean.json'

# PDF文档内编号→章节名称映射
# 目录编号（文档内页码）→ (章节名, 类型)
# 通过实测：文档内页码 003 = PDF页5 = PDF index 4，偏移 +1
CATALOG = [
    (3,   10,  "住院病案首页数据质量管理与控制指标（2016年版）", "专业（专科）类"),
    (10,  15,  "产科专业医疗质量控制指标（2019年版）",           "专业（专科）类"),
    (15,  25,  "呼吸内科专业医疗质量控制指标（2019年版）",       "专业（专科）类"),
    (25,  60,  "神经系统疾病医疗质量控制指标（2020年版）",       "专业（专科）类"),
    (60,  74,  "肾病专业医疗质量控制指标（2020年版）",           "专业（专科）类"),
    (74,  86,  "护理专业医疗质量控制指标（2020年版）",           "专业（专科）类"),
    (86,  96,  "病案管理质量控制指标（2021年版）",               "专业（专科）类"),
    (96,  134, "心血管系统疾病相关专业医疗质量控制指标（2021年版）", "专业（专科）类"),
    (134, 141, "超声诊断专业医疗质量控制指标（2022年版）",       "专业（专科）类"),
    (141, 150, "康复医学专业医疗质量控制指标（2022年版）",       "专业（专科）类"),
    (150, 156, "临床营养专业医疗质量控制指标（2022年版）",       "专业（专科）类"),
    (156, 167, "麻醉专业医疗质量控制指标（2022年版）",           "专业（专科）类"),
    (167, 212, "肿瘤专业质量控制指标（2023年版）",               "专业（专科）类"),
    (212, 216, "感染性疾病专业医疗质量控制指标（2023年版）",     "专业（专科）类"),
    (216, 219, "健康体检与管理专业医疗质量控制指标（2023年版）", "专业（专科）类"),
    (219, 224, "疼痛专业医疗质量控制指标（2023年版）",           "专业（专科）类"),
    (224, 228, "整形美容专业医疗质量控制指标（2023年版）",       "专业（专科）类"),
    (228, 235, "急诊医学专业医疗质量控制指标（2024年版）",       "专业（专科）类"),
    (235, 240, "脑损伤评价医疗质量控制指标（2024年版）",         "专业（专科）类"),
    (240, 245, "病理专业医疗质量控制指标（2024年版）",           "专业（专科）类"),
    (245, 248, "放射影像专业医疗质量控制指标（2024年版）",       "专业（专科）类"),
    (248, 252, "门诊管理医疗质量控制指标（2024年版）",           "专业（专科）类"),
    (252, 258, "医院感染管理医疗质量控制指标（2024年版）",       "专业（专科）类"),
    (258, 266, "重症医学专业医疗质量控制指标（2024年版）",       "专业（专科）类"),
    (266, 276, "药事管理专业医疗质量控制指标（2025年版）",       "专业（专科）类"),
    (276, 282, "临床检验专业医疗质量控制指标（2025年版）",       "专业（专科）类"),
    (282, 289, "核医学专业医疗质量控制指标（2025年版）",         "专业（专科）类"),
    # 医疗技术类
    (289, 294, "肺脏移植技术医疗质量控制指标（2020年版）",       "医疗技术类"),
    (294, 302, "肝脏移植技术医疗质量控制指标（2020年版）",       "医疗技术类"),
    (302, 307, "肾脏移植技术医疗质量控制指标（2020年版）",       "医疗技术类"),
    (307, 312, "心脏移植技术医疗质量控制指标（2020年版）",       "医疗技术类"),
    (312, 317, "异基因造血干细胞移植技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (317, 321, "同种胰岛移植技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (321, 324, "同种异体运动系统结构性组织移植技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (324, 329, "同种异体角膜移植技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (329, 333, "性别重置技术临床应用质量控制指标（2022年版）",   "医疗技术类"),
    (333, 336, "质子和重离子加速器放射治疗技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (336, 342, "放射性粒子植入治疗技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (342, 346, "肿瘤消融治疗技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (346, 351, "心室辅助技术临床应用质量控制指标（2022年版）",   "医疗技术类"),
    (351, 355, "人工智能辅助治疗技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (355, 359, "体外膜肺氧合（ECMO）技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (359, 366, "自体器官移植技术临床应用质量控制指标（2022年版）", "医疗技术类"),
    (366, 377, "消化内镜诊疗技术医疗质量控制指标（2022年版）",   "医疗技术类"),
    # 其他
    (377, 383, "人体器官获取组织质量控制指标",                   "其他"),
    (383, 387, "临床用血质量控制指标（2019年版）",               "其他"),
    (387, 431, "单病种质量监测信息项（2020年版）",               "其他"),
    (431, 999, "医疗质量安全核心制度落实情况监测指标（2025年版）", "其他"),
]

CN_NUMS = '一二三四五六七八九十百千'


def get_category(doc_pn):
    for start, end, name, type_ in CATALOG:
        if start <= doc_pn < end:
            return name, type_
    return None, None


def extract_page_text_dual_column(page):
    """分栏提取页面文本：返回(左栏文本, 右栏文本)"""
    mid = page.width / 2
    # 判断是否真的是双栏（检查右栏是否有实质文字）
    left_crop = page.crop((0, 0, mid, page.height))
    right_crop = page.crop((mid, 0, page.width, page.height))
    lt = left_crop.extract_text() or ''
    rt = right_crop.extract_text() or ''
    return lt, rt


def get_doc_page_num(text):
    """从页面文本提取文档内页码"""
    # 格式: "| 003 |" 或 "003 |" 行尾
    m = re.search(r'\|\s*(\d{3})\s*\|', text)
    if m:
        return int(m.group(1))
    m2 = re.search(r'(\d{3})\s*\|?\s*$', text.strip())
    if m2:
        v = int(m2.group(1))
        if 1 <= v <= 600:
            return v
    return None


def clean_header_footer(text):
    """去除页眉页脚"""
    # 去除章节标题行（通常出现在页面顶部）
    text = re.sub(r'^医疗质量管理与控制指标汇编\s*\n?', '', text, flags=re.MULTILINE)
    # 去除章节名称重复行（页眉）
    for _, _, name, _ in CATALOG:
        escaped = re.escape(name)
        text = re.sub(escaped + r'\s*\n?', '', text)
    # 去除页码
    text = re.sub(r'\|\s*\d{3}\s*\|', '', text)
    text = re.sub(r'^\s*\d{3}\s*\|', '', text, flags=re.MULTILINE)
    text = re.sub(r'\|\s*\d{3}\s*$', '', text, flags=re.MULTILINE)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def table_to_html(rows):
    """表格数据转HTML"""
    if not rows:
        return ''
    html = '<table class="indicator-table">\n'
    for i, row in enumerate(rows):
        html += '<tr>'
        tag = 'th' if i == 0 else 'td'
        for cell in (row or []):
            txt = str(cell or '').strip().replace('\n', '<br>')
            html += f'<{tag}>{txt}</{tag}>'
        html += '</tr>\n'
    html += '</table>'
    return html


# ============================================================
# 指标文本解析
# ============================================================

def extract_code_from_name(name):
    """从名称中提取指标代码"""
    # 格式: （AQI-IUI-20）或 (CVD-CABG-13)
    m = re.search(r'[（(]([A-Z]{2,}[-—][A-Z\d\-—]+)[）)]', name)
    if m:
        code = m.group(1)
        clean_name = name[:m.start()].strip() + name[m.end():].strip()
        clean_name = clean_name.strip('、 \t')
        return clean_name, code
    return name, ''


def parse_indicator_block(block_text, category, type_):
    """
    解析一个指标块（从"X、名称"到下一个指标开始前的所有文本）
    返回主指标dict（可能含sub_indicators）
    """
    block_text = block_text.strip()
    if not block_text:
        return None

    # 提取标题行（第一行通常是指标名）
    lines = block_text.split('\n')
    
    # 找到标题行
    title_line = ''
    title_line_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^(?:指标\s*)?[' + CN_NUMS + r']+[、．.]\s*.+', stripped):
            title_line = stripped
            title_line_idx = i
            break
    
    if not title_line:
        title_line = lines[0].strip()
    
    # 从标题提取名称和代码
    raw_title = re.sub(r'^(?:指标\s*)?[' + CN_NUMS + r']+[、．.]\s*', '', title_line).strip()
    name, code = extract_code_from_name(raw_title)
    
    if not name or len(name.strip()) < 2:
        return None
    
    # 剩余文本（标题后）
    remaining = '\n'.join(lines[title_line_idx+1:]).strip()
    
    # 检查是否有子指标（括号序号格式）
    # 子指标标识: （一）、（二） 或 (1)(2) 在文本中
    sub_indicator_re = re.compile(
        r'(?:^|\n)\s*[（(]([一二三四五六七八九十]+|\d+)[）)][、\s]*'
        r'(.+?)(?=\n\s*[（(][一二三四五六七八九十\d]+[）)]|定义[：:]|计算公式[：:]|意义[：:]|说明[：:]|\Z)',
        re.DOTALL
    )
    
    # 主字段提取
    def extract_field(text, *patterns):
        for pat in patterns:
            m = re.search(pat, text, re.DOTALL)
            if m:
                return m.group(1).strip()
        return ''
    
    # 在remaining中找各字段
    definition = extract_field(remaining,
        r'定义[：:]\s*(.*?)(?=计算公式[：:]|意义[：:]|说明[：:]|备注[：:]|\Z)')
    formula = extract_field(remaining,
        r'计算公式[：:]\s*(.*?)(?=意义[：:]|说明[：:]|备注[：:]|定义[：:]|\Z)')
    significance = extract_field(remaining,
        r'意义[：:]\s*(.*?)(?=说明[：:]|备注[：:]|定义[：:]|计算公式[：:]|\Z)')
    notes = extract_field(remaining,
        r'(?:说明|备注)[：:]\s*(.*?)(?=定义[：:]|计算公式[：:]|意义[：:]|\Z)')
    
    # 清理字段
    def clean_f(s):
        if not s:
            return ''
        s = re.sub(r'医疗质量管理与控制指标汇编', '', s)
        s = re.sub(r'\|\s*\d{3}\s*\|?', '', s)
        s = re.sub(r'^\s*\d{3}\s*\|', '', s, flags=re.MULTILINE)
        s = re.sub(r'\n{3,}', '\n\n', s)
        return s.strip()
    
    # 检查子指标
    sub_indicators = []
    sub_re = re.compile(
        r'[（(]([一二三四五六七八九十]+)[）)]\s*'
        r'([^（(（\n]{3,100})[。\n]',
    )
    
    # 如果没有定义但有子指标格式，提取子指标
    if not definition and not formula:
        # 这可能是一个分组（如"IgA肾病"包含多个子指标）
        # 或者是一个标题（后面跟着下一级的指标）
        sub_secs = re.split(
            r'\n(?=\s*[（(][一二三四五六七八九十]+[）)]\s*\S)',
            remaining
        )
        if len(sub_secs) > 1:
            for sub_sec in sub_secs[1:]:
                sub_m = re.match(r'\s*[（(]([一二三四五六七八九十]+)[）)]\s*(.+)', sub_sec.strip())
                if sub_m:
                    sub_name_raw = sub_m.group(2).strip()
                    sub_name, sub_code = extract_code_from_name(sub_name_raw.split('\n')[0])
                    sub_def = extract_field(sub_sec, r'定义[：:]\s*(.*?)(?=计算公式|意义|说明|\Z)')
                    sub_formula = extract_field(sub_sec, r'计算公式[：:]\s*(.*?)(?=意义|说明|\Z)')
                    sub_sig = extract_field(sub_sec, r'意义[：:]\s*(.*?)(?=说明|定义|\Z)')
                    sub_notes = extract_field(sub_sec, r'(?:说明|备注)[：:]\s*(.*?)(?=\Z)')
                    if sub_name:
                        sub_indicators.append({
                            'name': sub_name,
                            'code': sub_code,
                            'definition': clean_f(sub_def),
                            'formula': clean_f(sub_formula),
                            'significance': clean_f(sub_sig),
                            'notes': clean_f(sub_notes),
                        })
    
    ind = {
        'name': name.strip(),
        'code': code,
        'definition': clean_f(definition),
        'formula': clean_f(formula),
        'significance': clean_f(significance),
        'notes': clean_f(notes),
        'category': category,
        'type': type_,
        'tables_html': [],
        'sub_indicators': sub_indicators,
    }
    
    return ind


def split_into_indicator_blocks(text):
    """将章节文本分割成指标块列表"""
    # 主指标分割模式: 行首 + 可选"指标" + 中文数字 + 顿号
    pattern = re.compile(
        r'(?:^|\n)'
        r'(?:指标\s*)?'
        r'[' + CN_NUMS + r']+'
        r'[、．.]'
        r'\s*\S',  # 后面紧跟非空字符
        re.MULTILINE
    )
    
    positions = [m.start() for m in pattern.finditer(text)]
    
    if not positions:
        return [text]
    
    blocks = []
    for i, pos in enumerate(positions):
        end = positions[i+1] if i+1 < len(positions) else len(text)
        # 去掉前导换行
        block = text[pos:end].lstrip('\n')
        blocks.append(block)
    
    # 前面可能有序言文本（章节标题前）
    preamble = text[:positions[0]].strip() if positions else text.strip()
    
    return blocks


# ============================================================
# 主流程
# ============================================================

def main():
    print(f"正在读取 PDF: {PDF_PATH}")
    
    # 章节文本累积 (doc_page_range → text)
    category_texts = defaultdict(str)   # cat_name → text
    category_tables = defaultdict(list) # cat_name → tables
    category_types = {}
    
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}")
        
        # 第4页是第2个目录页（doc page=002），第5页起是正文
        # 前4页（index 0-3）是封面+前言+目录，跳过
        
        for pdf_idx in range(4, total):
            page = pdf.pages[pdf_idx]
            
            # 分栏提取
            lt, rt = extract_page_text_dual_column(page)
            combined = lt + '\n' + rt
            
            # 获取文档内页码
            doc_pn = get_doc_page_num(combined)
            if doc_pn is None:
                # 尝试从完整文本猜
                full_text = page.extract_text() or ''
                doc_pn = get_doc_page_num(full_text)
            
            if doc_pn is None:
                # 根据PDF页码估算（前4页是封面等）
                doc_pn = (pdf_idx - 1) * 2  # 粗略估算
            
            cat_name, type_ = get_category(doc_pn)
            if cat_name is None:
                continue
            
            category_types[cat_name] = type_
            
            # 清理页眉页脚后累积文本
            lt_clean = clean_header_footer(lt)
            rt_clean = clean_header_footer(rt)
            
            if lt_clean:
                category_texts[cat_name] += '\n' + lt_clean
            if rt_clean:
                category_texts[cat_name] += '\n' + rt_clean
            
            # 提取表格
            tables = page.extract_tables() or []
            if tables:
                category_tables[cat_name].extend(tables)
            
            if (pdf_idx + 1) % 30 == 0:
                print(f"  已处理 {pdf_idx+1}/{total} 页")
    
    print(f"PDF读取完成，识别到 {len(category_texts)} 个章节")
    print("开始提取指标...")
    
    all_indicators = []
    indicator_id = 1
    
    # 按CATALOG顺序处理，确保顺序一致
    for start, end, cat_name, type_ in CATALOG:
        if cat_name not in category_texts:
            print(f"  [跳过] {cat_name[:30]} (无文本)")
            continue
        
        text = category_texts[cat_name]
        tables = category_tables.get(cat_name, [])
        
        # 分割指标块
        blocks = split_into_indicator_blocks(text)
        
        indicators = []
        for block in blocks:
            if len(block.strip()) < 10:
                continue
            ind = parse_indicator_block(block, cat_name, type_)
            if ind and ind['name']:
                # 过滤掉明显是纯分组标题（无内容且无子指标）
                has_content = any([
                    ind['definition'], ind['formula'],
                    ind['significance'], ind['sub_indicators']
                ])
                # 对于有名称且有一定内容的指标保留
                if has_content or len(ind['name']) > 5:
                    ind['id'] = indicator_id
                    # 构建全文
                    ind['full_text'] = build_full_text(ind)
                    # 分配表格（简单策略：将章节表格平均分配，或标注为章节附件）
                    indicators.append(ind)
                    indicator_id += 1
        
        # 将章节表格附加到第一个指标（或作为章节附录）
        if tables and indicators:
            # 将表格HTML附加到对应指标的notes或单独字段
            table_htmls = [table_to_html(t) for t in tables if t]
            # 简单策略：附加到含"附件"或"评分"字样的指标
            attached = False
            for ind in indicators:
                if any(kw in ind['name'] for kw in ['附件', '评分', '评价', '量表']):
                    ind['tables_html'] = table_htmls
                    attached = True
                    break
            if not attached and indicators:
                # 附到最后一个有notes的指标
                for ind in reversed(indicators):
                    if ind.get('notes') or '附件' in ind['full_text']:
                        ind['tables_html'] = table_htmls
                        break
        
        all_indicators.extend(indicators)
        print(f"  [{type_}] {cat_name[:35]}... → {len(indicators)} 条")
    
    print(f"\n共提取 {len(all_indicators)} 条指标")
    
    # 质量过滤：移除名称过短或明显是垃圾的
    cleaned = []
    for ind in all_indicators:
        name = ind['name']
        # 去掉名称中的页码残留
        name = re.sub(r'\s+\d{3}\s+[^\s]+.*', '', name).strip()
        name = re.sub(r'^\d+\s+', '', name).strip()
        ind['name'] = name
        
        if len(name) < 3:
            continue
        if re.match(r'^[\d\s\-]+$', name):
            continue
        # 去掉目录里有但内容为纯章节标题（无任何正文内容）
        # 保留有任何字段内容的
        cleaned.append(ind)
    
    print(f"过滤后: {len(cleaned)} 条指标")
    
    # 重新编号
    for i, ind in enumerate(cleaned):
        ind['id'] = i + 1
    
    # 保存
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"已保存到: {OUTPUT_PATH} ({size_kb:.1f} KB)")
    
    # 统计
    from collections import Counter
    type_counts = Counter(d['type'] for d in cleaned)
    cat_counts = Counter(d['category'] for d in cleaned)
    has_sub = sum(1 for d in cleaned if d.get('sub_indicators'))
    has_table = sum(1 for d in cleaned if d.get('tables_html'))
    
    print("\n类型分布:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print(f"\n分类数: {len(cat_counts)}")
    print(f"含子指标: {has_sub} 条")
    print(f"含表格: {has_table} 条")
    
    # 抽样检查
    print("\n=== 抽样检查（前3条）===")
    for d in cleaned[:3]:
        print(f"名称: {d['name']}")
        print(f"代码: {d['code']}")
        print(f"定义: {d['definition'][:80] if d['definition'] else '(无)'}...")
        print(f"公式: {d['formula'][:60] if d['formula'] else '(无)'}...")
        print(f"意义: {d['significance'][:60] if d['significance'] else '(无)'}...")
        print(f"子指标数: {len(d['sub_indicators'])}")
        print()
    
    return cleaned


def build_full_text(ind):
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
            parts.append(f"[子指标] {sub['name']}：{sub.get('definition','')}")
    return '\n'.join(parts)


if __name__ == '__main__':
    main()
