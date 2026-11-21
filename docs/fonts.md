# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| (game's own) BAT_TIM 0x480000 full-width Latin cells | the game's 12 px font | game data | yes (already on the disc) | dialogue VWF, `vwf` font in gfx/rows.tsv | ink moved to cell left edge (tools/font.py) |
| fonts/nunito/Nunito[wght].ttf | github.com/google/fonts ofl/nunito (2026-11-22) | OFL 1.1 (fonts/nunito/OFL.txt) | yes, as rendered glyphs | chapter cards (G8), 26 px wght 900 | - |
| fonts/tiny5/Tiny5.ttf | github.com/google/fonts ofl/tiny5 (2026-11-22) | OFL 1.1 | yes, as rendered glyphs | small labels (8 px em, 5 px caps) | - |
| fonts/silkscreen/Silkscreen-Regular.ttf | github.com/google/fonts ofl/silkscreen (2026-11-22) | OFL 1.1 | yes, as rendered glyphs | small caps labels (8 px em) | - |
| fonts/pixelifysans/PixelifySans[wght].ttf | github.com/google/fonts ofl/pixelifysans (2026-11-22) | OFL 1.1 | yes, as rendered glyphs | candidate for mid-size labels | - |
| fonts/cinzel/Cinzel[wght].ttf | github.com/google/fonts ofl/cinzel (2026-11-22) | OFL 1.1 | yes, as rendered glyphs | candidate (credits headings) | - |
