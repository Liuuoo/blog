# 个人博客

基于 FastAPI + Markdown 的轻量级文件博客系统，不依赖数据库，支持本地文章目录、外部笔记目录、代码文件展示、分类加密，以及“未归档”虚拟目录浏览。

## 功能概览

- 纯文件驱动：直接读取 `posts/` 和外部目录中的文件
- Markdown 渲染：支持代码块、表格、任务列表、删除线、单换行
- 代码文件展示：可直接浏览 `.py`、`.cpp`、`.js` 等源码文件
- 虚拟“未归档”：目录同时包含子文件夹和直属文件时，直属文件自动归入“未归档”
- 分类加密：支持为指定分类设置访问密码
- 聚合分类：例如多个“年份日记”目录可以聚合成一个“日记”入口
- 前端单页浏览：支持分类、目录、正文、面包屑跳转

## 快速开始

### 1. 准备环境

要求：

- Python 3.10+

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 准备配置

项目默认读取根目录下的 `config.yaml`。如果没有这个文件，会回退读取 `config.example.yaml`。

第一次使用时，建议复制一份示例配置：

```bash
cp config.example.yaml config.yaml
```

Windows PowerShell：

```powershell
Copy-Item config.example.yaml config.yaml
```

然后按你的实际环境修改：

- 博客标题、副标题、作者
- `posts_dir`
- 加密分类密码
- 外部目录路径
- 媒体资源目录

### 3. 启动项目

```bash
python main.py
```

默认访问地址：

```text
http://127.0.0.1:10024
```

## 常见使用方式

### 写一篇 Markdown 文章

在 `posts/` 或其子目录里新建 `.md` 文件：

```markdown
---
title: "文章标题"
date: "2026-03-24"
summary: "首页摘要"
---

这里是正文内容。
```

支持的常用 Markdown 能力：

- 代码块
- 表格
- 任务列表
- 删除线
- 单换行转 `<br>`
- Obsidian 风格图片和链接
- KaTeX 数学公式

### 放入源码文件

你也可以直接把源码文件放进文章目录，比如：

- `.py`
- `.cpp`
- `.c`
- `.h`
- `.hpp`
- `.js`
- `.ts`
- `.go`
- `.java`
- `.html`
- `.css`
- `.json`
- `.yaml`
- `.yml`
- `.sh`

系统会自动把它们当作可浏览内容展示，并按语言高亮。

### 浏览“未归档”

如果某个目录里同时有：

- 子文件夹
- 直属文件

那么直属文件不会和文件夹混在同一级，而是自动进入一个虚拟目录“未归档”。

这只是浏览规则，不会改动你的真实磁盘结构。

### 使用加密分类

在 `config.yaml` 的 `locked_categories` 中设置分类密码，例如：

```yaml
locked_categories:
  个人心得: "123456"
  日记: "diary2025"
```

前端点击这些分类时会先要求输入密码，验证通过后才能进入。

### 使用聚合分类

如果你在 `locked_categories` 中配置了一个分类名，而外部来源里存在多个以它结尾的目录分类，系统会自动把它们聚合成一个入口。

例如：

```yaml
locked_categories:
  日记: "diary2025"

external_sources:
  - path: "C:/Users/you/DailyNote/2025"
    category: "2025年日记"
  - path: "C:/Users/you/DailyNote/2026"
    category: "2026日记"
```

这时前端会显示一个“日记”入口，而不是分散显示多个年份入口。

以后如果这些真实目录里新增：

- 新文章
- 新源码文件
- 新子文件夹

浏览页也会自动纳入，无需额外修改代码。

## 配置说明

### 示例配置

仓库内提供了 [config.example.yaml](./config.example.yaml) 作为模板。

关键字段：

- `blog`：博客标题、副标题、作者
- `posts_dir`：本地文章目录
- `admin_password`：管理密码，用于重命名分类显示名
- `category_aliases`：分类显示别名
- `locked_categories`：加密分类密码
- `external_sources`：外部目录来源
- `media_dirs`：图片/媒体搜索目录

### 外部目录配置

示例：

```yaml
external_sources:
  - path: "D:/Notes/Programming"
    category: "编程教学"
  - path: "D:/Notes/Projects"
    category: "项目文档"
```

这样外部目录会被当作博客分类来浏览。

### 媒体目录配置

如果文章中使用了 Obsidian 图片引用，可配置媒体目录：

```yaml
media_dirs:
  - "D:/Notes"
  - "D:/Assets"
```

## 目录结构

```text
blog/
├─ app/                    # 后端代码
│  ├─ routes/              # API 路由
│  ├─ config.py            # 配置读取
│  ├─ services.py          # 文章扫描、渲染、路径解析
│  ├─ models.py            # 数据模型
│  └─ state.py             # 运行时状态
├─ posts/                  # 本地文章目录
├─ tests/                  # 回归测试
├─ web/                    # 前端静态资源
├─ main.py                 # 启动入口
├─ config.example.yaml     # 示例配置
├─ config.yaml             # 本地私有配置，不建议提交
└─ requirements.txt
```

## 开发与测试

运行测试：

```bash
python -m unittest discover -s tests -v
```

前端脚本检查：

```bash
node --check web/js/app.js
```

## 部署建议

### Windows

可以直接运行：

```bash
python main.py
```

或者双击 `start_blog.bat`。

### Linux 服务器

推荐：

- `uvicorn` + `systemd`
- `nginx` 反向代理
- `certbot` 配置 HTTPS

## API 简表

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/config` | 获取博客基础配置 |
| `GET` | `/api/stats` | 获取统计信息 |
| `GET` | `/api/categories` | 获取分类列表 |
| `GET` | `/api/browse?path=` | 浏览目录 |
| `GET` | `/api/posts?category=` | 获取文章列表 |
| `GET` | `/api/posts/{slug}` | 获取文章正文或源码内容 |
| `POST` | `/api/verify-password` | 验证分类密码 |
| `POST` | `/api/admin/rename-category` | 修改分类显示名 |

## 发布到 GitHub 前的建议

- 不要提交真实的 `config.yaml`
- 不要提交本机绝对路径和私人密码
- 如果需要公开仓库，优先提交 `config.example.yaml`
- 提交前确认 `posts/` 中没有不希望公开的内容
