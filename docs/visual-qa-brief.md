# Visual-QA reviewer brief - Shin Masou Kishin: Panzer Warfare (PS1)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/sheets/`, same scene names; the JP and EN runs mash the
  same way but drift apart, so match by content, not tile number) and `glossary.md` (read it with offset/limit:
  reads over ~4 KB come back as a stub). `$SKILL` = the output of `python tools/skill.py`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble: a few pixels of misalignment don't show
  at sheet scale. To measure one: `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- Japanese inside graphics (chapter-card logo 真魔装機神 / PANZER WARFARE, the title logo, the Cybuster advert FMV
  mov01, the memory-card system title 真・魔装機神システム and the card's save line: kept Japanese, D5 / D14);
- graphics-text screens not yet redrawn in the build the tour ran on (map command / status / option / battle
  labels, prologue pages, credits): `ok` with the note "gfx pending" unless the text layer itself is broken;
- dialogue speaker label above the text, honorifics like -san / -sama (D1), no 「」 quotes (D8);
- the 8 HUD army labels abbreviated V./N./R. Soldier/Knight, Rebel Sol./Kt. (D15, the JP abbreviates too).

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
