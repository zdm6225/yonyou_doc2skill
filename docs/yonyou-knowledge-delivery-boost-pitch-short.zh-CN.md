# Yonyou Knowledge Delivery Boost 答辩精简版

## 1. 项目是什么

Yonyou Knowledge Delivery Boost 是一个面向 **AI 项目交付** 的知识接入提效 skill。

它能够把企业文档、Wiki、FAQ、案例、实施资料等来源，快速整理成可直接被 AI 使用的交付知识资产和 RAG 数据。

一句话概括：

**把企业文档、Wiki、FAQ 和案例快速接入 RAG，并同步沉淀为可复用的交付知识底座。**

---

## 2. 项目解决什么问题

在 AI 项目交付里，最常见的问题不是没有资料，而是：

- 实施手册、FAQ、案例、Wiki 分散在多个位置
- 交付同学反复手工整理、复制、解释同一批知识
- AI 问答系统没有稳定知识底座，结果不稳定
- RAG 接入常常停留在“把原始文档直接扔进向量库”

Yonyou Knowledge Delivery Boost 解决的是“企业知识如何稳定、高效进入 AI 项目交付”的问题，重点是压缩知识准备周期，而不是只做一个结果展示工具。

---

## 3. 为什么它不只是一个 RAG 预处理工具

它的重点不是只做 chunk，而是同时解决三件事：

- **知识接入**：把文档、Wiki、FAQ、案例接入 AI 项目
- **知识整理**：沉淀为 references、skill、结构化数据
- **知识复用**：服务交付问答、排障、复盘和后续项目

所以它不是只做技术数据加工，而是面向交付场景的知识接入与复用提效 skill。

---

## 4. 它怎么落地

1. 接入来源  
   文档、Confluence、FAQ、案例、公开资料

2. 抽取与整理  
   提取标题、正文、FAQ、代码块、参考链接，分类生成 references

3. 生成交付知识资产  
   生成 `SKILL.md`、references、结构化 JSON

4. 导出到 AI 链路  
   导出为 `langchain` / `llama-index` 等 RAG 可消费格式

---

## 5. 典型场景

- 把实施手册蒸馏成排障型 `troubleshooting skill`
- 把 FAQ、Wiki 蒸馏成交付问答型 `internal-wiki` 资产
- 把项目案例、经验文档接入 RAG
- 把项目资料沉淀为可复用的交付知识底座

---

## 6. CLI 怎么用

### 6.1 生成交付知识资产

```bash
yonyou-doc2skill create ./delivery-faq.docx --name delivery-faq --profile internal-wiki --enhance-level 0
```

### 6.2 生成排障资产

```bash
yonyou-doc2skill create ./implementation-guide.pdf --name delivery-troubleshooting --profile troubleshooting --enhance-level 0
```

### 6.3 接入 Confluence

```bash
yonyou-doc2skill confluence \
  --base-url https://wiki.example.com \
  --space-key TEAM \
  --token 'YOUR_TOKEN' \
  --name team-delivery-wiki
```

### 6.4 导出到 RAG

```bash
yonyou-doc2skill package output/delivery-faq --target langchain
yonyou-doc2skill package output/delivery-faq --target llama-index
```

### 6.5 增强模式

```bash
yonyou-doc2skill enhance output/delivery-faq --agent codex
```

---

## 7. 最适合答辩时的一句话

**Yonyou Knowledge Delivery Boost 面向 AI 项目交付，把企业文档、Wiki、FAQ 和案例快速接入 RAG，并同步沉淀为可复用的交付知识底座，提升交付知识接入效率、问答稳定性和长期复用能力。**
