#!/usr/bin/env python3
"""
Generate a Rashi quiz HTML file from Sefaria source data.

Usage:
    python generate_quiz.py chayei_sarah_source.json "Chayei Sarah" "חיי שרה" Rashi-Chayei-Sarah.html
"""

import sys
import os
import json
import re
import time
from pathlib import Path
from functools import partial

print = partial(print, flush=True)

import anthropic


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if creds_path.exists():
        creds = json.loads(creds_path.read_text())
        token = creds.get("claudeAiOauth", {}).get("accessToken")
        if token:
            return anthropic.Anthropic(auth_token=token)
    raise RuntimeError("No credentials found.")


QUIZ_SYSTEM = """\
You generate quiz questions for a Rashi study app. You will receive a batch of Rashi commentaries with their verses.

For each Rashi, generate 1-2 quiz "points" (questions). Each point tests understanding of what Rashi is explaining.

For each Rashi entry you receive, return a JSON object with:
- "id": same id from input
- "dh": the dibbur hamaschil (opening words of Rashi, in Hebrew, WITHOUT the verse text prefix — just Rashi's own first words)
- "points": array of 1-2 objects, each with:
  - "q": a clear question about what Rashi is teaching (in English)
  - "options": exactly 3 answer choices (first one correct)
  - "kasha": what textual difficulty is bothering Rashi (in English)
  - "answer": Rashi's answer/explanation (in English, 1-2 sentences)

Guidelines:
- Questions should test comprehension, not trivia
- The correct answer is ALWAYS options[0] — the app will shuffle them
- Keep language clear and concise
- The "kasha" explains what problem in the verse prompted Rashi to comment
- Extract the dibbur hamaschil carefully from the Hebrew Rashi text (the bold/leading words before the commentary begins)

Return ONLY a JSON array. No markdown fences."""


def extract_dh(rashi_he: str) -> str:
    """Try to extract dibbur hamaschil from Hebrew Rashi text."""
    # Usually the DH is the first phrase before a period or dash or commentary marker
    # Sefaria format often has DH as first words followed by a dash or period
    text = rashi_he.strip()
    # Look for common separators
    for sep in [' — ', ' – ', '. ', '־ ']:
        if sep in text:
            return text.split(sep)[0].strip()
    # Fallback: first 3 words
    words = text.split()
    return ' '.join(words[:3])


def generate_quiz_batch(client, entries, attempt_num=0):
    """Send a batch of Rashi entries to Claude for quiz generation."""
    batch_input = []
    for e in entries:
        batch_input.append({
            "id": e["id"],
            "verse_en": e["en"],
            "verse_he": e["he"][:150],
            "rashi_he": e["rashi_he"],
            "rashi_en": e["rashi_en"],
        })

    for attempt in range(5):
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=16000,
                system=QUIZ_SYSTEM,
                messages=[{"role": "user", "content": json.dumps(batch_input, ensure_ascii=False, indent=2)}],
            )
            break
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"   Rate limited, waiting {wait}s...")
            time.sleep(wait)
    else:
        raise Exception("Rate limit exceeded after 5 retries")

    text = msg.content[0].text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def build_data_array(source_data: dict, quiz_results: list) -> list:
    """Combine source data with quiz results into the DATA array format."""
    quiz_map = {q["id"]: q for q in quiz_results}
    data = []

    for key in sorted(source_data.keys(), key=lambda k: (int(k.split(':')[0]), int(k.split(':')[1]))):
        entry = source_data[key]
        ch, v = entry["ch"], entry["v"]

        for r_idx, rashi in enumerate(entry["rashis"]):
            rid = f"{ch}:{v}.{r_idx+1}"
            quiz = quiz_map.get(rid)
            if not quiz:
                continue

            dh = quiz.get("dh", extract_dh(rashi["he"]))
            # Build pasuk_html with <mark> around dh
            pasuk_html = entry["he"]
            dh_clean = re.sub(r'[\u0591-\u05C7]', '', dh)
            pasuk_clean = re.sub(r'[\u0591-\u05C7]', '', pasuk_html)
            start = pasuk_clean.find(dh_clean)
            if start >= 0:
                # Map back to real positions
                real_start = _cons_to_real(pasuk_html, start)
                real_end = _cons_to_real(pasuk_html, start + len(dh_clean))
                pasuk_html = (pasuk_html[:real_start] + "<mark>" +
                             pasuk_html[real_start:real_end] + "</mark>" +
                             pasuk_html[real_end:])

            item = {
                "id": rid,
                "ch": ch,
                "v": v,
                "n": r_idx + 1,
                "dh": dh,
                "pasuk_html": pasuk_html,
                "pasuk_en": entry["en"],
                "rashi_he": rashi["he"],
                "rashi_en": rashi["en"],
                "note": "",
                "points": quiz.get("points", []),
            }
            data.append(item)

    return data


