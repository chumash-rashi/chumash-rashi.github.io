#!/usr/bin/env python3
"""
Convert Rashi quiz HTML files to fully Hebrew UI + content.
- Fetches pasuk text with taamei hamikra from Sefaria
- Translates all quiz content (questions, options, explanations) to Hebrew via Claude API
- Updates HTML UI strings to Hebrew
"""

import re
import json
import time
import sys
import os
from pathlib import Path
from functools import partial

# Force unbuffered output
print = partial(print, flush=True)

import requests
import anthropic


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

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
    raise RuntimeError("No credentials found. Set ANTHROPIC_API_KEY or ensure Claude Code is logged in.")


# ---------------------------------------------------------------------------
# Sefaria: fetch verses with taamim
# ---------------------------------------------------------------------------

def fetch_chapter_sefaria(book: str, chapter: int) -> dict[int, str]:
    """Fetch all verses of a chapter with taamim. Returns {verse_num: hebrew_text}."""
    url = f"https://www.sefaria.org/api/texts/{book}.{chapter}?context=0&pad=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.sefaria.org/",
    }
    sess = requests.Session()
    resp = sess.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    verses = {}
    he = data.get("he", [])
    if isinstance(he, list):
        for i, txt in enumerate(he):
            if isinstance(txt, str):
                # Strip HTML tags if any
                clean = re.sub(r'<[^>]+>', '', txt)
                verses[i + 1] = clean
    return verses


def fetch_all_taamim(chapters: list[int], book: str = "Genesis") -> dict[str, str]:
    """Fetch all verses for given chapters. Returns {"ch:v": text} mapping."""
    mapping = {}
    for ch in chapters:
        print(f"  Fetching {book} chapter {ch}...")
        try:
            verses = fetch_chapter_sefaria(book, ch)
            for v, txt in verses.items():
                mapping[f"{ch}:{v}"] = txt
            print(f"    Got {len(verses)} verses")
            time.sleep(0.5)  # be polite
        except Exception as e:
            print(f"    ERROR: {e}")
    return mapping


# ---------------------------------------------------------------------------
# Extract DATA from HTML
# ---------------------------------------------------------------------------

def extract_data_from_html(html_path: str) -> tuple[str, list[dict], str]:
    """Extract the DATA JSON array from the HTML file.
    Returns (pre_data_html, data_list, post_data_html)."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the DATA array
    m = re.search(r'const DATA = (\[.*?\]);\s*\n', content, re.DOTALL)
    if not m:
        raise ValueError(f"Could not find DATA array in {html_path}")

    data_str = m.group(1)
    data = json.loads(data_str)
    pre = content[:m.start(1)]
    post = content[m.end(1):]

    return pre, data, post


# ---------------------------------------------------------------------------
# Translate quiz content to Hebrew via Claude
# ---------------------------------------------------------------------------

TRANSLATE_SYSTEM = """\
You are translating a Torah/Rashi quiz from English to Hebrew.

You will receive a batch of quiz entries as JSON. Each entry has these fields to translate:
- "q": the question about Rashi's commentary
- "options": array of 3 answer choices
- "kasha": what is bothering Rashi (the textual difficulty)
- "answer": Rashi's answer/explanation

Translate ALL of these fields to clear, natural Hebrew. Use nikkud (vowels) on all Hebrew text.
For Torah/Rashi terminology, use standard Hebrew terms.
Keep the meaning precise — this is a Torah study quiz, accuracy matters.

