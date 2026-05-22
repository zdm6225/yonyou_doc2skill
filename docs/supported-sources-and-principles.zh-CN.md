# Yonyou Doc2Skill 支持来源与解析原理

本文说明 Yonyou Doc2Skill 当前支持的数据源类型，以及每一种来源的解析原理。核心结论是：它不是单一爬虫，而是一条“来源识别 -> 专用解析器 -> 结构化中间数据 -> skill / references / RAG 资产”的知识蒸馏流水线。

## 1. 总体流程

```text
用户输入来源
  -> 判断来源类型
  -> 选择对应解析器
  -> 抽取正文、标题、章节、代码、表格、链接、元数据
  -> 生成统一结构化数据
  -> 输出 SKILL.md、references、可选 RAG/外部框架格式
```

统一产物通常包括：

- `output/<name>/SKILL.md`：给 AI agent 使用的技能说明。
- `output/<name>/references/`：结构化后的知识资料。
- `output/<name>_extracted.json`：抽取后的中间数据。
- 可选 package 产物：Claude skill、LangChain、LlamaIndex 等格式。

## 2. 当前对外支持的数据源

| 来源 | 典型输入 | 主要解析方式 |
| --- | --- | --- |
| 公开文档网站 | `https://nextjs.org/docs` | 优先读 `llms.txt`，其次 sitemap，再解析 HTML |
| GitHub 仓库 | `owner/repo` 或 Git URL | GitHub API / clone 后分析仓库文件 |
| 本地代码库 | `./my-codebase` | 遍历本地目录，按语言和文件类型解析 |
| PDF | `manual.pdf` | PDF 页面文本、目录、表格、图片信息抽取 |
| Word | `manual.docx` | DOCX 转 HTML + 段落、标题、表格解析 |
| 本地 HTML | `page.html` | DOM 解析正文、标题、代码块、链接 |
| AsciiDoc | `guide.adoc` | AsciiDoc 结构解析，失败时走文本 fallback |
| PowerPoint | `slides.pptx` | 按页读取标题、正文、备注和结构 |
| 视频 | 视频 URL / 本地视频 | 字幕、转写、关键帧和视觉信息抽取 |
| Confluence | space/page/export | REST API、Cookie/token 鉴权、storage body 解析 |
| Slack / Discord 导出 | export JSON | 消息、线程、代码片段、链接、附件解析 |

## 3. 公开文档网站

