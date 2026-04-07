# 美业门店小红书内容助手

[![CI](https://github.com/deepsota-ai/content-sota/actions/workflows/ci.yml/badge.svg)](https://github.com/deepsota-ai/content-sota/actions/workflows/ci.yml)

一个面向美业门店（美甲 / 精油推背 / 纹眉 / 面部轻医美）的小红书内容自动化工具，帮助快速生成标题、钩子文案、制作封面并发布到小红书。

---

## 功能概述

| 模块 | 说明 |
|------|------|
| **单篇创作向导** | 一句话描述需求 → 向导式生成草稿 → 选标题 → 选钩子 → 封面编辑 → 配图 → 保存 |
| **批量处理** | 基于 `material.txt` 素材文件，分步批量生成优化文案、钩子和标题，整理后引导到下一步 |
| **封面生成** | 蒙版叠加、Canvas 文字编辑（字号/颜色/位置）、裁剪比例（1:1 / 3:4 / 4:3） |
| **发布管理** | 预览并微调每条素材的标题/正文，一键发布（图文 & 视频），搭配爱贝壳插件自动填充 |

---

## 技术栈

- **后端**：Python + Flask、Google Gemini API、Pillow、DrissionPage
- **前端**：HTML5 + CSS3 + Vanilla JS、Canvas API
- **测试**：pytest + pytest-cov
- **CI**：GitHub Actions（Python 3.10 / 3.11 / 3.12）

---

## 项目结构

```
ContentCreatorHelper/
├── app.py                          # Flask 入口（端口 5001）
├── .env                            # 环境变量（不提交 Git）
├── requirements.txt
├── .github/workflows/ci.yml        # GitHub Actions CI
├── tests/                          # 单元测试
│   ├── test_publish_controller.py
│   ├── test_content_generate.py
│   └── test_app_routes.py
├── backend/
│   ├── controller/
│   │   ├── content/
│   │   ├── cover/
│   │   ├── publish/
│   │   ├── load/
│   │   └── clean/
│   └── service/
│       ├── content/content_generate.py   # Gemini AI 生成
│       ├── cover/                         # 蒙版、裁剪
│       └── publish/ibeike_extension.py    # Chrome 自动化
├── frontend/
│   ├── html/
│   │   ├── index.html
│   │   ├── content-generator.html         # 单篇/批量入口
│   │   ├── publish-page.html
│   │   └── subpages/
│   │       ├── single-post.html           # 单篇创作向导（6步）
│   │       ├── title-subpage.html
│   │       ├── hook-subpage.html
│   │       └── content-subpage.html
│   ├── js/
│   └── css/
└── data/
    ├── contentGeneration/
    │   ├── material.txt                   # 门店素材（# 分隔）
    │   └── tip/
    │       ├── title.txt                  # 标题创作技巧
    │       ├── hook.txt                   # 钩子创作技巧
    │       ├── content.txt                # 正文草稿指引
    │       ├── hashtag.txt                # 固定标签（发布时自动追加）
    │       └── emoji.txt                  # 小红书专属 emoji 列表
    ├── coverGeneration/
    │   ├── toPs/                          # 放入原始图片
    │   ├── cover/mask/                    # 加蒙版后输出
    │   └── cover/crop/                    # 裁剪后输出
    └── publish/
        └── {YYYY.M.D}/
            └── 素材_{n}/
                ├── 1.txt                  # title: xxx\ndesc: xxx
                ├── 1.jpg                  # 封面（图文 / 视频封面）
                ├── 2.jpg, 3.jpg…          # 配图（图文帖可选）
                └── video.MOV              # 视频文件（视频帖可选）
```

---

## 快速开始

### 前置要求

- Python 3.10+
- Google Chrome（自动发布功能需要）
- 爱贝壳 Chrome 插件（小红书发布自动化需要）

### 安装

```bash
git clone git@github.com:deepsota-ai/content-sota.git
cd content-sota
pip install -r requirements.txt
```

### 配置环境变量

在项目根目录创建 `.env`：

```env
# 必填
GEMINI_API_KEY=your_gemini_api_key_here

# 自动发布（可选，有默认值）
CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
CHROME_USER_DATA_DIR=D:\Users\ChromeAutomationProfile
IBEIKE_EXTENSION_ID=jejejajkcbhejfiocemmddgbkdlhhngm
```

获取 Gemini API Key：[Google AI Studio](https://aistudio.google.com) → Get API key（免费）

### 启动

```bash
python app.py
```

浏览器访问：`http://localhost:5001`

---

## 使用流程

### 单篇创作（推荐）

1. 内容生成 → **单篇创作**
2. 输入一句话需求（如"为新款卡其色美甲写一篇文案"）→ 生成草稿
3. 点击草稿 → 自动生成标题和钩子选项，点选确认
4. 上传封面图 → 可裁剪比例、叠蒙版、添加文字 → 保存
5. 上传配图（可选）→ 保存发布目录

### 批量处理

1. 编辑 `data/contentGeneration/material.txt`（`#` 开头分隔每块素材）
2. 内容生成 → **批量处理** → 依次执行：优化文案 → 钩子 → 标题
3. 每步整理完成后，自动出现「→ 下一步」引导按钮
4. 前往发布管理完成发布

### 发布管理

1. 进入发布管理，选择日期 → 选择素材文件夹
2. **预览编辑**：右侧面板预览标题和正文，可直接修改并保存（覆盖 `1.txt`）
3. 点击**发布**（图文或视频自动识别）或**小红书完善**（见下方说明）

---

## 自动发布配置

发布功能通过 **爱贝壳 Chrome 插件 + DrissionPage** 实现，需以下准备：

### 发布类型自动识别

| 素材文件夹内容 | 识别结果 |
|--------------|--------|
| 含 `.MOV` / `.mov` | 视频帖发布模式 |
| 仅含图片（`.jpg`）| 图文帖发布模式 |

两种模式均需要 `1.txt`（标题 + 正文）和 `1.jpg`（封面 / 首图）。

### 配置爱贝壳插件

1. 在 Chrome 应用商店安装「爱贝壳」发布插件
2. 前往 `chrome://extensions`，开启开发者模式，记录插件 ID
3. 在 `.env` 中填写 `IBEIKE_EXTENSION_ID`（默认值：`jejejajkcbhejfiocemmddgbkdlhhngm`）

### 首次登录小红书

```
1. 点击发布页「发布」按钮，工具会自动以专用用户目录启动 Chrome
2. 在弹出的 Chrome 中手动登录 creator.xiaohongshu.com
3. 后续发布自动复用登录状态，无需重新登录
```

### 小红书完善功能

「小红书完善」用于在小红书草稿页面自动上传封面图，使用前需满足：
- Chrome 已在 9223 端口运行（由工具自动启动）
- 小红书创作者中心页面已打开且处于发布编辑状态

---

## 内容配置文件

| 文件 | 说明 | 可自定义 |
|------|------|---------|
| `data/contentGeneration/material.txt` | 门店素材，`#` 开头行为分隔符 | ✅ |
| `data/contentGeneration/tip/title.txt` | 标题创作技巧（供 AI 参考） | ✅ |
| `data/contentGeneration/tip/hook.txt` | 钩子创作技巧（供 AI 参考） | ✅ |
| `data/contentGeneration/tip/content.txt` | 正文草稿生成指引 | ✅ |
| `data/contentGeneration/tip/hashtag.txt` | 固定标签，发布时自动追加到正文末尾 | ✅ |
| `data/contentGeneration/tip/emoji.txt` | 小红书专属 `[XXX]` 格式 emoji 列表，AI 生成时优先使用 | ✅ |

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 获取可用 Gemini 模型列表 |
| GET | `/api/hashtags` | 读取 hashtag.txt 内容 |
| GET | `/api/load-material` | 加载并分块素材文件 |
| POST | `/api/generate-drafts` | 根据一句话需求生成正文草稿 |
| POST | `/api/generate-content` | 批量生成标题 / 钩子 / 优化文案 |
| POST | `/api/generate-mask-cover` | 添加蒙版 |
| POST | `/api/generate-cropped-image` | 裁剪图片 |
| POST | `/api/save-edited-image` | 保存 Canvas 编辑后的图片 |
| POST | `/api/organize-content` | 整理内容到发布目录 |
| GET/POST | `/api/publish/content` | 读取 / 更新素材 1.txt |
| GET | `/api/publish/folders` | 获取发布文件夹列表 |
| POST | `/api/publish/<folder>` | 执行自动发布（图文或视频） |
| POST | `/api/publish/xhs_perfect/<folder>` | 小红书封面自动完善 |
| POST | `/api/clean-data` | 清理生成目录 |

---

## 开发 & 测试

```bash
# 运行全部测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=backend --cov-report=term-missing
```

测试覆盖：
- `PublishController`：读取/更新内容、发布模式判断（图文/视频自动识别）
- `ContentCreatorService`：JSON 解析、emoji 加载、API mock、草稿生成
- Flask 路由：hashtags、publish/content、generate-drafts、models

---

## 浏览器兼容性

Chrome 90+ / Firefox 88+ / Edge 90+

## 许可证

MIT License
