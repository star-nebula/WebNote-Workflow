---
name: webnote-workflow
description: 把网页/本地内容整理成"可信本地笔记"的完整工作流：采集→归类→提炼→独立核查→待确认。当用户给出一批网页 URL、浏览器剪藏、本地 PDF/DOCX/图片/视频/音频/小红书链接，要求"整理成笔记/存到本地 md/提炼要点/做网页笔记"时使用。含两种执行模式（支持 subagent 的多 Agent 版 / 单对话框分段版）。细则见项目内 Webpage note workflow.md。
agent_created: true
---

# WebNote-Workflow · 总编排 skill

把"内容采集 → 整理分类 → 提炼笔记 → 确认发布"组织为**调度器（主会话）+ 三个独立执行角色**。项目目标是**可信**：正文不凭空编、核查必须独立、落地必待确认。

## 定位与资源引用

本 skill 是整个 WebNote-Workflow 仓库的 AI 入口。**先定位项目根**：本文件位于 `<项目根>/skills/webnote-workflow/`，项目根即其上级的上级目录。随后读取：

| 资源 | 位置（相对项目根） | 用途 |
|---|---|---|
| 主流程细则 | `Webpage note workflow.md` | 五步流程的完整定义，**必读** |
| 图片提取方法论 | `skills/image-extract/SKILL.md` | 内容含图片时加载 |
| 视频提取方法论 | `skills/video-extract/SKILL.md` | 内容含视频时加载 |
| 小红书流水线 | `skills/xhs-note/SKILL.md` | 内容是小红书链接时加载 |
| 采编工具 | `tools/*.py` | 文本提取的确定性 CLI |

**规则**：一切五步细则以 `Webpage note workflow.md` 为准；本 SKILL.md 只给编排骨架与执行模式。

## 触发与内容确认

用户给出内容（URL / 本地路径 / 已存正文）并要整理成笔记时触发。先做**内容清单确认**：逐个判断媒体格式（图文/图片/视频/音频/文档/小红书/无法判断），拿不准就问用户，不擅自猜测。

## 前置检查

1. 确认 `tools/` 下工具存在（extract-document / extract-webpage / extract-video-text / extract-video-asr / extract-video-frames / extract-image-ocr / extract-xhs / run-xhs-note / ds_vision）。
2. 内容涉及**图片语义 / 视频画面**且需要理解时：检查环境变量 `DEEPSEEK_API_KEY`，未设置则提示用户配置，不擅自跳过、不编造 Key。
3. 小红书需 Cookie（三选一，见 xhs-note skill）；浏览器页面读取走 BrowserSkill（用户已登录浏览器）。

## 执行模式（二选一，看 AI 工具能力）

### 模式 A · 多 Agent（工具支持 subagent 时，推荐）

调度器（主会话）自做**采编**与**确认**；归类师 → 笔记匠 → 核查官用**三个独立 subagent**：
- 核查官**必须全新上下文**，与笔记匠不是同一个（独立核查，不能自己查自己）。

### 模式 B · 单对话框分段（无 subagent 能力时的降级）

同一对话内完成采编 / 归类 / 提炼 → **在核查前停下**，提示用户把 `00/01/02` 产物与原文带到**新对话**执行核查（在本对话继续等于自查）→ 核查表带回后做确认。需给出明确的换对话操作指引。

## 五步骨架（细则以主文档为准）

1. **采编**（调度器自己做）：按媒体格式调对应工具提取文本 → `00-采编清单.md`
   - 图文（有正文）：直接使用，不调工具；正文为空：`extract-webpage.py <URL>`（BrowserSkill）
   - 文档：`extract-document.py <文件路径>`
   - 图片：`extract-image-ocr.py` 取逐字文字；需画面语义时 `ds_vision.py --mode image`（需 Key）→ 加载 **image-extract** skill
   - 视频/音频：`extract-video-text.py <URL>` 页面文本 → 不足（<200 字符）`extract-video-asr.py <URL>` 语音 → 教程/录屏/演示类加 `extract-video-frames.py --input <本地视频>` 画面文字+语义（需 Key）→ 加载 **video-extract** skill；**无法判断是否需要画面采集时，必须询问用户**
   - 小红书：`run-xhs-note.py <URL>`（需 Cookie）→ 加载 **xhs-note** skill
   - 所有工具输出统一 JSON 到 stdout，取 `text` 字段
2. **归类师**（subagent / 本段）：读有正文内容做四选一语义分类（学习/借鉴/内容补充/可归档）→ `01-整理清单.md`
3. **笔记匠**（subagent / 本段）：每页提取 3~5 条核心要点 + 保留理由 + 修订建议 → `02-笔记.md`
4. **核查官**（全新 subagent / 新对话）：逐条比对原文 vs 笔记，标"已核实"或"可疑/原文无依据" → `03-核查表.md`
5. **确认**（调度器自己做）：汇总 00~03 → `04-待确认提案.md`，每条建议动作（保留/修正/删除），可疑条目单列

## 产出与纪律

- 输出目录：每次运行在 `runs/` 下建 `YYYY-MM-DD-主题/`，五个文件并列写入；原文**只读**，不复制、不移动，清单只记录来源路径
- **三条不可逾越**：
  1. **正文不凭空编**——文本来自工具提取或用户已有，没有就如实写"无"
  2. **核查独立**——核查者不能是笔记的撰写者（subagent 全新上下文 / 新对话）
  3. **落地必待确认**——所有删除/归档/发布/写入长期记录的动作停在"待确认"，用户逐条点头才执行
- **收尾**：把 `04-待确认提案.md` 展示给用户，等逐条确认后执行落地动作
