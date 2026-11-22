# Shin Masou Kishin: Panzer Warfare English translation

Unofficial English fan translation of **Shin Masou Kishin: Panzer Warfare** (PlayStation, Banpresto, 1999,
SLPS-02319): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Story dialogue, chapter intro scrolls, battle quotes | Translated |
| Menus, unit / pilot / weapon names, spirit commands, system messages | Translated |
| Chapter cards, map and status UI, menus, prologue pages, loading screen | Translated (redrawn) |
| Staff roll | Translated (redrawn) |
| Attract movie (boot advert) captions | English subtitles burned in |
| Name entry | None in this game (names are fixed) |
| Memory-card save title (shown by the PS1 BIOS card manager) | Left in Japanese (too narrow, see `docs/decisions.md` D14) |
| A few single-kanji status icons with no English spirit (加幸旋結協超) | Left in Japanese |

Known issues: none known; see [Issues](../../issues).

### Base disc and patching

The patch (xdelta3) applies to the Redump dump *Shin Masou Kishin - Panzer Warfare (Japan)*, single track:

| File | Size | CRC32 | MD5 | SHA-1 |
|---|---|---|---|---|
| `Shin Masou Kishin - Panzer Warfare (Japan).bin` | 380257248 | A2E984CE | 924d016753b2031ebf07b99ff2976321 | e0b0a78b9d1c48a0c6a150ab1cd55a6e72977298 |

The release zip's README.txt lists the patched image's hashes and the steps. Tested in PCSX-Redux (SCPH-5500 BIOS);
start from a cold boot, since savestates from the Japanese disc carry the old font and text.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/shin-masou-kishin-panzer-warfare-en
cd shin-masou-kishin-panzer-warfare-en
# copy your dump to: rom/Shin Masou Kishin - Panzer Warfare (Japan).bin (+ .cue)
#   (380257248 bytes, SHA-1 e0b0a78b9d1c48a0c6a150ab1cd55a6e72977298; the build refuses any other dump, see rom.sha1)
python -X utf8 build.py                                # -> build/smk_en.bin + .cue
python -X utf8 tools/check.py                          # tests + text lint
python -X utf8 tools/release.py                        # gates, xdelta patch, release/SMK_EN_vX.Y.zip
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Banpresto's and is included only so
the translation can be checked against it. Shin Masou Kishin: Panzer Warfare is (c) Banpresto; this project is not
affiliated with them. Fonts: Nunito (SIL OFL), see `docs/fonts.md`. Disc tools: mkpsxiso/dumpsxiso, armips.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
