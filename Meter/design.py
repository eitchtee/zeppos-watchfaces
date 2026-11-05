"""
Meter - residential energy meter watchface design.

Draws every asset into assets/bip6/, writes the layout block in
watchface/index.js, and renders preview.png / preview_aod.png.

    python tools/build.py Meter            (from the repo root)

Needs Bahnschrift (ships with Windows 10+). On other systems point FONT at any
condensed DIN-style TTF and drop the set_variation_by_name calls.
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from zepp import icons as I  # noqa: E402
from zepp.draw import mask_screen, text_img  # noqa: E402
from zepp.project import WEEK, Face, H, W  # noqa: E402

face = Face(__file__)

# ---------------------------------------------------------------- palette
PLATE = (186, 188, 186)
INK = (22, 22, 24, 255)         # stamped black text
EMBOSS = (232, 234, 232, 150)   # light edge under stamped text
WHEEL = (20, 20, 21)            # black number wheel
WHEEL_RED = (146, 22, 20)       # the fractional wheels of a real meter are red
FIGURE = (242, 240, 228)
WHITE = (240, 240, 234, 255)
BOX = (16, 16, 17, 255)
BRASS = (214, 164, 72, 255)
GHOST = (146, 148, 146, 255)    # status icon stamped in, not inked
AOD_FIG = (150, 148, 138, 255)
AOD_DIM = (96, 96, 90, 255)

# ---------------------------------------------------------------- text
FONT = "C:/Windows/Fonts/bahnschrift.ttf"
SS = 4


def text(s, h, color=INK, style="Bold Condensed", skew=0.0):
    """Tight-width RGBA text on a canvas 2h tall: capitals span y = h/2 .. 3h/2,
    leaving room for accents and descenders."""
    probe = ImageFont.truetype(FONT, 200)
    probe.set_variation_by_name(style)
    t, b = probe.getbbox("H")[1], probe.getbbox("H")[3]
    font = ImageFont.truetype(FONT, round(200 * h * SS / (b - t)))
    font.set_variation_by_name(style)
    l, _, r, _ = font.getbbox(s)
    top = font.getbbox("H")[1]
    pad = h * SS // 2
    big = Image.new("RGBA", (r - l + SS, h * SS + 2 * pad), (*color[:3], 0))
    ImageDraw.Draw(big).text((-l, pad - top), s, font=font, fill=color)
    if skew:
        big = big.transform((big.width + int(big.height * skew), big.height), Image.AFFINE,
                            (1, skew, -big.height * skew, 0, 1, 0), Image.BICUBIC)
    return big.resize((max(1, big.width // SS), big.height // SS), Image.LANCZOS)


def stamp(canvas, xy, s, h, anchor="l", **kw):
    """Stamped-in plate lettering. Anchor "l", "c" or "r" on x; y = cap top."""
    im = text(s, h, INK, **kw)
    x = xy[0] - {"l": 0, "c": im.width // 2, "r": im.width}[anchor]
    y = xy[1] - h // 2
    canvas.alpha_composite(text(s, h, EMBOSS, **kw), (x, y + 1))
    canvas.alpha_composite(im, (x, y))


def caps(im, h):
    """Crop text() to its ink width and exactly the capital height."""
    x0, _, x1, _ = im.getbbox()
    return im.crop((x0, h // 2, x1, h // 2 + h))


DIGITS = "0123456789"
VAL_H, TAG_H = 22, 18


def cells(h, color):
    """Equal-width digits: TEXT_IMG gives every digit the same width."""
    ims = {c: caps(text(c, h, color), h) for c in DIGITS}
    w = max(i.width for i in ims.values())
    out = {}
    for c, im in ims.items():
        o = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        o.alpha_composite(im, ((w - im.width) // 2, 0))
        out[c] = o
    return out


def glyph(ch, h, color=WHITE):
    """Punctuation at its own width, on the digits' baseline."""
    return caps(text(ch, h, color), h)


VAL, TAG, TAG_AOD = cells(VAL_H, WHITE), cells(TAG_H, WHITE), cells(TAG_H, AOD_FIG)
VAL_W, TAG_W = VAL["8"].width, TAG["8"].width

