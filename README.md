# WebNote-Workflow · 网页笔记工作流

> 把"内容采集 → 整理分类 → 提炼笔记 → 确认发布"拆成**调度器（主会话） + 三个独立 Agent** 分工协作。确定性的事调度器（主会话）自己干（画面采集为可选 AI 增强），只有真正需要独立判断的才交给 subagent。

[English](README.en.md) · [中文文档](#目录结构)

---

## 快速开始：两条路径

本项目以 **`skills/webnote-workflow`（总编排 skill）** 为 AI 入口——完整工作流（五步流程 + 视频画面采集 + 确认边界）的方法论都封装在其中。任选一条路径：

**路径 A · 装配（推荐）**：把项目内 `skills/` 目录装进你的 AI 工具，之后**自然对话即触发**——直接说"把这个网页整理成笔记"，AI 自动加载 webnote-workflow skill 并按流程执行。

- WorkBuddy / Codex / Claude Code：把 `<项目>/skills/` 链接或复制到该工具的项目级 skills 目录（如 `.workbuddy/skills/`、`.codex/skills/`、`.claude/skills/`）
- 若工具不支持项目级 skill：退化为每次复制下方"路径 B"提示词

**路径 B · 兜底（不装配也能用）**：把下面这段复制给你的 AI（WorkBuddy / Codex / Claude Code）：

```
你正在使用「WebNote-Workflow」网页笔记工作流，项目在 <当前项目目录>。
先读取 skills/webnote-workflow/SKILL.md 获取编排与两种执行模式，再读取 Webpage note workflow.md 获取五步细则（均在项目内）。
按其中流程处理我接下来给出的网页/本地内容：先做内容清单确认与前置检查（含 DEEPSEEK_API_KEY、Cookie），拿不准时问我。
产出统一写入 runs/<日期-主题>/，所有删除/发布/改记忆类动作停在"待确认"。
```

> 分层说明：`webnote-workflow` 是**总编排 skill**（含多 Agent / 单对话框两种执行模式）；图片、视频、小红书三条内容提取链路分别由 `skills/image-extract`、`skills/video-extract`、`skills/xhs-note` 承载，采编时按内容类型加载。五步细则见 [Webpage note workflow.md](Webpage%20note%20workflow.md)。

---

## 中文文档

### 项目简介

WebNote-Workflow 是一套**以"可信"为核心的网页内容整理工作流**。它的目标不是帮你更快地生产，而是帮你**更可靠地把网页内容变成自己的知识**。

> 本项目在 [Axton Liu《Agent OS 的第一课：会分工，才会用 Agent》](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division) 一文的理念启发下自行实现与改进，落地成一套可直接复用、按文件流水线运行的工作流。原文为付费 Newsletter，本仓库仅借鉴其"分工隔离 / 独立核查 / 确认闸门"三层设计思路，所有文档与提示词均为独立撰写。

### 架构

**不是每一步都需要独立的 AI 上下文。** 确定性的事调度器（主会话）自己干（画面采集为可选 AI 增强），只有真正需要独立判断的才交给 subagent：

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
| 采编 | ❌ 主会话内化 | URL 分类用正则，文本提取调用 CLI 工具——**默认确定性逻辑不需要 AI**（画面采集为可选 AI 增强，见下） |
| 归类师 | ✅ 独立 | 四选一分类需要理解正文语义，归类师的判断不应影响笔记匠 |
| 笔记匠 | ✅ 独立 | 核心创作任务，需要完整上下文专注正文 |
| 核查官 | ✅ **必须独立** | 安全闸门——笔记匠自己核查自己等于自检，查不出自己编了什么 |
| 确认 | ❌ 主会话内化 | 不读原文、不做新判断，只是汇总 + 约束落地行为 |

### 功能说明

| 阶段 | 执行者 | 输入 | 输出 | 关键约束 |
|------|--------|------|------|---------|
| 采编 | 调度器（主会话） | 原始 URL + 已有正文 | `00-采编清单.md` | 正则分类 + CLI 工具，默认不依赖 AI；**画面采集（教程/录屏类视频）为可选 AI 增强** |
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
├── Webpage note workflow.md            # 工作流主文档（完整五步定义，被总 skill 引用）
├── tools/                              # 采编阶段的工具（默认确定性 CLI；画面采集为可选 AI 增强）
│   ├── extract-document.py             # PDF/DOCX 文本提取
│   ├── extract-webpage.py              # BrowserSkill 图文页面提取
│   ├── extract-video-text.py           # BrowserSkill 视频页面提取
│   ├── extract-video-asr.py            # 视频 ASR 语音转写（faster-whisper）
│   ├── extract-video-frames.py         # 视频画面采集（抽帧+本地OCR+云端 Vision 语义，需 Key）
│   ├── ds_vision.py                    # DeepSeek Vision 多图理解（被画面采集调用）
│   ├── extract-image-ocr.py            # 图片本地 OCR（RapidOCR，与视频画面采集统一）
│   ├── extract-xhs.py                  # 小红书笔记拉取 + 图片/视频落盘（需 Cookie）
│   └── run-xhs-note.py                 # 小红书单条笔记流水线驱动（fetch→OCR→ASR→Markdown）
├── skills/                             # 项目内置的 AI skill（本项目的"能力库"）
│   ├── webnote-workflow/               # ★ 总编排 skill（AI 入口：五步流程 + 两种执行模式）
│   ├── image-extract/                  # 图片内容提取（OCR 文字 + 画面语义）
│   ├── video-extract/                  # 视频内容提取（语音 ASR + 画面文字/语义）
│   └── xhs-note/                       # 小红书笔记流水线（拉取 + OCR + ASR → md）
├── BrowserSkill Installation Guide.md  # BrowserSkill 安装指南
├── BrowserSkill Command Reference.md   # bsk CLI 命令速查
├── posts/                              # 可发布到博客平台的内容
├── runs/                               # 每次运行的产出目录（内容被 .gitignore 忽略）
│   └── YYYY-MM-DD-主题/
│       ├── 00-采编清单.md               # 调度器（主会话）产出
│       ├── 01-整理清单.md               # 归类师产出
│       ├── 02-笔记.md                   # 笔记匠产出
│       ├── 03-核查表.md                 # 核查官产出
│       └── 04-待确认提案.md             # 调度器（主会话）产出
├── LICENSE                             # MIT 许可证
├── .gitignore                          # 忽略 runs/ 产出、密钥(.key/.env)、__pycache__
├── README.md                            # 中文文档 + 快速开始（装配/兜底双路径）
├── README.en.md                         # English documentation + quick start
```

### 使用方法

#### 0. 前置准备：先把正文存好（工具自选）

正文**由你自己存好，本工作流不去抓网页**——直接让 AI 现抓十有八九抓不全，付费墙和需登录的页更抓不到。**用哪种工具、用不用，完全由你决定**，以下任选其一即可：

- **手动复制粘贴**：最稳，零依赖
- **Obsidian 网页剪藏 / 简悦 / Cubox / Readwise Reader** 等稍后读工具
- **BrowserSkill（可选）**：腾讯开源的浏览器桥接，可操控你已登录的浏览器读取页面，适合需要登录态的批量抓取（[安装指南](BrowserSkill%20Installation%20Guide.md)）。**并非必需**，只是其中一种方式

**可选：若要用视频画面采集**（教程/课程/录屏类视频，提取画面文字与语义），需额外准备：

```bash
export DEEPSEEK_API_KEY="sk-xxx"   # 云端 DeepSeek Vision，绝不写进代码 / 提交 git
```

该能力为**可选增强**：不用则整个工作流完全不依赖 AI 做采集（见"采编"说明）。仅画面采集涉及调用云端模型，其余提取均为本地/确定性工具。

#### 执行模式（两种，AI 按工具能力二选一）

完整编排见 [`skills/webnote-workflow/SKILL.md`](skills/webnote-workflow/SKILL.md)，这里只列要点：

**模式 A · 多 Agent（工具支持 subagent 时，推荐）**：调度器（主会话）执行采编与确认，创建 3 个独立 subagent：
- 归类师 → 四选一语义分类；笔记匠 → 每页 3~5 条核心要点；核查官（**全新上下文**）→ 逐条比对原文 vs 笔记
- 核查官不能是笔记匠——自己查自己查不出编造内容

**模式 B · 单对话框分段（无 subagent 能力时的降级）**：同对话完成采编 + 归类 + 提炼 → **停下**，要求用户把产物与原文带到**新对话**核查 → 核查表带回后确认。

> 核查必须独立（新 subagent 或新对话），否则查不出自己编的内容。

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
| 删除 / 归档 / 移动资料 | URL 正则分类、调用 CLI 工具（含画面采集；其云端 Vision 调用为只读理解，非落地动作） |
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