The "pasuk_en" field should be translated to Hebrew as well (it's an English translation of the verse).
The "rashi_en" field should also be translated to Hebrew.

Return ONLY a JSON array with the same structure, where the translated fields replace the English ones.
Each entry in your output must have: "id", "q", "options", "kasha", "answer", "pasuk_en", "rashi_en".
Use the same "id" from the input so we can match entries.
Do NOT include any markdown formatting or code fences — just raw JSON."""

def translate_batch(client: anthropic.Anthropic, entries: list[dict]) -> list[dict]:
    """Send a batch of entries to Claude for Hebrew translation."""
    # Prepare the batch: extract only the fields we need translated
    batch = []
    for e in entries:
        item = {"id": e["id"]}
        for pt_idx, pt in enumerate(e["points"]):
            item[f"q_{pt_idx}"] = pt["q"]
            item[f"options_{pt_idx}"] = pt["options"]
            item[f"kasha_{pt_idx}"] = pt.get("kasha", "")
            item[f"answer_{pt_idx}"] = pt["answer"]
        item["pasuk_en"] = e["pasuk_en"]
        item["rashi_en"] = e["rashi_en"]
        item["num_points"] = len(e["points"])
        batch.append(item)

    for attempt in range(5):
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=16000,
                system=TRANSLATE_SYSTEM,
                messages=[{"role": "user", "content": json.dumps(batch, ensure_ascii=False, indent=2)}],
            )
            break
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"   Rate limited, waiting {wait}s (attempt {attempt+1}/5)...")
            time.sleep(wait)
    else:
        raise Exception("Rate limit exceeded after 5 retries")

    # Parse the response
    text = msg.content[0].text.strip()
    # Remove code fences if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Response preview: {text[:500]}")
        raise

    return result


def apply_translations(data: list[dict], translations: list[dict]) -> list[dict]:
    """Apply translated fields back into the data entries."""
    trans_map = {t["id"]: t for t in translations}

    for entry in data:
        t = trans_map.get(entry["id"])
        if not t:
            print(f"  WARNING: No translation for {entry['id']}")
            continue

        entry["pasuk_en"] = t.get("pasuk_en", entry["pasuk_en"])
        entry["rashi_en"] = t.get("rashi_en", entry["rashi_en"])

        for pt_idx, pt in enumerate(entry["points"]):
            pt["q"] = t.get(f"q_{pt_idx}", pt["q"])
            pt["options"] = t.get(f"options_{pt_idx}", pt["options"])
            pt["kasha"] = t.get(f"kasha_{pt_idx}", pt.get("kasha", ""))
            pt["answer"] = t.get(f"answer_{pt_idx}", pt["answer"])

    return data


# ---------------------------------------------------------------------------
# Update pasuk_html with taamim text
# ---------------------------------------------------------------------------

def update_pasuk_with_taamim(data: list[dict], taamim: dict[str, str]):
    """Replace pasuk_html with taamim version, preserving <mark> tags."""
    for entry in data:
        key = f"{entry['ch']}:{entry['v']}"
        taamim_text = taamim.get(key)
        if not taamim_text:
            continue

        # The current pasuk_html has <mark>...</mark> around the dibbur hamaschil
        # We need to find where the dh words appear in the taamim text and wrap them
        dh = entry["dh"]

        # Strip taamim and nikkud from dh to get consonants for matching
        dh_cons = strip_diacritics(dh)
        taamim_cons = strip_diacritics(taamim_text)

        # Find the dh in the taamim text by consonant matching
        start = taamim_cons.find(dh_cons)
        if start >= 0:
            # Map consonant position back to full text position
            real_start = consonant_pos_to_real(taamim_text, start)
            real_end = consonant_pos_to_real(taamim_text, start + len(dh_cons))
            marked = (taamim_text[:real_start] +
                     "<mark>" + taamim_text[real_start:real_end] + "</mark>" +
                     taamim_text[real_end:])
            entry["pasuk_html"] = marked
        else:
            # Fallback: just use taamim text without mark
            entry["pasuk_html"] = taamim_text


def strip_diacritics(text: str) -> str:
    """Remove all Hebrew diacritics (nikkud + taamim + other marks), keeping consonants and spaces."""
    return re.sub(r'[\u0591-\u05C7]', '', text).replace('\u05BE', '-').replace('־', '-')


def consonant_pos_to_real(text: str, cons_pos: int) -> int:
    """Map a position in the consonant-only string back to the position in the full text."""
    count = 0
    for i, ch in enumerate(text):
        if not ('\u0591' <= ch <= '\u05C7') and ch != '\u05BE' or ch == '-':
            if count == cons_pos:
                return i
            count += 1
    return len(text)


# ---------------------------------------------------------------------------
# Update HTML UI to Hebrew
# ---------------------------------------------------------------------------

def hebraize_ui(html: str, parsha_name_he: str, parsha_name_en: str, sefer_he: str) -> str:
    """Replace English UI strings with Hebrew equivalents."""
    replacements = [
        # Header
        (f'Rashi on {parsha_name_en}', f'רש״י על {parsha_name_he}'),
        # Buttons and labels
        ('Next unanswered', 'הבא ללא מענה'),
        ('Start over', 'התחל מחדש'),
        ('Go to', 'עבור אל'),
        ("Keys: 1–3 to answer · Enter or → for next · ← back",
         "מקשים: 3-1 לתשובה · Enter או ← להבא · → לחזור"),
        # Card labels
        ('Bothering Rashi', 'מה מקשה רש״י'),
        ('Rashi says', 'רש״י אומר'),
        ('Rashi on', 'רש״י על'),
        # Verdicts
        ("'Right.'", "'נכון.'"),
        ("'Not quite.'", "'לא בדיוק.'"),
        # Nav buttons
        ('Next Rashi →', 'רש״י הבא ←'),
        ('Answer to continue', 'ענה כדי להמשיך'),
        ('← Back', 'חזור →'),
        # Details
        ("Show Rashi's own words", 'הצג את לשון רש״י'),
        # Stats
        ('Rashis', 'רש״יות'),
        ('right', 'נכון'),
        # Sefer name in card ref
        (f'Bereishis', sefer_he),
        # End screen
        ('You finished', 'סיימת'),
        ('of', 'מתוך'),
        ('questions right', 'תשובות נכונות'),
        ('Rashis not finished', 'רש״יות לא הושלמו'),
        ('Go to first one', 'עבור לראשון'),
        ('Rashis to review', 'רש״יות לחזרה'),
        # Points
        ('Point ', 'נקודה '),
        # Confirm reset
        ('Erase progress?', 'למחוק התקדמות?'),
        ('Yes, start over', 'כן, התחל מחדש'),
        ('Cancel', 'ביטול'),
        # Rashi count
        ('Rashi ', 'רש״י '),
        (' on this posuk', ' על פסוק זה'),
        ('1 Rashi on this posuk', 'רש״י 1 על פסוק זה'),
        # Text label
        ('Text: Sefaria (Hebrew); translation: Metsudah Rashi Chumash',
         'טקסט: ספריא; תרגום: מצודה רש״י על חומש'),
    ]

    for eng, heb in replacements:
        html = html.replace(eng, heb)

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_file(html_path: str, parsha_he: str, parsha_en: str, chapters: list[int], sefer_he: str = "בראשית"):
    print(f"\n{'='*60}")
    print(f"Processing: {parsha_en} → Hebrew")
    print(f"{'='*60}")

    # 1. Extract DATA
    print("\n1. Extracting DATA from HTML...")
    pre, data, post = extract_data_from_html(html_path)
    print(f"   Found {len(data)} entries")

    # 2. Fetch taamim
    print("\n2. Fetching taamei hamikra from Sefaria...")
    taamim_file = html_path.replace('.html', '_taamim.json')
    if os.path.exists(taamim_file):
        print(f"   Using cached taamim from {taamim_file}")
        with open(taamim_file, 'r', encoding='utf-8') as f:
            taamim = json.load(f)
    else:
        taamim = fetch_all_taamim(chapters)
        with open(taamim_file, 'w', encoding='utf-8') as f:
            json.dump(taamim, f, ensure_ascii=False, indent=2)
        print(f"   Saved taamim to {taamim_file}")

    # 3. Update pasuk with taamim
    print("\n3. Updating pasukim with taamei hamikra...")
    update_pasuk_with_taamim(data, taamim)

    # 4. Translate to Hebrew
    print("\n4. Translating quiz content to Hebrew...")
    client = get_client()

    # Check for cached translations
    trans_file = html_path.replace('.html', '_translations.json')
    if os.path.exists(trans_file):
        with open(trans_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        if cached:
            cached_ids = {t["id"] for t in cached}
            print(f"   Found {len(cached)} cached translations")
        else:
            cached = []
            cached_ids = set()
    else:
        cached = []
        cached_ids = set()

    # Filter out already-translated entries
    remaining = [e for e in data if e["id"] not in cached_ids]
    print(f"   {len(remaining)} entries still need translation")

    # Process in batches of 5 (smaller to avoid rate limits)
    BATCH = 5
    all_translations = list(cached)
    for i in range(0, len(remaining), BATCH):
        batch = remaining[i:i+BATCH]
        batch_num = i // BATCH + 1
        total_batches = (len(remaining) + BATCH - 1) // BATCH
        print(f"   Batch {batch_num}/{total_batches} (entries {i+1}-{min(i+BATCH, len(remaining))})...")
        try:
            translated = translate_batch(client, batch)
            all_translations.extend(translated)
            print(f"   Got {len(translated)} translations")
        except Exception as e:
            print(f"   ERROR in batch {batch_num}: {e}")
            break
        # Save progress after each batch
        with open(trans_file, 'w', encoding='utf-8') as f:
            json.dump(all_translations, f, ensure_ascii=False, indent=2)
        if i + BATCH < len(remaining):
            time.sleep(5)  # rate limit

    # Save final translations
    with open(trans_file, 'w', encoding='utf-8') as f:
        json.dump(all_translations, f, ensure_ascii=False, indent=2)
    print(f"   Saved {len(all_translations)} translations to {trans_file}")

    # 5. Apply translations
    print("\n5. Applying translations to DATA...")
    data = apply_translations(data, all_translations)

    # 6. Rebuild HTML
    print("\n6. Rebuilding HTML...")
    data_json = json.dumps(data, ensure_ascii=False)
    new_html = pre + data_json + post

    # 7. Hebraize UI
    print("\n7. Updating UI to Hebrew...")
    new_html = hebraize_ui(new_html, parsha_he, parsha_en, sefer_he)

    # Add dir="rtl" to body if not present
    if 'dir="rtl"' not in new_html:
        new_html = new_html.replace('<body>', '<body dir="rtl">')

    # Write output
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"\n   ✓ Written to {html_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))

    # Process Vayera first (user is actively using it)
    process_file(
        os.path.join(base, "Rashi-Vayera.html"),
        parsha_he="וירא",
        parsha_en="Vayera",
        chapters=list(range(18, 23)),
    )

    # Then Lech Lecha
    process_file(
        os.path.join(base, "Rashi-Lech-Lecha.html"),
        parsha_he="לך לך",
        parsha_en="Lech Lecha",
        chapters=list(range(12, 18)),
    )

    print("\nDone! Both files updated to Hebrew.")
