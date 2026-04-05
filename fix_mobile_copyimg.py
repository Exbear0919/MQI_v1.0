"""
修复手机端搜索框溢出 + 添加复制为图片功能
"""
import re

with open('medical_quality_indicators_offline.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ─────────────────────────────────────────────
# 1. 手机端搜索框溢出修复：在 @media 之前插入 mobile-only 样式
# ─────────────────────────────────────────────
mobile_fix = """
/* ===== 手机端搜索框强制不溢出 ===== */
@media(max-width:767px){
  .search-wrap{
    padding:10px 12px 14px !important;
    overflow:hidden;
  }
  .search-box{
    width:100% !important;
    max-width:100% !important;
    padding:0 12px !important;
    gap:6px;
  }
  .search-box input{
    font-size:15px !important;
    padding:10px 0;
  }
  .si{font-size:15px !important}
  .clr-btn{font-size:16px !important;padding:2px 6px !important}
}
"""

# 在 @media(min-width:768px) 之前插入
insert_point = html.find('@media(min-width:768px)')
if insert_point != -1:
    html = html[:insert_point] + mobile_fix + html[insert_point:]
else:
    # fallback: 插入在 </style> 之前
    html = html.replace('</style>', mobile_fix + '\n</style>')

# ─────────────────────────────────────────────
# 2. 在 </head> 之前插入 html2canvas CDN
# ─────────────────────────────────────────────
cdn_script = '<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>\n'
html = html.replace('</head>', cdn_script + '</head>')

# ─────────────────────────────────────────────
# 3. 修改底部按钮区域：复制文字 + 复制图片
# ─────────────────────────────────────────────
old_footer = '<button class="act-btn act-copy" id="copyBtn" onclick="copyAll()">📋 复制全文</button>'
new_footer = '''<button class="act-btn act-copy" id="copyBtn" onclick="copyAll()">📋 复制文字</button>
      <button class="act-btn act-img" id="imgBtn" onclick="copyImage()">🖼 复制图片</button>'''
html = html.replace(old_footer, new_footer)

# ─────────────────────────────────────────────
# 4. 添加图片按钮 CSS 样式
# ─────────────────────────────────────────────
img_btn_css = """
/* 图片复制按钮 */
.act-img{background:#fff4e8;color:#d97706;border:1.5px solid #fcd34d}
.act-img:hover{background:#fef3c7}
.act-img.ok{background:#d1fae5;color:#065f46}
"""
html = html.replace('.act-copy.ok{background:#d4f0d4;color:#2d7a2d}', '.act-copy.ok{background:#d4f0d4;color:#2d7a2d}' + img_btn_css)

# ─────────────────────────────────────────────
# 5. 在 copyAll() 函数之后插入 copyImage() 函数
# ─────────────────────────────────────────────
copy_image_fn = """
function copyImage(){
  if(!curItem) return;
  const btn=document.getElementById('imgBtn');
  btn.textContent='⏳ 生成中…'; btn.disabled=true;
  const body=document.getElementById('mBody');

  // 临时创建一个用于渲染的高质量 div（宽度固定 680px，移动端缩放）
  const W=Math.min(680,window.innerWidth-32);
  const wrapper=document.createElement('div');
  wrapper.style.cssText='width:'+W+'px;padding:20px;background:#fff;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;';

  // 标题
  const title=document.createElement('div');
  title.style.cssText='font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:6px;line-height:1.4;word-break:break-all';
  title.textContent=curItem.name;
  wrapper.appendChild(title);

  // 编码
  if(curItem.code){
    const code=document.createElement('div');
    code.style.cssText='font-size:12px;color:#888;font-family:monospace;margin-bottom:14px';
    code.textContent='代码：'+curItem.code;
    wrapper.appendChild(code);
  }

  // 内容区
  const contentDiv=document.createElement('div');
  contentDiv.style.cssText='display:flex;flex-direction:column;gap:12px';
  const sections=body.querySelectorAll('.sec');
  sections.forEach(sec=>{
    const clone=sec.cloneNode(true);
    // 去掉展开按钮
    const expandBtn=clone.querySelector('.expand-btn');
    if(expandBtn) expandBtn.remove();
    // 移除公式的按钮样式，只保留结构
    clone.querySelectorAll('.formula-visual,.sub-formula-visual').forEach(f=>{
      f.style.display='';
    });
    // 去掉按钮
    clone.querySelectorAll('.toggle-btn').forEach(b=>b.remove());
    contentDiv.appendChild(clone);
  });
  wrapper.appendChild(contentDiv);

  // 水印
  const watermark=document.createElement('div');
  watermark.style.cssText='margin-top:16px;padding-top:12px;border-top:1px solid #eee;font-size:11px;color:#bbb;text-align:center';
  watermark.textContent='医疗质量指标检索系统';
  wrapper.appendChild(watermark);

  // 应用样式到 clone 内容
  const style=document.createElement('style');
  style.textContent=[
    '.sec{margin-bottom:0}',
    '.sec-label{font-size:13px;font-weight:600;color:#1a5ea8;margin-bottom:6px}',
    '.sec-content{font-size:13px;color:#333;line-height:1.8;white-space:pre-wrap;word-break:break-all}',
    '.formula-visual{background:#f8f9ff;border-radius:8px;padding:12px;margin:4px 0;font-size:14px}',
    '.formula-row{display:flex;align-items:center;gap:8px;padding:3px 0;flex-wrap:wrap}',
    '.frac{display:inline-flex;flex-direction:column;align-items:center;min-width:60px}',
    '.num-line{border-top:2px solid #1a5ea8}',
    '.frac-expr{font-size:14px;padding:2px 4px;color:#333}',
    '.frac-op{font-size:13px;color:#888;margin:0 6px}',
    '.sub-section{background:#f8fafd;border-radius:8px;padding:12px}',
    '.sub-title{font-weight:600;font-size:13px;margin-bottom:8px;color:#444}',
    '.sub-label{font-size:12px;color:#888;margin-top:6px}',
    '.sub-def,.sub-sig,.sub-notes{font-size:12px;color:#444;line-height:1.6;white-space:pre-wrap}',
    '.tag{display:inline-block;padding:3px 10px;border-radius:50px;font-size:11px;font-weight:600;margin:2px}',
    '.tag-spec{background:#e8f5e9;color:#2e7d32}',
    '.tag-tech{background:#fff3e0;color:#e65100}',
    '.tag-other{background:#f3e5f5;color:#7b1fa2}',
    '.m-tags{margin-bottom:14px}',
    '.table-wrap{overflow-x:auto;margin:4px 0}',
    '.indicator-table{width:100%;border-collapse:collapse;font-size:12px}',
    '.indicator-table th,.indicator-table td{border:1px solid #ddd;padding:5px 7px;text-align:left}',
    '.indicator-table th{background:#eaf1fb;color:#1a5ea8;font-weight:600}'
  ].join('');
  wrapper.appendChild(style);

  // 渲染
  document.body.appendChild(wrapper);
  html2canvas(wrapper,{scale:2,useCORS:true,backgroundColor:'#ffffff',logging:false}).then(canvas=>{
    document.body.removeChild(wrapper);
    canvas.toBlob(blob=>{
      if(!blob){btn.textContent='🖼 复制图片';btn.disabled=false;showToast('生成图片失败');return;}
      const item=new ClipboardItem({'image/png':blob});
      navigator.clipboard.write([item]).then(()=>{
        btn.textContent='✅ 已复制';btn.classList.add('ok');
        showToast('图片已复制到剪贴板');
        setTimeout(()=>{btn.textContent='🖼 复制图片';btn.classList.remove('ok');btn.disabled=false;},2500);
      }).catch(()=>{
        // 不支持直接复制图片，降级为下载
        const a=document.createElement('a');
        a.href=URL.createObjectURL(blob);
        a.download='指标_'+curItem.name.replace(/[\\/:*?\"<>|]/g,'_')+'.png';
        a.click();
        btn.textContent='✅ 已下载';btn.classList.add('ok');
        showToast('浏览器不支持图片复制，已自动下载');
        setTimeout(()=>{btn.textContent='🖼 复制图片';btn.classList.remove('ok');btn.disabled=false;},2500);
      });
    },'image/png');
  }).catch(err=>{
    document.body.removeChild(wrapper);
    btn.textContent='🖼 复制图片';btn.disabled=false;
    showToast('生成失败，请重试');
  });
}
"""

# 在 copyAll 函数末尾（最后一个 } 之后，showOk 之前）插入
insert_fn_point = html.find('function showOk()')
if insert_fn_point != -1:
    html = html[:insert_fn_point] + copy_image_fn + html[insert_fn_point:]

with open('medical_quality_indicators_offline.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ 修复完成！')
print('  1. 手机端搜索框不再溢出屏幕')
print('  2. 弹窗底部新增「🖼 复制图片」按钮')
print('  3. 复制图片会生成带水印的高质量 PNG')
print('  4. 移动端自动缩放为适应屏幕的宽度')
