# 内容创作者助手

一个自动化的内容创作辅助工具，帮助快速生成标题、钩子、制作封面并发布到小红书等平台。

## 功能概述

1. **AI 内容生成** - 根据素材和技巧自动生成标题、钩子
2. **封面生成** - 自动添加蒙版、裁剪图片、文字编辑
3. **发布完善** - 搭配爱贝壳完善发布流程
4. **广告推广** - 在评论区发布广告

## 技术栈

### 后端
- Python + Flask
- Google Gemini API (AI 内容生成)
- 图像处理 (Pillow)

### 前端
- HTML5 + CSS3 + JavaScript
- Fabric.js (画布编辑)
- 响应式设计

## 项目结构

```
contentCreatorHelper/
├── backend/                    # 后端代码
│   ├── app.py                 # Flask 应用入口
│   ├── controllers/           # 控制器
│   │   ├── content_gen_controller.py
│   │   ├── cover_gen_controller.py
│   │   ├── publish_controller.py
│   │   └── clean_controller.py
│   └── service/               # 服务层
│       ├── content/           # 内容生成服务
│       ├── cover/             # 封面生成服务
│       ├── publish/           # 发布服务
│       └── clean/             # 清理服务
├── frontend/                  # 前端代码
│   ├── html/                  # HTML 页面
│   │   ├── index.html         # 首页
│   │   ├── content-generation.html
│   │   ├── cover-generator.html
│   │   ├── text-edit-subpage.html
│   │   └── publish.html
│   ├── css/                   # 样式文件
│   │   └── style.css
│   ├── js/                    # JavaScript 文件
│   │   ├── content-gen.js
│   │   ├── cover-generator.js
│   │   ├── text-edit-subpage.js
│   │   └── publish.js
│   └── fonts/                 # 字体文件
│       └── XinQingNian.otf
└── data/                      # 数据目录
    ├── material/              # 素材文件
    ├── tip/                   # 技巧文件
    ├── coverGeneration/       # 封面生成相关
    └── publish/               # 发布相关数据
```

## 功能说明

### 1. 内容生成 (Content Generation)

根据素材内容和标题/钩子创作技巧，使用 AI 自动生成吸引人的标题和开头钩子。

**支持领域：**
- 程序员
- 技术
- 赚钱

**功能特性：**
- 读取素材文件 (`material.txt`)
- 读取标题技巧 (`tip/title.txt`)
- 读取钩子技巧 (`tip/hook.txt`)
- AI 自动生成 3-5 个标题和钩子
- 支持文案优化（有情绪、有画面、有代入感）

### 2. 封面生成 (Cover Generation)

完整的封面制作流程，支持蒙版、裁剪、文字编辑。

**流程：**
1. **蒙版** - 为图片添加透明蒙版
2. **文字编辑** - 在画布上编辑文字，支持自定义字体
3. **裁剪** - 同时裁剪为 3:4 和 3:2 两种比例

**文字编辑特性：**
- 多图画布同时编辑
- 双击画布添加文字
- 键盘 Delete 删除选中文字
- 支持字体大小、颜色、描边调整
- 使用 XinQingNian 自定义字体
- 批量保存功能

### 3. 发布完善 (Publishing Enhancement)

- 按日期管理素材
- 集成爱贝壳发布平台
- 一键填充标题、视频、封面

### 4. 清理功能 (Cleaning)

一键清理数据目录：
- 清空 `data/material` 目录
- 清空 `data/tip` 目录
- 清理前需要二次确认

## 环境配置

### 前置要求
- Python 3.8+
- Node.js (可选，用于前端开发)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd contentCreatorHelper
   ```

2. **安装 Python 依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**

   创建 `.env` 文件在项目根目录：
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **准备数据文件**

   - 将素材内容放入 `data/material/material.txt`
   - 将标题技巧放入 `data/tip/title.txt`
   - 将钩子技巧放入 `data/tip/hook.txt`

5. **运行后端**
   ```bash
   cd backend
   python app.py
   ```

6. **访问前端**

   在浏览器中打开 `frontend/html/index.html`

## API 接口

### 内容生成
- `POST /api/generate` - 生成标题和钩子
- `POST /api/optimize_content` - 优化文案

### 封面生成
- `GET /api/mask_images` - 获取蒙版图片列表
- `POST /api/add_mask` - 添加蒙版
- `GET /api/get_text_edit_images` - 获取文字编辑图片列表
- `POST /api/save_edited_image` - 保存编辑后的图片
- `GET /api/get_cropped_images` - 获取裁剪图片列表
- `POST /api/crop_images` - 裁剪图片

### 发布
- `GET /api/publish/folders` - 获取日期文件夹
- `POST /api/publish/save` - 保存发布内容

### 清理
- `POST /api/clean` - 清理数据目录

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 许可证

MIT License
