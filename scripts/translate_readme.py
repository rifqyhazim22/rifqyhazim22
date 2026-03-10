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

# Initialize translator
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

    # Order matters: most specific patterns first.
    # 1. Protect HTML tags (including self-closing)
    text = re.sub(r'<[^>]+>', make_placeholder, text)
    # 2. Protect Markdown link URLs: ](url)
    text = re.sub(r'\]\([^)]*\)', make_placeholder, text)
    # 3. Protect inline code
    text = re.sub(r'`[^`]+`', make_placeholder, text)

    return text, placeholders


def restore_patterns(text, placeholders):
    """Restore all placeholders to their original values."""
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


def has_translatable_content(text):
    """Check if the protected text still has real words to translate."""
    # Remove placeholders
    cleaned = re.sub(r'XPLACEHOLDERX\d+X', '', text)
    # Remove markdown syntax characters
    cleaned = re.sub(r'[#*_\[\]()>!\-\s\d\.]', '', cleaned)
    return len(cleaned) > 0


def is_skip_line(line):
    """Return True if the line should not be translated at all."""
    stripped = line.strip()
    # Empty line
    if not stripped:
        return True
    # Horizontal rule
    if re.match(r'^[-*_]{3,}$', stripped):
        return True
    # Line is a single HTML block element (no inner text visible)
    # e.g. <div align="center"> or </div> or <br />
    if re.match(r'^<(?:div|/div|br\s*/?)[\s>]', stripped):
        return True
    return False


def translate_line(line):
    """Translate a single line of markdown, preserving all syntax."""
    if is_skip_line(line):
        return line

    # Protect all non-translatable patterns
    protected, placeholders = protect_patterns(line)

    # If nothing is left to translate, return original
    if not has_translatable_content(protected):
        return line

    try:
        translated = translator.translate(protected)
        if translated:
            return restore_patterns(translated, placeholders)
    except Exception as e:
        print(f"  [Warning] Could not translate line: {e}", file=sys.stderr)
        time.sleep(1)  # Brief pause on error to avoid rate limiting

    return line  # Fallback to original on failure


def translate_readme(input_path="README.md", output_path="README_id.md"):
    """Read, translate, and write the README."""
    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    translated_lines = []
    in_code_block = False

    for i, line in enumerate(lines):
        # Toggle code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            translated_lines.append(line)
            continue

        # Never translate inside code blocks
        if in_code_block:
            translated_lines.append(line)
            continue

        translated_line = translate_line(line)
        translated_lines.append(translated_line)

        # Small delay to avoid hitting rate limits
        if i % 10 == 0 and i > 0:
            time.sleep(0.3)

    print(f"Writing {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(translated_lines)

    print(f"✅ Done! Translated {len(lines)} lines → {output_path}")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "README_id.md"
    translate_readme(input_file, output_file)
