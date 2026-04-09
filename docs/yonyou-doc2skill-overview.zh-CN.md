# Yonyou Doc2Skill 总览

## 1. 定位

**Yonyou Doc2Skill** 是一个 **目标驱动的企业知识蒸馏引擎**，也是一个 **CLI-first 的企业知识资产生成工具**。

它的核心目标不是简单做摘要，也不是把几句提示词包装成一个 skill，而是把企业文档、代码仓库、Wiki、交付资料、聊天记录等来源，蒸馏成可直接被 AI 使用的知识资产。

一句话定位：

**把企业知识从“文档存量”变成“可执行资产”。**

---

## 2. 价值

### 2.1 对业务的价值

- 降低知识整理和 AI 接入门槛
- 提升研发、交付、培训、知识问答等场景的复用效率
- 减少 AI 使用中的上下文缺失和答非所问
- 把原本分散的文档、代码、Wiki 沉淀为统一知识资产

### 2.2 对使用成本的价值

- 首次蒸馏更像一次离线建索引，**相对省 token**
- 后续复用时，不需要反复把整份文档重新喂给模型
- 更适合企业长期积累和持续更新知识资产

### 2.3 对流程的价值

- 以前：人工找资料、复制上下文、手动整理知识
- 现在：来源输入 -> 自动提炼 / 定向蒸馏 -> skill / references / RAG 资产输出

---

## 3. 创新点

### 3.1 自动提炼 + 定向蒸馏双模式

- **自动提炼**：只给来源，快速生成通用 skill 或知识包
- **定向蒸馏**：补一句目标，例如“给 Codex 做编码规范 skill”，系统按目标输出更贴场景的结果

### 3.2 增强模式

- **增强模式**：在初始蒸馏结果基础上，再用 AI 对 `SKILL.md` 做二次增强
- 重点增强的不是“改几个词”，而是：
  - 跨 references 的综合归纳
  - 关键概念提炼
  - 触发场景与边界条件说明
  - 高价值样例重组
- 可以把“自动生成的知识包”进一步提升为“更像专家助手的可交付 skill”

### 3.3 同源多产物

同一份知识，不止生成一个通用 skill，而是可以按目标输出不同资产：

- 面向研发：`reference` / `builder` / `tutorial`
- 面向交付：`troubleshooting`
- 面向知识问答：`internal-wiki`
- 面向通用场景：`general`

### 3.4 Skill + Runtime，而不是静态 Prompt

Yonyou Doc2Skill 不是几句提示词，而是一套完整执行链路：

- 有 skill 入口
- 有本地执行器
- 有结构化抽取数据
- 有 references 参考文件
- 有最终生成的 `SKILL.md`

### 3.5 多来源统一蒸馏流水线

公开文档、代码仓库、PDF、Wiki、Word、HTML、PPT、聊天记录等，可以进入同一条知识蒸馏流水线。

---

## 4. 包含功能

### 4.1 来源接入

当前对外支持：

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
- Slack / Discord 聊天导出

### 4.2 结构化抽取

- 标题、章节、正文抽取
- 代码块抽取与语言识别
- 链接与参考资料归类
- references 分类输出
- 抽取结果 JSON 输出

### 4.3 Skill 生成

- 自动生成 `SKILL.md`
- 支持 profile 定向输出
- 支持自动 profile 判断
- 支持增强模式和后处理

### 4.4 打包与分发

- skill 打包
- 安装到 agent / skill 目录
- 上传到平台或向量数据库
- 支持增量更新、恢复、质量评估等辅助能力

---

## 5. 所有 CLI 命令

当前主命令：

```bash
yonyou-doc2skill
```

当前帮助输出中的命令如下：

```text
create
doctor
config
confluence
chat
enhance
enhance-status
package
upload
estimate
install
install-agent
extract-test-examples
resume
quality
workflows
sync-config
stream
update
multilang
```

### 5.1 命令说明

- `create`：从任意支持来源生成 skill
- `doctor`：检查环境、依赖和运行状态
- `config`：配置 GitHub token、API key 和其他设置
- `confluence`：从 Confluence 空间或页面抽取内容
- `chat`：从 Slack / Discord 导出中抽取内容
- `enhance`：对产出的 skill 做 AI 增强
- `enhance-status`：查看增强任务状态
- `package`：把 skill 打包成特定目标格式
- `upload`：上传到平台或向量数据库
- `estimate`：抓取前估算页面规模
- `install`：一条链路执行抓取、增强、打包、上传
- `install-agent`：把 skill 安装到 agent 目录
- `extract-test-examples`：从测试中提取示例
- `resume`：恢复中断任务
- `quality`：对 `SKILL.md` 做质量评分
- `workflows`：管理增强工作流预设
- `sync-config`：同步配置中的入口 URL
- `stream`：大文件流式处理
- `update`：增量更新 docs / skill
- `multilang`：多语言文档支持

---

## 6. 具体用法

