---
name: yonyou-doc2skill
description: 当用户希望把企业文档、代码仓库、Wiki、交付资料等来源按目标场景蒸馏成可直接被 AI 使用的 skill 或知识资产时使用。
---

# Yonyou Doc2Skill

这是一个目标驱动的企业知识蒸馏引擎。

它不是单纯把文档做成摘要，而是把企业文档、代码仓库、Wiki、交付资料等来源，按目标场景蒸馏成可直接被 AI 使用的 skill 或知识资产。

- 同一份来源，可以面向研发、交付、培训、问答等不同目标输出不同结果
- 默认支持自动提炼，也支持带目标的定向蒸馏
- 执行层由当前技能包内的 `python3 scripts/run.py` 提供

## 一句话定位

把企业知识从“文档存量”变成“可执行资产”。

## 核心价值

- 降低知识整理和 AI 接入门槛
- 提升研发与交付复用效率
- 减少 AI 使用中的上下文缺失和答非所问
- 支持“同源多产物”的目标驱动蒸馏，而不是静态摘要

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
- Slack / Discord chat / 聊天导出

## 两种模式

### 1. 自动提炼

- 用户只给来源时，默认走通用蒸馏
- 优先自动判断最合适的 profile
- 适合先快速产出一个可用 skill

### 2. 定向蒸馏

- 用户明确说明“给谁用、解决什么问题、希望产出成什么形态”时，按目标定向蒸馏
- 优先把目标映射到 `--profile general|tutorial|reference|builder|troubleshooting|internal-wiki`
- 比纯摘要更贴近真实业务场景

不要强制用户填复杂表单。优先接受一句自然语言目标，例如：

- 给研发新人做 onboarding skill
- 给 Codex 做编码规范 skill
- 给交付同学做实施排障 skill
- 给制度问答机器人做 internal-wiki skill

## 路由规则

- 默认使用 `python3 scripts/run.py create <source> --name <skill_name>`
- `--name` 使用简短、文件系统安全的名称
- 用户明确要某种 skill 形态时，传对应的 `--profile`
- 用户只给来源时，先让 Doc2Skill auto-detect 最可能的 profile
- 如果意图仍然模糊，只追问一句：这是更偏 tutorial、reference、builder、troubleshooting 还是 internal-wiki
- 除非用户明确要求增强，否则保持 `--enhance-level 0`
- 只有用户明确要求打包产物时，才使用 `python3 scripts/run.py package <output_dir>`
- 首次运行时，预期会先看到初始化步骤，再进入生成

## 常见目标场景

- 把《用友专业开发红皮书》蒸馏成给 Codex 使用的编码规范 skill
  建议 `--profile builder` 或 `--profile reference`
- 把研发规范站点蒸馏成给新人使用的 onboarding / tutorial skill
  建议 `--profile tutorial`
- 把实施手册、项目交付文档蒸馏成交付同学使用的排障 skill
  建议 `--profile troubleshooting`
- 把公司制度、流程、FAQ 蒸馏成员工问答机器人使用的 internal-wiki skill
  建议 `--profile internal-wiki`
- 把框架/API 官方文档蒸馏成查询型 reference skill
  建议 `--profile reference`
- 把通用知识资料先快速生成一个可用版本
  不指定 `--profile`，走 auto-detect

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
python3 scripts/run.py create https://docs.example.com --name my-docs-skill --profile reference --enhance-level 0
python3 scripts/run.py create owner/repo --name repo-skill --enhance-level 0
python3 scripts/run.py create /path/to/project --name local-project-skill --profile builder --enhance-level 0
python3 scripts/run.py create /path/to/file.pdf --name pdf-skill --profile tutorial --enhance-level 0
python3 scripts/run.py create /path/to/page.html --name html-skill --enhance-level 0
python3 scripts/run.py confluence --base-url https://wiki.example.com --space-key TEAM --token "$TOKEN" --name team-wiki
python3 scripts/run.py package output/my-docs-skill
```

## 期望产物

- 抽取数据 JSON：`output/<name>_extracted.json`
- skill 目录：`output/<name>/`
- 主 skill 文件：`output/<name>/SKILL.md`
- references：`output/<name>/references/`
- 运行时初始化状态：`.runtime/`

## 工作方式

- 先确认来源和目标 skill 名称
- 如果用户表达了明确目标场景，优先走定向蒸馏并传对应 `--profile`
- 如果用户只给来源，先走自动提炼
- 如果用户表达不清，只补问一句，不要让用户填长表单
- 运行最窄、最直接的 `python3 scripts/run.py ...` 命令
- 完成后明确回报输出目录
- 如果用户要求打包，再补充回报打包产物路径
