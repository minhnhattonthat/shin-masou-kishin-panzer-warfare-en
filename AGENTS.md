# Shin Masou Kishin: Panzer Warfare (PS1, SLPS-02319) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, `python tools/skill.py` prints it). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Hooks:    `git config core.hooksPath tools/hooks` (once per clone; the pre-commit hook runs Check)
- Build:    `python -X utf8 build.py` -> build/smk_en.bin + .cue (checks the dump against `rom.sha1`, unpacks fresh into `build/disc/`, repacks; ~3 s)
- Check:    `python -X utf8 tools/check.py`  (tests + lint)
- Extract:  `python -X utf8 tools/extract.py [--merge]` -> `script/` (writes missing files; `--merge` refreshes jp, keeps en; reads `work/disc/tree`)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/smk_en.cue --out work/qa/smoke --frames 3600 --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/smk_en.cue --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames <frames column> --sheet` (scenes: `tools/debug/scenes.tsv`, RAM facts `docs/re/debug.md`; never ask the user to play to a scene)
- Warp all: `python -X utf8 tools/debug/warp_all.py [NAME..] [--rom CUE] [--states]` (cold boot each scene, exit 1 if any is not reached; `work/qa/warp/summary.tsv`)
- Release:  `python -X utf8 tools/release.py` (xdelta vs the .bin; never publish without the user) (phase 9)
- Clean:    `python -X utf8 tools/clean.py`

## Paths
- Original disc: `rom/Shin Masou Kishin - Panzer Warfare (Japan).bin/.cue` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`).
- Emulator: `tools/pcsx/` (PCSX-Redux nightly 32338.20261121.15 via `$SKILL/scripts/fetch_emu.py pcsx`; gitignored). BIOS `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`). Confirm = circle.
- Disc tools: `tools/mkpsxiso/mkpsxiso-2.30-win64/` (dumpsxiso/mkpsxiso v2.30, github.com/Lameguy64/mkpsxiso), `tools/armips/armips.exe` (v0.11.0). Unpacked disc: `work/disc/tree`, `work/disc/layout.xml`. Savestates: `work/states/`.
- Text: `script/` (JSON). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Close the emulator (by the PID emu.py prints) before building. Disc rebuild with mkpsxiso is byte-identical to the original (verified 2026-11-21).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
