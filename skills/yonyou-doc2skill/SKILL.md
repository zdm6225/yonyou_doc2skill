---
name: yonyou-doc2skill
description: 目标驱动的企业知识蒸馏引擎，把企业知识从“文档存量”变成“可执行资产”。当用户希望把企业文档、公开网站、GitHub、Wiki、交付资料蒸馏成可直接被 AI 使用的 skill 或知识资产时使用。
---

# Yonyou Doc2Skill

这是一个目标驱动的企业知识蒸馏引擎，把企业知识从“文档存量”变成“可执行资产”。

它不是静态摘要工具，也不是几句提示词，而是把文档、网站、仓库、Wiki、交付资料等来源，蒸馏成可直接被 AI 使用的 skill、references、RAG 资产或可分享的脱敏资料包。

## 适用范围

- 文档站、公开网站、PDF、Word、HTML、AsciiDoc、PPT、视频等来源蒸馏
- GitHub 仓库、本地代码库蒸馏
- Confluence 空间或页面蒸馏
- iKM 知识地图、门户、关键词检索蒸馏
- Slack / Discord chat 导出蒸馏
- 已生成 skill 的增强优化
- 交付资料、项目资料、扫描件、截图、Visio 的脱敏
- skill/RAG 产物的打包导出

## 不处理事项

- 与知识蒸馏、知识增强、资料脱敏无关的普通办公任务
- 没有可访问来源、也没有导出文件时的“凭空生成”
- 在缺少认证的情况下直接撞受保护 Wiki、Confluence、iKM 登录页
- 用户未确认前直接对客户资料做不可逆覆盖；脱敏默认生成新产物目录

## 关键规则

- 本 skill 的执行入口以当前技能包内的 `python3 scripts/run.py` 为准。
- 默认先按“用户要完成什么任务”选流程，不要先按文件后缀机械路由。
- 用户只给来源时，默认走自动提炼；用户给了“给谁用、做什么、想生成什么”，优先走定向蒸馏。
- `--name` 必须简短、文件系统安全、可直接作为输出目录名。
- 用户明确要某种 skill 形态时，传对应 `--profile general|tutorial|reference|builder|troubleshooting|internal-wiki`。
- 用户没有明确 profile 时，不强行追问长表单；意图不清时最多补问一句。
- 默认保持 `--enhance-level 0`；只有用户明确要求增强，或目标明显偏比赛展示/专家助手效果时，才走增强。
- 用户给的是 Confluence 页面链接时，优先识别为受保护 Wiki，不要先按普通公开网页抓取。
- 用户给的是 iKM 链接时，优先识别为 iKM 来源，不要先按普通网页抓取。
- 对受保护来源，先补认证，再执行蒸馏；不要先去撞登录页。
- 如果用户给的是交付目录、Office 文档、ZIP、截图、扫描件、Visio，优先判断是否应该走 `sanitize-assets` 而不是 `create`。
- 脱敏默认先产出确认清单，再 `apply`，最后 `verify`；不要直接建议用户跳过校验。
- `preview` 或 `scan` 跑完后，不要只回报文件路径；要把核心确认清单直接回显给用户。
- 打包对外分发时，优先保留 `SKILL.md`、`package.json`、`requirements.txt`、`scripts/`、`runtime/`、`templates/`；不要混入 `.runtime`、`output`、缓存和演示垃圾文件。

## 快速路由

- 用户给文档站、官网、PDF、Word、HTML：走“文档蒸馏流程”
- 用户给 GitHub 仓库或本地代码目录：走“代码库蒸馏流程”
- 用户给 Confluence 页面或空间：走“Confluence 蒸馏流程”
- 用户给 iKM 地图、门户或主题：走“iKM 蒸馏流程”
- 用户说“已经生成了，再优化一下”：走“增强流程”
- 用户给交付资料、截图、扫描件、Visio，要对外分享：走“脱敏流程”
- 用户说“导出给 Claude / LangChain / LlamaIndex”：走“打包导出流程”

