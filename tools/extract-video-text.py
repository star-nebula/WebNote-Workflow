#!/usr/bin/env python3
"""
Agent 0 · 采编 — 视频页面文本提取工具（通过 BrowserSkill）

通过 bsk CLI 操控浏览器读取视频页面的可见文本（标题、描述、评论），
并尝试提取页面中内嵌的字幕/CC 数据。输出 JSON 到 stdout。

用法：
  python extract-video-text.py <URL>

依赖：bsk CLI（已安装）
"""

import json
import subprocess
import sys


# 单行压缩的 JS（提取视频页面所有可见文本 + 字幕数据）
EXTRACT_VIDEO_TEXT_JS = (
    '(function(){'
    'var e=["script","style","noscript","svg","canvas","video","audio"];'
    'var t=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,{acceptNode:function(n){'
    'var r=n.parentElement;if(!r)return NodeFilter.FILTER_REJECT;'
    'var i=r.tagName?r.tagName.toLowerCase():"";'
    'if(e.indexOf(i)!==-1)return NodeFilter.FILTER_REJECT;'
    'var s=window.getComputedStyle(r);'
    'if(s.display==="none"||s.visibility==="hidden")return NodeFilter.FILTER_REJECT;'
    'if(r.offsetWidth===0&&r.offsetHeight===0)return NodeFilter.FILTER_REJECT;'
    'return NodeFilter.FILTER_ACCEPT}},false);'
    'var a=[],n;while(n=t.nextNode()){var o=n.textContent.trim();if(o.length>0)a.push(o)}'
    'var r={title:document.title,visibleText:a.join("\\n"),charCount:a.join("").length,subtitles:[]};'
    'var c=document.querySelectorAll("script");'
    'for(var u=0;u<c.length;u++){'
    'var l=c[u].textContent||"";'
    'var f=l.match(/window\\.__INITIAL_STATE__\\s*=\\s*(\\{[\\s\\S]*?\\});/);'
    'if(f){try{var p=JSON.parse(f[1]);'
    'if(p&&p.videoData&&p.videoData.subtitle)'
    'r.subtitles.push({source:"bilibili",data:JSON.stringify(p.videoData.subtitle).substring(0,3000)})}catch(e){}}'
    'var d=l.match(/ytInitialPlayerResponse\\s*=\\s*(\\{[\\s\\S]*?\\});/);'
    'if(d){try{var h=JSON.parse(d[1]);'
    'if(h&&h.captions)'
    'r.subtitles.push({source:"youtube",data:JSON.stringify(h.captions).substring(0,3000)})}catch(e){}}'
    '}'
    'return JSON.stringify(r)'
    '})()'
)


def run_bsk(args, timeout=30):
    """运行 bsk 命令，返回 stdout"""
    try:
        result = subprocess.run(
            ['bsk'] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return '', -1
    except FileNotFoundError:
        return '', -2


def main():
    if len(sys.argv) < 2:
        output = {
            'success': False, 'text': '', 'char_count': 0,
            'method': 'error', 'error': '用法: python extract-video-text.py <URL>'
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    url = sys.argv[1]

    # 1. 创建会话
    stdout, rc = run_bsk(['session', 'start'])
    if rc != 0:
        output = {
            'success': False, 'text': '', 'char_count': 0,
            'method': 'error',
            'error': 'bsk session start 失败: bsk 未安装或 daemon 未运行'
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    session_id = stdout.strip()
    if not session_id:
        output = {
            'success': False, 'text': '', 'char_count': 0,
            'method': 'error', 'error': 'bsk 未返回 session ID'
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    try:
        # 2. 导航
        stdout, rc = run_bsk(['navigate', '--session', session_id, url])
        if rc != 0:
            output = {
                'success': False, 'text': '', 'char_count': 0,
                'method': 'error',
                'error': f'导航失败: {stdout[:200] if stdout else "浏览器扩展未连接"}'
            }
            print(json.dumps(output, ensure_ascii=False))
            return

        # 3. 等待页面加载（视频页面通常较慢）
        run_bsk(['wait-ms', '5000'])

        # 4. evaluate JS
        stdout, rc = run_bsk(
            ['evaluate', '--session', session_id, '--json', EXTRACT_VIDEO_TEXT_JS],
            timeout=30
        )

        if rc != 0 or not stdout:
            output = {
                'success': False, 'text': '', 'char_count': 0,
                'method': 'error',
                'error': f'JS evaluate 失败 ({rc}): {stdout[:200] if stdout else "浏览器扩展可能未连接"}'
            }
            print(json.dumps(output, ensure_ascii=False))
            return

        # 5. 解析 JSON
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            output = {
                'success': True if stdout.strip() else False,
                'text': stdout.strip(),
                'char_count': len(stdout.strip().replace('\n', '')),
                'method': 'bsk-video-raw',
                'error': None if stdout.strip() else '页面未返回有效文本'
            }
            print(json.dumps(output, ensure_ascii=False))
            return

        # bsk --json 输出格式: {"ok": true, "tab_id": ..., "value": "..."}
        # value 可能是 JSON 字符串（需要二次解析），也可能是普通字符串
        raw = None
        if isinstance(data, dict) and 'value' in data:
            raw = data['value']
        elif isinstance(data, dict) and 'data' in data:
            raw = data['data']
        else:
            raw = stdout

        # 尝试二次解析（value 是 JSON 字符串的情况）
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    data = parsed
                else:
                    data = raw
            except (json.JSONDecodeError, TypeError):
                data = raw
        else:
            data = raw

        # 6. 组装输出
        title = data.get('title', '') if isinstance(data, dict) else ''
        visible_text = data.get('visibleText', '') if isinstance(data, dict) else ''
        subtitles = data.get('subtitles', []) if isinstance(data, dict) else []

        parts = []
        if title:
            parts.append(f'标题: {title}')
        if visible_text:
            parts.append(visible_text)
        if subtitles:
            parts.append('\n--- 字幕数据 ---')
            for sub in subtitles:
                parts.append(f'[来源: {sub.get("source", "unknown")}]')
                parts.append(sub.get('data', ''))

        full_text = '\n'.join(parts)
        char_count = len(full_text.replace('\n', ''))

        if char_count > 0:
            output = {
                'success': True, 'text': full_text, 'char_count': char_count,
                'method': 'bsk-video', 'error': None
            }
        else:
            output = {
                'success': False, 'text': '', 'char_count': 0,
                'method': 'error', 'error': '视频页面未提取到文本内容'
            }

        print(json.dumps(output, ensure_ascii=False))

    finally:
        run_bsk(['session', 'stop', '--session', session_id], timeout=10)


if __name__ == '__main__':
    main()
