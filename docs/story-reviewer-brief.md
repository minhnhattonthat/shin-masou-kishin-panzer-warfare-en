# Story reviewer brief - Shin Masou Kishin: Panzer Warfare (PS1)

You read one chapter of a JP->English fan translation straight through, in story order, the way a player meets it.
Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Return the report as your final message; the controller saves it.

## Inputs (paths in your dispatch)
Files over ~4 KB come back as a stub from a whole-file Read: read every file with offset/limit, 120 lines per call,
until the end.
- Chapter file `work/qa/story/chapters/NN_evXXX.txt`: every line of the chapter in script order,
  `>> id | speaker | kind | JP` then `   EN` (` / ` = line break). Read ALL of it before judging.
  Script order is story order, except that battle win/lose branches and the answers to a `choice` sit side by side:
  don't read alternatives as one sequence. Long multi-paragraph entries with no speaker are chapter-intro scroll pages.
- `docs/synopsis.md` (plot, who is who, late reveals), `docs/style-reference.md` (voice per character),
  `glossary.md` (rulings at the top; names must match it exactly).

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early; the same JP line repeated reads the same way.
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others (Captain / Alma / Princess...). Name the line where a voice drifts or goes neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.
- Width is checked by tool: a dialogue box holds 3 lines of ~40 characters (wrapped automatically), so a suggestion
  must stay within about 115 characters; keep scroll-page line structure (same ` / ` breaks) and each line <= 45 chars.

## Report: TSV lines only, nothing else
One line per finding, tab-separated: `SEV<TAB>id<TAB>suggested full English for that id<TAB>JP gist and problem`.
SEV = C (continuity break, reveal given away, wrong speaker), I (voice drifted or flattened, emotional beat lost,
setup or callback dropped, joke dead), M (minor style, deferred to the polish pass). The suggested English replaces the
whole entry: write it complete, ` / ` only where a hard break is wanted, no notes in it.
Last line: `VERDICT<TAB>ok|issue<TAB>one sentence why` (ok = no C/I).