## 文档蒸馏流程

1. 用户给的是文档站、公开网站、PDF、Word、HTML、AsciiDoc、PPT、视频链接或本地文件时，优先走 `create`。
2. 先确认来源和目标名称；名称不合适时，主动收敛成短名称。
3. 用户只给来源时，直接自动提炼，默认让系统 auto-detect 最合适的 profile；用户给了目标，例如“给 Codex 做编码规范 skill”，再补 `--profile`。
4. 如果用户要的是查询型知识，优先 `reference`；如果是让 AI 按规范做事，优先 `builder`；如果是培训上手，优先 `tutorial`。
5. 公开网站默认直接执行：

```bash
python3 scripts/run.py create <source> --name <skill_name> --enhance-level 0
```

6. 产出完成后，回报 `output/<name>/`；如果用户还要更像专家助手，继续建议走增强。

## 代码库蒸馏流程

1. 用户给的是 GitHub 仓库 `owner/repo` 或本地代码目录时，优先走 `create`。
2. 代码库场景默认优先考虑 `builder` 或 `reference`，不要默认生成偏摘要型产物。
3. 如果用户要“给 Codex/Claude/Cursor 辅助编码”，优先 `builder`。
4. 如果用户要“查 API、查约定、查目录结构”，优先 `reference`。
5. 直接执行：

```bash
python3 scripts/run.py create <source> --name <skill_name> --profile builder --enhance-level 0
```

或

```bash
python3 scripts/run.py create <source> --name <skill_name> --profile reference --enhance-level 0
```

6. 产出后说明主 skill 和 references 在 `output/<name>/` 下，必要时再建议增强。

## Confluence 蒸馏流程

1. 用户给的是 `viewpage.action?pageId=...`、`/wiki/spaces/...` 或明显企业 Wiki 域名时，优先识别为 Confluence。
2. 第一反应不是直接抓取，而是先补认证。要求用户提供任一种：
   - `cookie`
   - `token`
   - `username + token`
3. 在拿到认证前，不要先按普通网页 `create <url>` 试抓。
4. 有 `base-url + space-key` 时，优先走空间蒸馏；只有页面链接时，先根据页面归属补足空间信息或按已有抓取器支持方式执行。
5. 典型命令：

```bash
python3 scripts/run.py confluence --base-url https://wiki.example.com --space-key TEAM --token "$TOKEN" --name team-wiki --profile internal-wiki
```

6. 产出后，默认说明这是适合内部问答/交付检索的知识 skill；若用户要展示效果更强，再走增强。

## iKM 蒸馏流程

1. 用户给的是 iKM 详情页、知识地图、门户或主题检索需求时，优先识别为 iKM。
2. 必须先有 `cookie` 或环境变量 `IKM_COOKIE`；没有认证时不要直接按公开网页抓。
3. 按用户目标选三种模式：
   - 知识地图：`--mode map`
   - 门户/栏目：`--mode portal`
   - 关键词主题：`--mode search`
4. 如果知识主要在附件里，默认追加 `--parse-attachments`，把 PDF、Word、PPT、文本附件解析进 references。
5. 典型命令：

```bash
python3 scripts/run.py ikm --mode map --pk MAP_ID --actionlocid PORTAL_ID --parse-attachments --name ikm-map-skill
```

```bash
python3 scripts/run.py ikm --mode portal --actionlocid PORTAL_ID --parse-attachments --name ikm-portal-skill
```

```bash
python3 scripts/run.py ikm --mode search --keyword YonLinker --actionlocid PORTAL_ID --parse-attachments --name ikm-topic-skill
```

6. 这类产物通常更适合交付知识库、internal-wiki、RAG 接入或增强后再展示。

## 增强流程

