#!/usr/bin/env python3
"""
Agent 0 · 采编 — 图片本地 OCR 工具（纯本地，无云端）

对图片（小红书图文笔记下载的本地图片，或任意本地图片）做中文 OCR，
使用 PaddleOCR PP-OCRv4，完全离线、数据不出本机。

用法：
  python extract-image-ocr.py --input <图片目录 | extract-xhs.py 的 JSON>
  python extract-image-ocr.py --images img1.png img2.png

依赖（建议在 Python 3.11 虚拟环境安装，PaddlePaddle 暂未提供 3.13 wheel）：
  pip install paddleocr paddlepaddle==3.0.0rc1   # CPU 版；或 paddlepaddle-gpu
  # 注意：请用 Python 3.11 创建 venv 后安装，避免与项目其他 3.13 依赖冲突

输出 JSON 到 stdout（通用契约 + 扩展）：
  {
    "success": true,
    "text": "<所有图片 OCR 文字合并>",
    "char_count": N,
    "method": "paddleocr-ch",
    "error": null,
    "per_image": [{"file": "images/img_0.png", "text": "..."}, ...]
  }
"""

import argparse
import glob
import json
import os
import sys

IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')


def log(msg, file=sys.stderr):
    print(f'[ocr] {msg}', file=file)


def collect_images(args):
    """返回 (图片绝对路径列表, 基准目录) —— 用于把相对路径写回结果。"""
    if args.images:
        paths = [os.path.abspath(p) for p in args.images if os.path.isfile(p)]
        return paths, os.getcwd()

    inp = args.input
    if not inp:
        return [], os.getcwd()

    if inp.lower().endswith('.json'):
        with open(inp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        work_dir = data.get('work_dir') or os.path.dirname(os.path.abspath(inp))
        imgs = data.get('images', [])
        paths = [os.path.join(work_dir, p) if not os.path.isabs(p) else p for p in imgs]
        paths = [p for p in paths if os.path.isfile(p)]
        return paths, work_dir

    if os.path.isdir(inp):
        paths = []
        for ext in IMAGE_EXTS:
            paths.extend(glob.glob(os.path.join(inp, f'**/*{ext}'), recursive=True))
        return sorted(paths), inp

    return [], os.getcwd()


def main():
    parser = argparse.ArgumentParser(description='图片本地 OCR（PaddleOCR）')
    parser.add_argument('--input', help='图片目录，或 extract-xhs.py 输出的 JSON 文件')
    parser.add_argument('--images', nargs='+', help='一张或多张图片路径')
    args = parser.parse_args()

    image_paths, base_dir = collect_images(args)
    if not image_paths:
        out = {
            'success': False, 'text': '', 'char_count': 0, 'method': 'error',
            'error': '未找到任何图片：请通过 --input <目录|JSON> 或 --images 指定',
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    try:
        from paddleocr import PaddleOCR
    except ImportError as e:
        out = {
            'success': False, 'text': '', 'char_count': 0, 'method': 'error',
            'error': f'paddleocr 未安装（请使用 Python 3.11 venv: pip install paddleocr paddlepaddle）: {e}',
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    log(f'初始化 PaddleOCR（PP-OCRv4, lang=ch, CPU）... 首次会下载模型')
    try:
        ocr = PaddleOCR(lang='ch', use_angle_cls=True, use_gpu=False)
    except Exception as e:
        out = {
            'success': False, 'text': '', 'char_count': 0, 'method': 'error',
            'error': f'PaddleOCR 初始化失败: {e}',
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    per_image = []
    combined = []
    for img in image_paths:
        rel = os.path.relpath(img, base_dir).replace('\\', '/')
        try:
            result = ocr.ocr(img, cls=True)
            lines = []
            if result:
                for frame in result:
                    if not frame:
                        continue
                    for line in frame:
                        # line: [bbox, (text, score)]
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                        if text and text.strip():
                            lines.append(text.strip())
            text = '\n'.join(lines)
        except Exception as e:
            log(f'OCR 失败 {rel}: {e}')
            text = ''
        per_image.append({'file': rel, 'text': text})
        if text:
            combined.append(f'### 图片 {rel}\n{text}')

    full_text = '\n\n'.join(combined)
    out = {
        'success': True,
        'text': full_text,
        'char_count': len(full_text.replace('\n', '').replace(' ', '')),
        'method': 'paddleocr-ch',
        'error': None,
        'per_image': per_image,
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
