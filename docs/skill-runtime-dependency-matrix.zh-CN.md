# Yonyou Doc2Skill 运行时依赖矩阵

本文说明各场景依赖什么能力、哪些能随 skill 自动初始化、哪些需要宿主环境额外提供。

## 总结

- 基础蒸馏能力：主要依赖 skill 内嵌 Python runtime 自动初始化。
- 高级能力：会按场景追加浏览器、OCR、视频或本地 agent 能力。
- 不是所有能力都能简单说成“都是 Python”。

## 场景依赖矩阵

| 场景 | 主要命令 | Skill 自动初始化的 Python 依赖 | 额外系统/宿主依赖 | 是否纯 Python | 备注 |
|---|---|---|---|---|---|
| 文档站/公开网站蒸馏 | `create <url>` | `requests` `beautifulsoup4` `httpx` | 无 | 基本是 | 静态站点直接可用 |
| 动态网站/SPA 蒸馏 | `create <url> --browser` | `playwright` | Chromium 浏览器运行时 | 否 | 需要 `playwright install chromium` |
| GitHub 仓库蒸馏 | `create owner/repo` | `PyGithub` `GitPython` | `git` | 否 | 代码里直接 `git clone` |
| 本地代码库蒸馏 | `create ./repo` | Python 核心依赖 | 无 | 是 | 只要能读目录即可 |
| PDF 蒸馏 | `create xxx.pdf` | `PyMuPDF` | 无 | 是 | 文本型 PDF 直接可用 |
| Word 蒸馏 | `create xxx.docx` | `mammoth` `python-docx` | 无 | 是 | `.docx` 支持好，`.doc` 不算完整支持 |
| PPT 蒸馏 | `create xxx.pptx` | `python-pptx` | 无 | 是 | 主要抽文本、表格、备注、图片信息 |
| HTML / AsciiDoc 蒸馏 | `create xxx.html/.adoc` | 解析相关 Python 包 | 无 | 是 | 本地文件直读 |
| 视频基础蒸馏 | `create <video>` | `yt-dlp` `youtube-transcript-api` | 网络访问 | 基本是 | 偏元数据/字幕抽取 |
| 视频深度蒸馏 | 视频增强链路 | `faster-whisper` `opencv-python-headless` `pytesseract` | `tesseract`，可能还需要更强硬件 | 否 | 视觉/OCR/本地转写更重 |
| Confluence 蒸馏 | `confluence ...` | `requests` `beautifulsoup4` | 可用认证 | 基本是 | 认证通过后直接调用 REST/API 页面 |
| iKM 蒸馏 | `ikm --mode ...` | `requests` `beautifulsoup4` | 可用 `cookie` | 基本是 | 附件解析仍走 Python 侧 |
| chat 导出蒸馏 | `chat --export-path ...` | `slack-sdk` 等 | 无 | 是 | 依赖导出文件质量 |
| 普通增强 | `enhance output/...` | `anthropic` / `openai` 客户端 | API Key 或本地 agent CLI | 否 | 两种模式二选一 |
| LOCAL 增强 | `enhance ... --agent codex` | Python 命令框架 | `codex` / `claude` / `copilot` / `opencode` CLI | 否 | 依赖宿主 PATH 里存在对应命令 |
| API 增强 | `enhance ... --target claude/openai` | `anthropic` `openai` | 对应 API Key、网络 | 否 | 最适合托管环境 |
| 文本型脱敏 | `sanitize` / `sanitize-assets` | `PyMuPDF` `python-docx` 等 | 无 | 基本是 | 文本、Office、PDF 文本层可直接处理 |
| 图片/截图脱敏 | `sanitize-assets apply --ocr-engine ...` | `rapidocr` / `paddleocr` / `pytesseract` `opencv-python-headless` | `tesseract`（若走该引擎） | 否 | OCR 引擎不同，依赖不同 |
| Logo 脱敏 | `sanitize-assets logo-scan` | `opencv-python-headless` `numpy` | 无 | 基本是 | 主要靠模板匹配 |
| 扫描版 PDF 脱敏 | `sanitize-assets apply/verify` | `PyMuPDF` + OCR 相关包 | `tesseract` 或更强 OCR 环境 | 否 | 是否稳定取决于 OCR 能力 |
| Visio `.vsdx` 脱敏 | `sanitize-assets apply` | `zipfile` + XML 处理 + 图像脱敏链路 | 图片脱敏时仍可能需要 OCR/OpenCV | 基本不是纯 Python 闭环 | 文本替换是 Python，图像部分依赖 OCR/OpenCV |
| RAG 导出 | `package --target langchain/llama-index` | `langchain` `llama-index` | 无 | 是 | 导出本身是 Python |

## 哪些依赖会跟 skill 一起走

skill 包里当前会带：

- `SKILL.md`
- `package.json`
- `requirements.txt`
- `scripts/`
- `runtime/`
- `templates/`

其中：

- `requirements.txt` 里的依赖，会在首次运行时由 skill 自己的 `.runtime/.venv` 自动安装。
- 但系统二进制和宿主命令不会被 skill 自动“打进包里”。

## 哪些能力不是 skill 自己能完全打包的

### 1. `git`

GitHub 仓库蒸馏实际会执行 `git clone`，所以宿主环境必须有 `git`。

### 2. Playwright Chromium

动态网站蒸馏除了 Python 包 `playwright`，还需要 Chromium 浏览器运行时。

### 3. `tesseract`

如果 OCR 回退或指定走 `pytesseract`，宿主环境必须安装 `tesseract` 二进制。

### 4. 本地 agent CLI

如果增强模式走 LOCAL agent：

- `codex`
- `claude`
- `copilot`
- `opencode`

这些命令必须存在于宿主环境 PATH。

## 上传到 OpenClaw 后，增强模式还能不能用

结论分两种。

### 情况 A：走 API 增强

可以，只要 OpenClaw 的 skill 执行环境满足：

- 能访问外网
- 注入了可用的 API Key
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - 或其他受支持 provider 的 key

这时增强模式仍可用，因为它本质上是 Python 客户端调用远端模型。

### 情况 B：走 LOCAL agent 增强

通常不能直接假设可用。

因为 LOCAL 增强依赖宿主机本身装了对应 CLI，例如：

- `codex`
- `claude`

如果 OpenClaw 只是“加载一个 skill 包并运行 Python 脚本”，但运行容器里并没有这些命令，那 LOCAL 增强就会失败。

### 最稳妥的对外口径

如果 skill 要上传到 OpenClaw 或类似托管平台，建议这样表述：

- 基础蒸馏、Confluence、iKM、普通脱敏：可直接运行
- 增强模式：优先按 API 模式接入
- LOCAL agent 增强：只在宿主环境预装 agent CLI 时可用

## OpenClaw 场景建议

| 部署场景 | 建议增强方式 | 原因 |
|---|---|---|
| 你自己本机 / Codex 本机 | LOCAL `--agent codex` | 你本机已经有 agent CLI，成本最低 |
| OpenClaw 托管 skill | API 增强 | 不依赖宿主机预装 `codex` / `claude` |
| 客户现场离线环境 | 关闭增强或改本地预装 agent | API 不一定可达 |

## 最后一句结论

不要把整个产品描述成“都是 Python”。

更准确的说法是：

> 基础能力主要由 skill 内嵌 Python runtime 自动初始化；高级能力会按场景依赖浏览器、OCR、系统二进制或本地/远端 AI agent。
