#!/usr/bin/env python3
"""
Agent 0 · 采编 — DeepSeek Vision 多图理解工具（云端）

对一组图片（如视频抽帧），用 deepseek-v4-flash-vision-exp 理解每帧的画面语义。
OCR 管"逐字文字提取"，本工具管"画面在讲什么 / 是什么场景"。

用法：
  DEEPSEEK_API_KEY=sk-xxx python ds_vision.py <img1.jpg> [img2.jpg ...] [--detail high]
       [--times "0s,5s,10s"] [--prompt "<自定义提示词>"]

说明：
  - Key 从环境变量 DEEPSEEK_API_KEY 读取，绝不写进代码 / 提交 git。
  - 模型必须 deepseek-v4-flash-vision-exp（其他模型不收图，会 400）。
  - 关键修复（必须保留）：
      * reasoning_effort:"none" —— 否则模型思考占满 max_tokens，正文返回空。
      * detail:"high"（默认）—— 保持原图；"low" 压到 512x512 会诱发幻觉。
  - 单图最多 384 token，单请求最多 600 图；建议调用方按 14 帧/批切分后多次调用。

输出 JSON 到 stdout（通用契约 + 扩展）：
  {"success": true, "text": "<逐帧语义 Markdown>", "char_count": N,
   "method": "ds-vision", "error": null,
   "per_image": [{"file": "...", "t": "125s", "text": "..."}]}
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash-vision-exp"


def log(msg, file=sys.stderr):
    print(f"[vision] {msg}", file=file)


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build_instruction(times=None, user_prompt=None):
    """构造提示词。times: ["125s","145s",...] 与图片一一对应。"""
    if user_prompt:
        return user_prompt
    times_hint = ""
    if times:
        times_hint = f"每张对应的真实时间戳依次是：{', '.join(times)}。"
    return (
        f"下面按顺序给你若干张视频截图。{times_hint}\n"
        "请逐张用中文回答，每张以【图N @ 真实时间戳】开头（时间戳用上面给的，不要自编）。\n"
        "1) 这是什么界面/场景？\n2) 在做什么操作/处于什么阶段？\n"
        "3) 抄录能看清的主要文字（看不清用[?]标注，不要编造）。\n"
        "每张控制在100字内，简洁。"
    )


def ask(api_key, image_paths, detail="high", times=None, user_prompt=None):
    instruction = build_instruction(times, user_prompt)
    content = [{"type": "text", "text": instruction}]
    for p in image_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64(p)}", "detail": detail},
        })
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 3000,
        "stream": False,
        "reasoning_effort": "none",
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def parse_vision_to_per_image(vision_text, image_paths, times):
    """把 Vision 的逐段输出拆成 per_image（尽力而为；若解析失败则整段放第一项）。"""
    import re
    # 按【图N 开头切分；blocks[0] 通常是空（split 在开头切）
    blocks = [b for b in re.split(r'(?=【图\d)', vision_text or "") if b.strip()]
    per = []
    for i, (path, t) in enumerate(zip(image_paths, times or [""] * len(image_paths))):
        block = blocks[i] if i < len(blocks) else ""
        per.append({"file": path, "t": t, "text": block.strip()})
    return per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", help="图片路径（视频抽帧）")
    ap.add_argument("--detail", default="high", choices=["low", "high", "original"])
    ap.add_argument("--times", default=None, help="逗号分隔的时间戳，如 '125s,145s,160s'")
    ap.add_argument("--prompt", default=None)
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        out = {
            "success": False, "text": "", "char_count": 0,
            "method": "error",
            "error": "未找到 DEEPSEEK_API_KEY 环境变量",
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    times = None
    if args.times:
        times = [t.strip() for t in args.times.split(",") if t.strip()]

    log(f"{len(args.images)} 张, detail={args.detail}, model={MODEL}")
    t0 = time.time()
    try:
        r = ask(api_key, args.images, args.detail, times, args.prompt)
        msg = r["choices"][0]["message"]["content"] or ""
        usage = r.get("usage", {})
        per_image = parse_vision_to_per_image(msg, args.images, times or [""] * len(args.images))
        out = {
            "success": True,
            "text": msg,
            "char_count": len(msg.replace("\n", "").replace(" ", "")),
            "method": f"ds-vision-{MODEL}",
            "error": None,
            "usage": usage,
            "per_image": per_image,
            "elapsed_s": round(time.time() - t0, 1),
        }
        print(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        out = {
            "success": False, "text": "", "char_count": 0,
            "method": "error", "error": f"DeepSeek Vision 调用失败: {e}",
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