典型输入：

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-reference
```

解析原理：

- 第一步会尝试发现 `llms.txt` 或 `llms-full.txt`。
- 如果站点提供 `llms.txt`，优先使用它作为官方给 AI 使用的文档索引。
- 如果没有 `llms.txt`，会尝试读取 `sitemap.xml`，从站点地图中发现文档页面。
- 如果 sitemap 不完整，会退回到 HTML 页面解析和同站链接发现。
- 对普通 HTML 页面，会提取 `title`、`h1/h2/h3`、正文段落、代码块、表格、链接、图片 alt 等内容。
- 对前端渲染较重的网站，可通过浏览器渲染能力获取最终页面内容。
- 支持通过 include/exclude 规则限定 URL 范围，避免抓取无关页面。

适合场景：

- 框架/API 官方文档蒸馏为 reference skill。
- 产品帮助中心蒸馏为 internal-wiki skill。
- 开发规范站点蒸馏为 builder/reference skill。

限制：

- 需要页面可访问。
- 需要登录的网站必须提供 Cookie、token 或导出文件。
- 如果站点反爬、页面强依赖动态接口，抓取效果取决于浏览器渲染和网络权限。

## 4. GitHub 仓库

典型输入：

```bash
yonyou-doc2skill create django/django --name django-codebase
```

解析原理：

- 识别 `owner/repo`、Git URL 或本地 clone 目录。
- 优先获取仓库元数据，例如 README、目录结构、语言、依赖文件、配置文件。
- 对代码文件按语言类型解析，提取类、函数、接口、注释、导入关系、测试样例和配置。
- 对文档文件继续走 Markdown/HTML/文本解析。
- 输出时会把仓库结构、核心模块、使用方式、开发约定整理成 skill references。

适合场景：

- 把开源仓库蒸馏成代码理解 skill。
- 把内部工程蒸馏成给 Codex/Cursor 使用的 builder skill。
- 把 SDK 仓库蒸馏成 reference skill。

限制：

- 私有仓库需要本地已有权限或 token。
- 超大仓库建议用 include/exclude 限定范围。

## 5. 本地代码库

典型输入：

```bash
yonyou-doc2skill create ./my-codebase --name project-builder
```

解析原理：

- 遍历本地目录文件。
- 默认跳过 `.git`、`node_modules`、`dist`、`build`、缓存目录等无关内容。
- 根据文件后缀识别语言和文档类型。
- 抽取 README、配置、依赖、源码结构、测试、脚本、接口定义等信息。
- 对代码侧重点是结构化理解，不是简单拼接文件内容。

适合场景：

- 内部项目交接。
- 给 AI 编码助手补充项目上下文。
- 从已有项目生成开发规范、模块说明和 onboarding skill。

限制：

- 如果代码量很大，需要限制目录，否则产物会膨胀。
- 二进制文件和生成文件通常不应进入知识资产。

## 6. PDF

典型输入：

```bash
yonyou-doc2skill create manual.pdf --name manual-skill
```

解析原理：

- 逐页读取 PDF 文本。
- 尝试识别标题、章节、页码、段落、表格和图片占位信息。
- 对可复制文本型 PDF 效果最好。
- 对扫描件 PDF，需要 OCR 能力配合，否则只能拿到有限文本或图片信息。
- 解析结果会按页和章节组织，写入 references。

适合场景：

- 产品手册。
- 实施手册。
- 培训材料。
- 制度文件。

限制：

- 扫描件、图片型 PDF 效果依赖 OCR。
- 排版复杂的表格可能需要人工复核。

## 7. Word `.docx`

典型输入：

```bash
yonyou-doc2skill create manual.docx --name manual-skill
```

解析原理：

- 先将 DOCX 内容转换为结构化 HTML。
- 再解析标题、段落、列表、表格、图片引用和样式层级。
- 同时读取文档元数据和表格内容。
- 最终按章节生成 references。

适合场景：

- 内部制度文档。
- 交付方案。
- 项目总结。
- 培训材料。

限制：

- Word 中复杂排版、文本框、嵌入对象可能不能完整还原。
- 图片中的文字需要 OCR 才能被理解。

## 8. 本地 HTML

典型输入：

```bash
yonyou-doc2skill create page.html --name html-skill
```

解析原理：

- 直接读取本地 HTML 文件。
- 使用 DOM 解析正文、标题、列表、代码块、表格、链接、图片说明。
- 去除脚本、样式、导航等低价值内容。
- 将页面内容转换为 Markdown/reference 结构。

适合场景：

- 已导出的网页。
- 需要登录系统的页面离线保存后再蒸馏。
- Confluence 或知识库页面 HTML 导出。

限制：

- 只解析本地文件本身，不会自动拥有原网站登录态。
- 页面依赖外部脚本动态渲染时，本地 HTML 可能不完整。

## 9. AsciiDoc

典型输入：

```bash
yonyou-doc2skill create guide.adoc --name guide-skill
```

解析原理：

- 优先按 AsciiDoc 语法识别标题、属性、include、代码块、表格、提示块。
- 在专业解析器不可用时，退回到文本规则解析。
- 保留章节结构和示例代码。

适合场景：

- 技术规范。
- 开源项目文档。
- 架构设计文档。

限制：

- include 文件缺失时，无法还原完整文档。
- 自定义宏需要额外适配。

## 10. PowerPoint `.pptx`

典型输入：

```bash
yonyou-doc2skill create slides.pptx --name training-skill
```

解析原理：

- 按 slide 逐页读取。
- 提取标题、正文文本、项目符号、备注和基本页面顺序。
- 将演示型内容转换为教程型或培训型 references。

适合场景：

- 培训课件。
- 方案汇报。
- 项目复盘材料。

限制：

- 图形中的文字、复杂流程图需要 OCR 或视觉模型辅助。
- PPT 的视觉布局不会完整转成结构化文本。

## 11. 视频

典型输入：

```bash
yonyou-doc2skill create https://example.com/video --name video-skill
yonyou-doc2skill create demo.mp4 --name video-skill
```

解析原理：

- 优先获取已有字幕或 transcript。
- 对公开视频可尝试读取平台字幕。
- 对本地视频可结合转写能力提取语音文本。
- 可抽取关键帧、时间轴、标题画面、屏幕文字等视觉信息。
- 将 transcript 和视觉线索合并成章节化内容。

适合场景：

- 培训视频转教程 skill。
- 会议录屏转知识沉淀。
- 产品演示视频转操作手册。

限制：

- 无字幕视频依赖本地转写能力。
- 噪声、口音、多人说话会影响转写准确率。
- 视觉理解能力取决于是否启用对应依赖。

## 12. Confluence

典型输入：

```bash
yonyou-doc2skill confluence \
  --base-url https://wiki.example.com \
  --space-key TEAM \
  --username user \
  --token "$TOKEN" \
  --name team-wiki
