# Yonyou Knowledge Delivery Boost 总览

## 1. 定位

**Yonyou Knowledge Delivery Boost** 是一个 **面向 AI 项目交付的知识接入提效 skill**。

它的重点不是通用研发蒸馏，而是解决交付环节里企业知识如何快速进入 AI 项目、问答系统和 RAG 链路的问题。

一句话定位：

**把企业文档、Wiki、FAQ 和案例快速接入 RAG，并同步沉淀为可复用的交付知识底座。**

---

## 2. 价值

### 2.1 对交付的价值

- 缩短企业知识进入 AI 项目的准备周期
- 降低实施同学手工整理 FAQ、案例、排障资料的成本
- 提高交付问答、排障、知识复盘的复用效率
- 让交付资料从“项目文档”升级为“可复用的交付知识底座”

### 2.2 对 AI 项目的价值

- 支持把交付资料结构化接入 RAG
- 输出 references、结构化 JSON 和 RAG 可消费数据
- 比直接把原始网页、PDF 扔进向量库更干净、更可控

### 2.3 对成本的价值

- 首次蒸馏更像一次离线建索引，**相对省 token**
- 后续问答、检索、复用时不需要反复投喂长文档
- 更适合企业长期积累和持续更新交付知识资产

---

## 3. 创新点

### 3.1 交付知识接入 + 资产化双目标

- 既解决企业知识如何接入 AI 项目
- 也解决交付资料如何长期复用和沉淀

### 3.2 自动提炼 + 定向蒸馏 + 增强模式

- **快速接入**：只给来源，先生成通用交付知识包
- **场景定向**：按交付问答、排障、RAG 接入等目标输出不同结果
- **增强模式**：对初始结果做 FAQ 化、场景化、案例化的二次优化

### 3.3 一份资料，多种交付结果

同一份交付资料可以同时输出：

- `internal-wiki`
- `troubleshooting skill`
- `references`
- `LangChain / LlamaIndex` RAG 数据

### 3.4 Skill + Runtime，而不是静态 Prompt

Yonyou Knowledge Delivery Boost 不是几句提示词，而是一套完整执行链路：

- 有 skill 入口
- 有本地执行器
- 有结构化抽取数据
- 有 references 参考文件
- 有最终生成的 `SKILL.md`
- 有后续导出的 RAG 数据

---

## 4. 包含功能

### 4.1 来源接入

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

### 4.2 结构化抽取

- 标题、章节、正文抽取
- 代码块抽取与语言识别
- 链接与参考资料归类
- references 分类输出
- 抽取结果 JSON 输出

### 4.3 交付资产生成

- 自动生成 `SKILL.md`
- 支持 `internal-wiki`、`troubleshooting` 等定向输出
- 支持自动 profile 判断
- 支持增强模式和后处理

### 4.4 RAG 接入

- 支持导出 `claude` skill 包
- 支持导出 `langchain` JSON
- 支持导出 `llama-index` JSON

---

## 5. 典型场景

- 把实施手册和 FAQ 整理成交付问答知识资产
- 把 Confluence 项目资料接入 RAG
- 把排障案例蒸馏成交付排障 skill
- 把项目复盘资料沉淀为可复用交付知识底座

---

## 6. 具体用法

### 6.1 生成交付问答资产

```bash
yonyou-doc2skill create ./delivery-faq.docx --name delivery-faq --profile internal-wiki --enhance-level 0
```

### 6.2 生成排障型知识资产

```bash
yonyou-doc2skill create ./implementation-guide.pdf --name delivery-troubleshooting --profile troubleshooting --enhance-level 0
```

### 6.3 从 Confluence 生成

```bash
yonyou-doc2skill confluence \
  --base-url https://wiki.example.com \
  --space-key TEAM \
  --token 'YOUR_TOKEN' \
  --name team-delivery-wiki
```

### 6.4 接入 RAG

```bash
yonyou-doc2skill package output/delivery-faq --target langchain
yonyou-doc2skill package output/delivery-faq --target llama-index
```

### 6.5 增强模式

```bash
yonyou-doc2skill enhance output/delivery-faq --agent codex
```
