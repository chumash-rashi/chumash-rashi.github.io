# Changelog

Version number is shown in the footer of every page (`APP_VERSION` in each Rashi-*.html). To release: bump `APP_VERSION`, add an entry here, commit, then `git tag vX.Y.Z` and push the tag to both remotes (`origin` and `pages`).

Feedback: the footer "Feedback" link opens a pre-filled GitHub issue at https://github.com/yishairasowsky/chumash_rashi/issues (needs a free GitHub account).

## 1.3.2
- Words quoted in single quotes now take their vowels from the pasuk (e.g. תּוֹמִם).

## 1.3.1
- Pasuk: removed cantillation marks that sat under a vowel and overlapped it.

## 1.3.0
- After answering, Rashi's words are shown directly under the citation (with the Sefaria link); the show/hide button is gone.

## 1.2.0 — 2026-11-15
- After answering, a citation line shows the chapter and verse, the dibbur hamaschil, and a link to that Rashi on Sefaria.

## 1.1.1 — 2026-11-15
- After answering, the screen now shows only the green/red marking on the choices and the 'Rashi's language' button; the separate explanation box was removed.

## 1.1.0 — 2026-11-15
- New: Parshas Vayetze (Bereishis 28:10 – 32:3), 197 Rashis with a Hebrew quiz and niqqud on all questions and choices. Text from Sefaria (public export).
- Fixed: Lech Lecha, Toldot and Chayei Sarah all saved progress under the same browser key and overwrote each other. Each parsha now has its own key (Toldot and Chayei Sarah progress starts fresh).
- New scripts: build_parsha_data.py (source data from the Sefaria export) and build_parsha_page.py (assembles a page from the Toldot template).

## 1.0.1 — 2026-11-15
- Toldot: words quoted from the pasuk in questions and choices now take their niqqud directly from the pasuk (e.g. יָצֹא יָצָא), fixing wrong vowels.

## 1.0.0 — 2026-11-15
- Toldot: all quiz questions and answer choices now have full niqqud.
- Toldot: quiz written directly in natural Hebrew.
- Quotation marks no longer appear flipped in right-to-left text.
- After answering: choices stay visible with green/red marking, followed by a one-line explanation; no more overlapping panels.
- Fixed text shrinking to a tiny size after answering; explanation now scales with the rest of the layout and fits any window height.
- "Show Rashi's language" is now a clear button.
- No auto-advance after answering; use the Next button.
- Added version number and Feedback link in the footer.
