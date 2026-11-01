#!/usr/bin/env python3
"""
Chumash with Rashi Lesson Generator

Parses a Chabad.org Torah-reading HTML file and generates a
clear, listenable lesson using the Claude API.

Usage:
    python generate_lesson.py <input.html> [output.txt]

If output path is omitted, it defaults to <input>.txt in the same directory.
"""

import re
import sys
from pathlib import Path

import json
import os

import anthropic
from bs4 import BeautifulSoup


def get_client() -> anthropic.Anthropic:
    """Return an Anthropic client, preferring API key then falling back to Claude Code OAuth."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)

    # Fall back to the OAuth token Claude Code stores locally
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if creds_path.exists():
        creds = json.loads(creds_path.read_text())
        token = creds.get("claudeAiOauth", {}).get("accessToken")
        if token:
            return anthropic.Anthropic(auth_token=token)

    raise RuntimeError(
        "No credentials found. Set ANTHROPIC_API_KEY or ensure Claude Code is logged in."
    )

# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def clean_text(element) -> str:
    """Return plain text from a BS4 element, collapsing whitespace."""
    if element is None:
        return ""
    text = element.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def parse_html(html_path: Path) -> list[dict]:
    """
    Parse the Chabad Torah-reading HTML and return a list of dicts with keys:
      - type: 'heading' | 'verse' | 'rashi'
      - For heading: text
      - For verse:   num, text
      - For rashi:   title (Hebrew words – English gloss), text
    """
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    parsha_div = soup.find("div", id="ParshaContent")
    if not parsha_div:
        raise ValueError("Could not find <div id='ParshaContent'> in the HTML file.")

    sections = []

    for elem in parsha_div.find_all(["h3", "tr"]):
        if elem.name == "h3":
            text = elem.get_text(strip=True)
            if text:
                sections.append({"type": "heading", "text": text})
            continue

        row_classes = elem.get("class", [])

        if "Co_Verse" in row_classes:
            tds = elem.find_all("td", recursive=False)
            english_td = tds[0] if tds else None
            if not english_td:
                continue

            num_elem = english_td.find("span", class_="co_VerseNum")
            text_elem = english_td.find("span", class_="co_VerseText")
            if num_elem and text_elem:
                sections.append({
                    "type": "verse",
                    "num": num_elem.get_text(strip=True),
                    "text": clean_text(text_elem),
                })

        elif "Co_Rashi" in row_classes:
            tds = elem.find_all("td", recursive=False)
            english_td = tds[0] if tds else None
            if not english_td:
                continue

            container = english_td.find("span", class_="Co_RashiContainer")
            if not container:
                continue

            title_elem = container.find("span", class_="co_RashiTitle")
            text_elem = container.find("span", class_="co_RashiText")

            title = clean_text(title_elem) if title_elem else ""
            text = clean_text(text_elem) if text_elem else ""

            if title or text:
                sections.append({"type": "rashi", "title": title, "text": text})

    return sections


# ---------------------------------------------------------------------------
# Formatting for Claude
# ---------------------------------------------------------------------------

def format_for_claude(sections: list[dict]) -> str:
    """Turn the parsed sections into structured plain text for Claude."""
    lines = []
    for item in sections:
        if item["type"] == "heading":
            lines.append(f"\n=== {item['text']} ===\n")
        elif item["type"] == "verse":
            lines.append(f"VERSE {item['num']}: {item['text']}")
        elif item["type"] == "rashi":
            lines.append(f"  RASHI [{item['title']}]: {item['text']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude system prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a Torah teacher who explains Chumash with Rashi in a clear, listenable way.

You go step by step, in order, without skipping anything. For each pasuk (verse), \
you first explain the simple meaning in plain English so it's easy to follow. \
Then you go through each Rashi on that pasuk one at a time. For every Rashi, \
you first explain what question or problem in the verse is bothering Rashi, \
and then you explain how Rashi answers it.

You clearly signal where we are as you go — for example: \
"Now the next pasuk", "Now the first Rashi", "Now the second Rashi" — \
so it's easy to follow even just by listening.

You keep the language smooth and natural for audio, using simple English \
and gentle transliteration when helpful, so it sounds good read aloud \
rather than technical or academic.

You will receive the full text of a parsha section with its Rashi commentary, \
structured as VERSE lines and RASHI lines. Generate the complete lesson, \
covering every verse and every Rashi in order."""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_lesson(html_path: Path, output_path: Path) -> None:
    print(f"Parsing {html_path.name} ...")
    sections = parse_html(html_path)

    n_verses = sum(1 for s in sections if s["type"] == "verse")
    n_rashis = sum(1 for s in sections if s["type"] == "rashi")
    print(f"  Found {n_verses} verses and {n_rashis} Rashis.")

    formatted = format_for_claude(sections)

    print("Calling Claude API (streaming) ...")
    client = get_client()

    with open(output_path, "w", encoding="utf-8") as out:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Please generate the full lesson for the following "
                        "parsha text with Rashi commentary:\n\n" + formatted
                    ),
                }
            ],
        ) as stream:
            for text_chunk in stream.text_stream:
                out.write(text_chunk)
                print(text_chunk, end="", flush=True)

    print(f"\n\nLesson written to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_lesson.py <input.html> [output.txt]")
        sys.exit(1)

    html_in = Path(sys.argv[1])
    if not html_in.exists():
        print(f"Error: file not found: {html_in}")
        sys.exit(1)

    txt_out = Path(sys.argv[2]) if len(sys.argv) >= 3 else html_in.with_suffix(".txt")

    generate_lesson(html_in, txt_out)
