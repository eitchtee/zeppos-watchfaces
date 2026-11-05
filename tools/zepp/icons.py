"""Pixel-art icon grids ("X" = lit). Render with draw.pixel(grid, scale, color)."""
from .draw import compose

ICON_HEART = [
    "..XXX...XXX..",
    ".XXXXX.XXXXX.",
    "XXXXXXXXXXXXX",
    "XXXXXXXXXXXXX",
    "XXXXXXXXXXXXX",
    ".XXXXXXXXXXX.",
    "..XXXXXXXXX..",
    "...XXXXXXX...",
    "....XXXXX....",
    ".....XXX.....",
    "......X......",
]

ICON_STEPS = [
    "........XXX.",
    ".......XXXXX",
    ".......XXXXX",
    ".XXX...XXXXX",
    "XXXXX...XXX.",
    "XXXXX.......",
    "XXXXX...XXX.",
    ".XXX....XXX.",
    "............",
    ".XXX........",
    ".XXX........",
]

ICON_FLAME = [
    ".....X......",
    ".....XX.....",
    "....XXX.....",
    "....XXXX....",
    "...XXXXX..X.",
    "..XXXXXXX.XX",
    "..XXXXXXXXXX",
    ".XXXXX.XXXXX",
    "XXXXX...XXXX",
    "XXXX..X..XXX",
    "XXX..XXX.XXX",
    ".XX.XXXX.XX.",
    "..XXXXXXXX..",
]

ICON_PIN = [
    "...XXXXX...",
    "..XXXXXXX..",
    ".XXX...XXX.",
    ".XX.....XX.",
    ".XX.....XX.",
    ".XXX...XXX.",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "...XXXXX...",
    "....XXX....",
    ".....X.....",
    "...........",
    "XXXXXXXXXXX",
]

ICON_BT = [
    "...X...",
    "...XX..",
    ".X.X.X.",
    "..XXX..",
    "...X...",
    "..XXX..",
    ".X.X.X.",
    "...XX..",
    "...X...",
]

ICON_BT_OFF = [  # rune + small x: lit only when the phone is disconnected
    "...X.......",
    "...XX......",
    ".X.X.X.....",
    "..XXX......",
    "...X.......",
    "..XXX..X.X.",
    ".X.X.X..X..",
    "...XX..X.X.",
    "...X.......",
]

ICON_ALARM = [
    "XX.....XX",
    "X.XXXXX.X",
    ".X..X..X.",
    "X...X...X",
    "X...XX..X",
    "X.......X",
    ".X.....X.",
    "..XXXXX..",
    ".X.....X.",
]

ICON_MOON_S = [
    "..XXX....",
    ".XX......",
    "XX.......",
    "XX.......",
    "XX.......",
    "XX......X",
    ".XX....XX",
    "..XXXXXX.",
    "...XXXX..",
]

ICON_LOCK = [
    "..XXX..",
    ".X...X.",
    ".X...X.",
    "XXXXXXX",
    "XXX.XXX",
    "XXX.XXX",
    "XXXXXXX",
    "XXXXXXX",
]

ICON_DROP = [  # SpO2
    "....X....",
    "....X....",
    "...XXX...",
    "...XXX...",
    "..XXXXX..",
    ".XXXXXXX.",
    ".XXXXXXX.",
    "XXXXXXXXX",
    "X.XXXXXXX",
    "X.XXXXXXX",
    ".X.XXXXX.",
    "..XXXXX..",
]

ICON_STRESS = [  # lightning bolt
    "....XXXX",
    "...XXXX.",
    "..XXXX..",
    ".XXXX...",
    "XXXXXXXX",
    "XXXXXXXX",
    "...XXXX.",
    "..XXXX..",
    "..XXX...",
    ".XXX....",
    ".XX.....",
    "XX......",
]

ICON_BED = [
    "X............",
    "X............",
    "X............",
    "X.XXX........",
    "XXXXX.XXXXXXX",
    "XXXXXXXXXXXXX",
    "XXXXXXXXXXXXX",
    "X...........X",
    "X...........X",
]

ICON_STAND = [  # standing person
    "...XXX...",
    "...XXX...",
    "...XXX...",
    ".........",
    "..XXXXX..",
    ".XXXXXXX.",
    "X.XXXXX.X",
    "X.XXXXX.X",
    "..XX.XX..",
    "..XX.XX..",
    "..XX.XX..",
    "..XX.XX..",
    "..XX.XX..",
]

