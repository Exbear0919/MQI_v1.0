"""
提取医疗质量管理与控制指标PDF中的所有指标
"""
import pdfplumber
import json
import re

PDF_PATH = r'C:/Users/Bear/Desktop/医疗质量管理与控制指标汇编（8.0）.pdf'

# 目录：专业名称 -> 起始页码（PDF页码，1-based）
# 从目录页读取
TOC = {
    "住院病案首页数据质量管理与控制指标（2016年版）": 5,
    "产科专业医疗质量控制指标（2019年版）": 10,
    "呼吸内科专业医疗质量控制指标（2019年版）": 15,
    "神经系统疾病医疗质量控制指标（2020年版）": 25,
    "肾病专业医疗质量控制指标（2020年版）": 60,
    "护理专业医疗质量控制指标（2020年版）": 74,
    "病案管理质量控制指标（2021年版）": 86,
    "心血管系统疾病相关专业医疗质量控制指标（2021年版）": 96,
    "超声诊断专业医疗质量控制指标（2022年版）": 134,
    "康复医学专业医疗质量控制指标（2022年版）": 141,
    "临床营养专业医疗质量控制指标（2022年版）": 150,
    "麻醉专业医疗质量控制指标（2022年版）": 156,
    "肿瘤专业质量控制指标（2023年版）": 167,
    "感染性疾病专业医疗质量控制指标（2023年版）": 212,
    "健康体检与管理专业医疗质量控制指标（2023年版）": 216,
    "疼痛专业医疗质量控制指标（2023年版）": 219,
    "整形美容专业医疗质量控制指标（2023年版）": 224,
    "急诊医学专业医疗质量控制指标（2024年版）": 228,
    "脑损伤评价医疗质量控制指标（2024年版）": 235,
    "病理专业医疗质量控制指标（2024年版）": 240,
    "放射影像专业医疗质量控制指标（2024年版）": 245,
    "门诊管理医疗质量控制指标（2024年版）": 248,
    "医院感染管理医疗质量控制指标（2024年版）": 252,
    "重症医学专业医疗质量控制指标（2024年版）": 258,
    "药事管理专业医疗质量控制指标（2025年版）": 266,
    "临床检验专业医疗质量控制指标（2025年版）": 276,
    "核医学专业医疗质量控制指标（2025年版）": 282,
    "肺脏移植技术医疗质量控制指标（2020年版）": 289,
    "肝脏移植技术医疗质量控制指标（2020年版）": 294,
    "肾脏移植技术医疗质量控制指标（2020年版）": 302,
    "心脏移植技术医疗质量控制指标（2020年版）": 307,
    "异基因造血干细胞移植技术临床应用质量控制指标（2022年版）": 312,
    "同种胰岛移植技术临床应用质量控制指标（2022年版）": 317,
    "同种异体运动系统结构性组织移植技术临床应用质量控制指标（2022年版）": 321,
    "同种异体角膜移植技术临床应用质量控制指标（2022年版）": 324,
    "性别重置技术临床应用质量控制指标（2022年版）": 329,
    "质子和重离子加速器放射治疗技术临床应用质量控制指标（2022年版）": 333,
    "放射性粒子植入治疗技术临床应用质量控制指标（2022年版）": 336,
    "肿瘤消融治疗技术临床应用质量控制指标（2022年版）": 342,
    "心室辅助技术临床应用质量控制指标（2022年版）": 346,
    "人工智能辅助治疗技术临床应用质量控制指标（2022年版）": 351,
    "体外膜肺氧合（ECMO）技术临床应用质量控制指标（2022年版）": 355,
    "自体器官移植技术临床应用质量控制指标（2022年版）": 359,
    "消化内镜诊疗技术医疗质量控制指标（2022年版）": 366,
    "人体器官获取组织质量控制指标": 377,
    "临床用血质量控制指标（2019年版）": 383,
    "单病种质量监测信息项（2020年版）": 387,
}

def page_num_to_pdf_index(page_num):
    """目录中的页码需要偏移（目录页码从003开始，PDF第5页）"""
    # 目录显示003对应第5页PDF，说明偏移量为PDF_index = page_num + 2
    return page_num + 2

def extract_all_text():
    """提取所有页面文字"""
    all_pages = []
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            all_pages.append(text)
            if (i+1) % 50 == 0:
                print(f"  已处理 {i+1}/{total} 页")
    return all_pages

