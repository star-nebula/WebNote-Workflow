#!/usr/bin/env python3
"""
Agent 0 · 采编 — 文档文本提取工具

从本地 PDF/DOCX 文件提取文本，输出 JSON 到 stdout。

用法：
  python extract-document.py <文件路径>

依赖：pip install pypdf python-docx
"""

import json
import os
import sys


def extract_pdf(filepath):
    """从 PDF 提取文本"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        texts = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                texts.append(t.strip())
        full_text = '\n'.join(texts)
        return full_text, len(full_text.replace('\n', '')), 'pypdf'
    except ImportError:
        return '', 0, 'error', 'pypdf 未安装，执行: pip install pypdf'
    except Exception as e:
        return '', 0, 'error', str(e)


def extract_docx(filepath):
    """从 DOCX 提取文本"""
    try:
        from docx import Document
        doc = Document(filepath)
        texts = []
        for para in doc.paragraphs:
            if para.text.strip():
                texts.append(para.text.strip())
        full_text = '\n'.join(texts)
        return full_text, len(full_text.replace('\n', '')), 'python-docx'
    except ImportError:
        return '', 0, 'error', 'python-docx 未安装，执行: pip install python-docx'
    except Exception as e:
        return '', 0, 'error', str(e)


def main():
    if len(sys.argv) < 2:
        output = {
            'success': False,
            'text': '',
            'char_count': 0,
            'method': 'error',
            'error': '用法: python extract-document.py <文件路径>'
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        output = {
            'success': False,
            'text': '',
            'char_count': 0,
            'method': 'error',
            'error': f'文件不存在: {filepath}'
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.pdf':
        text, char_count, method = extract_pdf(filepath)
    elif ext == '.docx':
        text, char_count, method = extract_docx(filepath)
    else:
        output = {
            'success': False,
            'text': '',
            'char_count': 0,
            'method': 'error',
            'error': f'不支持的文档格式: {ext}（支持: .pdf, .docx）'
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    if method == 'error':
        output = {
            'success': False,
            'text': '',
            'char_count': 0,
            'method': 'error',
            'error': text  # text 里存的是错误信息
        }
    else:
        output = {
            'success': True,
            'text': text,
            'char_count': char_count,
            'method': method,
            'error': None
        }

    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
