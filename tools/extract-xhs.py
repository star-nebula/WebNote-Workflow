#!/usr/bin/env python3
"""
Agent 0 · 采编 — 小红书笔记拉取与本地落盘工具（纯本地，无云端）

通过 xhs 库（需登录 Cookie）按 URL / note_id 拉取小红书笔记：
  - 图文笔记：下载所有图片到 <work_dir>/images/
  - 视频笔记：下载视频到 <work_dir>/video/
  - 同时提取标题 / 描述 / 标签等文本字段
图片与视频均来自小红书公开 CDN，下载本身不需要 Cookie（仅 API 拉取需要）。

用法：
  python extract-xhs.py <笔记URL或note_id> [--cookie <cookie字符串>] [--out <工作目录>]

Cookie 获取方式（三选一，优先级 --cookie > 环境变量 XHS_COOKIE > cookie.txt）：
  1. --cookie "a1b2c3...; web_session=..."
  2. 环境变量：export XHS_COOKIE="a1b2c3...; web_session=..."
  3. 在脚本同目录放 cookie.txt，写入完整 Cookie 字符串

依赖：pip install xhs requests

输出 JSON 到 stdout（在通用契约基础上扩展字段）：
  {
    "success": true,
    "text": "标题\\n\\n描述\\n\\n#标签...",
    "char_count": N,
    "method": "xhs-fetch",
    "error": null,
    "note_id": "...",
    "note_type": "image_text | video",
    "title": "...",
    "desc": "...",
    "tags": ["...", "..."],
    "images": ["images/img_0.png", ...],   # 相对 work_dir 的路径
    "video": "video/<title>.mp4" | null,    # 相对 work_dir 的路径
    "work_dir": "<绝对路径>"
  }
"""

import argparse
import json
import os
import re
import sys

# 日志走 stderr，不污染 stdout 的 JSON
def log(msg, file=sys.stderr):
    print(f'[xhs] {msg}', file=file)


UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')


def parse_note_id(raw):
    """从 URL 或原始 id 中提取 note_id。"""
    raw = (raw or '').strip()
    # https://www.xiaohongshu.com/explore/<id>
    m = re.search(r'xiaohongshu\.com/(?:explore|discovery/item)/([0-9a-zA-Z]+)', raw)
    if m:
        return m.group(1)
    # 也可能是 /user-profile/... 之类，但笔记通常走上面两种；兜底：取最后一段字母数字
    m = re.search(r'([0-9a-zA-Z]{8,})', raw)
    if m:
        return m.group(1)
    return raw


def load_cookie(args):
    """按优先级获取 Cookie：--cookie > 环境变量 > cookie.txt。"""
    if args.cookie:
        return args.cookie
    env = os.environ.get('XHS_COOKIE')
    if env:
        return env
    cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookie.txt')
    if os.path.exists(cookie_path):
        with open(cookie_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def _download(url, dest, referer='https://www.xiaohongshu.com/'):
    """带 UA/Referer 的稳健下载（公开 CDN，无需登录态）。"""
    import requests
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    headers = {'User-Agent': UA, 'Referer': referer}
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return dest


def extract_tags(note):
    """从 note['tag_list'] 提取标签名，兼容 dict / str 两种形式。"""
    tags = []
    for t in note.get('tag_list', []) or []:
        if isinstance(t, dict):
            name = t.get('name') or t.get('title') or ''
        else:
            name = str(t)
        name = (name or '').strip()
        if name:
            tags.append(name)
    return tags


def main():
    parser = argparse.ArgumentParser(description='小红书笔记拉取与本地落盘')
    parser.add_argument('target', help='笔记 URL 或 note_id')
    parser.add_argument('--cookie', help='小红书登录 Cookie 字符串')
    parser.add_argument('--out', help='工作目录（默认 ./xhs_output/<note_id>）')
    args = parser.parse_args()

    cookie = load_cookie(args)
    if not cookie:
        out = {
            'success': False, 'text': '', 'char_count': 0, 'method': 'error',
            'error': '未找到 Cookie：请通过 --cookie、环境变量 XHS_COOKIE 或 cookie.txt 提供小红书登录 Cookie',
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    note_id = parse_note_id(args.target)

    try:
        from xhs import XhsClient, NoteType
        from xhs.help import get_imgs_url_from_note, get_video_url_from_note
    except ImportError as e:
        out = {
            'success': False, 'text': '', 'char_count': 0, 'method': 'error',
            'error': f'xhs 未安装，执行: pip install xhs（{e}）',
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    try:
        client = XhsClient(cookie=cookie, user_agent=UA, timeout=15)
        note = client.get_note_by_id(note_id)
    except Exception as e:
        # 常见情况：假 Cookie / 过期 / 笔记不存在 / 风控，接口返回的数据里没有 note_card
        hint = '返回数据缺少笔记内容（Cookie 可能过期、笔记不存在或触发风控）'
        if 'index' in str(e) or 'NoneType' in str(e) or 'items' in str(e):
            detail = hint
        else:
            detail = f'{hint}：{e}'
        out = {
            'success': False, 'text': '', 'char_count': 0, 'method': 'error',
            'error': f'拉取笔记失败: {detail}',
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    title = (note.get('title') or '').strip()
    desc = (note.get('desc') or '').strip()
    tags = extract_tags(note)
    note_type = 'video' if note.get('type') == NoteType.VIDEO.value else 'image_text'

    work_dir = args.out or os.path.join(os.getcwd(), 'xhs_output', note_id)
    os.makedirs(work_dir, exist_ok=True)

    images_rel, video_rel = [], None

    if note_type == 'video':
        try:
            video_url = get_video_url_from_note(note)
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title) or note_id
            video_name = f'{safe_title}.mp4'
            video_path = os.path.join(work_dir, 'video', video_name)
            log(f'下载视频: {video_url}')
            _download(video_url, video_path)
            video_rel = os.path.relpath(video_path, work_dir).replace('\\', '/')
        except Exception as e:
            log(f'视频下载失败: {e}')
    else:
        try:
            img_urls = get_imgs_url_from_note(note)
            for i, url in enumerate(img_urls):
                if not url:
                    continue
                img_path = os.path.join(work_dir, 'images', f'img_{i}.png')
                try:
                    _download(url, img_path)
                    images_rel.append(os.path.relpath(img_path, work_dir).replace('\\', '/'))
                except Exception as e:
                    log(f'图片 {i} 下载失败: {e}')
        except Exception as e:
            log(f'图片列表解析失败: {e}')

    # 组装文本字段（供下游归类/提炼使用）
    text_parts = []
    if title:
        text_parts.append(title)
    if desc:
        text_parts.append(desc)
    if tags:
        text_parts.append(' '.join(f'#{t}' for t in tags))
    text = '\n\n'.join(text_parts)

    result = {
        'success': True,
        'text': text,
        'char_count': len(text.replace('\n', '').replace(' ', '')),
        'method': 'xhs-fetch',
        'error': None,
        'note_id': note_id,
        'note_type': note_type,
        'title': title,
        'desc': desc,
        'tags': tags,
        'images': images_rel,
        'video': video_rel,
        'work_dir': os.path.abspath(work_dir),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
