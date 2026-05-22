---
name: yonyou-knowledge-delivery-boost
description: 面向 AI 项目交付的知识接入提效技能。当用户希望将企业文档、Wiki、FAQ、案例和交付资料快速转化为可被 RAG、问答系统和交付流程直接复用的知识资产时使用。
---

# Yonyou Knowledge Delivery Boost

这是一个面向 AI 项目交付的知识接入与复用技能。

它解决的不是“资料能不能看”，而是“企业知识能不能高效进入 AI 项目交付链路”。它把企业文档、Confluence Wiki、FAQ、案例、实施资料等来源快速整理成可进入 RAG、问答系统和交付知识底座的可用资产，缩短交付项目中知识接入、知识清洗、FAQ 整理和案例复用的周期。

- 输入：实施手册、Confluence、FAQ、项目案例、制度流程、公开文档
- 输出：交付问答资产、排障知识资产、RAG 数据、references、交付知识包
- 模式：快速接入、场景定向、增强优化、RAG 导出

这不是静态提示词，而是一个包含本地 local 执行器、运行时、references 和可导出产物的技能包。执行层由当前技能包内的 `python3 scripts/run.py` 提供。

## 一句话定位

面向 AI 项目交付，把企业文档、Wiki、FAQ 和案例快速接入 RAG，并同步沉淀为可复用的交付知识底座。

## 核心价值

- 缩短企业知识进入 RAG 和问答系统的准备周期
- 降低交付同学手工整理 FAQ、案例、实施资料的成本
- 提高 AI 项目交付中的知识接入效率、问答稳定性和复用率
- 让交付资料从“项目文档”升级为“可复用的交付知识底座”

## 快速理解

- 只给来源：先快速接入并生成一个可用版本
- 再给一句目标：把同一份交付资料定向整理成交付问答、排障或 RAG 资产
- 需要更强结果：对初始产物启用增强模式，进一步做 FAQ 化和案例化优化
- 需要接 RAG：继续导出成 `langchain`、`llama-index` 等格式
- 需要对外安装：可直接分发当前 skill 包

## 前置条件

- 本机可用 `python3`
- agent 能读取用户提供的本地文件、仓库或导出文件
- 当前已安装的 skill 包包含 `scripts/` 目录
- 如果来源是 Confluence，本机已具备可用凭证
- 首次运行可能会在 `.runtime/` 下初始化私有运行环境，耗时会更长

## 支持的来源

- 文档网站
- GitHub 仓库
- 本地代码库
- PDF
- Word `.docx`
- 本地 HTML
- AsciiDoc
- PowerPoint `.pptx`
- 视频链接或本地视频
- Confluence
- Slack / Discord chat 导出

## 两种模式

### 1. 快速接入

- 用户只给来源时，默认先做通用接入和整理
- 优先自动判断最合适的 profile
- 适合先快速产出一个可用的交付知识包或 RAG 原始资产
- 适合先验证资料质量、分类质量和导出效果

### 2. 场景定向

- 用户明确说明“给谁用、解决什么问题、希望产出成什么形态”时，按目标定向整理
- 优先把目标映射到 `--profile general|tutorial|reference|builder|troubleshooting|internal-wiki`
- 适合直接面向交付问答、实施排障、知识接入、案例复用等场景落地

不要强制用户填复杂表单。优先接受一句自然语言目标，例如：

- 给交付问答机器人做 internal-wiki 资产
- 给 AI 项目做 RAG 知识接入资产
- 给实施同学做排障 skill
- 给项目复盘和 FAQ 复用做知识包

## 增强模式

- 默认模式先解决“从来源生成可用交付知识资产”
- 增强模式再解决“把可用知识资产提升为更像交付专家助手的可交付结果”
- 增强时重点做的是：
  - 跨 references 的综合归纳
  - FAQ 化和排障路径提炼
  - 交付场景触发条件说明
  - 高价值案例和注意事项重组

适合在这些情况下触发增强：

- 用户明确要求“增强”“优化”“润色”“补强”结果
- 用户想要做交付展示、方案演示、比赛答辩
- 用户觉得默认结果太模板化，希望更像交付专家知识包
- 用户已经完成一次蒸馏，想再做一轮质量提升

## 路由规则

- 默认使用 `python3 scripts/run.py create <source> --name <skill_name>`
- `--name` 使用简短、文件系统安全的名称
- 如果用户给的是 Confluence 页面链接，例如 `viewpage.action?pageId=...`、`/wiki/spaces/...`、或明显的企业 wiki 域名，优先把它视为受保护的 Confluence 知识源，不要先按普通公开网页抓取
- 命中这类 Confluence 链接时，先要求用户提供一种可用认证：`cookie`、`token`，或 `username + token`
- 在拿到认证前，不要先去撞登录页，也不要先按普通 `create <url>` 路径试抓
- 用户明确要交付问答、RAG 接入、排障知识时，优先传 `--profile internal-wiki` 或 `--profile troubleshooting`
- 用户只给来源时，先让系统 auto-detect 最可能的 profile
- 如果意图仍然模糊，只追问一句：这是更偏 internal-wiki、troubleshooting、reference 还是 general
- 除非用户明确要求增强，否则保持 `--enhance-level 0`
- 如果用户要求在生成时直接增强，优先使用 `--enhance-level 1`
- 如果用户已经有现成产物并要求优化，优先使用 `python3 scripts/run.py enhance <skill_dir> --agent codex`
- 如果用户明确要对接 RAG，优先在生成完成后继续执行 `python3 scripts/run.py package <output_dir> --target langchain` 或 `--target llama-index`
- 只有用户明确要求打包产物时，才使用 `python3 scripts/run.py package <output_dir>`
- 首次运行时，预期会先看到初始化步骤，再进入生成

