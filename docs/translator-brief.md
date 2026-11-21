# Translator brief - Shin Masou Kishin: Panzer Warfare (PS1, 1999)

You translate part of the Japanese script of Shin Masou Kishin: Panzer Warfare (Banpresto) into English for a fan
patch. A tactical mecha RPG: young knight-cadet Keigo pilots a Masoukishin for the holy kingdom of Vartzpheem against
the monsters of Daus and the armies of rival nations, on the world of A-Zeluth. Earnest, sometimes comic war drama.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before the
next. Do all translation yourself; do not dispatch subagents.

## Read first (files over ~4 KB: read with offset/limit, the Read tool may return a stub otherwise)
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch; `glossary.md` (Rulings, Style rules, tables).
3. `docs/synopsis.md` - plot, who is who and the late reveals. Don't give a reveal away early.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. ` / ` marks a line break in the Japanese. Lines are in story order:
use neighbours for context. Forms:
- `msg` - an event message box (speaker label is printed by the game; speaker empty = narration, a caption such as
  a place name, or a system line). Write it as one flowing text: the check word-wraps it to 240 px x 3 lines. Use a
  literal `\n` only for a caption/list whose lines must stay separate (place name / sub-place, a letter's heading).
  A box holds roughly 120 characters; if yours doesn't fit, tighten the wording, don't cut meaning.
- `choice` - a choice menu, one option per line: write exactly the same number of lines, joined by `\n`, each
  <= 228 px (~38 characters). Keep the parentheses if the JP options have them.
- `scroll` - a chapter-intro scroll page: lines joined by `\n`, at most the JP line count (empty lines count; keep
  them where the JP has stanza breaks), each <= 256 px (~42 characters). The game centres each line.
- `bq` - a battle quote (one character's line in the battle animation box): flowing text, auto-wrapped to 188 px x 2
  lines (~60 characters). Short and punchy.
- `menu` (exe strings: unit, weapon, command, help text) and `label` (save-slot chapter labels): `limit` is a hard
  byte count (1 byte per letter/space). Unit and weapon names keep official/glossary forms. Leading full-width spaces
  in the JP are layout: drop them (labels: the insert does not re-pad; just write the text). `{b}` etc. are codes.
- Control codes `{b} {h} {m} {r} {w} {z}` and `[XX]` must appear in the English exactly as often as in the JP
  (the colour codes wrap the coloured word: put them around the English equivalent).

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: `...`, `--`; no tabs inside the English, no
Japanese or full-width characters, no `\uXXXX`, no curly quotes.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.
It reports px overflow, too many lines, glyph-slot overflow (speaker + text > 140 letters), a stub last line (< 6
characters on the last wrapped line: reword so the last line is longer or the text shorter), byte limits, control
codes, glossary terms (a JP term present but its English form missing) and Avoid spellings.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Keep the speaker audible. JP register markers carry voice and must turn into English devices, not vanish: rough
  men's ぜ/ねぇ/ってんだ ("ain't", "ya", "damn", clipped grammar), old men's じゃ/のう/わし ("eh?", "my boy"),
  feminine かしら/わよ/のね ("I wonder...", "you know"), polite です/ます from a subordinate stays respectful, a
  noble's formal speech stays formal. A line any speaker could have said is a mistake.
- Names and terms exactly as in the glossary. Never abbreviate to fit; if a line can't fit without losing meaning,
  keep the meaning and report it as `LONG: id`.
- Honorifics: keep a JP honorific (-san, -sama, -dono) when the JP has one; titles (隊長 Captain, 教官 Instructor,
  陛下 Your Majesty, 殿下 Your Highness) become English titles. Name order Western.
- Punctuation per glossary Style rules: no 「」 quote marks in dialogue; thoughts in (parentheses); `...`; `!?`.
- Battle quotes: grunts and cries ("Ngh!", "Take this!") are fine; each quote stands alone in a random battle, so no
  references to "you" being a specific person unless the JP names one.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this, at most 15 lines)
`DONE: b0xx b0yy` (each with a passing check), then any of:
`NEW TERM: jp -> en (where)`, `UNSURE: id - note`, `LONG: id`, `CUT: id - what was dropped`.

## Notes from earlier batches
- (none yet)