```

解析原理：

- 通过 Confluence REST API 获取 space、page、body、children、labels、ancestors 等信息。
- 页面正文优先读取 Confluence storage 格式，再转换为 Markdown/reference。
- 支持用户名 + token、Bearer token、Cookie 等认证方式。
- 也可以读取已经导出的 Confluence JSON/HTML 文件。
- 对 `viewpage.action?pageId=...` 这类页面链接，需要先有认证，否则只能抓到登录页。

适合场景：

- 内部 Wiki 蒸馏为 internal-wiki skill。
- 项目空间蒸馏成交付知识库。
- 研发规范空间蒸馏成 builder/reference skill。

限制：

- 登录态是必要条件。
- 没有权限时工具不能绕过访问控制。
- 大空间建议限制 page 数或指定入口页面。

## 13. Slack / Discord 聊天导出

典型输入：

```bash
yonyou-doc2skill create ./slack-export --name team-chat-knowledge
```

解析原理：

- 读取 Slack/Discord 导出的 JSON 文件。
- 按频道、日期、线程、回复关系组织消息。
- 抽取问题、回答、代码片段、链接、附件引用和决策记录。
- 将零散聊天内容整理为 FAQ、决策记录、排障经验或 internal-wiki references。

适合场景：

- 从历史讨论沉淀 FAQ。
- 从交付群沉淀排障经验。
- 从研发群沉淀约定和决策。

限制：

- 导出质量决定结果质量。
- 私聊、附件内容、外链内容不一定包含在导出包里。
- 需要注意敏感信息脱敏。

## 14. 保留但非当前主推入口的解析器

代码中还保留了一些解析器能力，适合后续恢复或扩展，但当前不建议作为对外主推场景：

| 来源 | 解析思路 | 当前建议 |
| --- | --- | --- |
| EPUB | 解析电子书目录、章节 HTML、正文和元数据 | 可用于电子书知识包，需补交付验证 |
| Jupyter Notebook | 读取 `.ipynb` 的 Markdown、代码、输出和执行顺序 | 可用于教程/实验文档 |
| OpenAPI / Swagger | 解析 YAML/JSON 中的 paths、operations、schemas、examples | 可用于 API reference |
| RSS / Atom | 读取 feed 条目、标题、摘要、链接、发布时间 | 可用于资讯型知识流 |
| Man page | 解析命令手册章节、参数、示例 | 可用于 CLI reference |
| Notion | 读取 Notion API/export 的页面、数据库、block | 需要认证和更完整验证 |

## 15. 和普通 RAG 的区别

Doc2Skill 的解析阶段和 RAG 的文档接入类似，都会把原始资料变成结构化文本。但目标不同：

- RAG 更关注切 chunk、建索引、召回问答。
- Skill 更关注把知识变成 AI agent 可读的使用说明、工作流、边界条件和 references。
- Doc2Skill 可以同时输出 skill 和 RAG 友好的结构化数据。
- 对同一份资料，可以按 reference、builder、tutorial、troubleshooting、internal-wiki 等目标生成不同资产。