def parse_indicators(all_pages):
    """解析指标数据"""
    # 排序TOC by page
    toc_list = sorted(TOC.items(), key=lambda x: x[1])
    
    indicators = []
    
    for idx, (category, start_page) in enumerate(toc_list):
        # 确定结束页
        if idx + 1 < len(toc_list):
            end_page = toc_list[idx + 1][1]
        else:
            end_page = len(all_pages) + 1
        
        # 获取该专业的所有文字
        pdf_start = page_num_to_pdf_index(start_page)
        pdf_end = page_num_to_pdf_index(end_page)
        
        section_text = ""
        for p in range(pdf_start - 1, min(pdf_end - 1, len(all_pages))):
            section_text += all_pages[p] + "\n"
        
        # 解析各个指标（以"一、""二、"等中文序号开头）
        # 匹配模式：中文数字序号 + 、+ 指标名称
        pattern = r'[一二三四五六七八九十百]+[一二三四五六七八九十]?[、．]\s*(.+?)(?=\n[一二三四五六七八九十百]+[一二三四五六七八九十]?[、．]|\Z)'
        
        matches = re.findall(pattern, section_text, re.DOTALL)
        
        # 也尝试罗马数字/阿拉伯数字序号
        # 拆分文本为各指标块
        # 用更健壮的方式：寻找"一、""二、"...等行
        lines = section_text.split('\n')
        
        current_indicator = None
        current_text = []
        
        cn_nums = '一二三四五六七八九十百千'
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_text:
                    current_text.append('')
                continue
            
            # 检测新指标开始：中文序号 + 、
            is_new_indicator = False
            for cn in cn_nums:
                if line.startswith(cn + '、') or line.startswith(cn + '．'):
                    is_new_indicator = True
                    break
            # 两字中文序号
            if not is_new_indicator:
                m = re.match(r'^[一二三四五六七八九十][一二三四五六七八九十〇零]?[、．]', line)
                if m:
                    is_new_indicator = True
            
            if is_new_indicator:
                # 保存上一个指标
                if current_indicator:
                    full_text = '\n'.join(current_text).strip()
                    definition, formula, significance = parse_indicator_fields(full_text)
                    indicators.append({
                        "id": len(indicators) + 1,
                        "category": category,
                        "name": current_indicator,
                        "definition": definition,
                        "formula": formula,
                        "significance": significance,
                        "full_text": full_text[:1500],
                    })
                
                # 提取指标名（去掉序号）
                name = re.sub(r'^[一二三四五六七八九十百千]+[、．]\s*', '', line)
                current_indicator = name.strip()
                current_text = []
            else:
                if current_indicator:
                    current_text.append(line)
        
        # 保存最后一个
        if current_indicator:
            full_text = '\n'.join(current_text).strip()
            definition, formula, significance = parse_indicator_fields(full_text)
            indicators.append({
                "id": len(indicators) + 1,
                "category": category,
                "name": current_indicator,
                "definition": definition,
                "formula": formula,
                "significance": significance,
                "full_text": full_text[:1500],
            })
        
        print(f"  [{category[:15]}...] 提取到 {len([i for i in indicators if i['category']==category])} 个指标")
    
    return indicators

def parse_indicator_fields(text):
    """从指标全文中提取定义、计算公式、意义"""
    definition = ""
    formula = ""
    significance = ""
    
    # 定义
    m = re.search(r'定\s*义[：:]\s*(.*?)(?=计算公式|分子|分母|意\s*义|$)', text, re.DOTALL)
    if m:
        definition = m.group(1).strip()[:500]
    
    # 计算公式
    m = re.search(r'计算公式[：:]\s*(.*?)(?=意\s*义|注\s*:|备\s*注|$)', text, re.DOTALL)
    if m:
        formula = m.group(1).strip()[:300]
    
    # 意义
    m = re.search(r'意\s*义[：:]\s*(.*?)(?=\n[一二三四五六七八九十]|$)', text, re.DOTALL)
    if m:
        significance = m.group(1).strip()[:400]
    
    return definition, formula, significance

def get_category_type(category):
    """判断专业类别大类"""
    if '移植' in category or '技术' in category:
        return "医疗技术类"
    elif '用血' in category or '器官获取' in category or '单病种' in category:
        return "其他"
    else:
        return "专业（专科）类"

if __name__ == "__main__":
    print("开始提取PDF文字...")
    all_pages = extract_all_text()
    
    print("开始解析指标...")
    indicators = parse_indicators(all_pages)
    
    # 添加大类标签
    for ind in indicators:
        ind["type"] = get_category_type(ind["category"])
    
    print(f"\n总计提取指标: {len(indicators)} 个")
    
    # 统计各专业指标数
    from collections import Counter
    cat_count = Counter(i["category"] for i in indicators)
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat[:30]}: {cnt}个")
    
    # 保存JSON
    output_path = r'C:\Users\Bear\WorkBuddy\20260402212518\indicators_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(indicators, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_path}")
