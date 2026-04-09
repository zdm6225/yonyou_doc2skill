# Yonyou Doc2Skill 支持来源与抓取原理

本文用于说明 Yonyou Doc2Skill 当前对外支持的主要来源类型、各自的抽取原理，以及适合对外介绍时使用的简化说法。

## 总体原理

Yonyou Doc2Skill 整体分为两层：

- 入口层：判断用户给的来源类型，并路由到对应 converter
- 抽取层：针对不同来源执行内容抽取，先生成结构化中间数据，再生成 `SKILL.md`、`references/` 等产物

核心入口在：

- `src/yonyou_doc2skill/cli/source_detector.py`
- `src/yonyou_doc2skill/cli/create_command.py`

## 当前对外支持的来源

- 公开文档网站
- GitHub 仓库
- 本地代码库
- PDF
- Word `.docx`
- 本地 HTML
- AsciiDoc
- PowerPoint `.pptx`
- 视频链接 / 本地视频
- Confluence
- Slack / Discord chat 导出

说明：

- `epub / jupyter / openapi / rss / manpage / notion` 等旧能力源码仍有部分保留，但当前不作为公开主路径

## 各来源抓取原理

### 1. 公开文档网站

核心实现：

- `src/yonyou_doc2skill/cli/doc_scraper.py`
- `src/yonyou_doc2skill/cli/llms_txt_detector.py`
- `src/yonyou_doc2skill/cli/llms_txt_downloader.py`
- `src/yonyou_doc2skill/cli/browser_renderer.py`

抓取方式：

1. 优先检测站点是否提供 `llms.txt`
2. 如果存在 `llms.txt`，优先按它给出的 URL 列表抓取
3. 如果没有 `llms.txt`，就直接请求网页 HTML
4. 用 `BeautifulSoup` 提取正文区域、标题、heading、代码块、链接
5. 递归发现站内文档链接并继续抓取
6. 对 JS/SPA 站点可启用浏览器渲染后再抓

对外简化说法：

- 优先利用 `llms.txt` 等 AI 友好入口
- 没有时自动解析网页正文并抓取站内文档结构

### 2. GitHub 仓库

核心实现：

- `src/yonyou_doc2skill/cli/github_scraper.py`
- `src/yonyou_doc2skill/cli/github_fetcher.py`
- `src/yonyou_doc2skill/cli/codebase_scraper.py`

抓取方式：

1. 通过 GitHub API 获取仓库元数据、README、issues、releases
2. 通过 clone 或本地仓库路径获取真实代码内容
3. 对源码做结构分析，提取函数、类、接口、注释、测试样例、依赖关系
4. 合并“文档视角”和“代码视角”形成技能资产

对外简化说法：

- 不只是抓 README，而是同时理解仓库文档、代码结构和真实使用问题

### 3. 本地代码库

核心实现：

- `src/yonyou_doc2skill/cli/codebase_scraper.py`

抓取方式：

1. 遍历本地目录
2. 过滤 `.git`、`node_modules`、构建产物等无关目录
3. 根据语言后缀识别源码类型
4. 提取 API、类、函数、注释、依赖、配置模式

对外简化说法：

- 直接分析本地项目结构和源码语义，生成可供 AI 使用的工程知识

### 4. PDF

核心实现：

- `src/yonyou_doc2skill/cli/pdf_scraper.py`
- `src/yonyou_doc2skill/cli/pdf_extractor_poc.py`

抓取方式：

1. 逐页提取 PDF 文本、标题、代码、图片、表格
2. 生成中间 JSON
3. 再按章节或整本文档组织成 skill 和 references

对外简化说法：

- 可把 PDF 手册、规范、方案文档转成结构化 AI 知识资产

### 5. Word 文档

核心实现：

- `src/yonyou_doc2skill/cli/word_scraper.py`

抓取方式：

1. 用 `mammoth` 把 `.docx` 转成 HTML
2. 用 `python-docx` 获取元数据和表格
3. 用 `BeautifulSoup` 提取标题、段落、代码、表格

对外简化说法：

- 将 Word 文档转成结构化知识，不依赖人工复制整理

### 6. 本地 HTML

核心实现：

- `src/yonyou_doc2skill/cli/html_scraper.py`

抓取方式：

1. 读取单个 HTML 或 HTML 目录
2. 解析 DOM 结构
3. 按 `h1/h2` 切分章节
4. 提取正文、代码、表格、图片、链接

对外简化说法：

- 支持离线网页、导出页面和本地帮助文档直接转 skill

### 7. AsciiDoc

核心实现：