1. 用户说“增强、优化、润色、补强、做得更像专家助手、做比赛展示”时，走增强。
2. 如果还没有初始产物，先走一次普通 `create`；不要直接空跑增强。
3. 如果已经有 `output/<name>/`，优先增强现有产物，不要整套重抓。
4. 如果当前是在 Codex / OpenClaw / Claude 这类对话 agent 里工作，优先走 `prepare`，把增强上下文包准备出来，再由当前 agent 接手重写 `SKILL.md`。
5. 对话 agent 优先命令：

```bash
python3 scripts/run.py enhance output/<name> --mode prepare --intent "给 Codex 做编码规范 skill"
```

6. `prepare` 只生成 `output/<name>/.enhance/` 或 `<skill_dir>/.enhance/` 上下文包，不会直接改 `SKILL.md`。
7. 如果用户明确要脚本自己闭环增强，再走自动/API/LOCAL 增强，例如：

```bash
python3 scripts/run.py enhance output/<name> --agent codex
python3 scripts/run.py enhance output/<name> --target claude --api-key "$ANTHROPIC_API_KEY"
```

8. 增强后的重点是：补场景、补路由、补边界、补高价值样例，而不是重复摘要。
9. 普通模式生成完成后，如果用户没有明确结束，默认补一句可继续增强。

## 脱敏流程

1. 用户给的是交付资料目录、Word、PPT、Excel、PDF、ZIP、截图、扫描件、Visio，并且目标是“对外分享、客户展示、比赛展示、资料外发”时，优先走 `sanitize-assets`。
2. 脱敏场景的第一条回复只能是初始化选择页，先让用户一次性确认“清单生成方式 + 图片 OCR + Logo 脱敏”。
   第一条回复只能输出本初始化页，不得在初始化页之前夹带敏感信息摘要、报错说明或手工替代方案。
   不要在初始化页之前先总结文件里有哪些敏感信息。
   不要在初始化页之前先报告运行时报错、候选项、替换建议或手工替代方案。
3. 在初始化页之前，禁止先做这些事：
   - 先总结文件里包含哪些敏感信息
   - 先报告运行时报错
   - 先展示候选项、替换建议或确认清单摘要
   - 先给“我也可以手工帮你做一版”的替代方案
4. 即使脚本或运行时当前有报错，也必须先输出初始化页；只能在初始化页之后再补充执行失败或环境问题。
5. 初始化页必须原样输出，不要自行改写、压缩、重排这段文案：


```text
【资料脱敏初始化】

输入文件：
<input_path>

推荐选择：1 + 1 + 1
推荐说明：先做文本脱敏，快速拿到可信清单；确认无误后，再补跑 OCR 或 Logo。

一、脱敏清单生成方式

1. 规则扫描 + Agent 复核（推荐）
   适合：大多数交付资料
   速度：100MB Office 资料约 1-5 分钟
   开销：Agent 复核约 5k-20k tokens

2. 完全 Agent 扫描清单
   适合：文件少、语义复杂、需要强判断
   速度：单个 1-5MB 文件通常数分钟
   开销：大目录可能超过 100k tokens

3. 人工配置脱敏清单
   适合：正式交付前、强可控场景
   速度：最快
   开销：几乎不消耗额外模型 token

二、图片文字脱敏

1. 不开启图片文字脱敏（推荐）
   说明：只处理 Office / PDF 可提取文本、文件名和结构化内容
   优点：快，适合先验证规则

2. 开启 OCR 图片文字脱敏
   说明：处理截图、扫描件、扫描版 PDF、Office 内嵌图片文字
   提示：图片越多越慢，几十张通常 5-15 分钟，上千张可能 30 分钟以上

三、Logo 脱敏

1. 不开启 Logo 脱敏（推荐）
   说明：先不处理客户 Logo，避免额外扫描耗时

2. 开启 Logo 脱敏
   说明：需要提供 Logo 模板图
   用途：扫描 Word / PPT / PDF / 图片中的客户 Logo

补充规则：
- 如果第一项选择 3，则只表示“脱敏清单由人工配置”。
- 第二项、第三项仍严格按本轮选择执行，不会因为选择 3 而被重置。

直接回复以下任一格式即可

`选择：1 + 1 + 1`

如果要 Logo：

`选择：1 + 1 + 2`
`Logo 模板：/path/to/logo.png`

如果要正式完整脱敏：

`选择：1 + 2 + 2`
`Logo 模板：/path/to/logo.png`
```