def _cons_to_real(text, cons_pos):
    count = 0
    for i, ch in enumerate(text):
        if not ('\u0591' <= ch <= '\u05C7'):
            if count == cons_pos:
                return i
            count += 1
    return len(text)


def build_html(data: list, parsha_en: str, parsha_he: str) -> str:
    """Build the complete HTML quiz file using the template from existing files."""
    data_json = json.dumps(data, ensure_ascii=False)

    # Read the Lech Lecha HTML as template
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rashi-Lech-Lecha.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Extract everything before and after DATA
    m = re.search(r'const DATA = (\[.*?\]);\s*\n', template, re.DOTALL)
    if not m:
        raise ValueError("Could not find DATA in template")

    pre = template[:m.start(1)]
    post = template[m.end(1):]

    # Replace parsha name references
    pre = pre.replace('לך לך', parsha_he).replace('Lech Lecha', parsha_en)
    post = post.replace('לך לך', parsha_he).replace('Lech Lecha', parsha_en)

    return pre + data_json + post


def main():
    if len(sys.argv) < 5:
        print("Usage: python generate_quiz.py <source.json> <parsha_en> <parsha_he> <output.html>")
        sys.exit(1)

    source_path = sys.argv[1]
    parsha_en = sys.argv[2]
    parsha_he = sys.argv[3]
    output_path = sys.argv[4]

    with open(source_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    # Build flat list of Rashi entries
    entries = []
    for key in sorted(source_data.keys(), key=lambda k: (int(k.split(':')[0]), int(k.split(':')[1]))):
        entry = source_data[key]
        for r_idx, rashi in enumerate(entry["rashis"]):
            if not rashi["en"].strip():
                continue
            entries.append({
                "id": f"{entry['ch']}:{entry['v']}.{r_idx+1}",
                "he": entry["he"],
                "en": entry["en"],
                "rashi_he": rashi["he"],
                "rashi_en": rashi["en"],
            })

    print(f"Total Rashi entries to process: {len(entries)}")

    # Check for cached quiz results
    cache_path = source_path.replace('.json', '_quiz_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        cached_ids = {q["id"] for q in cached}
        print(f"Found {len(cached)} cached quiz results")
    else:
        cached = []
        cached_ids = set()

    remaining = [e for e in entries if e["id"] not in cached_ids]
    print(f"{len(remaining)} entries still need quiz generation")

    client = get_client()
    all_results = list(cached)

    BATCH = 8
    for i in range(0, len(remaining), BATCH):
        batch = remaining[i:i+BATCH]
        batch_num = i // BATCH + 1
        total_batches = (len(remaining) + BATCH - 1) // BATCH
        print(f"  Batch {batch_num}/{total_batches}...")
        try:
            results = generate_quiz_batch(client, batch)
            all_results.extend(results)
            print(f"    Got {len(results)} quiz entries")
        except Exception as e:
            print(f"    ERROR: {e}")
            break

        # Save progress
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        if i + BATCH < len(remaining):
            time.sleep(2)

    # Save final cache
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\nBuilding DATA array...")
    data = build_data_array(source_data, all_results)
    print(f"  {len(data)} quiz entries in DATA")

    print(f"Building HTML...")
    html = build_html(data, parsha_en, parsha_he)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nDone! Written to {output_path}")


if __name__ == "__main__":
    main()
