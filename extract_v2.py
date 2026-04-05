"""
改进版：扫描整个PDF，识别章节标题和指标名称
"""
import pdfplumber
import json
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF_PATH = r'C:/Users/Bear/Desktop/医疗质量管理与控制指标汇编（8.0）.pdf'

# 章节标题识别模式（专业章节标题关键词）
SECTION_PATTERNS = [
    r'(.+?专业医疗质量控制指标.+?版[）)]?)',
    r'(.+?质量控制指标.+?版[）)]?)',
    r'(.+?质量管理与控制指标.+?版[）)]?)',
    r'(.+?技术.*?质量控制指标.+?版[）)]?)',
    r'(.+?技术临床应用质量控制指标.+?版[）)]?)',
    r'(.+?监测信息项.+?版[）)]?)',
]

def extract_all_pages():
    pages = []
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}", flush=True)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({'page_num': i+1, 'text': text})
            if (i+1) % 50 == 0:
                print(f"  处理 {i+1}/{total} 页...", flush=True)
    return pages

def detect_section_title(text):
    """检测某行是否是章节标题"""
    # 章节标题通常是短行，包含"质量控制指标"
    lines = text.split('\n')
    for line in lines[:5]:  # 检查前5行
        line = line.strip()
        if len(line) < 5:
            continue
        if ('质量控制指标' in line or '质量管理与控制指标' in line or 
            '监测信息项' in line) and '（' in line:
            return line
    return None

def parse_all_indicators(pages):
    """解析所有页面，提取指标"""
    
    # 合并所有文本，同时记录页码
    full_text = ""
    page_boundaries = []  # (char_offset, page_num)
    
    for p in pages:
        page_boundaries.append(len(full_text))
        full_text += p['text'] + "\n\n"
    
    # 第一步：识别所有章节标题
    # 方法：扫描页面，每页前几行查找章节标题
    sections = {}  # {char_offset: section_name}
    
    for p in pages:
        title = detect_section_title(p['text'])
        if title and title not in sections.values():
            offset = page_boundaries[p['page_num'] - 1]
            sections[offset] = title

    # 如果章节识别太少，用备用方法：行扫描
    # 扫描全文中独立的章节标题行
    lines_with_offset = []
    pos = 0
    for line in full_text.split('\n'):
        lines_with_offset.append((pos, line))
        pos += len(line) + 1
    
    additional_sections = {}
    cn_index_pattern = re.compile(r'^[一二三四五六七八九十][、．]')
    
    for offset, line in lines_with_offset:
        line_stripped = line.strip()
        if len(line_stripped) < 8 or len(line_stripped) > 60:
            continue
        # 独立章节标题：包含"质量控制指标"、有年份、没有指标序号前缀
        if (('质量控制指标' in line_stripped or '质量管理' in line_stripped) and 
            ('年版' in line_stripped or '年版）' in line_stripped) and
            not cn_index_pattern.match(line_stripped)):
            if line_stripped not in additional_sections.values():
                additional_sections[offset] = line_stripped
    
    # 合并sections
    all_sections = {**sections, **additional_sections}
    
    # 按偏移量排序
    sorted_sections = sorted(all_sections.items())
    print(f"识别到 {len(sorted_sections)} 个章节", flush=True)
    for off, name in sorted_sections[:10]:
        print(f"  偏移{off}: {name}", flush=True)
    
    # 第二步：在每个章节内提取指标
    indicators = []
    
    def get_category_type(category):
        if '移植' in category or ('技术' in category and '体检' not in category):
            return "医疗技术类"
        elif '用血' in category or '器官获取' in category or '单病种' in category:
            return "其他"
        else:
            return "专业（专科）类"
    
    for i, (sec_offset, sec_name) in enumerate(sorted_sections):
        # 获取本章节文本范围
        if i + 1 < len(sorted_sections):
            next_offset = sorted_sections[i+1][0]
        else:
            next_offset = len(full_text)
        
        section_text = full_text[sec_offset:next_offset]
        
        # 在章节内提取指标
        section_indicators = extract_section_indicators(section_text, sec_name)
        
        for ind in section_indicators:
            ind['id'] = len(indicators) + 1
            ind['category'] = sec_name
            ind['type'] = get_category_type(sec_name)
            indicators.append(ind)
        
        print(f"  [{sec_name[:20]}...] {len(section_indicators)} 个指标", flush=True)
    
    return indicators

