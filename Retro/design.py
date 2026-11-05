"""
Retro - Casio-style LCD watchface design.

Draws every asset into assets/bip6/, writes the layout block in
watchface/index.js, and renders preview.png / preview_aod.png.

    python tools/build.py Retro            (from the repo root)
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from zepp import icons as I  # noqa: E402
from zepp.draw import (battery, degree_unit, mask_screen, pixel,  # noqa: E402
                       text_img, ttf_glyphs, ttf_word)
from zepp.project import FONTS, WEEK, Face, H, W  # noqa: E402

face = Face(__file__)

# ---------------------------------------------------------------- palette
LIT = (232, 228, 198, 255)     # warm LCD off-white
GHOST = (26, 26, 22, 255)      # unlit LCD segment, barely visible
AOD = (150, 148, 128, 255)     # dimmed lit colour for always-on display
AOD_GHOST = (16, 16, 13, 255)  # fainter ghost cells in always-on

# ---------------------------------------------------------------- fonts
# Every number and letter uses one TTF. Krafti Lab, free for personal use.
FONT = os.path.join(FONTS, "SevenSegment.ttf")
DIGITS = "0123456789"
BIG_H, SEC_H, MID_H, DATE_H, TINY_H, SM_H = 100, 40, 28, 26, 22, 18
XS = 0.78  # condense the big clock digits so HH:MM + ss fits the width


def glyphs(h, color, chars=DIGITS, ghost=None, fixed=True, xscale=1.0, align="right"):
    # no stroke: thickening the thin font closes the gaps between segments
    return ttf_glyphs(FONT, h, color, chars, ghost, fixed, 0, xscale=xscale, align=align)


def tight(h, ch, color=LIT, xscale=1.0):
    return glyphs(h, color, ch, fixed=False, xscale=xscale)[ch]


G = {
    # clock and date: LCD cells, "1" on the right segments over a ghost "8"
    "big": glyphs(BIG_H, LIT, ghost=GHOST, xscale=XS),
    "big_aod": glyphs(BIG_H, AOD, ghost=AOD_GHOST, xscale=XS),
    "sec": glyphs(SEC_H, LIT, ghost=GHOST),
    "date": glyphs(DATE_H, LIT, ghost=GHOST),
    "date_aod": glyphs(DATE_H, AOD, ghost=AOD_GHOST),
    # values: equal-width cells (TEXT_IMG needs them), "1" centred
    "mid": glyphs(MID_H, LIT, align="center"),
    "sm": glyphs(SM_H, LIT, align="center"),
    "tiny": glyphs(TINY_H, LIT, align="center"),
}
# punctuation at its own (tight) width
MINUS = {k: tight(h, "-") for k, h in [
    ("big", BIG_H), ("big_aod", BIG_H), ("sec", SEC_H), ("date", DATE_H),
    ("date_aod", DATE_H), ("mid", MID_H), ("sm", SM_H), ("tiny", TINY_H)]}
SM_DOT, SM_SLASH = tight(SM_H, "."), tight(SM_H, "/")


def lower_h(h):
    """7-segment lowercase h: the font only has capitals, so take its H
    (drawn 4x for clean edges) and drop the top-right segment."""
    big = tight(h * 4, "H")
    ImageDraw.Draw(big).rectangle([big.width * 0.5, 0, big.width, big.height * 0.47],
                                  fill=(0, 0, 0, 0))
    return big.resize((round(big.width / 4), h), Image.LANCZOS)


SM_HOURS = lower_h(SM_H)  # sleep "7.3h"
PCT = tight(TINY_H, "%")
# small % sitting on the baseline of the mid digits (SpO2), so 100% fits
PCT_SM = tight(SM_H, "%")
MID_PCT = Image.new("RGBA", (PCT_SM.width, MID_H), (0, 0, 0, 0))
MID_PCT.alpha_composite(PCT_SM, (0, MID_H - SM_H))
COLON = {c: tight(BIG_H, ":", c, XS) for c in (LIT, AOD)}
SLASH = {c: tight(DATE_H, "/", c) for c in (LIT, AOD)}
DEG = degree_unit((0, MID_H, 4), LIT)  # the font has no ° glyph
WEEK_H, WEEK_STROKE = DATE_H, 0  # same height as the date digits

# ---------------------------------------------------------------- layout
BIGW, SECW, DATEW = G["big"]["8"].width, G["sec"]["8"].width, G["date"]["8"].width
COLON_W, SLASH_W = COLON[LIT].width, SLASH[LIT].width
T_HSPACE, T_GAP, S_GAP, S_HSPACE = 6, 6, 8, 3
time_total = ((2 * BIGW + T_HSPACE) * 2 + 2 * T_GAP + COLON_W
              + S_GAP + 2 * SECW + S_HSPACE)
TX = (W - time_total) // 2
TY = 174

L = {}
L["hour"] = (TX, TY)
L["colon"] = (TX + 2 * BIGW + T_HSPACE + T_GAP, TY)
L["minute"] = (L["colon"][0] + COLON_W + T_GAP, TY)
L["second"] = (L["minute"][0] + 2 * BIGW + T_HSPACE + S_GAP, TY + BIG_H - SEC_H)
# AOD has no seconds, so HH:MM alone is centred
aod_total = (2 * BIGW + T_HSPACE) * 2 + 2 * T_GAP + COLON_W
AX = (W - aod_total) // 2
L["aod"] = {"hour": (AX, TY), "colon": (AX + 2 * BIGW + T_HSPACE + T_GAP, TY)}
L["aod"]["minute"] = (L["aod"]["colon"][0] + COLON_W + T_GAP, TY)
L["timeHSpace"] = T_HSPACE
L["secHSpace"] = S_HSPACE

# under the clock: dd/mm flush with its left edge, weekday with its right edge
D_GAP, D_HSPACE, DY = 4, 3, TY + BIG_H + 12
WEEK_W = max(ttf_word(w, FONT, WEEK_H, LIT, WEEK_STROKE).width
             for words in WEEK.values() for w in words)


def date_row(left, right):
    day = (left, DY)
    slash = (left + 2 * DATEW + D_HSPACE + D_GAP, DY)
    return {"day": day, "slash": slash, "month": (slash[0] + SLASH_W + D_GAP, DY),
            "week": (right - WEEK_W, DY)}



L.update(date_row(TX, TX + time_total))
L["aod"].update(date_row(AX, AX + aod_total))
L["dateHSpace"] = D_HSPACE

# status row
L["bt"] = (38, 28)
L["alarm"] = (80, 28)
L["dnd"] = (120, 28)
L["lock"] = (158, 28)
L["battery"] = (310, 28)
L["batteryText"] = (226, 28, 78)  # x, y, w (right-aligned)

# top row, four blocks on even centre lines: icon on top, value below
TOP_CX = [62, 151, 239, 328]  # heart, SpO2, stress, weather
ICON_BOTTOM, SIDE_VAL_Y, SIDE_W = 108, 118, 86


def icon_at(cx, grid, bottom, scale=3):
    """Top-left so the icon's ink is centred on cx and ends at bottom."""
    x0, _, x1, y1 = pixel(grid, scale, LIT).getbbox()
    return (cx - (x0 + x1) // 2, bottom - y1)


def ink_centred(im, w, h):
    """im's ink centred horizontally on a w x h canvas, bottom-aligned."""
    x0, y0, x1, y1 = im.getbbox()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(im.crop((x0, y0, x1, y1)), ((w - (x1 - x0)) // 2, h - (y1 - y0)))
    return out


WEATHER_BOX = 36  # 12x12 grids @3


def top_val(cx):
    # TEXT_IMG centres digits + unit together, right under the icon
    return (cx - SIDE_W // 2, SIDE_VAL_Y, SIDE_W)


L["heartIcon"] = icon_at(TOP_CX[0], I.ICON_HEART, ICON_BOTTOM)
L["spo2Icon"] = icon_at(TOP_CX[1], I.ICON_DROP, ICON_BOTTOM)
L["stressIcon"] = icon_at(TOP_CX[2], I.ICON_STRESS, ICON_BOTTOM)
L["weatherIcon"] = (TOP_CX[3] - WEATHER_BOX // 2, ICON_BOTTOM - WEATHER_BOX)
L["heartText"] = top_val(TOP_CX[0])
L["spo2Text"] = top_val(TOP_CX[1])
L["stressText"] = top_val(TOP_CX[2])
L["temp"] = top_val(TOP_CX[3])

# bottom metrics: five equal columns, no dividers
# kept off the rounded corners: columns span x 20..370
BOT_X0, BOT_COL = 20, 70
BOT_CX = [BOT_X0 + BOT_COL // 2 + i * BOT_COL for i in range(5)]
BOT_ICONS = [I.ICON_PIN, I.ICON_STEPS, I.ICON_FLAME, I.ICON_BED, I.ICON_STAND]
BOT_ICON_BOTTOM, BOT_VAL_Y, BOT_W = 374, 384, BOT_COL
for key, cx in zip(["distText", "stepText", "calText", "sleepText", "standText"], BOT_CX):
    L[key] = (cx - BOT_W // 2, BOT_VAL_Y, BOT_W)
L["smHSpace"] = 1


def top_click(cx):
    return (cx - SIDE_W // 2, 68, SIDE_W, 84)


def bot_click(cx):
    return (cx - BOT_COL // 2, 330, BOT_COL, 80)


L["click"] = {
    "heart": top_click(TOP_CX[0]),
    "spo2": top_click(TOP_CX[1]),
    "stress": top_click(TOP_CX[2]),
    "weather": top_click(TOP_CX[3]),
    "steps": bot_click(BOT_CX[1]),
    "cal": bot_click(BOT_CX[2]),
    "sleep": bot_click(BOT_CX[3]),
    "stand": bot_click(BOT_CX[4]),
}


# ---------------------------------------------------------------- build
def main():
    save = face.save
    files = {}

    # fonts
    for key, gs in G.items():
        files[key] = [save(gs[str(i)], f"font/{key}/{i}.png") for i in range(10)]
        files[key + "_minus"] = save(MINUS[key], f"font/{key}/minus.png")
    files["colon"] = save(COLON[LIT], "font/colon.png")
    files["colon_aod"] = save(COLON[AOD], "font/colon_aod.png")
    files["slash"] = save(SLASH[LIT], "font/slash.png")
    files["slash_aod"] = save(SLASH[AOD], "font/slash_aod.png")
    files["mid_deg"] = save(DEG, "font/mid/deg.png")
    files["mid_pct"] = save(MID_PCT, "font/mid/pct.png")
    files["tiny_pct"] = save(PCT, "font/tiny/pct.png")
    files["sm_dot"] = save(SM_DOT, "font/sm/dot.png")
    files["sm_h"] = save(SM_HOURS, "font/sm/h.png")
    files["sm_slash"] = save(SM_SLASH, "font/sm/slash.png")

    # weekday in the Seven Segment TTF
    files["week"] = {lang: [save(week_img(w, LIT), f"week/{lang}/{i}.png")
                            for i, w in enumerate(words)]
                     for lang, words in WEEK.items()}
    files["week_aod"] = {lang: [save(week_img(w, AOD), f"week/{lang}/aod_{i}.png")
                                for i, w in enumerate(words)]
                         for lang, words in WEEK.items()}

    # weather
    wicons = {k: ink_centred(pixel(v, 3, LIT), WEATHER_BOX, WEATHER_BOX)
              for k, v in I.weather_grids().items()}
    files["weather"] = [save(wicons[n], f"weather/{i}.png")
                        for i, n in enumerate(I.WEATHER_MAP)]

    # battery: 0..5 bars
    files["battery"] = [save(battery(i, 5, LIT, GHOST), f"battery/{i}.png")
                        for i in range(6)]

    # status icons (lit overlays; ghosts are baked into the background)
    files["bt_off"] = save(pixel(I.ICON_BT_OFF, 3, LIT), "status/bt_off.png")
    files["alarm"] = save(pixel(I.ICON_ALARM, 3, LIT), "status/alarm.png")
    files["dnd"] = save(pixel(I.ICON_MOON_S, 3, LIT), "status/dnd.png")
    files["lock"] = save(pixel(I.ICON_LOCK, 3, LIT), "status/lock.png")

    # background: static icons, colon, slash, ghost status icons
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for grid, key in [(I.ICON_BT, "bt"), (I.ICON_ALARM, "alarm"),
                      (I.ICON_MOON_S, "dnd"), (I.ICON_LOCK, "lock")]:
        bg.alpha_composite(pixel(grid, 3, GHOST), L[key])
    for grid, key in [(I.ICON_HEART, "heartIcon"), (I.ICON_DROP, "spo2Icon"),
                      (I.ICON_STRESS, "stressIcon")]:
        bg.alpha_composite(pixel(grid, 3, LIT), L[key])
    bg.alpha_composite(COLON[LIT], L["colon"])
    bg.alpha_composite(SLASH[LIT], L["slash"])
    for cx, grid in zip(BOT_CX, BOT_ICONS):
        bg.alpha_composite(pixel(grid, 3, LIT), icon_at(cx, grid, BOT_ICON_BOTTOM))
    files["bg"] = save(bg.convert("RGB"), "bg.png")

    files["icon"] = save(make_icon(), "icon.png")

    face.write_layout(L=L, F=files)
    make_previews(files)
    print("assets written to", face.assets)


def week_img(word, color):
    """Weekday flush right on a fixed-width canvas, so IMG_WEEK lines up
    with the right edge of the clock whatever the day."""
    im = ttf_word(word, FONT, WEEK_H, color, WEEK_STROKE)
    out = Image.new("RGBA", (WEEK_W, WEEK_H), (0, 0, 0, 0))
    out.alpha_composite(im, (WEEK_W - im.width, 0))
    return out


def make_icon():
    im = Image.new("RGBA", (248, 248), (0, 0, 0, 255))
    fs = glyphs(70, LIT, ghost=GHOST, xscale=XS)
    c = glyphs(70, LIT, ":", fixed=False, xscale=XS)[":"]
    text_img(im, 0, 89, "12", fs, 3, 248 // 2 - c.width // 2, "right")
    im.alpha_composite(c, (248 // 2 - c.width // 2, 89))
    text_img(im, 248 // 2 + c.width // 2, 89, "34", fs, 3)
    return im


# ---------------------------------------------------------------- preview
def make_previews(files):
    op = lambda r: Image.open(os.path.join(face.assets, r))
    font = lambda key: {str(i): op(files[key][i]) for i in range(10)}
    big, sec, dat, mid, sm, tiny = (font(k) for k in ("big", "sec", "date", "mid", "sm", "tiny"))
    mid.update({"-": op(files["mid_minus"]), "°": op(files["mid_deg"]),
                "%": op(files["mid_pct"])})
    sm.update({".": op(files["sm_dot"]), "/": op(files["sm_slash"]),
               "h": op(files["sm_h"])})
    tiny["%"] = op(files["tiny_pct"])

    im = op(files["bg"]).convert("RGBA")
    text_img(im, *L["hour"], "16", big, L["timeHSpace"])
    text_img(im, *L["minute"], "06", big, L["timeHSpace"])
    text_img(im, *L["second"], "33", sec, L["secHSpace"])
    text_img(im, *L["day"], "01", dat, L["dateHSpace"])
    text_img(im, *L["month"], "06", dat, L["dateHSpace"])
    im.alpha_composite(op(files["week"]["pt"][6]), L["week"])
    im.alpha_composite(op(files["battery"][4]), L["battery"])
    x, y, w = L["batteryText"]; text_img(im, x, y, "100%", tiny, 2, w, "right")
    im.alpha_composite(op(files["alarm"]), L["alarm"])
    im.alpha_composite(op(files["weather"][0]), L["weatherIcon"])
    for key, txt in [("heartText", "120"), ("spo2Text", "98%"), ("stressText", "45"),
                     ("temp", "-28°")]:
        x, y, w = L[key]; text_img(im, x, y, txt, mid, 3, w, "center")
    for key, txt in [("distText", "20.25"), ("stepText", "7500"), ("calText", "210"),
                     ("sleepText", "7.3h"), ("standText", "8/12")]:
        x, y, w = L[key]; text_img(im, x, y, txt, sm, L["smHSpace"], w, "center")
    mask_screen(im).save(face.path("preview.png"))

    # AOD
    ab, ad = font("big_aod"), font("date_aod")
    A = L["aod"]
    a = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    text_img(a, *A["hour"], "16", ab, L["timeHSpace"])
    a.alpha_composite(op(files["colon_aod"]), A["colon"])
    text_img(a, *A["minute"], "06", ab, L["timeHSpace"])
    text_img(a, *A["day"], "01", ad, L["dateHSpace"])
    a.alpha_composite(op(files["slash_aod"]), A["slash"])
    text_img(a, *A["month"], "06", ad, L["dateHSpace"])
    a.alpha_composite(op(files["week_aod"]["pt"][6]), A["week"])
    mask_screen(a).save(face.path("preview_aod.png"))


if __name__ == "__main__":
    main()
