#!/usr/bin/env python3
"""
Agent 0 · 采编 — 小红书单条笔记流水线驱动（纯本地，无云端）

串联三步，产出一份本地 Markdown 文档：
  1. extract-xhs.py        拉取笔记 + 下载图片/视频到本地
  2. extract-image-ocr.py  对图片做本地 OCR（RapidOCR）
  3. extract-video-asr.py  对视频做本地 ASR（faster-whisper）

特点：
  - 纯本地离线，数据不出本机（唯一外部依赖是拉取用的小红书 Cookie）
  - 各步独立输出 JSON，本驱动只做编排与 Markdown 组装
  - OCR / ASR 可指定不同的 Python 解释器（OCR 用 RapidOCR，3.13 可用）

用法：
  python run-xhs-note.py <笔记URL或note_id> [--out <目录>] [--cookie <cookie>]
                           [--asr-model small|large-v3-turbo]
                           [--ocr-python <python解释器>] [--asr-python <python解释器>]
                           [--skip-ocr] [--skip-asr]

输出 JSON 到 stdout：
  {"success": true, "text": "<Markdown>", "char_count": N, "method": "xhs-pipeline",
   "error": null, "note_md": "<绝对路径>", "work_dir": "<绝对路径>"}
"""

import argparse
import json
import os
import subprocess
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


def run_tool(python_exe, script, *cli_args, timeout=3600):
    """调用一个 extract-*.py 工具，返回解析后的 JSON。失败抛异常。"""
    cmd = [python_exe, os.path.join(TOOLS_DIR, script), *cli_args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        # 尝试从 stderr 找线索
        err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else '(无 stderr)'
        raise RuntimeError(f'{script} 失败 (exit {result.returncode}): {err}')
    # 工具 stdout 即为 JSON
    return json.loads(result.stdout)


def build_markdown(fetch, ocr_text, asr_text):
    title = fetch.get('title') or '(无标题)'
    desc = fetch.get('desc') or ''
    tags = fetch.get('tags') or []
    note_type = '视频' if fetch.get('note_type') == 'video' else '图文'
    work_dir = fetch.get('work_dir', '')
    source = fetch.get('source_url', '')

    lines = []
    lines.append(f'# {title}')
    lines.append('')
    meta = f'> 类型：{note_type} · 本地存档：`{work_dir}`'
    if source:
        meta += f' · 来源：{source}'
    lines.append(meta)
    lines.append('')

    if desc:
        lines.append('## 原文描述')
        lines.append('')
        lines.append(desc)
        lines.append('')

    if tags:
        lines.append('**标签**：' + ' '.join(f'#{t}' for t in tags))
        lines.append('')

    per_image = (ocr_text or {}).get('per_image') if isinstance(ocr_text, dict) else None
    if per_image:
        lines.append('## 图片文字（OCR · 本地 RapidOCR）')
        lines.append('')
        for item in per_image:
            rel = item.get('file', '')
            txt = (item.get('text') or '').strip()
            lines.append(f'![{rel}]({rel})')
            lines.append('')
            lines.append(txt if txt else '_(未识别到文字)_')
            lines.append('')
    elif fetch.get('images'):
        lines.append('## 图片文字（OCR · 本地 RapidOCR）')
        lines.append('')
        lines.append('_(未执行 OCR 或识别为空)_')
        lines.append('')

    if asr_text and isinstance(asr_text, dict) and asr_text.get('text'):
        lines.append('## 视频转写（ASR · 本地 faster-whisper）')
        lines.append('')
        lines.append(asr_text['text'])
        lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='小红书单条笔记流水线驱动（纯本地）')
    parser.add_argument('target', help='笔记 URL 或 note_id')
    parser.add_argument('--out', help='工作目录（默认 ./xhs_output/<note_id>）')
    parser.add_argument('--cookie', help='小红书登录 Cookie 字符串')
    parser.add_argument('--asr-model', default='large-v3-turbo',
                        choices=['small', 'medium', 'large-v3', 'large-v3-turbo'])
    parser.add_argument('--ocr-python', default=sys.executable,
                        help='运行 OCR 的 Python 解释器（默认同驱动）')
    parser.add_argument('--asr-python', default=sys.executable,
                        help='运行 ASR 的 Python 解释器（默认同驱动）')
    parser.add_argument('--skip-ocr', action='store_true', help='跳过图片 OCR')
    parser.add_argument('--skip-asr', action='store_true', help='跳过视频 ASR')
    args = parser.parse_args()

    fail = lambda msg: print(json.dumps(
        {'success': False, 'text': '', 'char_count': 0, 'method': 'error', 'error': msg},
        ensure_ascii=False))

    # 1. 拉取 + 落盘
    try:
        fetch_cli = [args.target]
        if args.out:
            fetch_cli += ['--out', args.out]
        if args.cookie:
            fetch_cli += ['--cookie', args.cookie]
        fetch = run_tool(sys.executable, 'extract-xhs.py', *fetch_cli)
    except Exception as e:
        fail(f'拉取笔记失败: {e}')
        sys.exit(1)

    if not fetch.get('success'):
        fail(f"拉取笔记失败: {fetch.get('error')}")
        sys.exit(1)

    fetch['source_url'] = args.target  # 回写来源，供 Markdown 展示
    work_dir = fetch['work_dir']
    fetch_json_path = os.path.join(work_dir, 'fetch.json')
    with open(fetch_json_path, 'w', encoding='utf-8') as f:
        json.dump(fetch, f, ensure_ascii=False, indent=2)

    ocr_result = None
    asr_result = None

    # 2. 图片 OCR
    if fetch.get('images') and not args.skip_ocr:
        try:
            ocr_result = run_tool(args.ocr_python, 'extract-image-ocr.py', '--input', fetch_json_path,
                                  timeout=1800)
        except Exception as e:
            print(f'[driver] OCR 跳过: {e}', file=sys.stderr)
    else:
        print('[driver] 无图片或 --skip-ocr，跳过 OCR', file=sys.stderr)

    # 3. 视频 ASR
    if fetch.get('video') and not args.skip_asr:
        video_abs = os.path.join(work_dir, fetch['video'])
        if os.path.isfile(video_abs):
            try:
                asr_result = run_tool(args.asr_python, 'extract-video-asr.py',
                                     '--input', video_abs, '--model', args.asr_model,
                                     timeout=3600)
            except Exception as e:
                print(f'[driver] ASR 跳过: {e}', file=sys.stderr)
        else:
            print(f'[driver] 视频文件不存在，跳过 ASR: {video_abs}', file=sys.stderr)
    else:
        print('[driver] 无视频或 --skip-asr，跳过 ASR', file=sys.stderr)

    # 4. 组装 Markdown
    md = build_markdown(fetch, ocr_result, asr_result)
    note_md = os.path.join(work_dir, 'note.md')
    with open(note_md, 'w', encoding='utf-8') as f:
        f.write(md)

    out = {
        'success': True,
        'text': md,
        'char_count': len(md.replace('\n', '').replace(' ', '')),
        'method': 'xhs-pipeline',
        'error': None,
        'note_md': os.path.abspath(note_md),
        'work_dir': work_dir,
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