def extract_section_indicators(section_text, section_name):
    """从章节文本中提取指标列表"""
    indicators = []
    
    lines = section_text.split('\n')
    cn_nums = '一二三四五六七八九十百千'
    
    current_name = None
    current_lines = []
    
    # 新指标检测：中文序号开头
    def is_indicator_start(line):
        line = line.strip()
        if not line:
            return False
        # "一、" "二、" "十一、" "二十、" 等
        m = re.match(r'^([一二三四五六七八九十百]+)[、．]\s*(.+)', line)
        if m:
            # 排除明显不是指标名的短词
            name_part = m.group(2).strip()
            if len(name_part) >= 2 and not name_part.startswith('分子') and not name_part.startswith('分母'):
                return True
        # "指标一、" "指标二、" 格式
        m2 = re.match(r'^指标[一二三四五六七八九十百]+[、．]\s*(.+)', line)
        if m2:
            return True
        return False
    
    def get_indicator_name(line):
        line = line.strip()
        m = re.match(r'^[一二三四五六七八九十百]+[、．]\s*(.+)', line)
        if m:
            return m.group(1).strip()
        m2 = re.match(r'^指标[一二三四五六七八九十百]+[、．]\s*(.+)', line)
        if m2:
            return m2.group(1).strip()
        return line
    
    for line in lines:
        if is_indicator_start(line):
            # 保存上一个指标
            if current_name and len(current_lines) > 0:
                full_text = '\n'.join(current_lines).strip()
                if len(full_text) > 20:  # 排除无内容的假指标
                    ind = parse_indicator_fields(current_name, full_text)
                    indicators.append(ind)
            
            current_name = get_indicator_name(line)
            current_lines = []
        else:
            if current_name:
                current_lines.append(line)
    
    # 保存最后一个
    if current_name and len(current_lines) > 0:
        full_text = '\n'.join(current_lines).strip()
        if len(full_text) > 20:
            ind = parse_indicator_fields(current_name, full_text)
            indicators.append(ind)
    
    return indicators

def parse_indicator_fields(name, text):
    """提取指标各字段"""
    definition = ""
    formula = ""
    significance = ""
    notes = ""
    
    # 定义
    m = re.search(r'定\s*义[：:]\s*(.*?)(?=计算公式|分子|分母|意\s*义|说\s*明|注|$)', text, re.DOTALL)
    if m:
        definition = m.group(1).strip()[:600]
    
    # 计算公式（包括分子/分母）
    m = re.search(r'(?:计算公式[：:]?\s*)?(.*?)(?=意\s*义|说\s*明|注\s*[:：]|备\s*注|$)', text, re.DOTALL)
    # 更精确地找公式
    m2 = re.search(r'计算公式[：:]\s*(.*?)(?=意\s*义|说\s*明|$)', text, re.DOTALL)
    if m2:
        formula = m2.group(1).strip()[:400]
    else:
        # 查找含"率"或"="的行
        formula_lines = []
        for line in text.split('\n'):
            if '=' in line and ('率' in line or '数' in line or '%' in line):
                formula_lines.append(line.strip())
        formula = '\n'.join(formula_lines[:5])
    
    # 意义
    m = re.search(r'意\s*义[：:]\s*(.*?)(?=说\s*明|注\s*[:：]|备\s*注|\n[一二三四五六七八九十]|$)', text, re.DOTALL)
    if m:
        significance = m.group(1).strip()[:500]
    
    # 说明/注释
    m = re.search(r'说\s*明[：:]\s*(.*?)$', text, re.DOTALL)
    if m:
        notes = m.group(1).strip()[:400]
    
    # 提取指标编码（如 ICU-01, CA-01 等）
    code_match = re.search(r'（([A-Z]{2,}-\d{2,3}(?:-\d{2})?)[）)]', name)
    code = code_match.group(1) if code_match else ""
    
    # 清理名称中的编码
    clean_name = re.sub(r'（[A-Z]{2,}-\d{2,3}(?:-\d{2})?）', '', name).strip()
    
    return {
        'name': clean_name or name,
        'code': code,
        'definition': definition,
        'formula': formula,
        'significance': significance,
        'notes': notes,
        'full_text': text[:2000],
    }

if __name__ == "__main__":
    print("提取PDF文字...", flush=True)
    pages = extract_all_pages()
    
    print("解析指标...", flush=True)
    indicators = parse_all_indicators(pages)
    
    print(f"\n总计: {len(indicators)} 个指标", flush=True)
    
    # 统计
    from collections import Counter
    cat_count = Counter(ind['category'] for ind in indicators)
    print("\n各专业指标数（前15）:")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1])[:15]:
        print(f"  {cat[:35]}: {cnt}个")
    
    # 保存
    output_path = r'C:\Users\Bear\WorkBuddy\20260402212518\indicators_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(indicators, f, ensure_ascii=False, indent=2)
    print(f"\n已保存: {output_path}", flush=True)
