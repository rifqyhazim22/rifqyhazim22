#!/usr/bin/env python3
"""
Auto-translate README.md (English) to README_id.md (Indonesian).
Uses deep-translator with Google Translate (free, no API key needed).
Smart markdown-aware: preserves HTML tags, badge URLs, links, code blocks.
"""

import re
import sys
import time
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='en', target='id')


def protect_patterns(text):
    """Replace non-translatable patterns with unique placeholders."""
    placeholders = {}
    counter = [0]

    def make_placeholder(match):
        key = f"XPLACEHOLDERX{counter[0]}X"
        placeholders[key] = match.group(0)
        counter[0] += 1
        return key

    # Order matters: most specific first.
    # 1. Protect HTML tags
    text = re.sub(r'<[^>]+>', make_placeholder, text)
    # 2. Protect Markdown link URLs: ](url)
    text = re.sub(r'\]\([^)]*\)', make_placeholder, text)
    # 3. Protect inline code
    text = re.sub(r'`[^`]+`', make_placeholder, text)

    return text, placeholders


def restore_patterns(text, placeholders):
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


def has_translatable_content(text):
    cleaned = re.sub(r'XPLACEHOLDERX\d+X', '', text)
    cleaned = re.sub(r'[#*_\[\]()>!\-\s\d\.]', '', cleaned)
    return len(cleaned) > 0


def is_skip_line(line):
    stripped = line.strip()
    if not stripped:
        return True
    if re.match(r'^[-*_]{3,}$', stripped):
        return True
    if re.match(r'^<(?:div|/div|br\s*/?)[\s>]', stripped):
        return True
    return False


def translate_line(line):
    if is_skip_line(line):
        return line

    protected, placeholders = protect_patterns(line)

    if not has_translatable_content(protected):
        return line

    try:
        translated = translator.translate(protected)
        if translated:
            return restore_patterns(translated, placeholders)
    except Exception as e:
        print(f"  [Warning] Could not translate: {e}", file=sys.stderr)
        time.sleep(1)

    return line


def translate_readme(input_path="README.md", output_path="README_id.md"):
    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Build header for Indonesian file
    id_header = (
        '<div align="center">\n\n'
        '[![EN](https://img.shields.io/badge/🇬🇧-English-blue?style=flat-square)](README.md)'
        ' &nbsp; '
        '[![ID](https://img.shields.io/badge/🇮🇩-Indonesia-red?style=flat-square)](#)\n\n'
        '</div>\n\n'
        '> ⚙️ *File ini di-generate otomatis oleh GitHub Actions dari `README.md`. Jangan edit manual.*\n\n'
    )

    translated_lines = []
    in_code_block = False
    skip_header = True  # Skip the EN toggle header (first div block) from source

    for i, line in enumerate(lines):
        # Skip the opening toggle div from the source (first 5 lines)
        if skip_header and i < 5:
            continue
        skip_header = False

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            translated_lines.append(line)
            continue

        if in_code_block:
            translated_lines.append(line)
            continue

        translated_lines.append(translate_line(line))

        if i % 10 == 0 and i > 0:
            time.sleep(0.3)

    print(f"Writing {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(id_header)
        f.writelines(translated_lines)

    print(f"✅ Done! Translated → {output_path}")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "README_id.md"
    translate_readme(input_file, output_file)
