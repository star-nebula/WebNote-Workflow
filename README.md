# WebNote-Workflow · 网页笔记四步工作流

> 把"存好正文 → 整理分类 → 提炼笔记 → 确认发布"拆成四个 Agent 分工协作。你丢给任何 AI 工具（WorkBuddy、Codex、Claude Code），它都能自动创建这四个 Agent 并完成任务。

[English](#english) · [中文文档](#中文文档)

---

## 中文文档

### 项目简介

WebNote-Workflow 是一套**以"可信"为核心的网页内容整理工作流**。它的目标不是帮你更快地生产，而是帮你**更可靠地把网页内容变成自己的知识**。

你先用现成工具把网页正文存好，再把这批内容交给四个 Agent 接力处理：

1. **整理** —— 把存好的正文登记成清单，做初步分类
2. **提炼** —— 从正文中提取结构化要点，写成个人笔记
3. **核查** —— 拿笔记逐条回到原文比对，专抓 AI 编造的内容
4. **确认** —— 汇总成"待确认提案"，你逐条点确认后才落地

### 为什么是四步，而不是一步

分工不是为了显得高级，是为了**隔离上下文、隔离责任、隔离风险**：

- 提炼的不能自己核查自己——它查不出自己刚才脑补了什么
- 核查的不能替你删东西——它只标"可疑"，不替你决定
- 确认的只出提案、不自动落地——最后那个确认键一直在你手里

一个 Agent 从头干到尾，AI 编的内容你根本发现不了。四个 Agent 各管一段，每一段都有独立上下文，"想包庇自己都做不到"。

### 功能说明

| 阶段 | Agent | 输入 | 输出 | 关键约束 |
|------|-------|------|------|---------|
| 1 | 整理 | 已存好的网页（标题+网址+正文） | `01-整理清单.md`（清单 + 四选一分类） | 不抓网页、不脑补、只归类 |
| 2 | 提炼 | 有正文的页面内容 | `02-笔记.md`（3–5 条要点 + 保留理由 + 修订建议） | 只依据正文，标注出处 |
| 3 | 核查 | 原文 + 笔记 | `03-核查表.md`（已核实 / 可疑） | 必须独立 Agent，逐条比对 |
| 4 | 确认 | 前三道产出 | `04-待确认提案.md`（建议动作） | 全部停在"待确认" |

四选一分类：

- **学习**：有能直接上手的技术、方法或知识
- **借鉴**：写法、结构、表达方式值得参考
- **内容补充**：能给我手头某个选题补事实或数据
- **可归档**：信号低、已经掌握、或重复

### 目录结构

```
WebNote-Workflow/
├── Webpage note workflow.md            # 工作流主文档（Agent 职责 / 输入输出 / 铁律）
├── Prompt-Multi-Agent.md               # 多 Agent 版系统提示词（调度器）
├── Prompt-Single-Dialog.md             # 单对话框版系统提示词（分段交付）
├── BrowserSkill Installation Guide.md  # BrowserSkill 安装指南
├── BrowserSkill Command Reference.md   # bsk CLI 命令速查
├── runs/                               # 每次运行的产出目录
│   └── YYYY-MM-DD-主题/
│       ├── content/                    # 你提供的原文（只读）
│       ├── 01-整理清单.md
│       ├── 02-笔记.md
│       ├── 03-核查表.md
│       └── 04-待确认提案.md
├── posts/                              # 可发布到博客平台的内容
└── README.md
```

### 使用方法

#### 0. 前置准备：存好正文 + 装好 BrowserSkill

正文**不让 AI 现去抓**——直接抓十有八九抓不全，付费墙和需登录的页更抓不到。用以下任一方式把正文存好：

- **BrowserSkill**：腾讯开源的浏览器桥接，操控你已登录的浏览器读取页面（[安装指南](BrowserSkill%20Installation%20Guide.md)）
- **Obsidian 网页剪藏 / 简悦 / Cubox / Readwise Reader** 等稍后读工具
- **手动复制粘贴**：最稳的方式

#### 1. 多 Agent 版（推荐，支持 subagent 的工具）

把 [`Prompt-Multi-Agent.md`](Prompt-Multi-Agent.md) 作为系统提示，连同 [`Webpage note workflow.md`](Webpage%20note%20workflow.md) 一起提供给 AI（WorkBuddy / Codex / Claude Code）。AI 会按文档自动创建四个独立 subagent 并依次接力。

#### 2. 单对话框版（零门槛）

把 [`Prompt-Single-Dialog.md`](Prompt-Single-Dialog.md) 作为系统提示。单个对话里 AI 自己提炼又自己核查等于自检，所以必须**分段交付**：

- 第一段：整理 + 提炼 → 停下
- 第二段：新开对话，粘贴核查提示词 + 原文 + 笔记 → 产出核查表
- 第三段：回到原对话，产出待确认提案

> 核查必须换新对话，否则查不出自己编的内容。

#### 3. 文件流水线（Claude Code / Codex / WorkBuddy）

把四个 Agent 做成四个 subagent，按文件流水线跑：读取你提供的原文文件 → 写出 `runs/<本次子目录>/` 下的四个文件。每次运行一个子目录（`YYYY-MM-DD-主题`），多次运行互不覆盖，原文只读不改。

输入可用 JSON 格式引用原文路径（不复制）：

```json
[
  {
    "id": "p01",
    "title": "某数据库年度报告",
    "domain": "example.org",
    "url": "example.org/db-report-2026",
    "source_path": "E:/notes/webpages/db-report-2026.md"
  },
  {
    "id": "p02",
    "title": "上下文工程演讲",
    "domain": "youtube.com",
    "url": "youtube.com/watch?v=xxxx",
    "source_path": null
  }
]
```

`source_path` 为 `null` 即表示无正文。

### 确认边界：什么 AI 能自动做，什么必须等你

这套分工最重要的不是自动化，是**可控的自动化**。判断标准很简单：**这个动作如果错了，撤得回来吗？**

| 必须停在"待确认" | 可以让 AI 直接干 |
|------------------|------------------|
| 删除 / 归档 / 移动资料 | 读、归类、提要点 |
| 发布（文章 / 社交媒体） | 列清单、出提案 |
| 改长期记忆 / 知识库 | 给建议、做对比、标可疑 |

**一句话：AI 可以无限地"想"和"建议"，但凡要"落地动手"，停在你这道闸前。**

### 参考

- 设计参考：[Agent OS 的第一课：会分工，才会用 Agent](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division)
- 工具依赖：[BrowserSkill（腾讯开源）](https://github.com/Tencent/BrowserSkill)

### 许可证

MIT

---

## English

> *The section below is a brief summary. For the full documentation — detailed usage, directory structure, I/O formats, and confirmation boundaries — see the Chinese section above.*

### Overview

WebNote-Workflow is a **trust-first** pipeline for turning saved web content into reliable personal notes. You save page text with existing tools, then hand the batch to four agents that run in sequence:

1. **Organize** — register saved pages into an inventory with a first-pass classification
2. **Distill** — extract structured key points into personal notes
3. **Verify** — check each note against the original text, catching AI fabrications
4. **Confirm** — summarize into a "pending-confirmation proposal" you approve item by item

### Why four steps, not one

The split exists for **context isolation, responsibility isolation, and risk isolation**:

- The distiller cannot verify itself — it can't catch what it just hallucinated
- The verifier cannot delete for you — it only flags "suspicious", it doesn't decide
- The confirmer only proposes, never executes — the final confirm button stays with you

Four agents, each with a clean context, simply cannot cover for themselves.

### Quick start

1. Save page text (BrowserSkill / clipper / copy-paste).
2. Use [`Prompt-Multi-Agent.md`](Prompt-Multi-Agent.md) as the system prompt together with [`Webpage note workflow.md`](Webpage%20note%20workflow.md) for tools that support subagents.
3. Or use [`Prompt-Single-Dialog.md`](Prompt-Single-Dialog.md) for a single-dialog, segment-by-segment flow.

### Confirmation boundary

Any delete / archive / publish / long-term-memory write stops at "pending confirmation" — the AI proposes, you press the button.

### License

MIT
