#!/usr/bin/env python3
"""
Auto-translate the ENGLISH section of README.md and update the INDONESIAN section in-place.

Structure of README.md:
  [header/toggle]
  <!-- ENGLISH_START -->
  ...english content...
  <!-- ENGLISH_END -->
  <!-- INDONESIAN_START -->
  ...indonesian content (auto-generated)...
  <!-- INDONESIAN_END -->

This script:
  1. Reads README.md
  2. Extracts the ENGLISH section
  3. Translates it line-by-line (preserving HTML, badges, links, code blocks)
  4. Replaces the INDONESIAN section content with the translation
  5. Writes back to README.md
"""

import re
import sys
import time
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='en', target='id')

ENGLISH_START = "<!-- ENGLISH_START -->"
ENGLISH_END   = "<!-- ENGLISH_END -->"
INDONESIAN_START = "<!-- INDONESIAN_START -->"
INDONESIAN_END   = "<!-- INDONESIAN_END -->"

INDONESIAN_HEADER = (
    "<!-- INDONESIAN_START -->\n"
    "## 🇮🇩 Versi Bahasa Indonesia\n\n"
    "> ⚙️ *Bagian ini di-generate otomatis oleh GitHub Actions. Edit di bagian Inggris di atas.*\n"
)


def protect_patterns(text):
    """Replace non-translatable patterns with unique placeholders."""
    placeholders = {}
    counter = [0]

    def make_placeholder(match):
        key = f"XPLACEHOLDERX{counter[0]}X"
        placeholders[key] = match.group(0)
        counter[0] += 1
        return key

    # Protect HTML tags
    text = re.sub(r'<[^>]+>', make_placeholder, text)
    # Protect Markdown link URLs: ](url)
    text = re.sub(r'\]\([^)]*\)', make_placeholder, text)
    # Protect inline code
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
    # Skip HTML comment markers
    if stripped.startswith('<!--') and stripped.endswith('-->'):
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


def translate_block(lines):
    """Translate a list of lines, skipping code blocks."""
    result = []
    in_code_block = False

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue

        if in_code_block:
            result.append(line)
            continue

        result.append(translate_line(line))

        # Small delay every 10 lines to avoid rate limiting
        if i % 10 == 0 and i > 0:
            time.sleep(0.3)

    return result


def update_readme(filepath="README.md"):
    print(f"Reading {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # --- Extract English section ---
    en_match = re.search(
        rf'{re.escape(ENGLISH_START)}\n(.*?)\n{re.escape(ENGLISH_END)}',
        content, re.DOTALL
    )
    if not en_match:
        print("ERROR: Could not find ENGLISH_START/ENGLISH_END markers in README.md", file=sys.stderr)
        sys.exit(1)

    english_content = en_match.group(1)
    english_lines = english_content.splitlines(keepends=True)

    # --- Translate ---
    print("Translating English section...")
    translated_lines = translate_block(english_lines)
    translated_content = "".join(translated_lines)

    # --- Build new Indonesian section ---
    new_indonesian_section = (
        f"{INDONESIAN_HEADER}\n"
        f"{translated_content}\n"
        f"{INDONESIAN_END}"
    )

    # --- Replace Indonesian section in file ---
    new_content = re.sub(
        rf'{re.escape(INDONESIAN_START)}.*?{re.escape(INDONESIAN_END)}',
        new_indonesian_section,
        content,
        flags=re.DOTALL
    )

    print(f"Writing updated {filepath}...")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Done! Indonesian section updated in {filepath}")


if __name__ == "__main__":
    readme_path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    update_readme(readme_path)