ARROW_DOWN = ["XXXXX", ".XXX.", "..X.."]

ARROW_UP = ["..X..", ".XXX.", "XXXXX"]

SUN = [
    ".....XX.....",
    ".X...XX...X.",
    "..X......X..",
    "....XXXX....",
    "...XXXXXX...",
    "XX.XXXXXX.XX",
    "XX.XXXXXX.XX",
    "...XXXXXX...",
    "....XXXX....",
    "..X......X..",
    ".X...XX...X.",
    ".....XX.....",
]

SUN_SMALL = [
    "..X.X..",
    "X.XXX.X",
    ".XXXXX.",
    "XXXXXXX",
    ".XXXXX.",
    "X.XXX.X",
    "..X.X..",
]

MOON = [
    "...XXXX.....",
    ".XXXX.......",
    ".XXX........",
    "XXX.........",
    "XXX.........",
    "XXX.........",
    "XXX........X",
    "XXXX......XX",
    ".XXXX....XXX",
    ".XXXXXXXXXX.",
    "..XXXXXXXX..",
    "....XXXX....",
]

MOON_SMALL = [
    "..XXX.",
    ".XX...",
    "XX....",
    "XX....",
    "XX...X",
    ".XXXXX",
    "..XXX.",
]

CLOUD = [
    "......XXX...",
    ".....XXXXX..",
    "..XX.XXXXX..",
    ".XXXXXXXXXX.",
    "XXXXXXXXXXXX",
    "XXXXXXXXXXXX",
    ".XXXXXXXXXX.",
]

RAIN = ["..X...X...X.", ".X...X...X..", "X...X...X..."]

SNOW = ["X.X...X.X...", ".X.....X..X.", "X.X.X....X.X"]

BOLT = ["....XX", "...XX.", "..XXXX", "....X.", "...X.."]

FOG = [
    "XXXXXXXXXX..",
    "............",
    "..XXXXXXXXXX",
    "............",
    "XXXXXXXXXX..",
    "............",
    "..XXXXXXXXXX",
    "............",
    "XXXXXXXXXX..",
]

QUESTION = [
    "...XXXXX....",
    "..XX...XX...",
    "..XX...XX...",
    ".......XX...",
    "......XX....",
    ".....XX.....",
    ".....XX.....",
    "............",
    ".....XX.....",
    ".....XX.....",
]

def weather_grids():
    def c(*layers):
        return compose(layers, 12, 12)
    g = {
        "sun": SUN,
        "moon": MOON,
        "cloud": c((CLOUD, 0, 3, False)),
        "partly": c((SUN_SMALL, 0, 0, False), (CLOUD, 0, 4, True)),
        "partly_night": c((MOON_SMALL, 1, 0, False), (CLOUD, 0, 4, True)),
        "rain": c((CLOUD, 0, 0, False), (RAIN, 0, 8, False)),
        "snow": c((CLOUD, 0, 0, False), (SNOW, 0, 8, False)),
        "storm": c((CLOUD, 0, 0, False), (BOLT, 4, 7, True)),
        "fog": c((FOG, 0, 1, False)),
        "unknown": c((QUESTION, 0, 1, False)),
    }
    return g

WEATHER_MAP = [
    "partly",       # 0 cloudy
    "rain",         # 1 showers
    "snow",         # 2 snow showers
    "sun",          # 3 sunny
    "cloud",        # 4 overcast
    "rain",         # 5 light rain
    "snow",         # 6 light snow
    "rain",         # 7 moderate rain
    "snow",         # 8 moderate snow
    "snow",         # 9 heavy snow
    "rain",         # 10 heavy rain
    "fog",          # 11 sandstorm
    "snow",         # 12 rain and snow
    "fog",          # 13 fog
    "fog",          # 14 hazy
    "storm",        # 15 t-storms
    "snow",         # 16 snowstorm
    "fog",          # 17 floating dust
    "rain",         # 18 very heavy rainstorm
    "storm",        # 19 rain and hail
    "storm",        # 20 t-storms and hail
    "rain",         # 21 heavy rainstorm
    "fog",          # 22 dust
    "fog",          # 23 heavy sand storm
    "rain",         # 24 rainstorm
    "unknown",      # 25 unknown
    "partly_night",  # 26 cloudy night
    "rain",         # 27 showers night
    "moon",         # 28 clear night
]
