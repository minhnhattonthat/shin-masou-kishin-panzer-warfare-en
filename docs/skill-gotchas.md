# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- references/platform-ps1.md: `iso9660.py` reads 2048-byte ISOs only; for a raw MODE2/2352 .bin, read the PVD at `16*2352+24` (this repo's `tools/disc_ls.py`).
- references/platform-ps1.md: script-text pools here are referenced by absolute RAM pointers inside fixed 16-byte commands; a RAM dump + `ramfind`-style chunk match found the load base in one step (`tools/ramfind.py`).
- SKILL.md / setup: context-mode trims Bash/Read output over ~4 KB even for `--help`; redirect help to a file and Read it with limit.
- references/graphics.md: no TIM scanner ships with the skill for PS1; this repo's `tools/tim.py` + `tools/montage.py` (find, decode, labelled contact sheets) did the survey.