- `src/yonyou_doc2skill/cli/asciidoc_scraper.py`

抓取方式：

1. 解析 `.adoc` 文档结构
2. 提取标题、段落、代码块、文档层级
3. 生成结构化参考内容

对外简化说法：

- 面向技术文档源码场景，直接把 AsciiDoc 转成 AI 可用知识

### 8. PowerPoint

核心实现：

- `src/yonyou_doc2skill/cli/pptx_scraper.py`

抓取方式：

1. 解析 `.pptx` 幻灯片文本与结构
2. 提取标题、要点、备注、页面顺序
3. 组织成适合培训或知识导航的结构化内容

对外简化说法：

- 可把培训课件、宣讲材料、方案汇报直接转换为学习型 skill

### 9. 视频链接 / 本地视频

核心实现：

- `src/yonyou_doc2skill/cli/video_scraper.py`
- `src/yonyou_doc2skill/cli/video_transcript.py`
- `src/yonyou_doc2skill/cli/video_visual.py`

抓取方式：

1. 先提取视频元数据
2. 优先获取现成字幕或 transcript
3. 本地视频可寻找外挂字幕
4. 没有字幕时，可用 Whisper 转录
5. 如果启用视觉能力，则抽帧 OCR 提取屏幕代码、终端和幻灯片文字
6. 对齐音频文本和视觉文本，生成结构化教程知识

对外简化说法：

- 不只是转字幕，还能结合视觉内容理解教程视频里的代码和操作过程

### 10. Confluence

核心实现：

- `src/yonyou_doc2skill/cli/confluence_scraper.py`

抓取方式：

有两种模式：

- API 模式：调用 Confluence REST API 抓取 space、page、层级和正文
- Export 模式：解析 Confluence 导出的 HTML/XML

认证方式支持：

- Cookie
- Bearer token
- username + token

对外简化说法：

- 优先走 Confluence 官方 API 或导出格式，不依赖脆弱的页面暴力爬取

### 11. Slack / Discord Chat

核心实现：

- `src/yonyou_doc2skill/cli/chat_scraper.py`

抓取方式：

有两种模式：

- Export 模式：解析 Slack 导出或 DiscordChatExporter JSON
- API 模式：调用 Slack / Discord API 抓取消息

提取内容包括：

- 消息正文
- 线程
- reaction
- 代码片段
- 链接
- 附件

再按频道、日期、topic 做分类。

对外简化说法：

- 可把团队聊天记录中的排障经验、FAQ 和讨论沉淀成知识资产

## create 命令是怎么判断来源的

核心实现：

- `src/yonyou_doc2skill/cli/source_detector.py`

基本判断顺序：

1. 先看文件后缀
   - `.pdf` → PDF
   - `.docx` → Word
   - `.html/.htm` → HTML
   - `.adoc/.asciidoc` → AsciiDoc
   - `.pptx` → PowerPoint
   - 视频后缀 → 视频文件
2. 再看是不是本地目录
   - 是目录 → 本地代码库
3. 再看是不是 GitHub 仓库格式
   - `owner/repo` 或 GitHub URL
4. 再看是不是普通 URL
   - `http(s)` 或域名推断为文档网站

说明：

- Confluence、Chat 这些不是 `create` 主入口自动识别，而是走独立子命令

## 统一产出逻辑

无论来源是什么，整体都会尽量走同一条产出路径：

1. 抽取原始内容
2. 转成结构化中间 JSON
3. 生成 `references/`
4. 生成主 `SKILL.md`
5. 可再按目标平台执行 `package`

## 适合对外介绍时的统一说法

可以统一说成：

Yonyou Doc2Skill 支持对文档、代码、Wiki、交付资料、视频和聊天记录等多类企业知识源进行自动蒸馏。对于公开网站，系统优先利用 `llms.txt` 等 AI 友好入口；没有时则自动解析网页正文和站内结构。对于代码仓库和本地项目，系统不仅提取文档，还会分析源码结构、接口模式和测试样例。对于 Confluence、聊天导出和视频等非标准文档来源，系统则分别通过官方 API、导出格式解析和 transcript/OCR 对齐方式提取知识，最终统一生成可被 AI 使用的 skill、知识包或 RAG 资产。

## 参赛时建议强调的点

- 不是单一网页爬虫，而是多来源知识蒸馏引擎
- 不同来源使用不同最优抽取方式
- 公开网站优先 `llms.txt`
- 企业内容优先官方 API / 导出格式
- 代码仓库不仅抓文档，还做结构分析
- 视频不仅抓字幕，还支持视觉内容理解
