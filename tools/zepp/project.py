"""Per-face plumbing: device constants, weekday/month strings, asset output and
injecting the generated layout into watchface/index.js."""
import json
import os

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

# Amazfit Bip 6
W, H = 390, 450
TARGET = "bip6"

# IMG_WEEK order is Monday..Sunday.
WEEK = {
    "pt": ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"],
    "en": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
    "es": ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"],
}
MONTHS_PT = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
             "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

LAYOUT_START = "// GENERATED LAYOUT START (do not edit, see design.py)\n"
LAYOUT_END = "// GENERATED LAYOUT END\n"


class Face:
    """A watchface folder: <root>/assets/bip6, <root>/watchface/index.js."""

    def __init__(self, design_file):
        self.root = os.path.dirname(os.path.abspath(design_file))
        self.assets = os.path.join(self.root, "assets", TARGET)

    def save(self, im, rel):
        """Write an image under assets/bip6 and return its path as used in JS."""
        p = os.path.join(self.assets, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        im.save(p)
        return rel.replace(os.sep, "/")

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def write_layout(self, **consts):
        """Replace the GENERATED block in watchface/index.js with
        `const NAME = <json>` for each keyword argument. The block is inlined
        (no import) because ZeppOS Player runs the source file directly."""
        index = self.path("watchface", "index.js")
        with open(index, encoding="utf-8") as f:
            src = f.read()
        if LAYOUT_START not in src or LAYOUT_END not in src:
            raise SystemExit(f"{index}: missing GENERATED LAYOUT markers")
        body = "".join(f"const {k} = {json.dumps(v)}\n" for k, v in consts.items())
        src = (src[:src.index(LAYOUT_START)] + LAYOUT_START + body
               + src[src.index(LAYOUT_END):])
        with open(index, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