6. 默认三步：
   - 第一步：扫描候选并生成脱敏确认清单
   - 第二步：按确认配置生成脱敏产物
   - 第三步：做残留校验
7. 如果平台支持直接执行脚本，第一轮也可以先执行：

```bash
python3 scripts/run.py sanitize-assets init <input_dir> --output <init_dir>
```

8. 用户确认后，扫描候选时执行：

```bash
python3 scripts/run.py sanitize-assets scan <input_dir> --output <scan_dir>
```

9. `scan` 跑完后，要把确认清单核心内容回显给用户，包括：
   - 识别到哪些可自动脱敏项
   - 建议替换成什么
   - 哪些是高可信自动项
   - 哪些待确认
   - 哪些疑似误判
10. 用户确认后，再执行：

```bash
python3 scripts/run.py sanitize-assets apply <input_dir> --output <output_dir> --config <scan_dir>/sanitize-config.suggested.json --ocr-engine auto --audit-detail
```

11. 最后执行：

```bash
python3 scripts/run.py sanitize-assets verify <output_dir> --output <verify_dir> --config <scan_dir>/sanitize-config.suggested.json --ocr-engine auto
```

12. 默认不要覆盖原始资料；脱敏结果写入新目录。
13. 真实对外交付前，如果 `verify` 仍有残留，不要建议直接发布。
14. 如果用户第一项选择 `3`，后续应生成人工模板并等待用户补业务词典；但图片 OCR 与 Logo 脱敏必须严格沿用同轮第 2、3 项选择，不得被默认关闭或重置。
15. 对于第一项选择 `3` 的场景，优先输出专门的“人工配置脱敏清单”页面和 `sanitize-config.reviewed.json`，不要继续展示通用扫描候选页。

## Logo 脱敏流程

1. 用户要求客户 Logo 脱敏时，不要先让用户填坐标。
2. 优先让用户提供一张 Logo 模板图。
3. 先执行 Logo 扫描：

```bash
python3 scripts/run.py sanitize-assets logo-scan <input_dir> --output <logo_scan_dir> --logo-template <logo.png>
```

4. `logo-scan` 现在不只扫普通图片，也会扫描 Office 包内的图片资源；对 Word / PPT 里的页眉、页脚、页面资源，会在 review 里标出 `office_header_candidate:*`、`office_footer_candidate:*`、`office_slide_candidate:*` 这类候选位置。
5. 如果直接命中模板，会在 `logo-config.suggested.json` 里记录具体 `file + location + box`，后续 `apply` 可直接复用。
6. 如果没有直接命中，但 review 里列出了 Office 候选，不要直接判定“扫不到”；应让用户先看 review，再决定是否继续结构级替换。
7. 用户确认后，再在 `apply` 时附带 `--logo-config`。
8. 如果用户暂时没给 Logo 模板，不要让 Logo 阻塞第一轮脱敏确认清单。

## 图片与扫描件规则

- 截图、扫描件、图片文字默认建议 `--ocr-engine auto`
- `auto` 会优先选择 `rapidocr -> paddleocr -> tesseract`
- 中文截图和扫描件当前优先推荐 `rapidocr`
- 扫描版 PDF 默认按 `OCR -> QR` 的顺序做 fallback
- Visio `.vsdx` 当前支持页面可见文本替换和内嵌图片脱敏，但复杂对象仍建议抽样人工验收

## 打包导出流程

1. 用户明确要求“打包、发布、给别人用、导出给 Claude/LangChain/LlamaIndex”时，才走打包。
2. skill 分发优先使用干净目录或 zip，不混入 `.runtime`、`output`、缓存、演示文件。
3. skill 平台打包使用：

