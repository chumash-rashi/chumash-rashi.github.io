#!/usr/bin/env python3
"""Regenerate the quiz points (and a plain-Hebrew explanation of each Rashi) directly in Hebrew
with a strong model, replacing the translated-from-English text in an existing Rashi-*.html file.

Usage: python regen_quiz_hebrew.py Rashi-Toldot.html toldot_source.json
"""
import sys, re, json, time
from concurrent.futures import ThreadPoolExecutor
from generate_quiz import get_client

MODEL = "claude-opus-5-5"

SYSTEM = """אתה מורה מנוסה לחומש ורש״י שכותב שאלות חזרה לתלמידים בעברית טובה, טבעית ומדויקת.

תקבל רש״י אחד (בעברית), את הפסוק שהוא מפרש, ותרגום אנגלי של הרש״י לעזר. עליך לכתוב 1–2 שאלות הבנה על מה שרש״י מלמד.

כללים:
- כתוב בעברית תקנית, קולחת וטבעית, בלי תרגום מילולי מאנגלית, בלי מילים מומצאות ובלי שגיאות דקדוק. כתיבה בלי ניקוד, מלבד ציטוטי מקרא/חז״ל שמועתקים כמות שהם.
- השאלה צריכה לבדוק הבנה של הנקודה של רש״י (מה הקשה לו, או מה הוא מסביר), לא פרטים שוליים ולא ידיעות כלליות. נסח אותה בבהירות וקצרות (עד כ-20 מילים).
- בדיוק 3 תשובות אפשריות; הראשונה היא הנכונה (האפליקציה תערבב). התשובות השגויות צריכות להיות סבירות ומפתות אך שגויות בבירור לפי רש״י, באורך דומה לנכונה, ולא מגוחכות. כל תשובה עד כ-14 מילים.
- "kasha": מה הקושי בפסוק שגרם לרש״י לפרש (משפט אחד בעברית טובה).
- "answer": תשובת רש״י במשפט או שניים, מדויקת לטקסט של רש״י. אל תמציא דברים שאינם ברש״י.
- "simple": הסבר קצר ופשוט בעברית של דברי רש״י כולו (1–3 משפטים).
- "dh": ראשי התיבות של דיבור המתחיל — המילים הראשונות של רש״י עד הנקודה, בדיוק כפי שהן כתובות (ללא ניקוד).
- אם רש״י קצר ופשוט (למשל מזהה מי/מאיפה/כמה) — שאלה אחת. שתי שאלות רק כשיש שני רעיונות נפרדים.

החזר JSON בלבד, ללא טקסט נוסף וללא גדרות קוד: מערך של אובייקטים:
{"id": "...", "dh": "...", "simple": "...", "points": [{"q": "...", "options": ["נכונה","שגויה","שגויה"], "kasha": "...", "answer": "..."}]}"""


def strip_niqqud(s):
    return re.sub(r'[֑-ׇ]', '', s)


def call(client, batch):
    payload = [{"id": e["id"], "pasuk": strip_niqqud(e["pasuk"]), "rashi_he": strip_niqqud(e["rashi_he"]),
                "rashi_en": e["rashi_en"]} for e in batch]
    last = None
    for attempt in range(5):
        try:
            r = client.messages.create(model=MODEL, max_tokens=8000, system=SYSTEM,
                                       messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}])
            text = r.content[0].text.strip()
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            out = json.loads(text)
            ids = {o["id"] for o in out}
            assert ids == {e["id"] for e in batch}, "id mismatch"
            for o in out:
                assert 1 <= len(o["points"]) <= 2
                for p in o["points"]:
                    assert len(p["options"]) == 3
            return out
        except Exception as ex:
            last = ex
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"batch failed: {last}")


def main():
    html_path, source_path = sys.argv[1], sys.argv[2]
    html = open(html_path, encoding='utf-8').read()
    m = re.search(r'(const DATA = )(\[.*?\])(;\s*\n)', html, re.S)
    data = json.loads(m.group(2))
    src = json.load(open(source_path, encoding='utf-8'))

    entries = []
    for x in data:
        ch, v = x["ch"], x["v"]
        s = src[f"{ch}:{v}"]
        r = s["rashis"][x["n"] - 1]
        entries.append({"id": x["id"], "pasuk": s["he"], "rashi_he": r["he"], "rashi_en": r["en"]})

    cache_path = html_path.replace('.html', '_hebrew_quiz.json')
    try:
        done = {o["id"]: o for o in json.load(open(cache_path, encoding='utf-8'))}
    except FileNotFoundError:
        done = {}
    todo = [e for e in entries if e["id"] not in done]
    print(f"{len(done)} cached, {len(todo)} to generate", flush=True)

    client = get_client()
    batches = [todo[i:i + 4] for i in range(0, len(todo), 4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for n, res in enumerate(pool.map(lambda b: call(client, b), batches), 1):
            for o in res:
                done[o["id"]] = o
            json.dump(list(done.values()), open(cache_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f"  batch {n}/{len(batches)} ok", flush=True)

    for x in data:
        o = done[x["id"]]
        x["points"] = o["points"]
        x["rashi_en"] = o["simple"]
    new = m.group(1) + json.dumps(data, ensure_ascii=False) + m.group(3)
    html = html[:m.start()] + new + html[m.end():]
    open(html_path, 'w', encoding='utf-8', newline='').write(html)
    print("done", len(data), flush=True)


if __name__ == "__main__":
    main()
