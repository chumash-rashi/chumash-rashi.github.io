"""
Fetch Hebrew verses WITH taamei hamikra (cantillation marks) from Sefaria API
for all (chapter, verse) pairs referenced in the Rashi HTML quiz files.

Outputs JSON mapping files: vayera_taamim.json and lech_lecha_taamim.json
"""

import re
import json
import time
import urllib.request
import urllib.error
import sys

def extract_chapter_verse_pairs(html_path):
    """Extract unique (ch, v) pairs from the DATA array in an HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # The DATA is a JS array of objects with ch: and v: fields
    # They may be quoted or unquoted keys. Try both patterns.
    # Pattern for ch:18,v:1 or "ch":18,"v":1
    pairs = set()
    for m in re.finditer(r'["\']?ch["\']?\s*:\s*(\d+)\s*,\s*["\']?v["\']?\s*:\s*(\d+)', text):
        ch = int(m.group(1))
        v = int(m.group(2))
        pairs.add((ch, v))

    return sorted(pairs)


def fetch_verse(chapter, verse, retries=3):
    """Fetch a single verse from the Sefaria API. Returns the Hebrew text with taamim."""
    url = f"https://www.sefaria.org/api/texts/Genesis.{chapter}.{verse}?context=0&pad=0"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            # First call: print structure for debugging
            if chapter == -1:  # special debug flag
                return data

            # Try to get Hebrew text. Sefaria API v2/v3 may vary.
            he_text = None

            # Option 1: "he" field (array or string)
            if "he" in data:
                he = data["he"]
                if isinstance(he, list):
                    he_text = he[0] if len(he) == 1 else " ".join(he)
                elif isinstance(he, str):
                    he_text = he

            # Option 2: "versions" field
            if not he_text and "versions" in data:
                for ver in data["versions"]:
                    if ver.get("language") == "he":
                        txt = ver.get("text", "")
                        if isinstance(txt, list):
                            he_text = txt[0] if len(txt) == 1 else " ".join(txt)
                        elif isinstance(txt, str):
                            he_text = txt
                        break

            return he_text

        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} for Genesis {chapter}:{verse}, attempt {attempt+1}")
            if attempt < retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"  Error for Genesis {chapter}:{verse}: {e}, attempt {attempt+1}")
            if attempt < retries - 1:
                time.sleep(2)

    return None


def check_taamim(text):
    """Check if text contains cantillation marks (U+0591-U+05AF)."""
    if not text:
        return False
    return any('\u0591' <= c <= '\u05AF' for c in text)


def process_file(html_path, output_path, label):
    """Process one HTML file and create the taamim JSON mapping."""
    print(f"\n{'='*60}")
    print(f"Processing: {label}")
    print(f"  HTML: {html_path}")
    print(f"  Output: {output_path}")
    print(f"{'='*60}")

    pairs = extract_chapter_verse_pairs(html_path)
    print(f"  Found {len(pairs)} unique (chapter, verse) pairs")
    if pairs:
        print(f"  Range: {pairs[0]} to {pairs[-1]}")
        print(f"  All pairs: {pairs}")

    # First, do a test fetch to see API structure
    if pairs:
        test_ch, test_v = pairs[0]
        print(f"\n  Test fetch: Genesis {test_ch}:{test_v}")
        url = f"https://www.sefaria.org/api/texts/Genesis.{test_ch}.{test_v}?context=0&pad=0"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            test_data = json.loads(resp.read().decode('utf-8'))

        print(f"  API response top-level keys: {list(test_data.keys())}")
        if "he" in test_data:
            he = test_data["he"]
            print(f"  'he' type: {type(he).__name__}")
            if isinstance(he, list):
                print(f"  'he' length: {len(he)}")
                if he:
                    sample = he[0] if isinstance(he[0], str) else str(he[0])
                    print(f"  'he'[0] (first 200 chars): {sample[:200]}")
                    print(f"  Has taamim: {check_taamim(sample)}")
            elif isinstance(he, str):
                print(f"  'he' (first 200 chars): {he[:200]}")
                print(f"  Has taamim: {check_taamim(he)}")

        if "versions" in test_data:
            print(f"  'versions' type: {type(test_data['versions']).__name__}")
            if isinstance(test_data["versions"], list):
                for i, v in enumerate(test_data["versions"]):
                    print(f"  version[{i}] keys: {list(v.keys()) if isinstance(v, dict) else 'not a dict'}")
                    if isinstance(v, dict):
                        print(f"    language: {v.get('language')}, versionTitle: {v.get('versionTitle', 'N/A')}")
                        txt = v.get("text", "")
                        if isinstance(txt, list) and txt:
                            sample = txt[0] if isinstance(txt[0], str) else str(txt[0])
                            print(f"    text[0] (first 200 chars): {sample[:200]}")
                            print(f"    Has taamim: {check_taamim(sample)}")
                        elif isinstance(txt, str):
                            print(f"    text (first 200 chars): {txt[:200]}")
                            print(f"    Has taamim: {check_taamim(txt)}")

    # Now fetch all verses
    mapping = {}
    for i, (ch, v) in enumerate(pairs):
        key = f"{ch}:{v}"
        print(f"  [{i+1}/{len(pairs)}] Fetching Genesis {key}...", end=" ")
        he_text = fetch_verse(ch, v)
        if he_text:
            has_t = check_taamim(he_text)
            print(f"OK (taamim: {has_t}, len: {len(he_text)})")
            mapping[key] = he_text
        else:
            print("FAILED")

        # Be polite to the API
        if i < len(pairs) - 1:
            time.sleep(0.3)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\n  Wrote {len(mapping)} verses to {output_path}")

    # Summary
    with_taamim = sum(1 for t in mapping.values() if check_taamim(t))
    print(f"  Verses with taamim: {with_taamim}/{len(mapping)}")

    return mapping


if __name__ == "__main__":
    import os
    base = os.path.dirname(os.path.abspath(__file__))

    process_file(
        os.path.join(base, "Rashi-Vayera.html"),
        os.path.join(base, "vayera_taamim.json"),
        "Vayera (Genesis 18-22)"
    )

    process_file(
        os.path.join(base, "Rashi-Lech-Lecha.html"),
        os.path.join(base, "lech_lecha_taamim.json"),
        "Lech Lecha (Genesis 12-17)"
    )

    print("\nDone!")
