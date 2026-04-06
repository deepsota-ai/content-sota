# 美业门店小红书内容助手

一个面向美业门店（美甲/精油推背/纹眉/轻医美）的小红书内容自动化工具，帮助快速生成标题、钩子文案、制作封面并发布到小红书。

## 功能概述

1. **AI 内容生成** — 根据门店素材自动生成小红书爆款标题和钩子
2. **文案优化** — 将原始素材改写为有情绪、有画面感的种草文案
3. **封面生成** — 自动添加蒙版、Canvas 文字编辑、裁剪为小红书比例
4. **发布完善** — 搭配爱贝壳插件完成视频+封面+文案一键填充发布

## 技术栈

- **后端**：Python + Flask、Google Gemini API（AI 内容生成）、Pillow（图像处理）、DrissionPage（Chrome 自动化）
- **前端**：HTML5 + CSS3 + JavaScript、Canvas API（封面编辑）

## 项目结构

```
ContentCreatorHelper/
├── app.py                        # Flask 应用入口（端口 5001）
├── .env                          # 环境变量（不提交到 Git）
├── requirements.txt
├── backend/
│   ├── controller/               # API 路由控制层
│   │   ├── content/
│   │   ├── cover/
│   │   ├── publish/
│   │   ├── load/
│   │   └── clean/
│   └── service/                  # 业务逻辑层
│       ├── content/content_generate.py   # Gemini AI 生成
│       ├── cover/                         # 蒙版、裁剪、文字
│       └── publish/ibeike_extension.py    # Chrome 自动化发布
├── frontend/
│   ├── html/
│   │   ├── index.html
│   │   └── subpages/             # 各功能子页面
│   ├── js/
│   ├── css/
│   └── fonts/
└── data/
    ├── contentGeneration/
    │   ├── material.txt          # 门店素材（用 # 分隔各素材块）
    │   └── tip/
    │       ├── title.txt         # 标题创作技巧
    │       └── hook.txt          # 钩子创作技巧
    ├── coverGeneration/
    │   ├── toPs/                 # 放入原始图片
    │   ├── cover/mask/           # 加蒙版后输出
    │   └── cover/crop/           # 裁剪后输出
    └── publish/
        └── {YYYY.M.D}/           # 按日期组织的发布素材
            └── 素材_{n}/
                ├── 1.txt         # title: xxx\ndesc: xxx
                ├── 1.jpg         # 封面图
                └── video.MOV     # 视频文件
```

## 环境配置

### 前置要求

- Python 3.8+
- Google Chrome（用于自动化发布）
- 爱贝壳 Chrome 插件（用于小红书发布）

### 安装步骤

**1. 克隆项目并安装依赖**

```bash
git clone <repository-url>
cd ContentCreatorHelper
pip install -r requirements.txt
```

**2. 配置 Gemini API Key**

在项目根目录创建 `.env` 文件：

```
GEMINI_API_KEY=your_gemini_api_key_here
```

获取 API Key：访问 [Google AI Studio](https://aistudio.google.com)，免费注册后在「Get API key」处创建。

**3. 准备素材文件**

编辑 `data/contentGeneration/material.txt`，用 `#` 开头的行作为每块素材的标题分隔：

```
# 美甲-奶油色推荐

这里写关于这款美甲的卖点、顾客反馈、使用场景等...

# 精油推背-肩颈放松

这里写关于精油推背项目的介绍、效果、适合人群...
```

**4. 启动服务**

```bash
python app.py
```

浏览器访问：`http://localhost:5001`

---

## 自动发布配置

发布功能通过 **爱贝壳 Chrome 插件 + DrissionPage** 实现自动化，需要以下配置。

### 第一步：安装爱贝壳插件

在 Chrome 应用商店搜索并安装「爱贝壳」发布插件，安装后记录插件 ID（在 `chrome://extensions` 页面开启开发者模式后可见）。

默认插件 ID：`jejejajkcbhejfiocemmddgbkdlhhngm`

如果你安装的版本 ID 不同，修改 `backend/service/publish/ibeike_extension.py` 第 9 行：

```python
target_extension_id = "你的插件ID"
```

### 第二步：配置 Chrome 路径

修改 `backend/service/publish/ibeike_extension.py` 第 7-8 行：

```python
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Chrome 安装路径
user_data_dir = r"D:\Users\ChromeAutomationProfile"                      # 自动化专用用户目录（可自定义路径）
```

`user_data_dir` 是自动化专用的独立 Chrome 用户目录，与你日常使用的 Chrome 互不干扰。

### 第三步：首次登录小红书

第一次使用时需要手动登录，之后自动记住登录态：

1. 在发布页面点击「启动 Chrome」按钮
2. 在自动打开的 Chrome 窗口中手动登录小红书创作者后台（creator.xiaohongshu.com）
3. 登录成功后关闭窗口，之后每次发布会自动使用此账号

### 发布素材格式

每次发布前，需在 `data/publish/{日期}/素材_{n}/` 目录下准备：

| 文件 | 说明 |
|------|------|
| `1.txt` | 内容文案，格式见下方 |
| `1.jpg` | 封面图（由封面生成功能自动保存） |
| `video.MOV` | 视频文件（支持 `.MOV` / `.mov`） |

`1.txt` 格式：

```
title: 你的小红书标题
desc: 正文内容，支持换行和 emoji
```

---

## 使用流程

```
准备素材 → 内容生成 → 封面制作 → 发布
```

### 内容生成

1. 编辑 `data/contentGeneration/material.txt` 填入门店素材
2. 打开内容生成页，选择 Gemini 模型（支持实时拉取最新模型列表）
3. 点击「生成标题」或「生成钩子」，AI 自动批量处理每块素材
4. 在筛选区挑选满意的标题和文案，点击「整理」保存到发布目录

### 封面生成

1. 将原始图片放入 `data/coverGeneration/toPs/`
2. **蒙版**：点击生成半透明遮罩，让文字更清晰
3. **文字编辑**：双击画布添加文字，支持自定义字体/大小/颜色/描边，批量保存
4. **裁剪**：自动裁剪为 3:4（竖版）和 3:2（横版）两种比例

### 发布

1. 确认发布目录中有 `1.txt`、`1.jpg`、视频文件
2. 点击「发布」，工具自动填充标题、描述、封面，等待确认后提交

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 从 Gemini API 获取可用模型列表 |
| GET | `/api/load-material` | 加载并分块素材文件 |
| POST | `/api/generate-content` | 生成标题 / 钩子 / 优化文案 |
| GET | `/api/get_to_ps_images` | 获取待处理图片列表 |
| POST | `/api/generate-mask-cover` | 添加蒙版 |
| POST | `/api/generate-cropped-image` | 裁剪图片 |
| POST | `/api/save-edited-image` | 保存 Canvas 编辑后的图片 |
| GET | `/api/publish/folders` | 获取发布文件夹列表 |
| POST | `/api/organize-content` | 整理内容到发布目录 |
| POST | `/api/publish/<folder>` | 执行自动发布 |
| POST | `/api/publish/xhs_perfect/<folder>` | 小红书封面自动完善 |
| POST | `/api/clean-data` | 清理生成目录 |

---

## 浏览器兼容性

Chrome 90+ / Firefox 88+ / Edge 90+

## 许可证

MIT License
