# Yonyou Doc2Skill 答辩精简版

## 1. 项目是什么

Yonyou Doc2Skill 是一个 **目标驱动的企业知识蒸馏引擎**，也是一个 **CLI-first 的企业知识资产生成工具**。

它能够把企业文档、代码仓库、Wiki、FAQ、交付资料等来源，自动蒸馏成可直接被 AI 使用的 skill、知识包和结构化资产。

一句话概括：

**把企业知识从“文档存量”变成“可执行资产”。**

---

## 2. 项目解决什么问题

企业里最常见的问题不是“没有文档”，而是：

- 文档很多，但分散在仓库、Wiki、PDF、FAQ、聊天记录里
- AI 虽然能回答问题，但缺少稳定上下文，经常答非所问
- 同一份知识需要反复整理、反复复制给不同人和不同工具

Yonyou Doc2Skill 解决的是“企业知识如何稳定进入 AI”的问题。

它把原始资料先做一次知识蒸馏，转换成结构化资产，后续就能持续复用，而不是每次都重新把大段文档塞给模型。

---

## 3. 为什么它不只是一个文档转 Skill 工具

我们认为它的创新点不在“把文档变成一个 skill”，而在两件事：

### 第一，支持两种模式

- **自动提炼**：只给来源，快速生成一个通用 skill
- **定向蒸馏**：补一句目标，例如“给 Codex 做编码规范 skill”，系统就按目标输出更适合场景的结果

### 第二，同源多产物

同一份知识，不只会生成一个通用版本，而是可以面向不同目标输出不同资产：

- 面向研发：`reference` / `builder` / `tutorial`
- 面向交付：`troubleshooting`
- 面向知识问答：`internal-wiki`

也就是说，它不是静态摘要工具，而是一个 **同源多产物的知识蒸馏引擎**。

---

## 4. 它怎么落地

Yonyou Doc2Skill 不是几句提示词，而是一套完整执行链路：

1. 接入来源  
   文档网站、GitHub 仓库、本地代码库、PDF、Word、HTML、PPT、Confluence、聊天记录等

2. 抽取与整理  
   提取标题、章节、正文、代码块、参考链接，分类生成 references

3. 生成知识资产  
   生成 `SKILL.md`、references、结构化中间数据

4. 面向不同目标输出  
   给研发、交付、培训、问答等不同场景提供不同形态的结果

它的交互是 skill 入口，但底层是可执行的本地 runtime 和 CLI，所以它不是 PPT 式概念，而是可以真正运行和交付的工具。

---

## 5. 典型场景

### 研发提效场景

- 把《用友专业开发红皮书》蒸馏成给 Codex 使用的编码规范 skill
- 把研发规范站点蒸馏成查询型 `reference skill`
- 把代码仓库和规范文档联合蒸馏成 `builder skill`

### 交付场景

- 把实施手册蒸馏成排障型 `troubleshooting skill`
- 把项目 FAQ、Wiki、经验资料蒸馏成交付知识资产

### 培训与知识问答场景

- 把培训资料蒸馏成 onboarding/tutorial skill
- 把制度、流程、FAQ 蒸馏成 internal-wiki / RAG 资产

---

## 6. 为什么值得做

它带来的价值主要有四点：

- 降低知识整理和 AI 接入门槛
- 提升研发和交付知识复用效率
- 减少 AI 使用中的上下文缺失和答非所问
- 让企业知识从“文档沉淀”升级为“资产化、可执行化”

尤其是在成本上，它的思路不是“每次问都重新喂长文档”，而是 **前置一次知识蒸馏，后续持续低 token 复用**。

---

## 7. CLI 怎么用

Yonyou Doc2Skill 的底层是一个 CLI-first 执行引擎，最常用的是这几类命令：