## 常见目标场景

- 把企业 FAQ、制度流程、交付知识库整理成给 AI 问答系统使用的 internal-wiki 资产
  建议 `--profile internal-wiki`
- 把实施手册、故障案例、运维说明整理成交付同学使用的排障 skill
  建议 `--profile troubleshooting`
- 把 Confluence、FAQ、案例资料接入 RAG，导出 LangChain / LlamaIndex 可消费数据
  建议 `--profile internal-wiki`，后续执行 `package`
- 把公开产品文档先快速整理成可接入 AI 项目的 reference 知识包
  建议 `--profile reference`
- 把培训资料、项目 onboarding 文档整理成交付培训知识包
  建议 `--profile tutorial`

## 执行信号

- 首次运行时，先看 `Phase 1/3: Initializing embedded runtime`
- bootstrap 随后会输出 `Step 1/6` 到 `Step 4/6`
- 安装依赖阶段会输出 `Dependency installation started` 和 `Dependency installation finished`
- 详细 pip 日志写入 `.runtime/logs/pip-install.log`
- 初始化完成后，会看到 `Phase 2/3` 和 `Phase 3/3`
- 抓取阶段把 `Page N saved: <url>` 视为稳定进度信号
- 长任务中还会周期性输出 `Progress: N pages saved ...`
- 一旦 `output/<name>/SKILL.md` 出现，仍可能在补 references 或 summary；命令结束前不要提前报成功
- 其他无关 skill 的 warning 不应视为本 skill 失败

## 命令模板

```bash
python3 scripts/run.py create /path/to/delivery-faq.docx --name delivery-faq --profile internal-wiki --enhance-level 0
python3 scripts/run.py create /path/to/implementation-guide.pdf --name delivery-troubleshooting --profile troubleshooting --enhance-level 0
python3 scripts/run.py create https://docs.example.com/product --name product-reference --profile reference --enhance-level 0
python3 scripts/run.py confluence --base-url https://wiki.example.com --space-key TEAM --token "$TOKEN" --name team-delivery-wiki --profile internal-wiki
python3 scripts/run.py enhance output/delivery-faq --agent codex
python3 scripts/run.py package output/delivery-faq --target claude
python3 scripts/run.py package output/delivery-faq --target langchain
python3 scripts/run.py package output/delivery-faq --target llama-index
```

如果用户给的是 Confluence 页面链接，而不是现成的 `--base-url + --space-key`，优先先补认证，再引导到 Confluence 路径。例如：

```text
检测到这是 Confluence 页面链接。继续蒸馏前，请提供以下任一种认证：
1. cookie
2. token
3. username + token
```

普通模式生成完成后，如果用户还想提升结果质量、做交付展示或对外演示，默认建议继续执行一轮增强：

```bash
python3 scripts/run.py enhance output/<name> --agent codex
```

如果用户要接入 RAG 或交付问答系统，默认建议继续执行一轮打包：

```bash
python3 scripts/run.py package output/<name> --target langchain
python3 scripts/run.py package output/<name> --target llama-index
```

## 期望产物

- 抽取数据 JSON：`output/<name>_extracted.json`
- skill 目录：`output/<name>/`
- 主 skill 文件：`output/<name>/SKILL.md`
- references：`output/<name>/references/`
- RAG 导出文件：`output/<name>-langchain.json` 或 `output/<name>-llama-index.json`
- 运行时初始化状态：`.runtime/`

## 工作方式

- 先确认来源和目标 skill 名称
- 如果用户表达了明确目标场景，优先走定向蒸馏并传对应 `--profile`
- 如果用户只给来源，先走自动提炼
- 如果用户表达不清，只补问一句，不要让用户填长表单
- 如果用户强调“结果质量”“展示效果”“更像交付专家助手”，主动建议增强模式
- 如果用户要对接 AI 项目、RAG、问答系统，主动建议后续 `package`
- 如果已经有产物目录，优先考虑 `enhance` 而不是整套重跑
- 如果用户刚完成一次普通 `create`，默认补一句可继续执行 `python3 scripts/run.py enhance output/<name> --agent codex`
- 运行最窄、最直接的 `python3 scripts/run.py ...` 命令
- 完成后明确回报输出目录
- 如果用户要求打包，再补充回报打包产物路径
