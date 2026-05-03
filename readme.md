# 美业门店小红书内容助手

[![CI](https://github.com/deepsota-ai/content-sota/actions/workflows/ci.yml/badge.svg)](https://github.com/deepsota-ai/content-sota/actions/workflows/ci.yml)

一个面向美业门店（美甲 / 精油推背 / 纹眉 / 面部轻医美）的小红书内容自动化工具，帮助快速生成标题、钩子文案、制作封面并发布到小红书。支持**本地单机运行**和**腾讯云 Docker 云端部署**两种模式。

---

## 功能概述

| 模块 | 说明 |
|------|------|
| **单篇创作向导** | 一句话描述需求 → 向导式生成草稿 → 选标题 → 选钩子 → 封面编辑 → 配图 → 保存 |
| **批量处理** | 基于 `material.txt` 素材，分步批量生成优化文案、钩子和标题，整理后引导到下一步 |
| **封面生成** | 蒙版叠加、Canvas 文字编辑（字号/颜色/位置）、裁剪比例（1:1 / 3:4 / 4:3） |
| **发布管理** | 预览并微调标题/正文，一键发布（图文 & 视频自动识别），支持多账号切换 |
| **账号管理** | 配置多个小红书账号（本地 Chrome Profile 或云端 Cookie），发布时按需选择 |

---

## 技术栈

- **后端**：Python + Flask、Google Gemini API、Pillow、DrissionPage、cryptography
- **前端**：HTML5 + CSS3 + Vanilla JS、Canvas API
- **发布自动化**：Chrome + 爱贝壳插件 + DrissionPage（本地 subprocess / 云端 Xvfb）
- **测试**：pytest + pytest-cov（59 个单元测试）
- **CI**：GitHub Actions（Python 3.11 / 3.12）
- **部署**：Docker + docker-compose（腾讯云 CVM）

---

## 项目结构

```
ContentCreatorHelper/
├── app.py                          # Flask 入口（端口 5001）
├── .env                            # 环境变量（不提交 Git）
├── requirements.txt
├── Dockerfile                      # 云端部署镜像
├── docker-compose.yml              # 腾讯云一键启动
├── .github/workflows/ci.yml        # GitHub Actions CI
├── tests/
│   ├── test_account_controller.py  # AccountController 单元测试
│   ├── test_publish_controller.py
│   ├── test_content_generate.py
│   └── test_app_routes.py
├── backend/
│   ├── controller/
│   │   ├── account/                # 账号 CRUD + QR 登录
│   │   ├── content/
│   │   ├── cover/
│   │   ├── publish/
│   │   ├── load/
│   │   └── clean/
│   └── service/
│       ├── content/content_generate.py   # Gemini AI 生成
│       ├── cover/                         # 蒙版、裁剪
│       └── publish/ibeike_extension.py    # Chrome 自动化（本地/云端双模式）
├── extensions/
│   └── ibeike/                     # 爱贝壳插件（云端部署前需手动填入）
├── frontend/
│   ├── html/
│   │   ├── index.html
│   │   ├── accounts-page.html      # 账号管理页
│   │   ├── content-generator.html  # 单篇/批量入口
│   │   ├── publish-page.html       # 发布管理（含账号选择器）
│   │   └── subpages/
│   │       ├── single-post.html    # 单篇创作向导（6步）
│   │       ├── title-subpage.html
│   │       ├── hook-subpage.html
│   │       └── content-subpage.html
│   ├── js/
│   └── css/
└── data/
    ├── accounts.json               # 账号配置（自动生成，cookies 加密存储）
    ├── contentGeneration/
    │   ├── material.txt            # 门店素材（# 分隔）
    │   └── tip/
    │       ├── title.txt           # 标题创作技巧
    │       ├── hook.txt            # 钩子创作技巧
    │       ├── content.txt         # 正文草稿指引
    │       ├── hashtag.txt         # 固定标签（发布时自动追加）
    │       └── emoji.txt           # 小红书专属 emoji 列表
    ├── coverGeneration/
    │   ├── toPs/                   # 放入原始图片
    │   ├── cover/mask/             # 加蒙版后输出
    │   └── cover/crop/             # 裁剪后输出
    └── publish/
        └── {YYYY.M.D}/
            └── 素材_{n}/
                ├── 1.txt           # title: xxx\ndesc: xxx
                ├── 1.jpg           # 封面（图文首图 / 视频封面）
                ├── 2.jpg, 3.jpg…   # 配图（图文帖可选）
                └── video.MOV       # 视频文件（视频帖可选）
```

---

## 快速开始（本地模式）

### 前置要求

- Python 3.11+
- Google Chrome
- 爱贝壳 Chrome 插件

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
CHROME_USER_DATA_DIR=C:\Users\<你的用户名>\ChromeAutomationProfile
IBEIKE_EXTENSION_ID=jejejajkcbhejfiocemmddgbkdlhhngm
```

获取 Gemini API Key：[Google AI Studio](https://aistudio.google.com) → Get API key（免费）

### 启动

```bash
python app.py
```

浏览器访问：`http://localhost:5001`

---

## 云端部署（腾讯云 Docker）

### 前置准备：打包爱贝壳插件

插件需在构建镜像前手动复制一次，之后自动打包进镜像：

```
1. 在本机 Chrome 中打开：chrome://extensions/
2. 找到爱贝壳插件，记录其 ID（默认：jejejajkcbhejfiocemmddgbkdlhhngm）
3. 复制以下目录中的所有文件：
   %LOCALAPPDATA%\Google\Chrome\User Data\Default\Extensions\<插件ID>\<版本号>\
4. 粘贴到项目的 extensions/ibeike/ 目录下
5. 确认 extensions/ibeike/manifest.json 存在
```

### 部署步骤

在腾讯云 CVM（Ubuntu）上执行：

```bash
# 克隆项目
git clone git@github.com:deepsota-ai/content-sota.git
cd content-sota

# 创建环境变量文件
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
ACCOUNT_ENCRYPT_KEY=your_random_secret_here
EOF

# 构建并启动（首次构建约需 5 分钟）
docker compose up -d

# 查看日志
docker compose logs -f
```

访问：`http://<腾讯云公网IP>:5001`

> **注意**：如需公网 HTTPS 访问，在腾讯云控制台为 CVM 绑定域名并配置 Nginx 反向代理 + SSL 证书。

### 本地 vs 云端行为对比

| 功能 | 本地模式（`DEPLOY_MODE=local`） | 云端模式（`DEPLOY_MODE=cloud`） |
|------|-------------------------------|-------------------------------|
| Chrome 启动 | subprocess 直接启动 | Xvfb 虚拟显示 + subprocess |
| 小红书登录 | 手动在 Chrome 中登录一次 | 扫码登录 → Cookie 加密存储 |
| 发布流程 | 同步阻塞（等待发布完成） | 异步任务（立即返回 job_id，前端轮询状态） |
| 多账号 | Chrome Profile 目录切换 | Cookie 注入切换 |

---

## 账号管理

### 本地模式：多 Chrome Profile

每个小红书账号对应一个独立的 Chrome 用户数据目录：

1. 首页 → **账号管理** → 添加账号
2. 填写账号名称和 Chrome Profile 路径（留空则使用 `.env` 中的默认目录）
3. 在对应 Profile 的 Chrome 中完成小红书登录
4. 发布时在发布管理页顶部的下拉框选择对应账号

### 云端模式：扫码登录

1. 首页 → **账号管理** → 添加账号 → 选择「云端扫码」
2. 填写账号名称 → 点击「获取二维码」
3. 服务器启动 Chrome，页面显示小红书登录二维码
4. 用手机小红书 App 扫码确认
5. 登录成功后，Cookie 自动加密存入 `data/accounts.json`，无需重复登录（有效期约 30-90 天）

---

## 使用流程

### 单篇创作（推荐）

1. 首页 → **内容生成** → **单篇创作**
2. 输入一句话需求（如"为新款卡其色美甲写一篇文案"）→ 生成草稿
3. 点击草稿 → 自动生成标题和钩子选项，点选确认
4. 上传封面图 → 可裁剪比例、叠蒙版、添加文字 → 保存
5. 上传配图（可选）→ 保存发布目录 → 前往发布管理

### 批量处理

1. 编辑 `data/contentGeneration/material.txt`（`#` 开头行为分隔符）
2. 首页 → **内容生成** → **批量处理** → 依次执行：优化文案 → 钩子 → 标题
3. 每步整理完成后，自动出现「→ 下一步」引导按钮
4. 前往发布管理完成发布

### 发布管理

1. 进入发布管理，顶部下拉选择发布账号（无账号配置时使用默认）
2. 选择日期 → 选择素材文件夹
3. 右侧面板预览标题和正文，可直接修改并点击**保存修改**
4. 点击**发布**（图文/视频自动识别）或**小红书完善**（自动上传封面）

---

## 发布模式自动识别

| 素材文件夹内容 | 识别结果 |
|--------------|--------|
| 含 `.MOV` / `.mov` | 视频帖发布模式 |
| 仅含图片（`.jpg`）| 图文帖发布模式 |

两种模式均需要 `1.txt`（标题 + 正文）和 `1.jpg`（封面 / 首图）。

---

## 小红书完善功能

「小红书完善」用于在小红书草稿页面自动上传封面图，使用前需满足：

- Chrome 已在 9223 端口运行（由发布按钮自动触发）
- 小红书创作者中心已打开且处于发布编辑状态

---

## 内容配置文件

| 文件 | 说明 | 可自定义 |
|------|------|---------|
| `data/contentGeneration/material.txt` | 门店素材，`#` 开头行为分隔符 | ✅ |
| `data/contentGeneration/tip/title.txt` | 标题创作技巧（供 AI 参考） | ✅ |
| `data/contentGeneration/tip/hook.txt` | 钩子创作技巧（供 AI 参考） | ✅ |
| `data/contentGeneration/tip/content.txt` | 正文草稿生成指引 | ✅ |
| `data/contentGeneration/tip/hashtag.txt` | 固定标签，发布时自动追加到正文末尾 | ✅ |
| `data/contentGeneration/tip/emoji.txt` | 小红书专属 `[XXX]` 格式 emoji，AI 生成时优先使用 | ✅ |

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 获取可用 Gemini 模型列表 |
| GET | `/api/hashtags` | 读取 hashtag.txt |
| GET | `/api/load-material` | 加载并分块素材文件 |
| POST | `/api/generate-drafts` | 根据需求生成正文草稿 |
| POST | `/api/generate-content` | 批量生成标题 / 钩子 / 优化文案 |
| POST | `/api/generate-mask-cover` | 添加蒙版 |
| POST | `/api/generate-cropped-image` | 裁剪图片 |
| POST | `/api/save-edited-image` | 保存 Canvas 编辑后的图片 |
| POST | `/api/organize-content` | 整理内容到发布目录 |
| GET/POST | `/api/publish/content` | 读取 / 更新素材 1.txt |
| GET | `/api/publish/folders` | 获取发布文件夹列表 |
| POST | `/api/publish/<folder>` | 执行自动发布（body 可含 `account_id`） |
| GET | `/api/publish/status/<job_id>` | 查询异步发布任务状态（云端模式） |
| POST | `/api/publish/xhs_perfect/<folder>` | 小红书封面自动完善 |
| GET | `/api/accounts` | 获取账号列表 |
| POST | `/api/accounts` | 添加本地账号（name + profile_dir） |
| DELETE | `/api/accounts/<id>` | 删除账号 |
| POST | `/api/accounts/start-qr` | 云端：启动扫码登录，返回二维码图片 |
| GET | `/api/accounts/qr-status` | 云端：轮询扫码登录状态 |
| POST | `/api/clean-data` | 清理生成目录 |

---

## 开发 & 测试

```bash
# 运行全部测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=backend --cov-report=term-missing
```

测试覆盖（59 个测试）：

| 测试文件 | 覆盖内容 |
|---------|---------|
| `test_account_controller.py` | 加密/解密、账号增删查、Cookie 不泄露验证 |
| `test_publish_controller.py` | 读取/更新内容、发布模式自动判断（图文/视频） |
| `test_content_generate.py` | JSON 解析、emoji 加载、AI mock、草稿生成 |
| `test_app_routes.py` | 所有 Flask 路由（账号管理、发布、任务状态等） |

---

## 浏览器兼容性

Chrome 90+ / Firefox 88+ / Edge 90+

## 许可证

MIT License
