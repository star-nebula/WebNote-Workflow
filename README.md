# WebNote-Workflow · 网页笔记工作流

> 把"内容采集 → 整理分类 → 提炼笔记 → 确认发布"拆成**调度器（主会话） + 三个独立 Agent** 分工协作。确定性的事调度器（主会话）自己干，只有真正需要独立判断的才交给 subagent。

[English](#english) · [中文文档](#中文文档)

---

## 中文文档

### 项目简介

WebNote-Workflow 是一套**以"可信"为核心的网页内容整理工作流**。它的目标不是帮你更快地生产，而是帮你**更可靠地把网页内容变成自己的知识**。

> 本项目在 [Axton Liu《Agent OS 的第一课：会分工，才会用 Agent》](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division) 一文的理念启发下自行实现与改进，落地成一套可直接复用、按文件流水线运行的工作流。原文为付费 Newsletter，本仓库仅借鉴其"分工隔离 / 独立核查 / 确认闸门"三层设计思路，所有文档与提示词均为独立撰写。

### 架构

**不是每一步都需要独立的 AI 上下文。** 确定性的事调度器（主会话）自己干，只有真正需要独立判断的才交给 subagent：

```
调度器（主会话）
├── 1. 采编（主会话自己做——URL 正则 + CLI 工具提取文本）
│      → 产出 00-采编清单.md
│
├── 2. 归类师（独立 subagent——四选一语义分类）
│      → 产出 01-整理清单.md
│
├── 3. 笔记匠（独立 subagent——提取 3~5 条核心要点）
│      → 产出 02-笔记.md
│
├── 4. 核查官（全新 subagent——逐条比对原文 vs 笔记）
│      → 产出 03-核查表.md
│
└── 5. 确认（主会话自己做——汇总提案，全部停在待确认）
       → 产出 04-待确认提案.md
```

**为什么有些步骤不是独立 Agent：**

| 步骤 | 是否独立 | 理由 |
|------|---------|------|
| 采编 | ❌ 主会话内化 | URL 分类用正则，文本提取调用 CLI 工具——确定性逻辑不需要 AI |
| 归类师 | ✅ 独立 | 四选一分类需要理解正文语义，归类师的判断不应影响笔记匠 |
| 笔记匠 | ✅ 独立 | 核心创作任务，需要完整上下文专注正文 |
| 核查官 | ✅ **必须独立** | 安全闸门——笔记匠自己核查自己等于自检，查不出自己编了什么 |
| 确认 | ❌ 主会话内化 | 不读原文、不做新判断，只是汇总 + 约束落地行为 |

### 功能说明

| 阶段 | 执行者 | 输入 | 输出 | 关键约束 |
|------|--------|------|------|---------|
| 采编 | 调度器（主会话） | 原始 URL + 已有正文 | `00-采编清单.md` | 正则分类 + CLI 工具，不依赖 AI |
| 归类师 | subagent | 采编清单中有正文的内容 | `01-整理清单.md` | 只归类，不提炼 |
| 笔记匠 | subagent | 整理清单中有正文的页面 | `02-笔记.md` | 只依据正文，标注出处 |
| 核查官 | subagent（全新） | 原文 + 笔记 | `03-核查表.md` | **必须独立 Agent**，逐条比对 |
| 确认 | 调度器（主会话） | 前四道产出 | `04-待确认提案.md` | 全部停在"待确认" |

四选一分类：

- **学习**：有能直接上手的技术、方法或知识
- **借鉴**：写法、结构、表达方式值得参考
- **内容补充**：能给我手头某个选题补事实或数据
- **可归档**：信号低、已经掌握、或重复

### 目录结构

```
WebNote-Workflow/
├── Webpage note workflow.md            # 工作流主文档（完整五步定义）
├── Prompt-Multi-Agent.md               # 多 Agent 版系统提示词（主会话）
├── Prompt-Single-Dialog.md             # 单对话框版系统提示词（分段交付）
├── tools/                              # 采编阶段的确定性工具
│   ├── extract-document.py             # PDF/DOCX 文本提取
│   ├── extract-webpage.py              # BrowserSkill 图文页面提取
│   ├── extract-video-text.py           # BrowserSkill 视频页面提取
│   ├── extract-video-asr.py            # 视频 ASR 语音转写（faster-whisper）
│   ├── extract-video-frames.py         # 视频画面采集（抽帧+OCR+云端 Vision 语义）
│   └── ds_vision.py                    # DeepSeek Vision 多图理解（被画面采集调用）
├── BrowserSkill Installation Guide.md  # BrowserSkill 安装指南
├── BrowserSkill Command Reference.md   # bsk CLI 命令速查
├── runs/                               # 每次运行的产出目录
│   └── YYYY-MM-DD-主题/
│       ├── 00-采编清单.md               # 调度器（主会话）产出
│       ├── 01-整理清单.md               # 归类师产出
│       ├── 02-笔记.md                   # 笔记匠产出
│       ├── 03-核查表.md                 # 核查官产出
│       └── 04-待确认提案.md             # 调度器（主会话）产出
├── posts/                              # 可发布到博客平台的内容
└── README.md
```

### 使用方法

#### 0. 前置准备：先把正文存好（工具自选）

正文**由你自己存好，本工作流不去抓网页**——直接让 AI 现抓十有八九抓不全，付费墙和需登录的页更抓不到。**用哪种工具、用不用，完全由你决定**，以下任选其一即可：

- **手动复制粘贴**：最稳，零依赖
- **Obsidian 网页剪藏 / 简悦 / Cubox / Readwise Reader** 等稍后读工具
- **BrowserSkill（可选）**：腾讯开源的浏览器桥接，可操控你已登录的浏览器读取页面，适合需要登录态的批量抓取（[安装指南](BrowserSkill%20Installation%20Guide.md)）。**并非必需**，只是其中一种方式

#### 1. 多 Agent 版（推荐，支持 subagent 的工具）

把 [`Prompt-Multi-Agent.md`](Prompt-Multi-Agent.md) 作为系统提示，连同 [`Webpage note workflow.md`](Webpage%20note%20workflow.md) 一起提供给 AI（WorkBuddy / Codex / Claude Code）。AI 会按文档自动：
- 调度器（主会话）执行采编（确定性逻辑）
- 创建 3 个独立 subagent：归类师 → 笔记匠 → 核查官（全新上下文）
- 调度器（主会话）执行确认（汇总提案）

#### 2. 单对话框版（零门槛）

把 [`Prompt-Single-Dialog.md`](Prompt-Single-Dialog.md) 作为系统提示。分三段交付：

- **第一段**：调度器（主会话）做采编 + 归类师 + 笔记匠 → 产出 00、01、02 → **停下**
- **第二段**：新开对话，粘贴核查官提示词 + 原文 + 笔记 → 产出 03-核查表
- **第三段**：调度器（主会话）汇总 00+01+02+03 → 产出 04-待确认提案

> 核查必须换新对话，否则查不出自己编的内容。

#### 3. 文件流水线

五个文件并列写入 `runs/<本次子目录>/`，调度器（主会话） + 3 个 subagent 接力。原文不复制、不移动，仅在清单中记录来源路径。多次运行互不覆盖。

输入可用 JSON 格式引用原文路径（不复制）：

```json
[
  {
    "id": "p01",
    "title": "某数据库年度报告",
    "domain": "example.org",
    "url": "https://example.org/db-report-2026",
    "source_path": "E:/notes/webpages/db-report-2026.md"
  },
  {
    "id": "p02",
    "title": "上下文工程演讲",
    "domain": "youtube.com",
    "url": "https://youtube.com/watch?v=xxxx",
    "source_path": null
  }
]
```

`source_path` 为 `null` 即表示无正文。

### 确认边界

AI 出提案，你按确认键。判断标准：**这个动作如果错了，撤得回来吗？**

| 必须停在"待确认" | 可以让调度器（主会话）直接干 |
|------------------|------------------|
| 删除 / 归档 / 移动资料 | URL 正则分类、调用 CLI 工具 |
| 发布（文章 / 社交媒体） | 读、归类、提要点 |
| 改长期记忆 / 知识库 | 列清单、出提案、给建议 |

**一句话：AI 可以无限地"想"和"建议"，但凡要"落地动手"，停在你这道闸前。**

### 参考

- 设计参考：[Agent OS 的第一课：会分工，才会用 Agent](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division)
- 工具依赖：[BrowserSkill（腾讯开源）](https://github.com/Tencent/BrowserSkill)

### 许可证与致谢

- 本仓库的文档与提示词采用 **MIT** 许可证，详见 [LICENSE](LICENSE)。你可自由使用、修改、再分发。
- 设计理念致谢 [Axton Liu《Agent OS 的第一课：会分工，才会用 Agent》](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division)。原文为付费内容，本项目仅借鉴其公开阐述的设计思路，未包含其原文正文或配套提示词包。

---

## English

> *The section below is a brief summary. For the full documentation — detailed usage, directory structure, I/O formats, and confirmation boundaries — see the Chinese section above.*

### Overview

WebNote-Workflow is a **trust-first** pipeline for turning saved web content into reliable personal notes. It uses a hybrid architecture: deterministic tasks (media format classification, text extraction, confirmation) are handled by the scheduler itself, while only the tasks that truly need independent AI judgment are delegated to subagents.

```
Scheduler (your AI tool)
├── 1. Collection (scheduler itself — regex + CLI tools)
├── 2. Classifier (subagent — semantic 4-way classification)
├── 3. Distiller (subagent — extract key points)
├── 4. Verifier (new subagent — compare notes against original)
└── 5. Confirmation (scheduler itself — summarize proposal, all pending)
```

Only **3 subagents** instead of 5 — the scheduler handles deterministic steps itself.

### Quick start

1. Save page text (BrowserSkill / clipper / copy-paste).
2. Use [`Prompt-Multi-Agent.md`](Prompt-Multi-Agent.md) as the system prompt together with [`Webpage note workflow.md`](Webpage%20note%20workflow.md) for tools that support subagents.
3. Or use [`Prompt-Single-Dialog.md`](Prompt-Single-Dialog.md) for a single-dialog, segment-by-segment flow.

### Confirmation boundary

Any delete / archive / publish / long-term-memory write stops at "pending confirmation" — the AI proposes, you press the button.

### License

MIT — see [LICENSE](LICENSE). Design credit: [Axton Liu, "Agent OS 的第一课"](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division) (ideas only; no original text reproduced).
