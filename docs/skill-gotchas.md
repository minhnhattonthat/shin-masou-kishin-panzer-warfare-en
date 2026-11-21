# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- references/platform-ps1.md: `iso9660.py` reads 2048-byte ISOs only; for a raw MODE2/2352 .bin, read the PVD at `16*2352+24` (this repo's `tools/disc_ls.py`).
- references/platform-ps1.md: script-text pools here are referenced by absolute RAM pointers inside fixed 16-byte commands; a RAM dump + `ramfind`-style chunk match found the load base in one step (`tools/ramfind.py`).
- SKILL.md / setup: context-mode trims Bash/Read output over ~4 KB even for `--help`; redirect help to a file and Read it with limit.
- references/graphics.md: no TIM scanner ships with the skill for PS1; this repo's `tools/tim.py` + `tools/montage.py` (find, decode, labelled contact sheets) did the survey.
- references/platform-ps1.md: ffmpeg's psxstr demuxer decodes a movie cut straight out of the raw .bin (2352-byte sectors from the file's LBA); split MOV.STR into movies where the STR frame number resets (`tools/str_movies.py`), then `-vf fps=1/3` frames + montage = FMV text survey in minutes, no jPSXdec.
- references/graphics.md: montage only byte-distinct TIMs (`montage.py --unique`) and skip the portrait size class: cut a 1500-TIM sweep from 33 sheets to 16.
- references/platform-ps1.md: to find the font path, a read watch on the event text pool (`watch.lua`, `--debugger`) gave the string loop in one run; its glyph lookup was a binary search over a 6-byte row table (`first code, row, page`), not Krom.
