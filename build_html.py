#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成离线单文件 HTML（v3）
- 数据内嵌，无需服务器
- 支持子指标展示
- 支持表格渲染
- 计算公式以数学分数形式展示（分子/横线/分母 × 百分比）
- 响应式：手机/平板/电脑自适应
"""
import json, os, re

data = json.load(open('indicators_clean.json', 'r', encoding='utf-8'))

if not data or not isinstance(data, list):
    raise SystemExit('数据为空，终止生成')

# 统计
total = len(data)
cats = sorted(set(d['category'] for d in data))
types_list = sorted(set(d['type'] for d in data))
cat_count = len(cats)
spec_count = sum(1 for d in data if d['type'] == '专业（专科）类')
tech_count = sum(1 for d in data if d['type'] == '医疗技术类')
other_count = sum(1 for d in data if d['type'] == '其他')

data_json = json.dumps(data, ensure_ascii=False)
cats_json = json.dumps(cats, ensure_ascii=False)
types_json = json.dumps(types_list, ensure_ascii=False)

# ============================================================
# JS 公式解析器（独立字符串，不在 f-string 中，无需双写花括号）
# ============================================================
FORMULA_JS = r"""
// ===== 公式解析渲染器 =====
// 把 PDF 提取出的文本公式解析为数学分数形式的 HTML
// 典型格式：
//   "分子文本\n指标名= ×100%\n分母文本"
//   "分子\n名= ×\n分母\n100000"（万分比/十万分比）
function renderFormula(raw, boxClass) {
  if (!raw) return '';
  const lines = raw.split('\n').map(s => s.trim()).filter(s => s);

  // 判断某行是否是"公式等号行"（含 = 且含 × 或 x）
  function isEqLine(l) {
    return /=\s*[×x]/i.test(l);
  }

  const equations = [];
  let i = 0;

  while (i < lines.length) {
    // 找下一个公式等号行
    let eqIdx = -1;
    for (let k = i; k < lines.length; k++) {
      if (isEqLine(lines[k])) { eqIdx = k; break; }
    }

    if (eqIdx === -1) {
      // 没有等号行了，剩余作纯文本
      for (let j = i; j < lines.length; j++) {
        equations.push({ type: 'text', text: lines[j] });
      }
      break;
    }

    // 等号行前的行 = 分子（可能多行，去掉纯数字行）
    const numeratorLines = lines.slice(i, eqIdx).filter(l => !/^[\d,，.\s]+$/.test(l));

    // 等号行本身
    const eqLine = lines[eqIdx];

    // 等号行后，找下一个等号行，中间的行 = 分母（去纯数字）
    let nextEqIdx = -1;
    for (let k = eqIdx + 1; k < lines.length; k++) {
      if (isEqLine(lines[k])) { nextEqIdx = k; break; }
    }
    const denomEnd = nextEqIdx === -1 ? lines.length : nextEqIdx;
    const denominatorLines = lines.slice(eqIdx + 1, denomEnd).filter(l => !/^[\d,，.\s]+$/.test(l));

    // 解析等号行：提取左边（指标名称）+ 右边倍率
    // 格式示例：
    //   "剖宫产率= ×100%"
    //   "孕产妇死亡活产比= × 100000"
    //   "某率= ×"（倍率在下一行）
    const eqMatch = eqLine.match(/^(.*?)\s*=\s*[×x]\s*([\d,.]+%?‰?)?(.*)$/i);
    let lhs = eqLine;
    let rawMult = '';
    if (eqMatch) {
      lhs = (eqMatch[1] || '').trim();
      rawMult = ((eqMatch[2] || '') + (eqMatch[3] || '')).trim();
    }

    // 如果倍率在分母行里（如 "100000"）
    if (!rawMult && denominatorLines.length > 0) {
      const last = denominatorLines[denominatorLines.length - 1];
      if (/^(100|1000|10000|100000|1000000)%?$/.test(last.trim())) {
        rawMult = last.trim();
        denominatorLines.pop();
      }
    }

    // 格式化倍率显示
    if (!rawMult) rawMult = '100%';
    let multDisplay = rawMult;
    const mv = rawMult.replace('%','').replace('‰','');
    if (mv === '100' || rawMult === '100%')         multDisplay = '× 100%';
    else if (mv === '1000')                          multDisplay = '× 1000‰';
    else if (mv === '10000')                         multDisplay = '× 10000（万）';
    else if (mv === '100000')                        multDisplay = '× 100000（10万）';
    else if (mv === '1000000')                       multDisplay = '× 1000000（百万）';
    else if (rawMult.endsWith('%'))                  multDisplay = '× ' + rawMult;
    else                                             multDisplay = '× ' + rawMult;

    const num = numeratorLines.join('；') || '—';
    const den = denominatorLines.join('；') || '—';

    equations.push({ type: 'fraction', lhs, num, den, mult: multDisplay });
    i = denomEnd;
  }

  if (equations.length === 0) {
    return '<div class="' + boxClass + '"><div class="formula-raw">' + esc(raw) + '</div></div>';
  }

  let inner = '<div class="formula-equations">';
  for (const eq of equations) {
    if (eq.type === 'text') {
      inner += '<div class="formula-raw">' + esc(eq.text) + '</div>';
    } else {
      inner += '<div class="formula-eq">';
      if (eq.lhs) {
        inner += '<div class="formula-lhs">' + esc(eq.lhs) + '</div>';
        inner += '<span class="formula-eq-sign">=</span>';
      }
      inner += '<div class="formula-fraction">'
             + '<div class="formula-numerator">' + esc(eq.num) + '</div>'
             + '<div class="formula-line"></div>'
             + '<div class="formula-denominator">' + esc(eq.den) + '</div>'
             + '</div>';
      if (eq.mult) {
        inner += '<div class="formula-multiplier">' + esc(eq.mult) + '</div>';
      }
      inner += '</div>';
    }
  }
  inner += '</div>';
  return '<div class="' + boxClass + '">' + inner + '</div>';
}
"""

# ============================================================
# HTML 模板（f-string）
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#1a5ea8">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>医疗质量指标检索系统</title>
<style>
/* ===== 重置 ===== */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --primary:#1a5ea8;--primary-light:#2d7dd9;--primary-bg:#eaf1fb;
  --accent:#e8813a;--text:#1a1a2e;--text-sec:#5a6a7e;--text-light:#8899aa;
  --border:#dde3ec;--bg:#f4f7fc;--card:#ffffff;
  --shadow:0 2px 12px rgba(26,94,168,.10);--shadow-h:0 6px 24px rgba(26,94,168,.18);
  --radius:12px;--radius-sm:8px;--tr:.18s ease;
}}
html{{font-size:16px}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh;-webkit-font-smoothing:antialiased}}

/* 顶部 */
.top-bar{{position:sticky;top:0;z-index:100;background:var(--primary);color:#fff;padding:12px 16px 10px;box-shadow:0 2px 8px rgba(0,0,0,.2)}}
.top-bar h1{{font-size:clamp(15px,4vw,20px);font-weight:700;text-align:center;line-height:1.3}}
.top-bar .sub{{text-align:center;font-size:11px;opacity:.75;margin-top:2px}}

/* 搜索 */
.search-wrap{{background:var(--primary);padding:10px 16px 14px}}
.search-box{{display:flex;align-items:center;background:#fff;border-radius:50px;padding:0 14px;gap:8px;box-shadow:0 2px 8px rgba(0,0,0,.15);max-width:680px;margin:0 auto}}
.si{{color:var(--text-light);font-size:16px;flex-shrink:0}}
.search-box input{{flex:1;border:none;outline:none;font-size:clamp(14px,3.5vw,16px);padding:11px 0;color:var(--text);background:transparent;min-width:0}}
.search-box input::placeholder{{color:var(--text-light)}}
.clr-btn{{background:none;border:none;cursor:pointer;color:var(--text-light);font-size:18px;padding:4px;display:none;line-height:1}}
.clr-btn.show{{display:block}}

/* Tab筛选 */
.filter-bar{{background:#fff;border-bottom:1px solid var(--border);overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:0 8px}}
.filter-bar::-webkit-scrollbar{{display:none}}
.ftab{{display:inline-block;padding:10px 14px;font-size:clamp(12px,3vw,14px);color:var(--text-sec);cursor:pointer;border-bottom:2px solid transparent;transition:color var(--tr),border-color var(--tr);user-select:none;-webkit-tap-highlight-color:transparent}}
.ftab:hover{{color:var(--primary)}}
.ftab.active{{color:var(--primary);border-bottom-color:var(--primary);font-weight:600}}

/* 分类下拉 */
.cat-wrap{{background:#fff;border-bottom:1px solid var(--border);padding:8px 12px;display:flex;align-items:center;gap:8px;max-width:900px;margin:0 auto}}
.cat-label{{font-size:13px;color:var(--text-sec);white-space:nowrap;flex-shrink:0}}
.cat-sel{{flex:1;border:1px solid var(--border);border-radius:var(--radius-sm);padding:6px 10px;font-size:clamp(12px,3vw,14px);color:var(--text);background:#fff;outline:none;cursor:pointer}}
.cat-sel:focus{{border-color:var(--primary)}}

/* 统计栏 */
.stats-bar{{padding:8px 16px;background:#fff;border-bottom:1px solid var(--border)}}
.stats-inner{{max-width:900px;margin:0 auto;display:flex;gap:12px;flex-wrap:wrap;align-items:center}}
.stat-item{{font-size:12px;color:var(--text-sec)}}
.stat-item strong{{color:var(--primary)}}

/* 结果 */
.result-bar{{padding:10px 16px 6px;max-width:900px;margin:0 auto}}
.result-count{{font-size:13px;color:var(--text-sec)}}
.result-count strong{{color:var(--primary);font-weight:700}}

/* 列表 */
.list-wrap{{padding:0 12px 20px;max-width:900px;margin:0 auto}}
.card{{background:var(--card);border-radius:var(--radius);padding:14px 16px;margin-bottom:10px;box-shadow:var(--shadow);cursor:pointer;transition:box-shadow var(--tr),transform var(--tr);-webkit-tap-highlight-color:transparent;border:1px solid transparent}}
.card:hover{{box-shadow:var(--shadow-h);transform:translateY(-2px);border-color:var(--primary-bg)}}
.card:active{{transform:scale(.99)}}
.card-name{{font-size:clamp(14px,3.5vw,16px);font-weight:600;color:var(--text);line-height:1.5;margin-bottom:6px}}
.card-name mark,.card-def mark{{background:#fff3b0;color:var(--text);border-radius:3px;padding:0 1px}}
.card-meta{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px;align-items:center}}
.tag{{font-size:11px;padding:2px 8px;border-radius:50px;font-weight:500}}
.tag-spec{{background:var(--primary-bg);color:var(--primary)}}
.tag-other{{background:#f0f4f0;color:#4a7a4a}}
.tag-tech{{background:#fef3e8;color:#c06010}}
.tag-sub{{background:#f5f0ff;color:#6644bb;font-size:10px}}
.card-cat{{font-size:12px;color:var(--text-light);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.card-def{{font-size:12px;color:var(--text-sec);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-top:6px;line-height:1.6}}
.load-more{{text-align:center;padding:16px}}
.more-btn{{background:var(--primary);color:#fff;border:none;border-radius:50px;padding:12px 40px;font-size:14px;cursor:pointer;box-shadow:var(--shadow);transition:background var(--tr),transform var(--tr)}}
.more-btn:hover{{background:var(--primary-light);transform:translateY(-1px)}}
.empty{{text-align:center;padding:60px 20px;color:var(--text-light)}}
.empty .ei{{font-size:48px;margin-bottom:16px}}
.empty p{{font-size:15px}}

/* 模态框 */
.overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;align-items:flex-end;justify-content:center;padding:0;backdrop-filter:blur(2px);-webkit-backdrop-filter:blur(2px)}}
.overlay.show{{display:flex}}
.modal{{background:var(--card);border-radius:var(--radius) var(--radius) 0 0;width:100%;max-width:800px;max-height:92vh;overflow-y:auto;-webkit-overflow-scrolling:touch;animation:slideUp .25s ease;position:relative}}
@keyframes slideUp{{from{{transform:translateY(60px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
.drag-bar{{width:36px;height:4px;background:var(--border);border-radius:2px;margin:10px auto 0}}
.modal-hd{{padding:14px 60px 14px 20px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--card);z-index:1}}
.modal-title{{font-size:clamp(15px,3.5vw,18px);font-weight:700;color:var(--text);line-height:1.5}}
.modal-code{{font-size:11px;color:var(--text-light);margin-top:3px;font-family:monospace}}
.m-close{{position:absolute;right:16px;top:50%;transform:translateY(-50%);background:var(--bg);border:none;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;color:var(--text-sec);margin-top:4px}}
.m-close:hover{{background:var(--border)}}
.modal-bd{{padding:16px 20px 8px}}
.m-tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}}

/* 详情节 */
.sec{{margin-bottom:18px}}
.sec-label{{font-size:11px;font-weight:700;letter-spacing:1px;color:var(--primary);margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.sec-label::before{{content:'';display:inline-block;width:3px;height:14px;background:var(--primary);border-radius:2px}}
.sec-content{{font-size:clamp(13px,3vw,15px);line-height:1.8;color:var(--text);white-space:pre-wrap;word-break:break-all}}

/* 子指标 */
.sub-section{{background:var(--bg);border-radius:var(--radius-sm);padding:12px 14px;margin-bottom:12px;border-left:3px solid #a090ee}}
.sub-title{{font-size:14px;font-weight:600;color:#6644bb;margin-bottom:8px}}
.sub-def,.sub-sig,.sub-notes{{font-size:clamp(12px,2.8vw,14px);line-height:1.7;color:var(--text);margin-bottom:6px;white-space:pre-wrap;word-break:break-all}}
.sub-label{{font-size:11px;font-weight:700;color:#6644bb;margin-bottom:3px}}

/* ===== 数学公式分数展示 ===== */
/* 主指标公式框 */
.formula-visual{{
  background:linear-gradient(135deg,#f0f6ff 0%,#eaf1fb 100%);
  border:1px solid #c5d8f5;
  border-radius:var(--radius-sm);
  padding:20px 16px 18px;
  overflow-x:auto;
  -webkit-overflow-scrolling:touch;
}}
/* 子指标公式框 */
.sub-formula-visual{{
  background:linear-gradient(135deg,#f8f5ff 0%,#f0eeff 100%);
  border:1px solid #c8c0ee;
  border-radius:6px;
  padding:16px 12px 14px;
  overflow-x:auto;
  -webkit-overflow-scrolling:touch;
  margin-bottom:6px;
}}
/* 多公式竖排 */
.formula-equations{{display:flex;flex-direction:column;gap:22px}}
/* 单条公式行：名称 = 分数 × 倍率 */
.formula-eq{{
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap:wrap;
  min-width:0;
}}
/* 左侧指标名称标签 */
.formula-lhs{{
  font-size:clamp(12px,2.8vw,13px);
  color:var(--primary);
  font-weight:700;
  white-space:nowrap;
  background:rgba(26,94,168,.08);
  padding:4px 10px;
  border-radius:6px;
  border:1px solid rgba(26,94,168,.2);
  line-height:1.4;
  max-width:200px;
  overflow:hidden;
  text-overflow:ellipsis;
}}
.sub-formula-visual .formula-lhs{{
  color:#6644bb;
  background:rgba(102,68,187,.08);
  border-color:rgba(102,68,187,.2);
}}
/* 等号 */
.formula-eq-sign{{
  font-size:clamp(18px,3.5vw,22px);
  color:var(--text-sec);
  font-weight:300;
  line-height:1;
  flex-shrink:0;
}}
/* 分数容器 */
.formula-fraction{{
  display:inline-flex;
  flex-direction:column;
  align-items:stretch;
  min-width:140px;
  max-width:calc(100vw - 200px);
}}
/* 分子 */
.formula-numerator{{
  font-size:clamp(11px,2.6vw,13px);
  color:var(--text);
  text-align:center;
  padding:7px 14px 6px;
  line-height:1.5;
  word-break:break-all;
  background:rgba(255,255,255,.8);
  border-radius:4px 4px 0 0;
  border:1px solid rgba(26,94,168,.12);
  border-bottom:none;
}}
/* 分数横线 */
.formula-line{{
  height:2px;
  background:var(--text);
  border-radius:1px;
  margin:0;
}}
/* 分母 */
.formula-denominator{{
  font-size:clamp(11px,2.6vw,13px);
  color:var(--text);
  text-align:center;
  padding:6px 14px 7px;
  line-height:1.5;
  word-break:break-all;
  background:rgba(255,255,255,.8);
  border-radius:0 0 4px 4px;
  border:1px solid rgba(26,94,168,.12);
  border-top:none;
}}
/* 乘以倍率 */
.formula-multiplier{{
  font-size:clamp(13px,2.8vw,15px);
  color:#c05000;
  font-weight:700;
  white-space:nowrap;
  flex-shrink:0;
  background:#fff3e8;
  padding:5px 10px;
  border-radius:6px;
  border:1px solid #f5c89a;
  line-height:1.4;
}}
.sub-formula-visual .formula-multiplier{{
  color:#7722aa;
  background:#f5eeff;
  border-color:#d4b8ee;
}}
/* 兜底纯文本行 */
.formula-raw{{
  background:rgba(255,255,255,.6);
  border:1px solid rgba(26,94,168,.12);
  border-radius:var(--radius-sm);
  padding:8px 12px;
  font-family:"Courier New",Consolas,monospace;
  font-size:clamp(11px,2.5vw,13px);
  white-space:pre-wrap;
  word-break:break-all;
  color:var(--text);
}}

/* 表格 */
.indicator-table{{width:100%;border-collapse:collapse;font-size:clamp(11px,2.5vw,13px);margin:8px 0;overflow-x:auto;display:block}}
.indicator-table th,.indicator-table td{{border:1px solid var(--border);padding:6px 8px;text-align:left;line-height:1.5}}
.indicator-table th{{background:var(--primary-bg);color:var(--primary);font-weight:600}}
.indicator-table tr:nth-child(even){{background:#f8fafd}}
.table-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:8px 0}}

/* 底部操作 */
.modal-ft{{display:flex;gap:10px;padding:12px 20px 20px;border-top:1px solid var(--border);position:sticky;bottom:0;background:var(--card)}}
.act-btn{{flex:1;padding:12px;border-radius:var(--radius-sm);border:none;font-size:14px;font-weight:600;cursor:pointer;transition:all var(--tr);-webkit-tap-highlight-color:transparent}}
.act-copy{{background:var(--primary-bg);color:var(--primary)}}
.act-copy:hover{{background:#d0e4f8}}
.act-copy.ok{{background:#d4f0d4;color:#2d7a2d}}

.toast{{position:fixed;bottom:100px;left:50%;transform:translateX(-50%) translateY(20px);background:rgba(0,0,0,.75);color:#fff;padding:10px 20px;border-radius:50px;font-size:14px;z-index:999;opacity:0;transition:all .25s;pointer-events:none;white-space:nowrap}}
.toast.show{{opacity:1;transform:translateX(-50%) translateY(0)}}

/* 桌面端 */
@media(min-width:768px){{
  .filter-bar{{display:flex;justify-content:center;padding:0 20px}}
  .ftab{{padding:12px 18px}}
  .cat-wrap,.result-bar,.list-wrap,.stats-bar .stats-inner{{max-width:900px}}
  .overlay{{align-items:center;padding:20px}}
  .modal{{border-radius:var(--radius);max-height:88vh}}
  .drag-bar{{display:none}}
}}
@media(min-width:1200px){{
  .search-box{{max-width:780px}}
  .list-wrap,.result-bar,.cat-wrap{{max-width:1000px}}
  .modal{{max-width:900px}}
}}
</style>
</head>
<body>

<div class="top-bar">
  <h1>🏥 医疗质量指标检索系统</h1>
  <div class="sub">共 {total} 条指标 · {cat_count} 个专业方向 · 离线可用</div>
</div>

<div class="search-wrap">
  <div class="search-box">
    <span class="si">🔍</span>
    <input type="search" id="kw" placeholder="搜索指标名称、定义、关键词…" autocomplete="off" autocorrect="off" spellcheck="false">
    <button class="clr-btn" id="clrBtn" onclick="clearKw()">✕</button>
  </div>
</div>

<div class="filter-bar" id="filterBar"></div>

<div style="background:#fff;border-bottom:1px solid var(--border)">
  <div class="cat-wrap">
    <span class="cat-label">专业方向：</span>
    <select class="cat-sel" id="catSel">
      <option value="">全部分类</option>
    </select>
  </div>
</div>

<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat-item">专科类 <strong>{spec_count}</strong></div>
    <div class="stat-item">技术类 <strong>{tech_count}</strong></div>
    <div class="stat-item">其他 <strong>{other_count}</strong></div>
    <div class="stat-item" id="resultCount" style="margin-left:auto">加载中…</div>
  </div>
</div>

<div class="list-wrap" id="listWrap"></div>

<div class="overlay" id="overlay">
  <div class="modal" id="modal">
    <div class="drag-bar"></div>
    <div class="modal-hd">
      <div class="modal-title" id="mTitle"></div>
      <div class="modal-code" id="mCode"></div>
      <button class="m-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-bd" id="mBody"></div>
    <div class="modal-ft">
      <button class="act-btn act-copy" id="copyBtn" onclick="copyAll()">📋 复制全文</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const ALL = {data_json};
let filtered=[], page=0, curType='all', curCat='', curKw='', curItem=null;
const PAGE=20;

// 初始化
(function(){{
  const types=['all',...{types_json}];
  const labels={{all:'全部','专业（专科）类':'专科','医疗技术类':'技术','其他':'其他'}};
  const fb=document.getElementById('filterBar');
  types.forEach(t=>{{
    const el=document.createElement('div');
    el.className='ftab'+(t==='all'?' active':'');
    el.textContent=labels[t]||t;
    el.dataset.type=t;
    el.addEventListener('click',()=>setType(t));
    fb.appendChild(el);
  }});
  const sel=document.getElementById('catSel');
  {cats_json}.forEach(c=>{{
    const o=document.createElement('option');
    o.value=c; o.textContent=c; sel.appendChild(o);
  }});
  sel.addEventListener('change',e=>{{curCat=e.target.value;applyFilter();}});
  const inp=document.getElementById('kw');
  let timer;
  inp.addEventListener('input',e=>{{
    const v=e.target.value;
    document.getElementById('clrBtn').classList.toggle('show',v.length>0);
    clearTimeout(timer);
    timer=setTimeout(()=>{{curKw=v.trim().toLowerCase();applyFilter();}},200);
  }});
  document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeModal();}});
  applyFilter();
}})();

function setType(t){{
  curType=t;
  document.querySelectorAll('.ftab').forEach(el=>el.classList.toggle('active',el.dataset.type===t));
  applyFilter();
}}
function clearKw(){{
  document.getElementById('kw').value='';
  document.getElementById('clrBtn').classList.remove('show');
  curKw=''; applyFilter();
  document.getElementById('kw').focus();
}}

function applyFilter(){{
  let r=ALL;
  if(curType!=='all') r=r.filter(d=>d.type===curType);
  if(curCat) r=r.filter(d=>d.category===curCat);
  if(curKw){{
    r=r.filter(d=>
      d.name.toLowerCase().includes(curKw)||
      d.category.toLowerCase().includes(curKw)||
      (d.definition&&d.definition.toLowerCase().includes(curKw))||
      (d.formula&&d.formula.toLowerCase().includes(curKw))||
      (d.significance&&d.significance.toLowerCase().includes(curKw))||
      (d.notes&&d.notes.toLowerCase().includes(curKw))||
      (d.full_text&&d.full_text.toLowerCase().includes(curKw))
    );
  }}
  filtered=r; page=0;
  const cnt=document.getElementById('resultCount');
  cnt.innerHTML='共 <strong>'+filtered.length+'</strong> 条'+(curKw?'（关键词：<em>'+esc(curKw)+'</em>）':'');
  renderList(true);
}}

function renderList(reset){{
  const wrap=document.getElementById('listWrap');
  if(reset) wrap.innerHTML='';
  const start=page*PAGE, end=Math.min(start+PAGE,filtered.length);
  const slice=filtered.slice(start,end);
  if(reset&&slice.length===0){{
    wrap.innerHTML='<div class="empty"><div class="ei">🔍</div><p>没有找到符合条件的指标</p></div>';
    return;
  }}
  const old=wrap.querySelector('.load-more');
  if(old) old.remove();
  slice.forEach(item=>{{
    const card=document.createElement('div');
    card.className='card';
    card.innerHTML=buildCard(item);
    card.addEventListener('click',()=>openModal(item));
    wrap.appendChild(card);
  }});
  if(end<filtered.length){{
    const more=document.createElement('div');
    more.className='load-more';
    more.innerHTML='<button class="more-btn" onclick="loadMore()">加载更多（还有'+(filtered.length-end)+'条）</button>';
    wrap.appendChild(more);
  }}
}}

function loadMore(){{page++;renderList(false);}}

function buildCard(d){{
  const kw=curKw;
  const tc=d.type==='专业（专科）类'?'tag-spec':d.type==='医疗技术类'?'tag-tech':'tag-other';
  const def=(d.definition||'').replace(/\\n/g,' ').trim();
  const hasSub=d.sub_indicators&&d.sub_indicators.length>0;
  return `
    <div class="card-name">${{hl(esc(d.name),kw)}}</div>
    <div class="card-meta">
      <span class="tag ${{tc}}">${{esc(d.type)}}</span>
      ${{hasSub?'<span class="tag tag-sub">含'+d.sub_indicators.length+'个子指标</span>':''}}
      ${{d.code?'<span style="font-size:11px;color:var(--text-light);font-family:monospace">'+esc(d.code)+'</span>':''}}
    </div>
    <div class="card-cat">${{esc(d.category)}}</div>
    ${{def?'<div class="card-def">'+hl(esc(def),kw)+'</div>':''}}
  `;
}}

function openModal(item){{
  curItem=item;
  document.getElementById('mTitle').textContent=item.name;
  document.getElementById('mCode').textContent=item.code||'';
  const tc=item.type==='专业（专科）类'?'tag-spec':item.type==='医疗技术类'?'tag-tech':'tag-other';
  let html=`<div class="m-tags">
    <span class="tag ${{tc}}">${{esc(item.type)}}</span>
    <span class="tag" style="background:#f0f4ff;color:#5566aa">${{esc(item.category)}}</span>
  </div>`;
  if(item.definition) html+=sec('📖 定义','<div class="sec-content">'+esc(item.definition)+'</div>');
  if(item.formula)    html+=sec('📐 计算公式', renderFormula(item.formula,'formula-visual'));
  if(item.significance) html+=sec('💡 指标意义','<div class="sec-content">'+esc(item.significance)+'</div>');
  if(item.notes)      html+=sec('📝 说明','<div class="sec-content">'+esc(item.notes)+'</div>');
  if(item.sub_indicators&&item.sub_indicators.length>0){{
    let subHtml='';
    item.sub_indicators.forEach(sub=>{{
      subHtml+=`<div class="sub-section">
        <div class="sub-title">▸ ${{esc(sub.name)}} ${{sub.code?'<span style="font-size:11px;color:#9988cc;font-family:monospace">'+esc(sub.code)+'</span>':''}}</div>
        ${{sub.definition?'<div class="sub-label">定义</div><div class="sub-def">'+esc(sub.definition)+'</div>':''}}
        ${{sub.formula?'<div class="sub-label">计算公式</div>'+renderFormula(sub.formula,'sub-formula-visual'):''}}
        ${{sub.significance?'<div class="sub-label">意义</div><div class="sub-sig">'+esc(sub.significance)+'</div>':''}}
        ${{sub.notes?'<div class="sub-label">说明</div><div class="sub-notes">'+esc(sub.notes)+'</div>':''}}
      </div>`;
    }});
    html+=sec('🔖 子指标（'+item.sub_indicators.length+'项）',subHtml);
  }}
  if(item.tables_html&&item.tables_html.length>0){{
    let tblHtml=item.tables_html.map(t=>'<div class="table-wrap">'+t+'</div>').join('');
    html+=sec('📊 参考表格',tblHtml);
  }}
  document.getElementById('mBody').innerHTML=html;
  document.getElementById('copyBtn').classList.remove('ok');
  document.getElementById('copyBtn').textContent='📋 复制全文';
  document.getElementById('overlay').classList.add('show');
  document.body.style.overflow='hidden';
}}

function sec(label,contentHtml){{
  return '<div class="sec"><div class="sec-label">'+label+'</div>'+contentHtml+'</div>';
}}
function closeModal(){{
  document.getElementById('overlay').classList.remove('show');
  document.body.style.overflow='';
}}
document.getElementById('overlay').addEventListener('click',function(e){{
  if(e.target===this) closeModal();
}});

function copyAll(){{
  if(!curItem) return;
  const d=curItem;
  let t='【'+d.name+'】\\n';
  t+='分类：'+d.category+'\\n类型：'+d.type+'\\n';
  if(d.code) t+='代码：'+d.code+'\\n';
  if(d.definition) t+='\\n定义：\\n'+d.definition+'\\n';
  if(d.formula) t+='\\n计算公式：\\n'+d.formula+'\\n';
  if(d.significance) t+='\\n指标意义：\\n'+d.significance+'\\n';
  if(d.notes) t+='\\n说明：\\n'+d.notes+'\\n';
  if(d.sub_indicators&&d.sub_indicators.length>0){{
    t+='\\n子指标：\\n';
    d.sub_indicators.forEach(sub=>{{
      t+='  【'+sub.name+'】\\n';
      if(sub.definition) t+='  定义：'+sub.definition+'\\n';
      if(sub.formula) t+='  公式：'+sub.formula+'\\n';
      if(sub.significance) t+='  意义：'+sub.significance+'\\n';
    }});
  }}
  const write=text=>{{
    if(navigator.clipboard&&navigator.clipboard.writeText){{
      navigator.clipboard.writeText(text).then(showOk).catch(()=>fbCopy(text));
    }}else fbCopy(text);
  }};
  write(t);
}}
function fbCopy(text){{
  const ta=document.createElement('textarea');
  ta.value=text; ta.style.cssText='position:fixed;left:-9999px;top:-9999px';
  document.body.appendChild(ta); ta.select();
  try{{document.execCommand('copy');showOk();}}catch(e){{showToast('复制失败，请手动选择');}}
  document.body.removeChild(ta);
}}
function showOk(){{
  const btn=document.getElementById('copyBtn');
  btn.textContent='✅ 已复制'; btn.classList.add('ok');
  showToast('已复制到剪贴板');
  setTimeout(()=>{{btn.textContent='📋 复制全文';btn.classList.remove('ok');}},2500);
}}
function showToast(msg){{
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2200);
}}
function esc(s){{
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
function hl(html,kw){{
  if(!kw) return html;
  const safe=kw.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&');
  return html.replace(new RegExp('('+safe+')','gi'),'<mark>$1</mark>');
}}

</script>
</body>
</html>"""

# 在 </script> 前插入公式解析器 JS（独立字符串，避免 f-string 花括号问题）
html = html.replace('\n</script>\n</body>', '\n' + FORMULA_JS + '\n</script>\n</body>')

out = 'medical_quality_indicators_offline.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(out) / 1024
print(f'✅ 生成完成: {out}')
print(f'   文件大小: {size_kb:.1f} KB ({size_kb/1024:.2f} MB)')
print(f'   指标总数: {total}')
print(f'   分类数量: {cat_count}')