```bash
python3 scripts/run.py package output/<name> --target claude
python3 scripts/run.py package output/<name> --target langchain
python3 scripts/run.py package output/<name> --target llama-index
```

4. 如果用户要分发当前官方 skill，本体应保留：
   - `SKILL.md`
   - `package.json`
   - `requirements.txt`
   - `scripts/`
   - `runtime/`
   - `templates/`

## 常见目标场景

- 把官方文档站蒸馏成研发查询用 `reference skill`
- 把代码仓库蒸馏成给 Codex 使用的 `builder skill`
- 把研发规范资料蒸馏成新人 `tutorial skill`
- 把实施手册、FAQ 蒸馏成交付排障 `troubleshooting skill`
- 把制度、Wiki、知识空间蒸馏成 `internal-wiki skill`
- 把交付资料脱敏后导出为可分享资产包
- 把知识资产导出为 LangChain / LlamaIndex / Claude 可消费格式

## 执行信号

- 首次运行先看 `Phase 1/3: Initializing embedded runtime`
- bootstrap 随后会输出 `Step 1/6` 到 `Step 4/6`
- 安装依赖阶段会输出 `Dependency installation started` 和 `Dependency installation finished`
- 详细 pip 日志在 `.runtime/logs/pip-install.log`
- 初始化完成后会看到 `Phase 2/3` 和 `Phase 3/3`
- 网站抓取阶段把 `Page N saved: <url>` 视为稳定进度信号
- 长任务中还会周期性输出 `Progress: N pages saved ...`
- 脱敏流程中重点看：确认清单、脱敏报告、校验报告是否已产出
- 一旦 `output/<name>/SKILL.md` 出现，仍可能在补 references 或 summary；命令结束前不要提前报成功

## 期望产物

- 蒸馏产物：`output/<name>/`
- 主 skill 文件：`output/<name>/SKILL.md`
- references：`output/<name>/references/`
- 抽取数据 JSON：`output/<name>_extracted.json`
- 脱敏配置模板：`templates/sanitize-config.template.json`、`templates/logo-config.template.json`
- 脱敏确认清单：`脱敏确认清单.md`
- 脱敏报告：`sanitize-report.md` / `sanitize-report.json` / `sanitize-detail.csv`
- 校验报告：`verify-report.md` / `verify-report.json`

## 参考命令

```bash
python3 scripts/run.py create https://nextjs.org/docs --name nextjs-reference --profile reference --enhance-level 0
python3 scripts/run.py create owner/repo --name repo-builder --profile builder --enhance-level 0
python3 scripts/run.py confluence --base-url https://wiki.example.com --space-key TEAM --token "$TOKEN" --name team-wiki --profile internal-wiki
python3 scripts/run.py ikm --mode map --pk MAP_ID --actionlocid PORTAL_ID --parse-attachments --name ikm-map-skill
python3 scripts/run.py enhance output/nextjs-reference --agent codex
python3 scripts/run.py sanitize-assets scan ./delivery-assets --output output/delivery-assets-scan
python3 scripts/run.py sanitize-assets logo-scan ./delivery-assets --output output/delivery-assets-logo-scan --logo-template ./customer-logo.png
python3 scripts/run.py sanitize-assets logo-scan ./header-logo.docx --output output/header-logo-scan --logo-template ./customer-logo.png
python3 scripts/run.py sanitize-assets apply ./delivery-assets --output output/delivery-assets-sanitized --config output/delivery-assets-scan/sanitize-config.suggested.json --logo-config output/delivery-assets-logo-scan/logo-config.suggested.json --ocr-engine auto --audit-detail
python3 scripts/run.py sanitize-assets verify output/delivery-assets-sanitized --output output/delivery-assets-verify --config output/delivery-assets-scan/sanitize-config.suggested.json --ocr-engine auto
python3 scripts/run.py package output/nextjs-reference --target claude
```
