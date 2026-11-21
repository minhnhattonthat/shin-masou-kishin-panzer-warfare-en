# Glossary - Shin Masou Kishin: Panzer Warfare

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` fails a line whose JP has a term below but whose English lacks the EN form (case-insensitive;
any of several EN forms separated by ` / ` counts). Rows marked (speaker) are the speaker labels insert.py prints.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Masaki-san). Name order: Western (given name first).
- Romanisation source: official English names (Super Robot Wars / Cybuster) where they exist, else an earlier fan
  source (Akurasu wiki: Vartzpheem, A-Zeluth, Zeldna, Thodd, Beumer Kurtz Baum...), else Hepburn without macrons.
- Credits: English.
- Register: natural modern English with a light medieval-military flavour (knights, kingdoms, a royal capital); no
  archaic thee/thou except where a character's JP is itself archaic. Soldiers and rough men talk casual/clipped;
  nobles and officers formal. Sound effects in text: English onomatopoeia (ビシッ -> "Whap!", ハハハッ -> "Hahaha!").
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening (D4).

## Style rules
- Dialogue: drop the 「」 brackets (the speaker label already shows who talks; the font has no opening quote mark).
  Inner thoughts （…） stay in parentheses: (Hmm? Who's that...?). Narration has no quotes.
- Quoted names/terms 『』/「」 inside a line: no quote marks, capitalise instead (the Arm of God). The font draws
  `"` and `'` as closing marks only, so avoid quote marks; apostrophes in contractions are fine.
- ・・・ / … / …… -> `...`; ！？ -> `!?`; ── -> `--`; ！！ -> `!!` at most. Plain ASCII only.
- Stammers keep their shape: も、もう -> "I-I can't..."
- Voices: see docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ケイゴ | Keigo | | protagonist, Keigo Kurtz Ferdinand; pilot of the Masoukishin | |
| フェルディナン | Ferdinand | | Keigo's family name | |
| アルマ | Alma | | Alma Kurtz Karina | |
| カーリナ | Karina | | Alma's family name | |
| クルツ | Kurtz | | middle name (Keigo, Alma, Beumer, Furcas) | |
| ベウマー | Beumer | | Beumer Kurtz Baum | |
| アルフレード | Alfredo | | | |
| ソッド | Thodd | | | Sod |
| トト | Toto | | Toto Qual Yuro | |
| クアル | Qual | | Toto's middle name | |
| マギーア | Magia | | | |
| イェン | Yen | | Yen Yang | |
| キャリ | Kyari | | | |
| アデノイド | Adenoid | | | |
| フルカス | Furcas | | Furcas Kurtz Cambie | |
| シェス | Shess | | | |
| ゼルドナ | Zeldna | | instructor; "Zeldna the Flash Blade" (閃剣のゼルドナ) | Zeldona |
| シャーナ | Shana | | | |
| ルジェロ | Ruggero | | | |
| ミラ | Mira | | | |
| ロセリニ | Rossellini | | | |
| ヤドラ | Yadora | | | |
| ヘレーナ | Helena | | Helena Zants Sugar | |
| ザンツ | Zants | | middle name (Helena, Drawbi, Blacky) | |
| ブラッキー | Blacky | | Blacky Zants Katis | |
| ドロービ | Drawbi | | Drawbi Zants Raymon | |
| バージェス | Burgess | | | |
| ジェムス | Jems | | | |
| ダンカン | Duncan | | | |
| マルコム | Malcolm | | | |
| ディソン | Dison | | | |
| ガルム | Garum | | King Garum Vartzpheem | |
| 兵士 | Soldier | | (speaker) | |
| ラガーシュ兵士 | Ragash Soldier | | (speaker) | |
| ラガーシュ兵 | Ragash Soldier | | (speaker) | |
| ラガーシュ騎士 | Ragash Knight | | (speaker) | |
| ラガーシュ文官 | Ragash Official | | (speaker) | |
| ナトゥーレ兵士 | Natoure Soldier | | (speaker) | |
| ナトゥーレ騎士 | Natoure Knight | | (speaker) | |
| バルツフィーム騎士 | Vartzpheem Knight | | (speaker) | |
| 通信兵 | Signalman | | (speaker) | |
| 日記 | Diary | | (speaker) | |
| ゲリラ兵 | Guerrilla | | (speaker) | |
| 隊長 | Captain | | (speaker; in dialogue also "captain") | |
| 騎士候補兵 | Knight Cadet | | (speaker) | |
| 従者 | Attendant | | (speaker) | |
| 整備兵 | Mechanic | | (speaker) | |
| 民間兵 | Militiaman | | (speaker) | |
| 群衆 | Crowd | | (speaker) | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ア・ゼルス | A-Zeluth | | the world | A Zels |
| バルツフィーム | Vartzpheem | | holy kingdom; the heroes' country | Baltzfeim |
| ラガーシュ | Ragash | | | |
| ナトゥーレ | Natoure | | | |
| ダウス | Daus | | the Abyss, 深淵の穴 = the Abyssal Pit of Daus | Dusk |
| 王都 | Royal Capital | | | |
| ミッダスト | Middast | | | |
| アルデンヌ | Ardennes | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 魔装機神 | Masoukishin | | the four elemental god-machines | Masou Kishin |
| 魔装機 | Masouki | | Panzer machines; plural Masouki | |
| 神の腕 | Arm of God | | | |
| プラーナ | Prana | | SRW official | |
| プラーナボム | Prana Bomb | | | |
| プラーナゲージ | Prana Gauge | | | |
| 精霊 | spirit | | elemental spirit | |
| サイバスター | Cybuster | | SRW official | |
| ザムジード | Zamzeed | | SRW official | |
| グランヴェール | Granveil | | SRW official | |
| ガッデス | Gaddess | | SRW official | |
| ゴーレム | Golem | | | |
| 解放軍 | Liberation Army | | | |
| イクナァト | Iknaat | | | |
| アグ・ゲブラ | Ag Gebra | | | |
| ティルウェス | Tilwes | | | |
| ジャメイム | Jameim | | | |

## Decisions from earlier batches
- (none yet)
