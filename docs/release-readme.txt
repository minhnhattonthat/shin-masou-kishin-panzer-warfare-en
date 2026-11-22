Shin Masou Kishin: Panzer Warfare - English translation v{version}
==================================================================

Unofficial English fan translation of Shin Masou Kishin: Panzer Warfare
(PlayStation, Banpresto, 1999, SLPS-02319). This zip holds only a patch:
you need your own dump of the Japanese disc. Do not share patched images.

What is translated
------------------
- All story dialogue, chapter intro scrolls and battle quotes.
- Menus, unit/pilot/weapon names, spirit commands, system messages.
- Graphics with text: chapter cards, map and status UI labels, menus,
  prologue pages, loading screen, staff roll, the attract-movie captions.
- Left in Japanese: the memory card's save title and save line (shown by
  the PS1 memory card manager), a few single-kanji status icons with no
  English spirit to show.

Base image (Redump: Shin Masou Kishin - Panzer Warfare (Japan))
---------------------------------------------------------------
File:   Shin Masou Kishin - Panzer Warfare (Japan).bin (single track)
Size:   {size} bytes
CRC32:  {crc}
MD5:    {md5}
SHA-1:  {sha1}

Patched image
-------------
Size:   {p_size} bytes
CRC32:  {p_crc}
MD5:    {p_md5}
SHA-1:  {p_sha1}

How to patch
------------
1. Check your .bin against the hashes above. Any other dump will not work.
2. Apply {patch} with xdelta3 (or a GUI such as Delta Patcher / xdelta UI):
     xdelta3 -d -s "Shin Masou Kishin - Panzer Warfare (Japan).bin" {patch} "Shin Masou Kishin - Panzer Warfare (English).bin"
3. Copy your .cue, rename it to match, and change the FILE line inside it
   to the new .bin name.

Playing
-------
Tested in PCSX-Redux (SCPH-5500 BIOS). Start from a cold boot of the
patched image; savestates made with the Japanese disc carry the old text
and font and will show garbage. In-game memory card saves are compatible.
Confirm = circle, as in the Japanese release.

Known issues: none known. Report bugs at
https://github.com/minhnhattonthat/shin-masou-kishin-panzer-warfare-en/issues
(a savestate helps most).

Credits
-------
Translation, hacking and tools: minhnhattonthat, with extensive AI
assistance (Claude by Anthropic). Corrections are very welcome.
Fonts: Nunito (SIL Open Font License), see the repository's docs/fonts.md.
Tools: mkpsxiso/dumpsxiso (Lameguy64), armips, PCSX-Redux.

Shin Masou Kishin: Panzer Warfare is (c) Banpresto. This is an unofficial
fan project, not affiliated with Banpresto or Bandai Namco; no game data
is included.
