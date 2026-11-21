# Graphics brief - Shin Masou Kishin: Panzer Warfare (PS1)

You redraw Japanese text drawn as graphics (menu sheets, battle labels, captions, credits) in English for a fan patch.
Work only on the groups named in your dispatch, one at a time in the order given, each one finished before the next.
Do all the drawing yourself; do not dispatch subagents. Read long files in parts (offset/limit): reads above ~4 KB
come back as a stub.

## Read first
1. `work/gfx/<group>.txt` - your rows: TIM file + offset, what is on it, where it shows in game, notes.
2. The pilot `gfx/cards.tsv` (37 chapter cards) and `tools/gfx.py` (its docstring: the row columns, `preview`,
   `check`, `export`). Every image is made by a row in `gfx/<group>.tsv`; the build reads every `gfx/*.tsv` and
   writes each redrawn TIM into every byte-identical copy on the disc, so you edit one copy only.
3. `glossary.md` (read in parts) and `docs/fonts.md` - names and terms exactly as in the glossary; only fonts under
   `fonts/`. Graphic labels must use the same words as the text menus: grep `script/exe.json` for the Japanese
   word (`"jp": "...移動`) and use its `en`; spirit commands, stats and terrain are also in the glossary.
4. `$SKILL/references/graphics.md` §Edit and re-import and §Lettering (`$SKILL` = output of `python tools/skill.py`).

## How to work
- See the original: `python -X utf8 tools/tim.py` output is already in `work/gfx/tim/<FILE>/<offset>.png` (first CLUT
  only). For another CLUT, `tools/gfx.py export FILE:OFF --rect 0,0,W,H --clut N --out <scratch>.png`.
  The colours a screen really uses are in the in-game shots named in your group file.
- Two ways to draw a label:
  - **text row**: font `vwf` (the game's own 12 px Latin, matches the dialogue), `tiny5` / `silk` (8 px em, 5 px
    caps: for cells under ~10 px tall), or a TTF under `fonts/` at a size. `ink`/`edge`/`bg` are TIM values
    (palette indices); `auto` copies them from the original rect. One font, size and edge per label class.
  - **img row** when a text row can't match the art (gradient fills, two-colour letters, hand-kerned pixel text):
    `export` the rect, draw on it with a small script `tools/gfx_<group>.py` (PIL, palette indices only, no
    antialiasing unless the original has it), save to `gfx/out/<group>/<name>.png`, and point an `img` row at it.
- Rects: cover every pixel of the Japanese (dakuten, tails, AA edges) and nothing of the neighbouring cell. Atlas
  cells are drawn at fixed sizes by the game code: the English must fit inside the original cell's rect.
- Full words, no abbreviations (D4). If something cannot fit even with `tiny5`, use the shortest full wording; if
  that still fails, abbreviate only that label and list it in your report as a flagged abbreviation.
- Keep English that is already in the art (START, LOAD, Game Over, INTERMISSION...) untouched.

## You may write only
`gfx/<group>.tsv`, `gfx/out/<group>/`, `tools/gfx_<group>.py`. Don't edit `tools/gfx.py`, the build, `glossary.md`
or another group's files; don't run `build.py` or an emulator, and don't commit. Shared-code changes you need go in
your report.

## Check every image, offline
- `python -X utf8 tools/gfx.py check --group <group>` exits 0 (fit, rectcover on every rect, no pixel changed outside
  the rects). A rect whose neighbour art truly touches the text may carry `spill-ok <reason>` in its note.
- `python -X utf8 tools/gfx.py preview --group <group>` then read each `work/gfx/preview/<FILE>_<OFF>.png` (JP | EN,
  x3, CLUT from the row's `clut` column): every letter readable, nothing left of the Japanese. Zoom with
  `python -X utf8 $SKILL/scripts/sheet.py PNG --crop x,y,w,h --zoom 2 --out <scratch>.png` when unsure.

## Report (your final message)
Per group: rows done, rows not done and why, flagged abbreviations, new terms (`JP<TAB>EN`), shared-code changes
you need.
