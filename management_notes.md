# management.html 无法重建说明

## 原因

`management.html` 是独立的 HTML 文件，不是由 `build_html.py` 生成的。
它直接读取 `indicators_clean.json` 进行数据管理和编辑。

## 正确使用方法

### 方式一：本地使用（推荐，无需网络）

1. 把 `management.html` 和 `indicators_clean.json` **放在同一个文件夹**
2. 用浏览器直接打开 `management.html`
3. 所有修改保存在浏览器本地（localStorage），换电脑会丢失

---

### 方式二：配合 GitHub Pages 使用

需要同时上传两个文件到 GitHub：

1. `indicators_clean.json`（数据文件）
2. `management.html`（编辑器页面）

**注意**：修改只能保存在**你自己的浏览器**里，不能同步到 GitHub。

---

### 方式三：彻底解决 — 使用 Gist API

把 GitHub Gist 作为数据存储，实现真正的在线编辑和保存。

需要我帮你实现吗？（需要 GitHub Personal Access Token）

---

## 当前优先修复顺序

1. **先**：上传最新 `medical_quality_indicators_offline.html` 到 GitHub（修复 notes/code 显示问题）
2. **再**：上传 `indicators_clean.json` + `management.html` 到 GitHub（启用在线编辑预览）
3. **可选**：实现 Gist 在线存储
