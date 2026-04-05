#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗质量指标 PDF 专业提取器 v3
- 正确识别主指标 / 子指标 / 备注 / 表格
- 保留原始医学内容，不截断
- 输出 indicators_v3.json
"""

import pdfplumber
import json
import re
import os

PDF_PATH = r'C:/Users/Bear/Desktop/医疗质量管理与控制指标汇编（8.0）.pdf'
OUTPUT_PATH = r'C:/Users/Bear/WorkBuddy/20260402212518/indicators_v3.json'

# ===== 目录信息（PDF目录页中读取，用于精确分类） =====
# 格式: (专业名称, 类型, 开始页码_PDF内部编号)
# PDF目录页码 → 实际PDF页码需要根据偏移量计算
# 通过观察：目录显示"003"对应PDF第5页（偏移=PDF页-目录页码）

CATALOG = [
    # 专业（专科）类
    ("住院病案首页数据质量管理与控制指标（2016年版）", "专业（专科）类", 3, 10),
    ("产科专业医疗质量控制指标（2019年版）", "专业（专科）类", 10, 15),
    ("呼吸内科专业医疗质量控制指标（2019年版）", "专业（专科）类", 15, 25),
    ("神经系统疾病医疗质量控制指标（2020年版）", "专业（专科）类", 25, 60),
    ("肾病专业医疗质量控制指标（2020年版）", "专业（专科）类", 60, 74),
    ("护理专业医疗质量控制指标（2020年版）", "专业（专科）类", 74, 86),
    ("病案管理质量控制指标（2021年版）", "专业（专科）类", 86, 96),
    ("心血管系统疾病相关专业医疗质量控制指标（2021年版）", "专业（专科）类", 96, 134),
    ("超声诊断专业医疗质量控制指标（2022年版）", "专业（专科）类", 134, 141),
    ("康复医学专业医疗质量控制指标（2022年版）", "专业（专科）类", 141, 150),
    ("临床营养专业医疗质量控制指标（2022年版）", "专业（专科）类", 150, 156),
    ("麻醉专业医疗质量控制指标（2022年版）", "专业（专科）类", 156, 167),
    ("肿瘤专业质量控制指标（2023年版）", "专业（专科）类", 167, 212),
    ("感染性疾病专业医疗质量控制指标（2023年版）", "专业（专科）类", 212, 216),
    ("健康体检与管理专业医疗质量控制指标（2023年版）", "专业（专科）类", 216, 219),
    ("疼痛专业医疗质量控制指标（2023年版）", "专业（专科）类", 219, 224),
    ("整形美容专业医疗质量控制指标（2023年版）", "专业（专科）类", 224, 228),
    ("急诊医学专业医疗质量控制指标（2024年版）", "专业（专科）类", 228, 235),
    ("脑损伤评价医疗质量控制指标（2024年版）", "专业（专科）类", 235, 240),
    ("病理专业医疗质量控制指标（2024年版）", "专业（专科）类", 240, 245),
    ("放射影像专业医疗质量控制指标（2024年版）", "专业（专科）类", 245, 248),
    ("门诊管理医疗质量控制指标（2024年版）", "专业（专科）类", 248, 252),
    ("医院感染管理医疗质量控制指标（2024年版）", "专业（专科）类", 252, 258),
    ("重症医学专业医疗质量控制指标（2024年版）", "专业（专科）类", 258, 266),
    ("药事管理专业医疗质量控制指标（2025年版）", "专业（专科）类", 266, 276),
    ("临床检验专业医疗质量控制指标（2025年版）", "专业（专科）类", 276, 282),
    ("核医学专业医疗质量控制指标（2025年版）", "专业（专科）类", 282, 289),
    # 医疗技术类
    ("肺脏移植技术医疗质量控制指标（2020年版）", "医疗技术类", 289, 294),
    ("肝脏移植技术医疗质量控制指标（2020年版）", "医疗技术类", 294, 302),
    ("肾脏移植技术医疗质量控制指标（2020年版）", "医疗技术类", 302, 307),
    ("心脏移植技术医疗质量控制指标（2020年版）", "医疗技术类", 307, 312),
    ("异基因造血干细胞移植技术临床应用质量控制指标（2022年版）", "医疗技术类", 312, 317),
    ("同种胰岛移植技术临床应用质量控制指标（2022年版）", "医疗技术类", 317, 321),
    ("同种异体运动系统结构性组织移植技术临床应用质量控制指标（2022年版）", "医疗技术类", 321, 324),
    ("同种异体角膜移植技术临床应用质量控制指标（2022年版）", "医疗技术类", 324, 329),
    ("性别重置技术临床应用质量控制指标（2022年版）", "医疗技术类", 329, 333),
    ("质子和重离子加速器放射治疗技术临床应用质量控制指标（2022年版）", "医疗技术类", 333, 336),
    ("放射性粒子植入治疗技术临床应用质量控制指标（2022年版）", "医疗技术类", 336, 342),
    ("肿瘤消融治疗技术临床应用质量控制指标（2022年版）", "医疗技术类", 342, 346),
    ("心室辅助技术临床应用质量控制指标（2022年版）", "医疗技术类", 346, 351),
    ("人工智能辅助治疗技术临床应用质量控制指标（2022年版）", "医疗技术类", 351, 355),
    ("体外膜肺氧合（ECMO）技术临床应用质量控制指标（2022年版）", "医疗技术类", 355, 359),
    ("自体器官移植技术临床应用质量控制指标（2022年版）", "医疗技术类", 359, 366),
    ("消化内镜诊疗技术医疗质量控制指标（2022年版）", "医疗技术类", 366, 377),
    # 其他
    ("人体器官获取组织质量控制指标", "其他", 377, 383),
    ("临床用血质量控制指标（2019年版）", "其他", 383, 387),
    ("单病种质量监测信息项（2020年版）", "其他", 387, 431),
    ("医疗质量安全核心制度落实情况监测指标（2025年版）", "其他", 431, 999),
]

def page_num_to_pdf_index(doc_page_num):
    """文档内部页码 → PDF 0-based 索引（偏移=2，目录显示003对应PDF第5页即index=4，偏移+2）"""
    return doc_page_num + 1  # 目录编号003 → PDF页index=4，偏移为+1

def get_category_type(doc_page_num):
    """根据文档内部页码获取分类和类型"""
    for name, type_, start, end in CATALOG:
        if start <= doc_page_num < end:
            return name, type_
    return "其他", "其他"

def table_to_html(table_data):
    """将表格数据转为HTML"""
    if not table_data:
        return ""
    html = '<table class="indicator-table">\n'
    for i, row in enumerate(table_data):
        html += '  <tr>\n'
        tag = 'th' if i == 0 else 'td'
        for cell in row:
            cell_text = str(cell).strip() if cell else ''
            cell_text = cell_text.replace('\n', '<br>')
            html += f'    <{tag}>{cell_text}</{tag}>\n'
        html += '  </tr>\n'
    html += '</table>'
    return html

def clean_text(text):
    """清理文本"""
    if not text:
        return ''
    # 去除页眉页脚
    text = re.sub(r'医疗质量管理与控制指标汇编\s*', '', text)
    text = re.sub(r'\|\s*\d+\s*\|?', '', text)
    text = re.sub(r'\d+\s*\|$', '', text, flags=re.MULTILINE)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_indicators_from_section(text, tables, category, type_):
    """从一个章节文本中提取指标列表"""
    indicators = []
    
    # 匹配各种编号格式的指标标题
    # 支持: 一、二、... 中文数字
    # 支持: 指标一、指标二...
    # 支持: （一）（二）...
    # 支持: 1. 2. 等
    
    # 主指标分割模式
    indicator_patterns = [
        # 中文序号 + 顿号：一、指标名  或  指标一、指标名
        r'(?:^|\n)((?:指标)?[一二三四五六七八九十百]+[、．.]\s*[^\n]+)',
        # 带括号的子分类：（一）
        r'(?:^|\n)(（[一二三四五六七八九十]+）[^\n]+)',
    ]
    
    # 更精准的提取：按"一、""二、"等分割
    cn_nums = '一二三四五六七八九十百千'
    
    # 先找所有指标标题位置
    # 模式1: "指标X、标题"
    # 模式2: "X、标题（代码）"
    title_pattern = re.compile(
        r'(?:^|\n)'
        r'(?:指标)?' 
        r'([' + cn_nums + r']+[、．.])'
        r'\s*'
        r'(.+?)(?=\n|$)',
        re.MULTILINE
    )
    
    matches = list(title_pattern.finditer(text))
    
    if not matches:
        # 没有找到标准格式，作为单个条目处理
        if text.strip():
            indicator = parse_single_indicator(text.strip(), None, category, type_)
            if indicator:
                indicators.append(indicator)
        return indicators
    
    # 按标题分割文本
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        
        title_prefix = match.group(1)  # 序号
        title_name = match.group(2).strip()  # 名称
        section_text = text[start:end].strip()
        
        # 判断是否为子章节标题（没有具体指标内容，如"一、XXX技术"）
        remaining = text[match.end():end].strip()
        
        # 检查是否有子指标
        sub_pattern = re.compile(
            r'(?:^|\n)'
            r'(?:指标)?'
            r'([（(][一二三四五六七八九十]+[）)]|\d+[、．.]|[（(]\d+[）)])'
            r'\s*'
            r'(.+?)(?=\n|$)',
            re.MULTILINE
        )
        sub_matches = list(sub_pattern.finditer(remaining))
        
        # 提取指标代码（括号中的大写字母+数字格式）
        code_match = re.search(r'[（(]([A-Z]{2,}[-—][A-Z\d\-]+)[）)]', title_name)
        code = code_match.group(1) if code_match else ''
        if code:
            title_name = re.sub(r'\s*[（(]' + re.escape(code) + r'[）)]', '', title_name).strip()
        
        indicator = parse_single_indicator(section_text, title_name, category, type_, code)
        if indicator:
            indicators.append(indicator)
    
    return indicators

def parse_single_indicator(text, title_override, category, type_, code=''):
    """解析单个指标的各字段"""
    text = clean_text(text)
    if not text:
        return None
    
    # 提取标题
    if title_override:
        name = title_override
    else:
        # 从文本第一行提取
        first_line = text.split('\n')[0].strip()
        name = re.sub(r'^(?:指标)?[一二三四五六七八九十百]+[、．.]\s*', '', first_line).strip()
    
    # 清理名称中的代码部分
    if not code:
        code_match = re.search(r'[（(]([A-Z]{2,}[-—][A-Z\d\-]+)[）)]', name)
        if code_match:
            code = code_match.group(1)
            name = re.sub(r'\s*[（(]' + re.escape(code) + r'[）)]', '', name).strip()
    
    if not name or len(name) < 2:
        return None
    
    # 提取定义
    def_match = re.search(
        r'定义[：:]\s*(.*?)(?=计算公式[：:]|意义[：:]|说明[：:]|备注[：:]|注[：:]|\Z)',
        text, re.DOTALL
    )
    definition = def_match.group(1).strip() if def_match else ''
    
    # 提取计算公式
    formula_match = re.search(
        r'计算公式[：:]\s*(.*?)(?=意义[：:]|说明[：:]|备注[：:]|注[：:]|\Z)',
        text, re.DOTALL
    )
    formula = formula_match.group(1).strip() if formula_match else ''
    
    # 提取意义
    sig_match = re.search(
        r'意义[：:]\s*(.*?)(?=说明[：:]|备注[：:]|注[：:]|\Z)',
        text, re.DOTALL
    )
    significance = sig_match.group(1).strip() if sig_match else ''
    
    # 提取说明/备注
    notes_match = re.search(
        r'(?:说明|备注|注)[：:]\s*(.*?)(?=\Z)',
        text, re.DOTALL
    )
    notes = notes_match.group(1).strip() if notes_match else ''
    
    # 清理各字段中的页眉残留
    def clean_field(s):
        if not s:
            return ''
        s = re.sub(r'医疗质量管理与控制指标汇编', '', s)
        s = re.sub(r'\|\s*\d+\s*\|?', '', s)
        return s.strip()
    
    return {
        'name': name,
        'code': code,
        'definition': clean_field(definition),
        'formula': clean_field(formula),
        'significance': clean_field(significance),
        'notes': clean_field(notes),
        'category': category,
        'type': type_,
        'tables': [],  # 表格数据，后续填充
    }


# ============================================================
# 主提取逻辑：逐页读取，按目录分配分类
# ============================================================

def main():
    print(f"正在读取 PDF: {PDF_PATH}")
    
    all_pages_text = []  # (doc_page_num, text, tables)
    
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}")
        
        for i, page in enumerate(pdf.pages):
            # 获取文本
            text = page.extract_text() or ''
            # 获取表格
            tables = page.extract_tables() or []
            
            # 从页眉或页脚推断文档内部页码
            # 页面底部通常有 "| 003 |" 格式
            page_num_match = re.search(r'\|\s*(\d{3})\s*\|', text)
            if page_num_match:
                doc_page_num = int(page_num_match.group(1))
            else:
                # 尝试从页面末尾找页码
                page_num_match2 = re.search(r'(\d{3})\s*\|?\s*$', text.strip())
                doc_page_num = int(page_num_match2.group(1)) if page_num_match2 else (i + 1) * 2
            
            all_pages_text.append((doc_page_num, text, tables))
            
            if (i+1) % 20 == 0:
                print(f"  已处理 {i+1}/{total} 页")
    
    print("PDF读取完成，开始按章节整合文本...")
    
    # 按章节整合：将同一分类的页面文本合并
    category_sections = {}  # category_name -> {'type':..., 'text':..., 'tables':[]}
    
    for doc_page_num, text, tables in all_pages_text:
        category, type_ = get_category_type(doc_page_num)
        if category not in category_sections:
            category_sections[category] = {'type': type_, 'text': '', 'tables': []}
        category_sections[category]['text'] += '\n' + text
        category_sections[category]['tables'].extend(tables)
    
    print(f"识别到 {len(category_sections)} 个章节")
    
    # 对每个章节进行指标提取
    all_indicators = []
    indicator_id = 1
    
    for cat_name, section_data in category_sections.items():
        type_ = section_data['type']
        full_text = section_data['text']
        tables = section_data['tables']
        
        # 清理章节标题行和页眉
        full_text = re.sub(r'医疗质量管理与控制指标汇编\s*', '', full_text)
        # 清理本章节标题（可能出现多次）
        escaped_cat = re.escape(cat_name.replace('（', '(').replace('）', ')'))
        full_text = re.sub(re.escape(cat_name), '', full_text)
        # 清理页码
        full_text = re.sub(r'\|\s*\d{3}\s*\|?', '', full_text)
        full_text = re.sub(r'^\s*\d{3}\s*\|', '', full_text, flags=re.MULTILINE)
        
        indicators = extract_indicators_from_text_advanced(full_text, tables, cat_name, type_)
        
        for ind in indicators:
            ind['id'] = indicator_id
            ind['full_text'] = build_full_text(ind)
            # tables字段转为HTML
            if ind.get('tables'):
                ind['tables_html'] = [table_to_html(t) for t in ind['tables']]
            else:
                ind['tables_html'] = []
            del ind['tables']
            all_indicators.append(ind)
            indicator_id += 1
        
        print(f"  [{type_}] {cat_name[:30]}... → {len(indicators)} 条指标")
    
    print(f"\n共提取 {len(all_indicators)} 条指标")
    
    # 保存结果
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_indicators, f, ensure_ascii=False, indent=2)
    
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"已保存到: {OUTPUT_PATH} ({size_kb:.1f} KB)")
    
    # 统计
    from collections import Counter
    type_counts = Counter(d['type'] for d in all_indicators)
    cat_counts = Counter(d['category'] for d in all_indicators)
    print("\n类型分布:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print(f"\n分类数: {len(cat_counts)}")
    
    return all_indicators


def extract_indicators_from_text_advanced(text, tables, category, type_):
    """高级指标提取：正确处理主指标、子指标、备注、表格"""
    indicators = []
    
    cn_nums = '一二三四五六七八九十百千'
    
    # 识别指标标题的多种模式
    # 1. "一、指标名称（代码）"
    # 2. "指标一、指标名称（代码）"  
    # 3. "（一）分组名" 这种是子分类
    # 4. 阿拉伯数字 "1." "1、" 有时也表示指标
    
    # 主标题匹配（中文序号+顿号）
    main_title_re = re.compile(
        r'(?:^|\n)'                          # 行首
        r'(?:指标\s*)?'                      # 可选"指标"前缀
        r'([' + cn_nums + r']+)'             # 中文数字
        r'[、．.]'                            # 顿号或句点
        r'\s*'
        r'(.+?)(?:\s*[（(]([A-Z][A-Z\d\-—]+)[）)])?'  # 名称 + 可选代码
        r'\s*(?=\n|$)',
        re.MULTILINE
    )
    
    # 找到所有主标题
    all_titles = list(main_title_re.finditer(text))
    
    if not all_titles:
        # 尝试更宽松的匹配
        loose_re = re.compile(
            r'(?:^|\n)((?:指标\s*)?[' + cn_nums + r']+[、．.]\s*.+?)(?=\n|$)',
            re.MULTILINE
        )
        all_titles = list(loose_re.finditer(text))
    
    if not all_titles:
        # 整个章节作为无序号指标处理（直接有定义/公式格式）
        ind = parse_unstructured_section(text, category, type_)
        if ind:
            indicators.extend(ind)
        return indicators
    
    # 按标题位置切割文本
    for i, title_match in enumerate(all_titles):
        section_start = title_match.start()
        section_end = all_titles[i+1].start() if i+1 < len(all_titles) else len(text)
        
        section_text = text[section_start:section_end].strip()
        
        # 提取标题信息
        groups = title_match.groups()
        raw_name = groups[1].strip() if len(groups) > 1 else ''
        code = groups[2].strip() if len(groups) > 2 and groups[2] else ''
        
        # 清理名称
        name = raw_name.strip('、．. \t')
        # 从名称末尾再次尝试提取代码
        if not code:
            cm = re.search(r'[（(]([A-Z][A-Z\d\-—]+)[）)]', name)
            if cm:
                code = cm.group(1)
                name = name[:cm.start()].strip()
        
        # 检查是否为纯分组标题（比如"一、XXX技术"下面跟的是子指标）
        # 判断条件：section内部还有子指标编号
        sub_indicator_re = re.compile(
            r'(?:^|\n)(?:指标\s*)?[' + cn_nums + r']+[、．.]\s*.+?(?=\n|$)',
            re.MULTILINE
        )
        # 跳过本行后的文本
        after_title = text[title_match.end():section_end]
        sub_in_section = list(sub_indicator_re.finditer(after_title))
        
        # 判断这是否是分组标题（下面还有更多同级指标，本身没有"定义："）
        has_definition = '定义' in section_text or '计算公式' in section_text
        
        # 解析字段
        ind = {
            'name': name,
            'code': code,
            'definition': '',
            'formula': '',
            'significance': '',
            'notes': '',
            'category': category,
            'type': type_,
            'tables': [],
            'sub_indicators': [],
            'is_group': False,
        }
        
        # 提取各字段
        ind = extract_fields(section_text, ind)
        
        # 检查是否有子指标（括号编号）
        sub_bracket_re = re.compile(
            r'[（(]([一二三四五六七八九十]+|[1-9]\d*)[）)]\s*'  # 括号序号
            r'(.+?)(?=\n[（(]|计算公式|意义|说明|备注|\Z)',
            re.DOTALL
        )
        sub_matches = list(sub_bracket_re.finditer(section_text))
        
        if sub_matches and not has_definition:
            ind['is_group'] = True
        
        if ind['name']:
            indicators.append(ind)
    
    return indicators


def extract_fields(text, ind):
    """从文本中提取定义、公式、意义、说明等字段"""
    
    def get_section(pattern, fallback_end=None):
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else ''
    
    # 定义
    ind['definition'] = get_section(
        r'定义[：:]\s*(.*?)(?=计算公式[：:]|意义[：:]|说明[：:]|备注[：:]|注[：:]|\Z)'
    )
    
    # 计算公式
    ind['formula'] = get_section(
        r'计算公式[：:]\s*(.*?)(?=意义[：:]|说明[：:]|备注[：:]|注[：:]|定义[：:]|\Z)'
    )
    
    # 意义
    ind['significance'] = get_section(
        r'意义[：:]\s*(.*?)(?=说明[：:]|备注[：:]|注[：:]|定义[：:]|计算公式[：:]|\Z)'
    )
    
    # 说明/备注
    notes_m = re.search(
        r'(?:说明|备注)[：:]\s*(.*?)(?=定义[：:]|计算公式[：:]|意义[：:]|\Z)',
        text, re.DOTALL
    )
    if notes_m:
        ind['notes'] = notes_m.group(1).strip()
    
    # 清理各字段
    for key in ['definition', 'formula', 'significance', 'notes']:
        val = ind.get(key, '')
        if val:
            # 去除页眉
            val = re.sub(r'医疗质量管理与控制指标汇编', '', val)
            val = re.sub(r'\|\s*\d{3}\s*\|?', '', val)
            val = re.sub(r'^\s*\d{3}\s*\|', '', val, flags=re.MULTILINE)
            val = re.sub(r'\n{3,}', '\n\n', val)
            ind[key] = val.strip()
    
    return ind


def parse_unstructured_section(text, category, type_):
    """处理没有标准编号的章节"""
    text = text.strip()
    if not text:
        return []
    
    # 直接看是否有"定义"字段
    if '定义' not in text and '计算公式' not in text:
        return []
    
    ind = {
        'name': category,  # 用分类名作为指标名
        'code': '',
        'definition': '',
        'formula': '',
        'significance': '',
        'notes': '',
        'category': category,
        'type': type_,
        'tables': [],
        'sub_indicators': [],
        'is_group': False,
    }
    ind = extract_fields(text, ind)
    return [ind] if ind['definition'] or ind['formula'] else []


def build_full_text(ind):
    """构建完整文本用于搜索"""
    parts = [ind['name']]
    if ind.get('definition'):
        parts.append('定义：' + ind['definition'])
    if ind.get('formula'):
        parts.append('计算公式：' + ind['formula'])
    if ind.get('significance'):
        parts.append('意义：' + ind['significance'])
    if ind.get('notes'):
        parts.append('说明：' + ind['notes'])
    return '\n'.join(parts)


if __name__ == '__main__':
    indicators = main()