# ---------------------------------------------------------------- drums
CELL_W, CELL_H = 52, 100
PITCH = 96      # distance between figures on the wheel
RADIUS = 86     # smaller than the true wheel: exaggerates the curve
FIG_H = 68
FIG_STYLE = "Bold SemiCondensed"
FRAMES = (0.14, 0.5, 0.86)  # in-between positions of a roll, 1 tick each
KS = 3


def figure(d, wheel):
    """One figure on its wheel colour, PITCH tall, at KS scale."""
    im = Image.new("RGB", (CELL_W * KS, PITCH * KS), wheel)
    g = caps(text(str(d), FIG_H * KS, (*FIGURE, 255), FIG_STYLE), FIG_H * KS)
    im.paste(g, ((im.width - g.width) // 2, (im.height - g.height) // 2), g)
    return im


def drum(top, bottom, phase, wheel):
    """The window onto a wheel: top moving out upwards, bottom coming in, phase
    0..1. Flat strip wrapped on a cylinder, neighbours peek in at the edges."""
    seq = [(top + 9) % 10, top, bottom, (bottom + 1) % 10]
    strip = Image.new("RGB", (CELL_W * KS, PITCH * KS * 4), wheel)
    for i, d in enumerate(seq):
        strip.paste(figure(d, wheel), (0, i * PITCH * KS))
    out = Image.new("RGB", (CELL_W * KS, CELL_H * KS))
    centre = (1.5 + phase) * PITCH * KS
    for row in range(out.height):
        theta = math.asin((row + 0.5 - out.height / 2) / (KS * RADIUS))
        src = int(centre + theta * RADIUS * KS)
        shade = max(0, math.cos(theta)) ** 3
        out.paste(strip.crop((0, src, strip.width, src + 1)).point(lambda v: int(v * shade)),
                  (0, row))
    # the wheel also falls into the window's shadow at its sides
    side = Image.new("L", (out.width, 1))
    for x in range(out.width):
        edge = min(x, out.width - 1 - x) / (7 * KS)
        side.putpixel((x, 0), int(255 * min(1, 0.45 + 0.55 * edge)))
    side = side.resize(out.size)
    out = ImageChops.multiply(out, Image.merge("RGB", (side, side, side)))
    return out.resize((CELL_W, CELL_H), Image.LANCZOS)


# rolls that aren't "next digit": 59->00 on tens, 23->00, 12->01 (12h clock)
ROLLS = [(d, (d + 1) % 10) for d in range(10)] + [(5, 0), (3, 0), (2, 0), (2, 1)]


def aod_digit(d):
    """Figure with no wheel: mostly black pixels for always-on."""
    g = caps(text(str(d), FIG_H, AOD_FIG, FIG_STYLE), FIG_H)
    o = Image.new("RGBA", (CELL_W, FIG_H), (0, 0, 0, 0))
    o.alpha_composite(g, ((CELL_W - g.width) // 2, 0))
    return o


# ---------------------------------------------------------------- layout
L = {}
PAIR_GAP, CELL_GAP = 12, 2
WIN_Y = 98
pair_w = 2 * CELL_W + CELL_GAP
win_w = 3 * pair_w + 2 * PAIR_GAP
CX0 = (W - win_w) // 2
pair_x = [CX0 + i * (pair_w + PAIR_GAP) for i in range(3)]
cell_x = [x + j * (CELL_W + CELL_GAP) for x in pair_x for j in range(2)]
L["cells"] = [(x, WIN_Y) for x in cell_x]
L["cellSpace"] = CELL_GAP
WINDOW = (CX0 - 5, WIN_Y - 5, CX0 + win_w + 5, WIN_Y + CELL_H + 5)

# the labels stay put in every language, so columns fit the longest word
LABELS = {
    "pt": dict(stress="Estr", steps="passos", sleep="h sono", stand="em pé"),
    "en": dict(stress="Strs", steps="steps", sleep="h sleep", stand="stand"),
    "es": dict(stress="Estr", steps="pasos", sleep="h sueño", stand="de pie"),
}
for words in LABELS.values():
    words.update(bpm="bpm", spo2="SpO2", km="km", kcal="kcal", deg="°", bat="Bat")
LBL_H = 16
BOX_H, BOX_PAD, BOX_LBL_GAP = 30, 6, 5
WX = 24  # weather icon size
ICON_BOX = 30
ROWS_Y = [254, 296, 338, 380]
COL2_X = 206  # second column of the two-item rows


def box_w(chars):
    return int(chars * (VAL_W + 1)) + 2 * BOX_PAD


def lbl_w(key):
    extra = ICON_BOX + 6 if key == "deg" else 0  # the weather icon follows the degree sign
    return max(text(w[key], LBL_H).getbbox()[2] for w in LABELS.values()) + extra


ROWS = [  # (widget, characters in box, label)
    [("heartText", 3, "bpm"), ("spo2Text", 3, "spo2"), ("stressText", 3, "stress")],
    [("stepText", 5, "steps"), ("distText", 5, "km")],
    [("calText", 5, "kcal"), ("temp", 5, "deg")],
    [("sleepText", 5, "sleep"), ("standText", 5, "stand")],
]
BOXES, LBLS = [], []  # (x, y, w), (x, y, key)
for row, y in zip(ROWS, ROWS_Y):
    total = sum(box_w(c) + BOX_LBL_GAP + lbl_w(k) for _, c, k in row)
    gap = (W - 2 * 26 - total) // (len(row) - 1)
    x = 26
    for i, (widget, c, key) in enumerate(row):
        if len(row) == 2 and i == 1:
            x = COL2_X
        w = box_w(c)
        BOXES.append((x, y, w))
        L[widget] = (x, y + (BOX_H - VAL_H) // 2, w)
        LBLS.append((x + w + BOX_LBL_GAP, y + (BOX_H - LBL_H) // 2 + 1, key))
        x += w + BOX_LBL_GAP + lbl_w(key) + gap
_deg_x = next(x for x, _, k in LBLS if k == "deg")
L["weatherIcon"] = (_deg_x + 14, ROWS_Y[2] + (BOX_H - WX) // 2)
L["valSpace"] = 1

# header
MOD_Y = 28
WEEK_BOX = (272, MOD_Y, 346, MOD_Y + 26)
L["week"] = (290, MOD_Y + 4)
TAG_Y = 60
DATE_BOX = (282, TAG_Y, 370, TAG_Y + 26)
L["day"] = (DATE_BOX[0] + 10, DATE_BOX[1] + 4)
L["slash"] = (L["day"][0] + 2 * TAG_W + 4, DATE_BOX[1] + 4)
L["slashW"] = glyph("/", TAG_H).width
L["dateSpace"] = 1

# CN row
BAT_Y = 212
BAT_BOX = (278, BAT_Y, 278 + box_w(3), BAT_Y + BOX_H)
L["batteryText"] = (BAT_BOX[0], BAT_Y + (BOX_H - VAL_H) // 2, box_w(3))

# status icons, in the top left of the plate
STATUS = ["bt", "alarm", "dnd", "lock"]
ICON_S = 26
for i, key in enumerate(STATUS):
    L[key] = (48 + i * 36, MOD_Y)
LABEL_RECT = (0, BAT_Y - 8, W, ROWS_Y[-1] + BOX_H + 4)  # what changes by language
L["labelsAt"] = LABEL_RECT[:2]

# always-on
a_w = 4 * CELL_W + 2 * CELL_GAP + PAIR_GAP
AX = (W - a_w) // 2
AY = 176
A_ROW = AY + FIG_H + 26
L["aod"] = {"hour": (AX, AY), "minute": (AX + pair_w + PAIR_GAP, AY),
            "day": (AX + 4, A_ROW), "slash": (AX + 4 + 2 * TAG_W + 4, A_ROW),
            "week": (AX + a_w - 44, A_ROW)}


def row_click(widget):
    x, y, w = L[widget]
    return (x - 4, y - 8, w + 40, BOX_H + 6)


L["click"] = {k: row_click(v) for k, v in dict(
    heart="heartText", spo2="spo2Text", stress="stressText", weather="temp",
    steps="stepText", cal="calText", sleep="sleepText", stand="standText").items()}


# ---------------------------------------------------------------- icons
# Drawn like the symbols stamped on electrical gear, not pixel art.
K = 8


def canvas(size):
    im = Image.new("RGBA", (size * K, size * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    return im, d, lambda *a: [v * K for v in a]


def done(im, size):
    return im.resize((size, size), Image.LANCZOS)


def ic_open_switch(c):
    """Schematic open switch: the phone link is broken."""
    im, d, p = canvas(ICON_S)
    d.line(p(0, 19, 4, 19), fill=c, width=3 * K)
    d.line(p(22, 19, 26, 19), fill=c, width=3 * K)
    d.ellipse(p(2, 16, 8, 22), fill=c)
    d.ellipse(p(18, 16, 24, 22), fill=c)
    d.line(p(5, 19, 20, 5), fill=c, width=3 * K)
    return done(im, ICON_S)


def ic_bell(c):
    """Electric bell: alarm set."""
    im, d, p = canvas(ICON_S)
    d.pieslice(p(6, 3, 20, 19), 180, 360, fill=c)
    d.rectangle(p(6, 11, 20, 18), fill=c)
    d.polygon(p(6, 16, 20, 16, 24, 21, 2, 21), fill=c)
    d.ellipse(p(10, 21, 16, 26), fill=c)
    d.rectangle(p(12, 0, 14, 4), fill=c)
    return done(im, ICON_S)


def ic_standby(c):
    """IEC standby symbol: do not disturb."""
    im, d, p = canvas(ICON_S)
    d.arc(p(3, 4, 23, 24), 300, 240, fill=c, width=3 * K)
    d.line(p(13, 1, 13, 13), fill=c, width=3 * K)
    return done(im, ICON_S)


def ic_lock(c):
    """Padlock: screen locked."""
    im, d, p = canvas(ICON_S)
    d.arc(p(7, 1, 19, 15), 180, 360, fill=c, width=3 * K)
    d.rectangle(p(7, 8, 10, 13), fill=c)
    d.rectangle(p(16, 8, 19, 13), fill=c)
    d.rounded_rectangle(p(3, 12, 23, 25), 2 * K, fill=c)
    d.ellipse(p(11, 15, 15, 19), fill=(0, 0, 0, 0))
    d.rectangle(p(12, 17, 14, 22), fill=(0, 0, 0, 0))
    return done(im, ICON_S)


STATUS_ICONS = dict(bt=ic_open_switch, alarm=ic_bell, dnd=ic_standby, lock=ic_lock)


def cloud(d, p, c, dy=0):
    """Cloud with a clear outline, so it stands off whatever is behind it."""
    for grow, fill in ((1.5, (0, 0, 0, 0)), (0, c)):
        d.ellipse(p(1 - grow, 9 + dy - grow, 11 + grow, 18 + dy + grow), fill=fill)
        d.ellipse(p(6 - grow, 4 + dy - grow, 18 + grow, 16 + dy + grow), fill=fill)
        d.ellipse(p(13 - grow, 9 + dy - grow, 23 + grow, 18 + dy + grow), fill=fill)
        d.rectangle(p(6, 12 + dy, 18, 18 + dy), fill=fill)


def sun(d, p, c, cx, cy, r, ray):
    for a in range(0, 360, 45):
        x, y = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line(p(cx + x * (r + 2), cy + y * (r + 2), cx + x * (r + ray), cy + y * (r + ray)),
               fill=c, width=2 * K)
    d.ellipse(p(cx - r, cy - r, cx + r, cy + r), fill=c)


def moon(d, p, c, cx, cy, r):
    d.ellipse(p(cx - r, cy - r, cx + r, cy + r), fill=c)
    d.ellipse(p(cx - r * 0.3, cy - r * 1.1, cx + r * 1.4, cy + r * 0.6), fill=(0, 0, 0, 0))


def bolt(d, p, c, x=0, y=0):
    d.polygon(p(14 + x, 10 + y, 8 + x, 17 + y, 12 + x, 17 + y, 9 + x, 24 + y,
                17 + x, 15 + y, 13 + x, 15 + y), fill=c)


def weather_icon(name, c=WHITE):
    im, d, p = canvas(WX)
    if name == "sun":
        sun(d, p, c, 12, 12, 5, 9)
    elif name == "moon":
        moon(d, p, c, 11, 12, 9)
    elif name == "cloud":
        cloud(d, p, c, 2)
    elif name == "partly":
        sun(d, p, c, 8, 8, 4, 7)
        cloud(d, p, c, 4)
    elif name == "partly_night":
        moon(d, p, c, 8, 8, 6)
        cloud(d, p, c, 4)
    elif name == "fog":
        for y, x0, x1 in ((6, 3, 21), (12, 1, 19), (18, 5, 23)):
            d.line(p(x0, y, x1, y), fill=c, width=3 * K)
    elif name == "unknown":
        cloud(d, p, c, 2)
        d.ellipse(p(10, 11, 14, 15), fill=(0, 0, 0, 0))
    else:
        cloud(d, p, c, -3)
        if name == "rain":
            for x in (7, 12, 17):
                d.line(p(x + 1, 17, x - 1, 23), fill=c, width=2 * K)
        elif name == "snow":
            for x, y in ((7, 18), (12, 21), (17, 18)):
                d.ellipse(p(x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=c)
        elif name == "storm":
            bolt(d, p, (0, 0, 0, 0), 0, -1)  # keep clear of the cloud
            bolt(d, p, c)
    return done(im, WX)


# ---------------------------------------------------------------- plate
def plate():
    r = random.Random(7)
    w, h = W // 2, H // 2
    grain = Image.frombytes("L", (w, h), r.randbytes(w * h))
    grain = grain.resize((W * 12, H), Image.BILINEAR).crop((0, 0, W, H))  # brushed
    grain = grain.point(lambda v: 128 + (v - 128) // 5)
    base = Image.new("L", (W, H))
    for y in range(H):  # soft top light, like the photo
        base.paste(int(150 + 18 * math.cos((y / H - 0.28) * math.pi)), (0, y, W, y + 1))
    tone = ImageChops.add(base, grain, 1, -100)
    return Image.merge("RGB", [tone.point(lambda v: min(255, v * c // PLATE[1]))
                               for c in PLATE]).convert("RGBA")


def inset(im, box, fill=BOX, r=2):
    """Dark box punched into the plate, lit from above."""
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 - 1, y0 - 1, x1, y1 + 1), r + 1, fill=(236, 238, 236, 255))
    d.rounded_rectangle((x0 - 1, y0 - 1, x1, y1), r + 1, fill=(70, 70, 70, 255))
    d.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), r, fill=fill)


def draw_plate():
    im = plate()
    d = ImageDraw.Draw(im)

    # counter window, with brass spacers between the wheel pairs
    inset(im, WINDOW, (6, 6, 6, 255), 3)
    for x in (pair_x[0] + pair_w + PAIR_GAP // 2, pair_x[1] + pair_w + PAIR_GAP // 2):
        for cy in (WIN_Y + CELL_H // 3, WIN_Y + 2 * CELL_H // 3):
            d.ellipse((x - 2, cy - 2, x + 2, cy + 2), fill=BRASS)
    stamp(im, (28, TAG_Y + 3), "kWh", 21)
    stamp(im, (DATE_BOX[0] - 8, TAG_Y + 5), "Rr", 18, "r")
    inset(im, DATE_BOX)
    inset(im, WEEK_BOX)
    stamp(im, (WEEK_BOX[0] - 8, MOD_Y + 6), "MOD.", 15, "r")

    # CN notch with the brass of the mechanism showing through
    cy = BAT_Y + BOX_H // 2
    d.pieslice((-14, cy - 17, 20, cy + 17), -90, 90, fill=(24, 24, 24, 255))
    d.pieslice((-8, cy - 11, 14, cy + 11), -90, 90, fill=BRASS)
    stamp(im, (26, cy - 8), "CN", 16)
    stamp(im, (52, cy - 8), "+", 16)

    # rotation arrows
    d.line((104, cy, 204, cy), fill=INK, width=3)
    d.polygon([(90, cy), (104, cy - 7), (104, cy + 7)], fill=INK)
    d.polygon([(218, cy), (204, cy - 7), (204, cy + 7)], fill=INK)
    d.rectangle((151, cy - 8, 157, cy + 8), fill=INK)

    inset(im, BAT_BOX)
    for x, y, w in BOXES:
        inset(im, (x, y, x + w, y + BOX_H))
    ix, iy = L["weatherIcon"]
    inset(im, (ix - 3, iy - 3, ix + WX + 3, iy + WX + 3))

    # glass cover glare
    glass = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glass).ellipse((-120, -260, 240, 120), fill=30)
    shine = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    shine.putalpha(glass.filter(ImageFilter.GaussianBlur(26)))
    im.alpha_composite(shine)
    return im


def labels(lang):
    """Language-specific lettering, transparent, cropped to LABEL_RECT."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    w = LABELS[lang]
    for x, y, key in LBLS:
        stamp(im, (x, y), w[key], LBL_H)
    stamp(im, (BAT_BOX[2] + 5, BAT_Y + 7), "%", LBL_H)
    stamp(im, (BAT_BOX[0] - 6, BAT_Y + 7), w["bat"], LBL_H, "r")
    return im.crop(LABEL_RECT)


def week_img(word, color):
    """Weekday on a canvas wide enough for any of them, centred in its box."""
    im = caps(text(word, TAG_H, color), TAG_H)
    out = Image.new("RGBA", (44, TAG_H), (0, 0, 0, 0))
    out.alpha_composite(im, ((out.width - im.width) // 2, 0))
    return out


# ---------------------------------------------------------------- build
def main():
    for x, _, w in BOXES:
        assert 0 < x and x + w < W, "box off screen"
    for x, _, key in LBLS:
        assert x + lbl_w(key) <= W - 20, f"label {key} off screen"
    for (x, _, key), (nx, _, _) in zip(LBLS, BOXES[1:] + [(W, 0, 0)]):
        assert x + lbl_w(key) <= nx or nx < x, f"label {key} runs into the next box"
    save = face.save
    files = {"labels": {}, "week": {}, "week_aod": {}}

    for name, wheel in (("black", WHEEL), ("red", WHEEL_RED)):
        files[name] = [save(drum(d, d, 0, wheel), f"drum/{name}/{d}.png") for d in range(10)]
        files[name + "_roll"] = {
            f"{a}{b}": [save(drum(a, b, p, wheel), f"drum/{name}/{a}{b}_{i}.png")
                        for i, p in enumerate(FRAMES)]
            for a, b in ROLLS}
    files["drum_aod"] = [save(aod_digit(d), f"drum/aod/{d}.png") for d in range(10)]

    files["val"] = [save(VAL[c], f"font/val/{c}.png") for c in DIGITS]
    files["tag"] = [save(TAG[c], f"font/tag/{c}.png") for c in DIGITS]
    files["tag_aod"] = [save(TAG_AOD[c], f"font/tag_aod/{c}.png") for c in DIGITS]
    files["val_minus"] = save(glyph("-", VAL_H), "font/val/minus.png")
    files["val_dot"] = save(glyph(".", VAL_H), "font/val/dot.png")
    files["val_slash"] = save(glyph("/", VAL_H), "font/val/slash.png")
    files["slash"] = save(glyph("/", TAG_H), "font/slash.png")
    files["slash_aod"] = save(glyph("/", TAG_H, AOD_FIG), "font/slash_aod.png")

    for lang, words in WEEK.items():
        files["labels"][lang] = save(labels(lang), f"labels/{lang}.png")
        files["week"][lang] = [save(week_img(w, WHITE), f"week/{lang}/{i}.png")
                               for i, w in enumerate(words)]
        files["week_aod"][lang] = [save(week_img(w, AOD_FIG), f"week/{lang}/aod_{i}.png")
                                   for i, w in enumerate(words)]

    wicons = {k: weather_icon(k) for k in set(I.WEATHER_MAP)}
    files["weather"] = [save(wicons[n], f"weather/{i}.png") for i, n in enumerate(I.WEATHER_MAP)]

    for key, src in dict(bt="bt_off", alarm="alarm", dnd="dnd", lock="lock").items():
        files[src] = save(STATUS_ICONS[key](INK), f"status/{src}.png")

    bg = draw_plate()
    for key in STATUS:  # stamped in the plate, inked when the status is on
        bg.alpha_composite(STATUS_ICONS[key](GHOST), L[key])
    files["bg"] = save(bg.convert("RGB"), "bg.png")

    aod_bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    ImageDraw.Draw(aod_bg).rectangle((AX - 8, AY - 12, AX + a_w + 8, AY + FIG_H + 12),
                                     outline=AOD_DIM)
    aod_bg.alpha_composite(caps(text("kWh", 15, AOD_DIM), 15), (AX - 8, AY - 34))
    cx = AX + pair_w + PAIR_GAP // 2
    for cy in (AY + FIG_H // 3, AY + 2 * FIG_H // 3):
        ImageDraw.Draw(aod_bg).ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=AOD_DIM)
    files["bg_aod"] = save(aod_bg.convert("RGB"), "bg_aod.png")

    files["icon"] = save(make_icon(), "icon.png")

    face.write_layout(L=L, F=files)
    make_previews(files)
    print("assets written to", face.assets)


def make_icon():
    im = Image.new("RGBA", (248, 248), (186, 188, 186, 255))
    ImageDraw.Draw(im).rounded_rectangle((12, 66, 235, 182), 6, fill=(6, 6, 6, 255))
    for x, (a, b, p, w) in zip((18, 90, 162), ((1, 1, 0, WHEEL), (2, 2, 0, WHEEL),
                                               (3, 4, 0.5, WHEEL_RED))):
        im.alpha_composite(drum(a, b, p, w).convert("RGBA").resize((68, 110)), (x, 69))
    return im


# ---------------------------------------------------------------- preview


def make_previews(files):
    op = lambda r: Image.open(os.path.join(face.assets, r)).convert("RGBA")
    val = dict(VAL)
    val.update({".": glyph(".", VAL_H), "/": glyph("/", VAL_H), "-": glyph("-", VAL_H)})
    lang = "pt"

    im = op(files["bg"])
    im.alpha_composite(op(files["labels"][lang]), LABEL_RECT[:2])
    for i, ((x, y), d) in enumerate(zip(L["cells"], "160633")):
        im.alpha_composite(op(files["black" if i < 4 else "red"][int(d)]), (x, y))
    # catch the last wheel mid-roll: that's the whole idea
    im.alpha_composite(op(files["red_roll"]["34"][1]), L["cells"][5])
    im.alpha_composite(op(files["week"][lang][6]), L["week"])
    text_img(im, *L["day"], "01", TAG, L["dateSpace"])
    im.alpha_composite(op(files["slash"]), L["slash"])
    text_img(im, L["slash"][0] + L["slashW"] + 4, L["day"][1], "06", TAG, L["dateSpace"])
    im.alpha_composite(op(files["weather"][0]), L["weatherIcon"])
    im.alpha_composite(op(files["alarm"]), L["alarm"])
    for key, txt in [("heartText", "120"), ("spo2Text", "98"), ("stressText", "45"),
                     ("temp", "-28"), ("stepText", "7500"), ("distText", "20.25"),
                     ("calText", "210"), ("sleepText", "7.3"), ("standText", "8/12"),
                     ("batteryText", "100")]:
        x, y, w = L[key]
        text_img(im, x, y, txt, val, L["valSpace"], w, "center")
    mask_screen(im).save(face.path("preview.png"))

    A = L["aod"]
    a = op(files["bg_aod"])
    big = {str(i): op(files["drum_aod"][i]) for i in range(10)}
    text_img(a, *A["hour"], "16", big, CELL_GAP)
    text_img(a, *A["minute"], "06", big, CELL_GAP)
    text_img(a, *A["day"], "01", TAG_AOD, 1)
    a.alpha_composite(op(files["slash_aod"]), A["slash"])
    text_img(a, A["slash"][0] + L["slashW"] + 4, A["day"][1], "06", TAG_AOD, 1)
    a.alpha_composite(op(files["week_aod"][lang][6]), A["week"])
    mask_screen(a).save(face.path("preview_aod.png"))


if __name__ == "__main__":
    main()
