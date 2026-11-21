"""Staff-roll redraw (G18): writes gfx/credits.tsv and the bullet-row PNGs in gfx/out/credits/.

The roll is overlay 4 (OVER.BIN sectors 0x1DE-0x1E5, loads at 0x801C2518): a 279-entry cell table at file 0x13F0
(12 bytes: u16 tpage, u16 clut x, u16 clut y 0x1E0, u8 u, u8 v, u16 w-1, u16 h-1), a pointer table, then 12-byte
timed placements (u32 time, u16 0, u16 cell, s16 x, s16 y). Cells are packed edge to edge in the 8 GRA5 pages
(clut x / 16 = page k at 0x1B64000 + k * 0x8800), so each English label must stay inside its cell's w x 16.
Usage (repo root): python -X utf8 tools/gfx_credits.py   then gfx.py check/preview --group credits."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402

OVER_OFF, TABLE, N = 0x1DE * 0x800, 0x13F0, 279
PAGE0, PAGE = 0x1B64000, 0x8800
OUT = ROOT / "gfx/out/credits"

# cell: (JP, EN). Names are "Given Family" (D1) and drawn on two lines; EN with `|` is used as written.
NAMES = {
    0: ("三木眞一郎", "Shinichiro Miki"), 1: ("田中敦子", "Atsuko Tanaka"), 2: ("子安武人", "Takehito Koyasu"),
    3: ("折笠愛", "Ai Orikasa"), 4: ("石塚堅", "Ken Ishizuka"), 5: ("真砂勝美", "Katsumi Masago"),
    6: ("手塚ちはる", "Chiharu Tezuka"), 7: ("永野広一", "Koichi Nagano"), 8: ("西村朋紘", "Tomohiro Nishimura"),
    9: ("平松晶子", "Akiko Hiramatsu"), 10: ("中田和宏", "Kazuhiro Nakata"), 11: ("柚木涼香", "Ryoka Yuzuki"),
    12: ("石川和之", "Kazuyuki Ishikawa"), 13: ("浅田葉子", "Yoko Asada"), 14: ("高橋広樹", "Hiroki Takahashi"),
    15: ("うすいたかやす", "Takayasu Usui"), 16: ("立木文彦", "Fumihiko Tachiki"), 17: ("大友龍三郎", "Ryuzaburo Otomo"),
    18: ("原沢勝広", "Katsuhiro Harasawa"), 19: ("土井俊明", "Toshiaki Doi"), 20: ("渡辺隼人", "Hayato Watanabe"),
    21: ("松本吉朗", "Yoshiro Matsumoto"), 22: ("小林和矢", "Kazuya Kobayashi"), 23: ("ひのもとはじめ", "Hajime Hinomoto"),
    24: ("田端紀行", "Noriyuki Tabata"), 25: ("黒岩勝人", "Katsuhito Kuroiwa"), 26: ("市川淳", "Jun Ichikawa"),
    27: ("熊谷将", "Sho Kumagai"), 28: ("尾鼻直人", "Naoto Obana"), 29: ("金丸仁", "Hitoshi Kanamaru"),
    30: ("加藤建志", "Takeshi Kato"), 31: ("佐々木美恵", "Mie Sasaki"), 32: ("菊池たけし", "Takeshi Kikuchi"),
    33: ("久保田悠羅", "Yura Kubota"), 34: ("高森健一", "Kenichi Takamori"), 35: ("成瀬史弥", "Fumiya Naruse"),
    36: ("河岸昌行", "Masayuki Kawagishi"), 37: ("米倉俵", "Tawara Yonekura"), 38: ("浅香学", "Manabu Asaka"),
    39: ("桝井剛", "Tsuyoshi Masui"), 40: ("桑原誠", "Makoto Kuwabara"), 41: ("黒瀬大輔", "Daisuke Kurose"),
    42: ("内田哲也", "Tetsuya Uchida"), 43: ("皆川ともゆき", "Tomoyuki Minagawa"), 44: ("佐藤まさふみ", "Masafumi Sato"),
    45: ("大和田直之", "Naoyuki Owada"), 46: ("舛館俊秀", "Toshihide Masudate"), 47: ("TAKEGUCHI KENJI", "Kenji Takeguchi"),
    48: ("内田広之", "Hiroyuki Uchida"), 49: ("嘉村弘之", "Hiroyuki Kamura"), 50: ("玄馬宣彦", "Nobuhiko Genma"),
    51: ("坂元大二郎", "Daijiro Sakamoto"), 52: ("鈴木卓郎", "Takuro Suzuki"),
    53: ("高木潤", "Jun Takagi"), 54: ("高山朋浩", "Tomohiro Takayama"), 55: ("田中真二", "Shinji Tanaka"),
    56: ("西島克彦", "Katsuhiko Nishijima"), 57: ("福田紀之", "Noriyuki Fukuda"), 58: ("古田誠", "Makoto Furuta"),
    59: ("牧野竜一", "Ryuichi Makino"), 60: ("松村和子", "Kazuko Matsumura"), 61: ("村尾稔", "Minoru Murao"),
    62: ("安田好孝", "Yoshitaka Yasuda"), 63: ("山沢実", "Minoru Yamazawa"), 64: ("鰐渕和彦", "Kazuhiko Wanibuchi"),
    65: ("斉藤裕之", "Hiroyuki Saito"), 66: ("新井達郎", "Tatsuro Arai"), 67: ("鈴木良尚", "Yoshinao Suzuki"),
    68: ("高橋暁史", "Akifumi Takahashi"), 69: ("竹谷徹平", "Teppei Taketani"), 70: ("田村敬太郎", "Keitaro Tamura"),
    71: ("辻本純友", "Sumitomo Tsujimoto"), 72: ("坪田慎太郎", "Shintaro Tsubota"), 73: ("樋口聡一", "Soichi Higuchi"),
    74: ("平林隆史", "Takashi Hirabayashi"), 75: ("渡辺邦州", "Kunishu Watanabe"), 76: ("川上善美", "Yoshimi Kawakami"),
    77: ("今井亜津子", "Atsuko Imai"), 78: ("鈴木寿枝", "Hisae Suzuki"), 79: ("川口恵美", "Emi Kawaguchi"),
    80: ("小崎英剛", "Hidetake Ozaki"), 81: ("関沢友紀", "Tomoki Sekizawa"), 82: ("青山智子", "Tomoko Aoyama"),
    83: ("赤坂江美子", "Emiko Akasaka"), 84: ("愛宕敏行", "Toshiyuki Atago"), 85: ("石原淳子", "Junko Ishihara"),
    86: ("岩本麻耶", "Maya Iwamoto"), 87: ("上野崇勤", "Takanori Ueno"), 88: ("大嶋三香子", "Mikako Oshima"),
    89: ("岡村健一", "Kenichi Okamura"), 90: ("小川浩司", "Koji Ogawa"), 91: ("笠嶋純子", "Junko Kasajima"),
    92: ("加藤ミオ", "Mio Kato"), 93: ("廉澤幸子", "Sachiko Kadosawa"), 94: ("君野和磨", "Kazuma Kimino"),
    95: ("君野充子", "Mitsuko Kimino"), 96: ("黒沢啓", "Kei Kurosawa"), 97: ("佐々木千恵", "Chie Sasaki"),
    98: ("嶋中均", "Hitoshi Shimanaka"), 99: ("杉本直子", "Naoko Sugimoto"), 100: ("鈴木穰", "Minoru Suzuki"),
    101: ("高橋和子", "Kazuko Takahashi"), 102: ("西村泰江", "Yasue Nishimura"), 103: ("野口安義", "Yasuyoshi Noguchi"),
    104: ("服部洋子", "Yoko Hattori"), 105: ("林大樹", "Daiki Hayashi"), 106: ("藤代奈津美", "Natsumi Fujishiro"),
    107: ("望月ゆきえ", "Yukie Mochizuki"), 108: ("八木秀一", "Shuichi Yagi"), 109: ("安村あき子", "Akiko Yasumura"),
    110: ("山根洋一", "Yoichi Yamane"), 111: ("鷲塚佳美", "Yoshimi Washizuka"), 112: ("成合由紀", "Yuki Naruai"),
    113: ("井田千里", "Chisato Ida"), 114: ("大津紘典", "Hironori Otsu"), 115: ("長尾仁", "Hitoshi Nagao"),
    116: ("高橋麻穂", "Maho Takahashi"), 117: ("小川ひとみ", "Hitomi Ogawa"), 118: ("海津利子", "Toshiko Kaizu"),
    119: ("和田豊子", "Toyoko Wada"), 120: ("大関裕三子", "Yumiko Ozeki"), 121: ("西尾文子", "Fumiko Nishio"),
    122: ("所智一", "Tomokazu Tokoro"), 123: ("林康次郎", "Kojiro Hayashi"), 124: ("吉岡宏夫", "Hiroo Yoshioka"),
    125: ("唐戸光博", "Mitsuhiro Karato"), 126: ("北村直樹", "Naoki Kitamura"), 127: ("白石慶一", "Keiichi Shiraishi"),
    128: ("一ノ蔵朋紘", "Tomohiro Ichinokura"), 129: ("岩井邦男", "Kunio Iwai"), 130: ("おばな なおと", "Naoto Obana"),
    131: ("鈴鹿巧一", "Koichi Suzuka"), 132: ("石田ヒロユキ", "Hiroyuki Ishida"), 133: ("あかやま寿文", "Hisafumi Akayama"),
    134: ("福地仁", "Hitoshi Fukuchi"), 135: ("畠山広文", "Hirofumi Hatakeyama"), 136: ("吉元孝則", "Takanori Yoshimoto"),
    137: ("近藤広幸", "Hiroyuki Kondo"), 138: ("小林良平", "Ryohei Kobayashi"), 139: ("成富聡一", "Soichi Naritomi"),
    140: ("井上俊次", "Shunji Inoue"), 141: ("田久保真見", "Mami Takubo"), 142: ("飯塚昌明", "Masaaki Iizuka"),
    143: ("村上聖", "Sei Murakami"), 144: ("宮島律子", "Ritsuko Miyajima"), 145: ("須藤賢一", "Kenichi Sudo"),
    146: ("沢井なつ美", "Natsumi Sawai"), 147: ("三浦亨", "Toru Miura"), 148: ("岩井直樹", "Naoki Iwai"),
    149: ("玉山文人", "Fumito Tamayama"), 150: ("成富聡一", "Soichi Naritomi"), 151: ("山田雅昭", "Masaaki Yamada"),
    152: ("えのもとじゅん", "Jun Enomoto"), 153: ("中島純一郎", "Junichiro Nakajima"), 154: ("松本健", "Ken Matsumoto"),
    155: ("森本浩二", "Koji Morimoto"), 156: ("石井克枝", "Katsue Ishii"), 157: ("白滝幸弘", "Yukihiro Shirataki"),
    158: ("田酔国尾", "Kunio Tayoi"), 159: ("岩井直樹", "Naoki Iwai"), 160: ("畠山拓", "Taku Hatakeyama"),
    161: ("上床光信", "Mitsunobu Uwatoko"), 162: ("藤田あきら", "Akira Fujita"), 163: ("櫛淵宣一", "Nobukazu Kushibuchi"),
    164: ("蛯原浩二", "Koji Ebihara"), 165: ("本田猛", "Takeshi Honda"), 166: ("中島良一", "Ryoichi Nakajima"),
    169: ("STR", "STR"), 170: ("Y・K", "Y·K"), 171: ("Joker.", "Joker."),  # already English, redrawn to match the rest
    172: ("のびきっ太", "Nobikitta"), 173: ("どらポンY", "Dorapon Y"), 174: ("穴 金", "Ana Kin"),
    175: ("金谷明", "Akira Kanaya"), 202: ("F.A.I.", "F.A.I."),
}
ONE_LINE = {173, 174}  # pseudonyms drawn on one line
# companies (EN = the official form where known; 有限会社 = Ltd., 株式会社 = Co., Ltd.)
COMPANIES = {
    177: ("株式会社バンプレソフト", "Banpresoft Co., Ltd."), 178: ("株式会社マクロウェーブ", "Macrowave Co., Ltd."),
    179: ("有限会社まるばつ組", "Marubatsu Gumi Ltd."), 180: ("有限会社F.E.A.R.", "F.E.A.R. Ltd."),
    181: ("有限会社アンスピーカブル", "Unspeakable Ltd."), 182: ("有限会社りっくりっく", "Rikkurikku Ltd."),
    183: ("スタジオ・がっしゅ", "Studio Gasshu"), 184: ("スタジオ エル デジタル部", "Studio L Digital Department"),
    185: ("スタジオ マーチ", "Studio March"), 186: ("スタジオ ちゅーりっぷ", "Studio Tulip"),
    187: ("株式会社AIC", "AIC Co., Ltd."), 188: ("有限会社SIS WORKS", "SIS WORKS Ltd."),
    189: ("株式会社ディジメーション", "Digimation Co., Ltd."), 190: ("有限会社エーエムピー", "AMP Ltd."),
    191: ("STUDIO MASH", "STUDIO MASH"), 192: ("株式会社フェザード", "Feathered Co., Ltd."), 193: ("有限会社スタジオクリシェ", "Studio Cliche Ltd."),
    194: ("株式会社エアーズ", "Airs Co., Ltd."), 195: ("有限会社スタジオ・スタット", "Studio Stat Ltd."),
    196: ("バンダイビジュアル株式会社", "Bandai Visual Co., Ltd."), 197: ("株式会社ミューラス", "Myurasu Co., Ltd."),
    198: ("株式会社レイ・アップ", "Ray-Up Co., Ltd."), 199: ("株式会社バンプレスト", "Banpresto Co., Ltd."),
    200: ("コンシューマー事業部", "Consumer Division"), 201: ("ソフト開発部", "Software Development|Department"),
}
VOICES = {  # character names of the voice cast, as in glossary.md
    204: ("ケイゴ", "Keigo"), 205: ("アルマ", "Alma"), 206: ("イェン", "Yen"), 207: ("トト", "Toto"),
    208: ("ベウマー", "Beumer"), 209: ("フルカス", "Furcas"), 210: ("ヘレーナ", "Helena"), 211: ("ドロービ", "Drawbi"),
    212: ("ブラッキー", "Blacky"), 213: ("シェス", "Shess"), 214: ("ソッド", "Thodd"), 215: ("ミラ", "Mira"),
    216: ("ヤドラ", "Yadora"), 217: ("キャリ", "Kyari"), 218: ("マギーア", "Magia"), 219: ("ゼルドナ", "Zeldna"),
    220: ("ルジェロ", "Ruggero"), 221: ("アデノイド", "Adenoid"),
}
ROLES = {
    226: ("シナリオ原案", "Scenario Concept"), 227: ("シナリオ制作", "Scenario Writing"),
    229: ("プロデューサー", "Producer"), 230: ("制作デスク", "Production Desk"),
    231: ("制作進行", "Production|Coordinator"), 232: ("サウンドサンプリング", "Sound Sampling"),
    233: ("キャラクターデザイン", "Character Design"), 234: ("総作画監督", "Chief Animation|Director"),
    235: ("作画監督", "Animation|Director"), 236: ("作監補", "Asst. Anim.|Director"),
    237: ("メカ作監", "Mecha Anim.|Director"), 238: ("原画", "Key|Frames"), 239: ("動画チェック", "In-Between Check"),
    240: ("動画", "In-|between"), 241: ("色指定", "Color|Design"), 242: ("仕上検査", "Finishing|Inspection"),
    243: ("デジタルペイント", "Digital Paint"), 244: ("美術監督", "Art Director"), 245: ("背景", "Back-|ground"),
    246: ("CGディレクター", "CG Director"), 247: ("コンポジット", "Compositing"),
    248: ("音響プロデューサー", "Sound Producer"), 249: ("音響監督(制作)", "Sound|Direction"),
    250: ("制作", "Pro-|duction"), 251: ("制作協力", "Production|Cooperation"), 253: ("制作", "Pro-|duction"),
    254: ("制作協力", "Production|Cooperation"), 255: ("オリジナルデザイン", "Original Design"),
    257: ("モデル制作", "Model Production"), 258: ("音響制作", "Sound|Production"),
    262: ("オープニング", "Opening"), 263: ("曲名", "Title"), 264: ("作詞", "Lyrics"), 265: ("作曲", "Music"),
    266: ("編曲", "Arranger"), 267: ("エンディング", "Ending"), 268: ("歌", "Vo-|cals"),
    270: ("(順不同)", "(In no order)"), 272: ("(順不同・敬称略)", "(In no order, titles omitted)"),
}
BULLETS = {  # headings that start with a round bullet: the bullet is redrawn small, text follows (img rows)
    203: ("声の出演", "Voice Cast"), 222: ("企画・ゲームデザイン", "Planning / Game Design"),
    223: ("ゲームプログラム", "Game Programming"), 224: ("ゲームグラフィック", "Game Graphics"),
    225: ("シナリオ", "Scenario"), 228: ("アニメーション制作", "Animation Production"),
    252: ("メカニックデザイン", "Mechanic Design"), 256: ("CGモデル／ムービー", "CG / Movie"),
    259: ("サウンド／SE", "Sound / Sound Effects"), 260: ("テーマソング制作", "Theme Song Production"),
    261: ("テーマソング", "Theme Song"), 269: ("制作協力", "Production|Cooperation"), 273: ("制作", "Production"),
    278: ("ゲーム", "Game"), 271: ("Special thanks", "Special Thanks"),
}
KEEP = {167: "single kanji, reading unknown", 168: "single kanji, reading unknown", 176: "unused",
        274: "song title, English", 275: "song title, English", 276: "unused duplicate", 277: "Fin"}  # cells left alone
RECT_W = {249: 64}  # the table says 96 but 250 overlaps its right 32 px: two rows, 64 + 32

BULLET = [".XXXX.", "XXXXXX", "XXXXXX", "XXXXXX", "XXXXXX", ".XXXX."]
INK, BG = 15, 0
FONT = "fonts/tiny5/Tiny5.ttf"  # 8 px em: caps are rows 2-6, baseline row 6, descenders row 7, i/j dots rows 1-2


def cells():
    d = (ROOT / "work/disc/tree/OVER.BIN").read_bytes()[OVER_OFF:OVER_OFF + 0x4000]
    out = []
    for i in range(N):
        tp, cx, cy, u, v, w, h = struct.unpack_from("<HHHBBHH", d, TABLE + 12 * i)
        assert cy == 0x1E0 and cx % 16 == 0 and cx // 16 < 8 and (h == 15 or i == 277), i  # 277 = Fin, 80 x 40
        out.append((PAGE0 + PAGE * (cx // 16), u, v, w + 1, h + 1))
    return out


def line_px(text):
    """{(x, y)} of one tiny5 line drawn at origin (0, 0) (no vertical crop, so every line shares the baseline),
    shifted left so the first ink column is 0; and its width."""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(str(ROOT / FONT), 8)
    img = Image.new("1", (int(f.getlength(text)) + 8, 12))
    dr = ImageDraw.Draw(img)
    dr.fontmode = "1"
    dr.text((0, 0), text, font=f, fill=1)
    px = img.load()
    on = {(x, y) for y in range(img.height) for x in range(img.width) if px[x, y]}
    x0 = min(x for x, _ in on)
    return {(x - x0, y) for x, y in on}, max(x for x, _ in on) - x0 + 1


def label_png(i, cell, w, text, bullet):
    """Cell i as a w x 16 palette PNG: background 0, bullet (optional) and the text lines in ink 15.
    Two lines sit at rows 1-7 and 9-15 (pitch 8); one line is centred (rows 4-10)."""
    from PIL import Image
    tim, u, v, _, h = cell
    path = OUT / ("c%d.png" % i)
    gfx.export("GRA5.BIN:%X" % tim, "%d,%d,%d,%d" % (u, v, w, h), 0, str(path))
    im = Image.open(path)
    im.paste(BG, (0, 0, w, h))
    lines = text.split("|")
    assert len(lines) <= 2, text
    x0 = 9 if bullet else 1
    if bullet:
        by = 4 if len(lines) == 1 else 5
        for j, row in enumerate(BULLET):
            for k, c in enumerate(row):
                if c == "X":
                    im.putpixel((1 + k, by + j), INK)
    for n, t in enumerate(lines):
        on, tw = line_px(t)
        assert x0 + tw <= w, "%d %r is %d px wide, cell is %d" % (i, t, x0 + tw, w)
        oy = 3 if len(lines) == 1 else 8 * n
        for x, y in on:
            im.putpixel((x0 + x, oy + y), INK)
    im.save(path)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cs = cells()
    seen = {}
    rows = []
    allc = {}
    for grp, two in ((NAMES, True), (COMPANIES, False), (VOICES, False), (ROLES, False), (BULLETS, False)):
        for i, (jp, en) in grp.items():
            assert i not in allc and i not in KEEP, i
            allc[i] = (jp, en, two, grp is BULLETS)
    for i in range(N):
        assert (i in allc) != (i in KEEP), "cell %d neither drawn nor kept" % i
    for i in sorted(allc):
        jp, en, two, bul = allc[i]
        tim, u, v, w, h = cs[i]
        w = RECT_W.get(i, w)
        if two and i not in ONE_LINE and "|" not in en and " " in en:
            a, b = en.rsplit(" ", 1)
            en = a + "|" + b
        key = (tim, u, v, w)
        assert key not in seen, (i, seen[key])
        seen[key] = i
        png = str(label_png(i, cs[i], w, en, bul).relative_to(ROOT)).replace("\\", "/")
        rows.append(("GRA5.BIN", "%X" % tim, u, v, w, h, 0, png, "img", "auto", "none", "auto", "left",
                     "credits cell %d: %s; spill-ok cells are packed edge to edge, glyphs touch the next cell" % (i, jp)))
    with open(ROOT / "gfx/credits.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("\t".join("file tim x y w h clut text font ink edge bg align note".split()) + "\n")
        for r in rows:
            f.write("\t".join(str(c) for c in r) + "\n")
    print(len(rows), "rows,", len(KEEP), "cells kept")


if __name__ == "__main__":
    main()
