import pdfplumber
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf = pdfplumber.open(r'C:/Users/Bear/Desktop/医疗质量管理与控制指标汇编（8.0）.pdf')

# 找各专业章节在PDF中的实际页码
keywords = ['超声诊断专业', '康复医学专业', '临床营养专业', '门诊管理', '医院感染管理', 
            '重症医学', '药事管理', '临床检验', '核医学', '肺脏移植', '临床用血']

found = {}
for i in range(len(pdf.pages)):
    text = pdf.pages[i].extract_text() or ''
    for kw in keywords:
        if kw in text and kw not in found:
            found[kw] = i+1
            print(f"'{kw}' 首次出现在 PDF第{i+1}页")

pdf.close()
print("查找完毕")