### 7.1 生成 skill

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-reference --profile reference --enhance-level 0
```

含义：

- `create`：从来源生成 skill
- `--name`：指定产物名称
- `--profile`：指定蒸馏目标形态
- `--enhance-level 0`：先关闭增强，快速看产物

### 7.2 生成交付 / Wiki 资产

```bash
yonyou-doc2skill confluence \
  --base-url https://wiki.example.com \
  --space-key TEAM \
  --token 'YOUR_TOKEN' \
  --name team-wiki
```

### 7.3 打包

```bash
yonyou-doc2skill package output/nextjs-reference
```

常见目标格式示例：

```bash
yonyou-doc2skill package output/nextjs-reference --target claude
yonyou-doc2skill package output/nextjs-reference --target langchain
yonyou-doc2skill package output/nextjs-reference --target llama-index
```

含义：

- `--target claude`：打包成 Claude / skill 侧可消费格式
- `--target langchain`：导出为 LangChain RAG 可消费格式
- `--target llama-index`：导出为 LlamaIndex RAG 可消费格式

### 7.4 常见 profile

- `reference`：查询型研发知识
- `builder`：给 AI 编码助手使用的实施型知识
- `tutorial`：学习路径 / onboarding
- `troubleshooting`：排障和 FAQ
- `internal-wiki`：企业知识问答 / Wiki 资产
- `general`：通用型

### 7.5 最常见的使用方式

#### 快速模式

```bash
yonyou-doc2skill create https://docs.example.com --name example-skill
```

只给来源，系统自动提炼一个通用 skill。

#### 目标模式

```bash
yonyou-doc2skill create https://docs.example.com --name example-skill --profile builder
```

给来源再加一个明确目标，让系统输出更贴场景的结果。

#### RAG 模式

先蒸馏，再打包：

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-rag --enhance-level 0
yonyou-doc2skill package output/nextjs-rag --target langchain
```

或者：

```bash
yonyou-doc2skill create https://nextjs.org/docs --name nextjs-rag --enhance-level 0
yonyou-doc2skill package output/nextjs-rag --target llama-index
```

这条链路的含义是：

- 先把原始来源蒸馏成结构化知识资产
- 再导出成 RAG 框架可直接使用的格式
- 比直接把原始网页/PDF 扔进向量库更干净、更适合检索

---

## 8. 最适合答辩时的一句话

**Yonyou Doc2Skill 是一个目标驱动的企业知识蒸馏引擎，它把企业文档、代码、Wiki 和交付资料，自动转化成可直接被 AI 使用的 skill 和知识资产，让同一份知识可以面向研发、交付、培训和问答场景持续复用。**

---

## 9. 30 秒介绍版

Yonyou Doc2Skill 解决的是“企业知识怎么真正进入 AI”这个问题。  
它不是简单做摘要，而是把文档、代码仓库、Wiki、交付资料等来源，蒸馏成可直接被 AI 使用的 skill 和知识资产。  
它既支持自动提炼，也支持定向蒸馏，同一份知识可以面向研发、交付、培训和问答输出不同结果。  
所以它的价值不是“又一个 prompt 工具”，而是把企业知识从文档存量变成可执行资产。

---

## 10. 2 分钟介绍版

在企业里，问题通常不是没有文档，而是知识太分散，散落在代码仓库、Wiki、PDF、FAQ 和聊天记录里。  
AI 工具虽然越来越强，但如果没有稳定、结构化的上下文，它依然容易答非所问。  

Yonyou Doc2Skill 的核心就是把这些原始资料做一次知识蒸馏，转换成 AI 能直接消费的 skill、references 和结构化资产。  
它有两个关键创新点：第一，支持自动提炼和定向蒸馏双模式；第二，支持同源多产物，同一份知识可以根据目标不同，输出成研发 reference skill、编码 builder skill、交付 troubleshooting skill，或者 internal-wiki / RAG 资产。  

所以它不是一个简单的文档转 skill 工具，而是一个目标驱动的企业知识蒸馏引擎。  
它能帮助企业把原本静态、分散的知识，真正转化成可执行、可复用、可被 AI 消费的资产。