### 6.1 最常用：create

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-reference --profile reference --enhance-level 0
```

含义：

- 从文档站生成一个叫 `nextjs-reference` 的 skill
- 使用 `reference` profile
- 不启用增强

### 6.2 从 GitHub 仓库生成

```bash
yonyou-doc2skill create vercel/next.js --name nextjs-repo --enhance-level 0
```

### 6.3 从本地项目生成

```bash
yonyou-doc2skill create ./my-project --name my-project-skill --profile builder --enhance-level 0
```

### 6.4 从 PDF 生成

```bash
yonyou-doc2skill create ./manual.pdf --name manual-skill --profile tutorial --enhance-level 0
```

### 6.5 从 Confluence 生成

```bash
yonyou-doc2skill confluence \
  --base-url https://wiki.example.com \
  --space-key TEAM \
  --token 'YOUR_TOKEN' \
  --name team-wiki
```

### 6.6 打包

```bash
yonyou-doc2skill package output/nextjs-reference
```

### 6.7 增强模式

直接在生成时启用：

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-reference-enhanced --profile reference --enhance-level 1
```

先蒸馏，再单独增强：

```bash
yonyou-doc2skill enhance output/nextjs-reference --agent codex
```

说明：

- `--enhance-level 0`：关闭增强
- `--enhance-level 1`：增强 `SKILL.md`
- 单独 `enhance`：对已有 skill 做二次增强，适合比赛展示“增强前后对比”

### 6.8 官方 Skill 模式

如果通过官方 skill 调用，则执行链路通常是：

```bash
python3 scripts/run.py create https://nextjs.org/docs --name nextjs-reference --profile reference --enhance-level 0
```

触发增强模式时，可直接这样调用：

```bash
python3 scripts/run.py create https://nextjs.org/docs --name nextjs-reference --profile reference --enhance-level 1
python3 scripts/run.py enhance output/nextjs-reference --agent codex
```

### 6.9 推荐使用方式

#### 快速模式

只给来源：

```bash
yonyou-doc2skill create https://docs.example.com --name example-skill
```

适合先快速出一个通用 skill。

#### 目标模式

给来源 + 目标：

```bash
yonyou-doc2skill create https://docs.example.com --name example-skill --profile builder
```

或者在 skill 交互里直接说：

- 给 Codex 做编码规范 skill
- 给交付同学做排障 skill
- 给新人做 tutorial skill

#### 增强模式

先生成，再增强：

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-reference --profile reference --enhance-level 0
yonyou-doc2skill enhance output/nextjs-reference --agent codex
```

适合：

- 对外展示更强的最终 skill 质量
- 做“增强前 / 增强后”对比
- 让结果从模板化产物变成更像专家助手的交付物

### 6.10 典型产物

运行完成后，通常会得到：

- `output/<name>/SKILL.md`
- `output/<name>/references/`
- `output/<name>_data/summary.json`
- `output/<name>_extracted.json`（视来源而定）

---

## 7. 场景

### 7.1 研发提效场景

适合赛道：**研发过程提效AI化赛道**

典型案例：

- 把《用友专业开发红皮书》蒸馏成给 Codex 使用的编码规范 skill
- 把研发规范站点蒸馏成 `reference` 或 `builder` skill
- 把本地代码库 + 文档联合蒸馏成 AI 编码辅助资产
- 把公开框架文档（如 Next.js）蒸馏成研发查询型 skill

推荐 profile：

- `reference`
- `builder`
- `tutorial`

### 7.2 交付场景

适合赛道延展：**交付智能化改进**

典型案例：

- 把实施手册蒸馏成排障 skill
- 把交付 FAQ 蒸馏成 troubleshooting 资产
- 把项目文档、Wiki、会议纪要沉淀成交付知识导航

推荐 profile：

- `troubleshooting`
- `internal-wiki`

### 7.3 培训场景

典型案例：

- 把新人培训材料蒸馏成 onboarding / tutorial skill
- 把规范、流程、指南蒸馏成学习路径型知识资产

推荐 profile：

- `tutorial`

### 7.4 企业知识问答场景

典型案例：

- 把制度、流程、FAQ 蒸馏成员工问答机器人可用的知识资产
- 把公司 Wiki 蒸馏成 internal-wiki / RAG 资产

推荐 profile：

- `internal-wiki`

### 7.5 产品创新场景

典型案例：

- 把 PRD、产品知识、术语表、FAQ 蒸馏成产品知识问答资产
- 把需求材料蒸馏成 AI 能直接消费的知识底座

推荐 profile：

- `general`
- `internal-wiki`

---

## 总结

Yonyou Doc2Skill 最值得强调的不是“能把文档做成 skill”，而是：

- 它是 **目标驱动的企业知识蒸馏引擎**
- 它是 **CLI-first 的可执行工具**
- 它支持 **自动提炼 + 定向蒸馏**
- 它把企业知识从文档、代码、Wiki、FAQ 中抽出来，转成 AI 能直接使用的资产

如果用于答辩或对外介绍，最推荐的核心表达是：

**同一份知识，按不同目标，蒸馏成不同资产。**
