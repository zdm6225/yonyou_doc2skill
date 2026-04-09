# Yonyou Doc2Skill Skill Profile Generation Design

## Goal

让最终用户在生成 skill 时，不再只得到一个“默认通用 skill”，而是得到更符合目标用途的 skill。

这版设计把生成输入从：

- 来源

升级为：

- 来源
- profile（技能用途类型）

同时保留“用户可以显式指定”和“系统可以自动判断”两条路径。

## Scope

本次设计只覆盖这些内容：

- profile 枚举与语义
- profile 自动判断规则
- CLI 参数与 skill 交互方式
- 不同 profile 对 `SKILL.md` 结构的影响
- 自动判断低置信度时的追问策略

不在这次设计范围内：

- 全量重写现有 skill 生成器
- 引入新的远程服务
- 复杂的多轮 LLM planner
- 对所有来源做完全不同的专用生成器

## Profiles

第一版提供 6 个 profile：

- `general`
  默认通用文档 skill。适合未知场景或混合型资料。

- `tutorial`
  偏学习路径和入门引导。强调概念顺序、学习路线、典型上手步骤。

- `reference`
  偏 API / 参数 / 组件 / 命令查询。强调快速检索和精确引用。

- `builder`
  偏“拿这个内容去生成代码、配置、实施方案”。强调可执行步骤、约束、模板、工作流。

- `troubleshooting`
  偏问题定位和故障排查。强调常见错误、排查路径、边界条件和诊断线索。

- `internal-wiki`
  偏企业内部知识整理。强调术语解释、流程、制度、角色分工、文档索引。

## User Experience

### CLI

新增参数：

```bash
--profile general|tutorial|reference|builder|troubleshooting|internal-wiki
```

行为：

- 用户显式传 `--profile` 时，直接使用该值
- 未传时，系统执行自动判断
- 自动判断结果写入产物元数据

示例：

```bash
yonyou-doc2skill create https://react.dev --name react --profile reference
yonyou-doc2skill create ./handbook.pdf --name onboarding --profile tutorial
yonyou-doc2skill create https://wiki.example.com --name team-wiki
```

第三条未指定 `--profile`，系统自动推断。

### Codex / Official Skill

官方 skill 的交互改为：

- 用户已明确说明目标时，直接映射到 profile
- 用户只给来源时，先自动判断
- 判断置信度低时，追问一句

追问原则：

- 只在低置信度时追问
- 一次只问一个问题
- 问法聚焦“你更想拿它做什么”

示例追问：

`这个来源更像是要做成查询型 reference skill，还是做成偏教程型 tutorial skill？`

## Auto-Detection

自动判断分两层：

### Layer 1: Source Heuristics

根据来源类型给初始倾向：

- GitHub repo
  默认偏 `builder`
- API/组件文档站
  默认偏 `reference`
- 培训手册 / onboarding 文档
  默认偏 `tutorial`
- Confluence / 内部 wiki
  默认偏 `internal-wiki`
- FAQ / support / troubleshooting 文档
  默认偏 `troubleshooting`

### Layer 2: Content Heuristics

根据抓取结果再加权：

- 标题、URL、heading、目录中包含这些词时偏 `tutorial`
  - getting started
  - learn
  - quick start
  - tutorial
  - guide
  - introduction

- 包含这些词时偏 `reference`
  - api
  - reference
  - props
  - parameters
  - component
  - command
  - options

- 包含这些词时偏 `builder`
  - build
  - generate
  - scaffold
  - example project
  - integration
  - workflow
  - implementation

- 包含这些词时偏 `troubleshooting`
  - error
  - debug
  - troubleshooting
  - warning
  - issue
  - failed
  - fix

- 包含这些词时偏 `internal-wiki`
  - policy
  - process
  - approval
  - role
  - department
  - internal
  - faq
  - standard

### Confidence

输出：

- `suggested_profile`
- `profile_confidence`
- `profile_reasons`

简单策略：

- 明显单一高分：直接使用
- 多个 profile 接近：标记低置信度
- skill wrapper 在低置信度时追问

## Output Shape Differences

不同 profile 不要求完全不同模板，但 `SKILL.md` 的重点区块要不同。

### general

- 简短描述
- 常见模式
- references 索引
- 通用使用方式

### tutorial

- 学习路径 / 推荐阅读顺序
- 入门步骤
- 关键概念
- 从新手到实战的建议路线

### reference

- 快速查询入口
- API / 组件 / 参数索引
- 术语和关键对象
- 少解释，多可检索结构

### builder

- 典型生成任务
- 输入约束
- 推荐命令 / 模板
- 实施步骤
- 输出样例

### troubleshooting

- 常见问题
- 诊断步骤
- 错误模式
- 定位建议
- 何时升级处理

### internal-wiki

- 组织术语
- 角色职责
- 流程索引
- 制度与规范
- 跨页面导航建议

## Architecture

新增一个轻量 profile 模块，职责保持独立。

建议结构：

```text
src/yonyou_doc2skill/cli/profile_detection.py
src/yonyou_doc2skill/cli/profile_templates.py
```

职责：

- `profile_detection.py`
  - 定义 profile 枚举
  - 根据来源和抓取结果做自动判断
  - 输出 profile + confidence + reasons

- `profile_templates.py`
  - 根据 profile 决定 `SKILL.md` 的结构重点
  - 复用现有 skill 生成内容，不重写全套生成流程

集成点：

- `create` 参数解析增加 `--profile`
- `doc_scraper` / 其他 source converter 在 build skill 前拿到最终 profile
- official skill wrapper 在无显式 profile 且低置信度时追问用户

## Data Flow

### CLI Path

1. 用户输入来源
2. 如果传了 `--profile`，直接使用
3. 否则根据来源和抽取结果做 profile 判断
4. 使用对应模板重点生成 `SKILL.md`
5. 把 profile 信息写入元数据或 summary

### Official Skill Path

1. 用户给来源
2. wrapper 判断是否已有明确意图
3. 若无，则自动判断 profile
4. 若低置信度，追问用户确认
5. 调用 `python3 scripts/run.py create ... --profile ...`

## Error Handling

- profile 值非法时，CLI 直接报错并列出可选值
- 自动判断失败时，回退到 `general`
- 低置信度时不硬猜，wrapper 应追问
- 如果运行环境不支持追问，则回退到 `general`，同时在日志里输出建议 profile

## Testing

至少覆盖这些测试：

- CLI 能解析 `--profile`
- 未指定 profile 时能自动判断
- 典型来源能得到合理 profile
- 低置信度场景会返回可追问状态
- 不同 profile 生成的 `SKILL.md` 关键区块不同
- official skill wrapper 能把确认后的 profile 传给底层命令

## Rollout Plan

第一阶段：

- 先支持 `general/tutorial/reference/builder/troubleshooting/internal-wiki`
- 先做规则判断，不强依赖 LLM
- 先改 `create` 主路径和 official skill wrapper

第二阶段：

- 再考虑把 enhancement 和 profile 联动
- 让增强模型按 profile 改写
- 再考虑更细的垂直 profile

## Recommendation

先做“规则判断 + 显式覆盖 + 低置信度追问”。

原因：

- 成本可控
- 用户能立即感知差异
- 不会把核心生成流程改得过深
- 后面增强模型有了明确方向，不再只是把通用 skill 写得更漂亮
