# WebNote-Workflow · Web-to-Note Workflow

> Turns "content collection → classify → distill → confirm publish" into **scheduler (main session) + three independent Agents**. Deterministic work is done by the scheduler itself (frame understanding is an optional AI enhancement); only what truly needs independent judgment goes to a subagent.

[中文](README.md) · [English](#quick-start)

---

## Quick Start: Two Paths

The project's AI entry point is the **`skills/webnote-workflow` (orchestrator skill)** — the whole workflow (five steps + video frame capture + confirmation boundary) is packaged inside it. Pick either path:

**Path A · Install (recommended)**: link or copy the `skills/` directory into your AI tool's project-level skills dir (e.g. `.workbuddy/skills/`, `.codex/skills/`, `.claude/skills/`). After that, natural conversation triggers it — just say "turn this webpage into a note" and the AI loads the webnote-workflow skill and follows the flow.

**Path B · Fallback (no install needed)**: copy the short block below to your AI (WorkBuddy / Codex / Claude Code):

```
You are using the "WebNote-Workflow" web-to-note pipeline, located at <current project dir>.
First read skills/webnote-workflow/SKILL.md for orchestration and its two execution modes, then read Webpage note workflow.md for the five-step details (both inside the project).
Follow them to process the web/local content I give next: do content-list confirmation and pre-flight checks (incl. DEEPSEEK_API_KEY, Cookie), ask me when unsure.
Write outputs under runs/<date-topic>/; any delete/publish/memory-write action stays "pending confirmation".
```

> Layering: `webnote-workflow` is the **orchestrator skill** (multi-agent / single-dialog modes); the three content pipelines live in `skills/image-extract`, `skills/video-extract`, `skills/xhs-note`, loaded by content type during collection. Five-step details: [Webpage note workflow.md](Webpage%20note%20workflow.md).

---

## Overview

WebNote-Workflow is a **trust-first** pipeline for turning saved web content into reliable personal notes. It uses a hybrid architecture: deterministic tasks (media format classification, text extraction, confirmation) are handled by the scheduler itself, while only the tasks that truly need independent AI judgment are delegated to subagents. Note: text extraction is deterministic by default; **video frame understanding** (for tutorial/screen-record content) is an optional AI enhancement that requires a `DEEPSEEK_API_KEY`.

```
Scheduler (your AI tool)
├── 1. Collection (scheduler itself — regex + CLI tools)
├── 2. Classifier (subagent — semantic 4-way classification)
├── 3. Distiller (subagent — extract key points)
├── 4. Verifier (new subagent — compare notes against original)
└── 5. Confirmation (scheduler itself — summarize proposal, all pending)
```

Only **3 subagents** instead of 5 — the scheduler handles deterministic steps itself.

### Execution modes (two; the AI picks by capability)

Full orchestration lives in [`skills/webnote-workflow/SKILL.md`](skills/webnote-workflow/SKILL.md). Highlights:

1. **Mode A · Multi-agent (recommended when subagents are supported)**: scheduler runs collection + confirmation; spawns 3 independent subagents — Classifier, Distiller, and a **fresh-context** Verifier (never the distiller itself, so it cannot rubber-stamp its own writing).
2. **Mode B · Single-dialog segmented (fallback)**: collection + classify + distill in one dialog, then **stop** — ask the user to run the verification in a **new dialog**, then confirm with the returned check sheet.
3. (Optional) For video frame understanding, set `DEEPSEEK_API_KEY` and call `tools/extract-video-frames.py --input <video>`.

### Confirmation boundary

Any delete / archive / publish / long-term-memory write stops at "pending confirmation" — the AI proposes, you press the button.

### License

MIT — see [LICENSE](LICENSE). Design credit: [Axton Liu, "Agent OS 的第一课"](https://www.axtonliu.ai/newsletters/ai-2/posts/agent-os-workstation-division) (ideas only; no original text reproduced).
