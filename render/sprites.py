"""
Procedural pixel-art sprites built with PNMImage — no external assets needed.
Each pixel is upscaled (scale=6) with FTNearest for a crisp pixel-art look.
"""
from __future__ import annotations

from panda3d.core import CardMaker, LColor, PNMImage, Texture, TransparencyAttrib

# ── Palette helpers ─────────────────────────────────────────────────────────
def _c(r: int, g: int, b: int, a: int = 255) -> tuple:
    return (r, g, b, a)

_ = (0, 0, 0, 0)  # transparent

# ── Hero (blue knight) ───────────────────────────────────────────────────────
_SK = _c(235, 195, 148)
_HH = _c(55,  38,  18)
_BB = _c(52,  92, 195)
_BD = _c(28,  52, 130)
_BS = _c(148, 168, 225)
_EE = _c(28,  22,  18)

HERO_PIXELS: list[list[tuple]] = [
    [_, _,  _HH,_HH,_HH,_HH, _,  _ ],
    [_, _HH,_HH,_HH,_HH,_HH,_HH, _ ],
    [_, _HH,_SK, _SK,_SK, _SK,_HH, _ ],
    [_, _,  _SK, _EE,_SK, _EE,_SK, _ ],
    [_, _,  _SK, _SK,_SK, _SK,_SK, _ ],
    [_, _,  _BB, _BB,_BB, _BB,_BB, _ ],
    [_, _BS,_BB, _BB,_BB, _BB,_BB,_BS],
    [_BS,_BS,_BS,_BB,_BB, _BB,_BS,_BS],
    [_, _BS,_BB, _BB,_BB, _BB,_BB,_BS],
    [_, _,  _BD, _BB,_BB, _BB,_BD, _ ],
    [_, _,  _BB, _BB, _,  _BB,_BB, _ ],
    [_, _,  _BB, _BB, _,  _BB,_BB, _ ],
    [_, _,  _BD, _BD, _,  _BD,_BD, _ ],
]

# ── Goblin (red-eyed raider) ─────────────────────────────────────────────────
_GS = _c(85, 155, 58)
_GL = _c(118, 205, 95)
_GD = _c(45, 100, 32)
_RE = _c(210, 48,  42)
_BR = _c(122, 82,  42)
_BRD= _c(72,  48,  22)
_WT = _c(235, 228, 210)

GOBLIN_PIXELS: list[list[tuple]] = [
    [_,   _GD, _GD, _GD, _GD, _GD, _GD,  _ ],
    [_GD, _GS, _GL, _GS, _GS, _GL, _GS, _GD],
    [_GD, _GS, _RE, _GS, _GS, _RE, _GS, _GD],
    [_GD, _GS, _GS, _GS, _GS, _GS, _GS, _GD],
    [_,   _GD, _WT, _GD, _GD, _WT, _GD,  _ ],
    [_,   _BR, _BR, _BR, _BR, _BR, _BR,  _ ],
    [_BR, _BR, _BR, _BR, _BR, _BR, _BR, _BR],
    [_,   _BR, _BR,_BRD,_BRD, _BR, _BR,  _ ],
    [_,   _,   _GS, _GS, _GS, _GS,  _,   _ ],
    [_,   _,   _BR, _BR, _BR, _BR,  _,   _ ],
    [_,   _,  _BRD, _BR, _BR,_BRD,  _,   _ ],
]

# ── Slime A (bright green blob) ──────────────────────────────────────────────
_SG = _c(62, 195, 78)
_SL = _c(125, 232, 128)
_SD = _c(32, 120, 48)
_SE = _c(12,  18,  12)

SLIME_A_PIXELS: list[list[tuple]] = [
    [_,   _,   _SG, _SG, _SG, _SG,  _,   _ ],
    [_,   _SG, _SL, _SG, _SG, _SL, _SG,  _ ],
    [_SG, _SG, _SE, _SG, _SG, _SE, _SG, _SG],
    [_SG, _SG, _SG, _SG, _SG, _SG, _SG, _SG],
    [_SG, _SL, _SG, _SG, _SG, _SG, _SL, _SG],
    [_,   _SG, _SG, _SD, _SD, _SG, _SG,  _ ],
    [_,   _,   _SG, _SG, _SG, _SG,  _,   _ ],
]

# ── Slime B (electric blue-purple variant) ────────────────────────────────────
_TB = _c(58,  95, 215)
_TL = _c(110, 148, 245)
_TD = _c(28,  45, 140)
_TY = _c(240, 225,  55)

SLIME_B_PIXELS: list[list[tuple]] = [
    [_,   _,   _TB, _TB, _TB, _TB,  _,   _ ],
    [_,   _TB, _TL, _TB, _TB, _TL, _TB,  _ ],
    [_TB, _TB, _TY, _TB, _TB, _TY, _TB, _TB],
    [_TB, _TB, _TB, _TB, _TB, _TB, _TB, _TB],
    [_TB, _TL, _TB, _TB, _TB, _TB, _TL, _TB],
    [_,   _TB, _TB, _TD, _TD, _TB, _TB,  _ ],
    [_,   _,   _TB, _TB, _TB, _TB,  _,   _ ],
]

# ── Blob Small (tiny first-floor enemy) ─────────────────────────────────────
_BG = _c(58, 175, 68)
_BL = _c(105, 215, 112)
_BDE= _c(22, 140, 38)
_BE2= _c(10,  14,  10)

BLOB_SMALL_PIXELS: list[list[tuple]] = [
    [_,   _BG, _BG, _BG, _BG, _ ],
    [_BG, _BL, _BE2,_BG, _BE2,_BG],
    [_BG, _BG, _BG, _BG, _BG, _BG],
    [_BG, _BL, _BG, _BG, _BL, _BG],
    [_,   _BG, _BDE,_BDE,_BG,  _ ],
]

# ── Bat (fast winged enemy) ──────────────────────────────────────────────────
_BA = _c(48,  35,  58)
_BM = _c(72,  52,  88)
_BEA= _c(195, 38,  35)
_BWL= _c(88,  68, 108)

BAT_PIXELS: list[list[tuple]] = [
    [_BA,  _,   _,   _BM, _BM,  _,   _,  _BA],
    [_BA, _BA, _BM, _BWL,_BWL, _BM, _BA, _BA],
    [_,   _BA, _BEA, _BA, _BA, _BEA,_BA,  _ ],
    [_,   _BA, _BA,  _BA, _BA,  _BA,_BA,  _ ],
    [_,    _,  _BA,  _BA, _BA,  _BA,  _,  _ ],
]

# ── Mushroom (poison caster) ─────────────────────────────────────────────────
_MR = _c(175, 55,  45)
_ML = _c(215, 88,  78)
_MD = _c(115, 32,  25)
_MS = _c(218, 195, 155)
_MW = _c(245, 240, 230)
_MS2= _c(185, 158, 112)

MUSHROOM_PIXELS: list[list[tuple]] = [
    [_,   _MR, _MR, _MR, _MR, _MR, _MR,  _ ],
    [_MR, _ML, _MR, _MW, _MR, _MW, _ML, _MR],
    [_MR, _MR, _MD, _MD, _MD, _MD, _MR, _MR],
    [_MR, _MR, _MR, _MR, _MR, _MR, _MR, _MR],
    [_,   _,   _MS, _MS, _MS, _MS,  _,   _ ],
    [_,   _,   _MS, _MS2,_MS2,_MS,  _,   _ ],
    [_,   _MS2,_MS, _MS, _MS, _MS, _MS2, _ ],
    [_,   _MS2,_MS2,_MS, _MS, _MS2,_MS2, _ ],
]

# ── Orc (heavy tank) ─────────────────────────────────────────────────────────
_OS = _c(98, 148, 62)
_OL = _c(138,195, 98)
_OD = _c(55,  95, 38)
_OE = _c(205, 42,  38)
_OT = _c(235, 228, 205)
_OA = _c(110,  95,  78)
_OAD= _c(68,  55,  42)

ORC_PIXELS: list[list[tuple]] = [
    [_,    _OD,  _OD, _OD, _OD, _OD,  _OD,  _ ],
    [_OD,  _OS,  _OL, _OS, _OS, _OL,  _OS, _OD],
    [_OD,  _OS,  _OE, _OS, _OS, _OE,  _OS, _OD],
    [_OD,  _OS,  _OT, _OS, _OS, _OT,  _OS, _OD],
    [_,    _OA,  _OA, _OA, _OA, _OA,  _OA,  _ ],
    [_OA,  _OA,  _OA, _OA, _OA, _OA,  _OA, _OA],
    [_OA,  _OA,  _OA, _OA, _OA, _OA,  _OA, _OA],
    [_OAD, _OA,  _OA, _OA, _OA, _OA,  _OA,_OAD],
    [_,    _OA,  _OA, _OA, _OA, _OA,  _OA,  _ ],
    [_,    _,    _OS, _OS, _OS, _OS,   _,   _ ],
    [_,    _,    _OA, _OA, _OA, _OA,   _,   _ ],
    [_,    _,    _OA, _OA, _OA, _OA,   _,   _ ],
    [_,    _,   _OAD,_OAD,_OAD,_OAD,   _,   _ ],
]

# ── Witch (magic caster) ─────────────────────────────────────────────────────
_WH = _c(42,  22,  72)
_WS = _c(228, 195, 155)
_WR = _c(105, 38, 145)
_WRL= _c(145, 72, 195)
_WE = _c(178, 55, 235)
_WW = _c(242, 225,  55)

WITCH_PIXELS: list[list[tuple]] = [
    [_,   _,    _WH, _WH, _WH,  _,    _,   _ ],
    [_,   _WH,  _WH, _WH, _WH, _WH,   _,   _ ],
    [_,   _WH,  _WH, _WH, _WH, _WH,  _WH,  _ ],
    [_,   _,    _WS, _WS, _WS, _WS,   _,   _ ],
    [_,   _,    _WS, _WE, _WS, _WE,   _,   _ ],
    [_,   _,    _WS, _WS, _WS, _WS,   _,   _ ],
    [_,   _WR,  _WR, _WR, _WR, _WR,  _WR,  _ ],
    [_WR, _WR,  _WR, _WR, _WR, _WR,  _WR, _WR],
    [_,   _WRL, _WR, _WR, _WW, _WRL, _WR,  _ ],
    [_,   _,    _WR, _WR, _WR, _WR,   _,   _ ],
    [_,   _,    _WR,  _,   _,  _WR,   _,   _ ],
]

# ── Slime King (boss — large crowned slime) ───────────────────────────────────
_CW = _c(242, 198,  35)
_CJ = _c(218,  42,  42)
_KG = _c(42, 195, 68)
_KL = _c(95, 232, 112)
_KD = _c(22, 125, 42)
_KE = _c(8,   12,   8)

SLIME_KING_PIXELS: list[list[tuple]] = [
    [_,   _CW, _CJ, _CW, _CW, _CJ, _CW,  _ ],
    [_,   _CW, _CW, _CW, _CW, _CW, _CW,  _ ],
    [_,   _KG, _KG, _KG, _KG, _KG, _KG,  _ ],
    [_KG, _KL, _KL, _KG, _KG, _KL, _KL, _KG],
    [_KG, _KG, _KE, _KG, _KG, _KE, _KG, _KG],
    [_KG, _KG, _KG, _KG, _KG, _KG, _KG, _KG],
    [_KG, _KL, _KG, _KG, _KG, _KG, _KL, _KG],
    [_,   _KG, _KG, _KD, _KD, _KG, _KG,  _ ],
    [_,   _,   _KG, _KG, _KG, _KG,  _,   _ ],
]

# ── Goblin Chief (boss — crowned goblin) ──────────────────────────────────────
_GGA= _c(195, 155, 40)  # gold armor
_GGD= _c(145, 108, 22)  # gold dark

GOBLIN_CHIEF_PIXELS: list[list[tuple]] = [
    [_,   _CW, _CJ, _CW, _CW, _CJ, _CW,  _ ],
    [_,   _CW, _CW, _CW, _CW, _CW, _CW,  _ ],
    [_,   _GD, _GD, _GD, _GD, _GD, _GD,  _ ],
    [_GD, _GS, _GL, _GS, _GS, _GL, _GS, _GD],
    [_GD, _GS, _RE, _GS, _GS, _RE, _GS, _GD],
    [_GD, _GS, _GS, _GS, _GS, _GS, _GS, _GD],
    [_,   _GD, _WT, _GD, _GD, _WT, _GD,  _ ],
    [_,   _GGA,_GGA,_GGA,_GGA,_GGA,_GGA, _ ],
    [_GGA,_GGA,_GGA,_GGA,_GGA,_GGA,_GGA,_GGA],
    [_,   _GGA,_GGD,_GGA,_GGA,_GGD,_GGA, _ ],
    [_,   _,   _GS, _GS, _GS, _GS,  _,   _ ],
    [_,   _,   _GGA,_GGA,_GGA,_GGA,  _,   _ ],
]

# ── Dark Knight (boss — dark armor) ──────────────────────────────────────────
_DK = _c(28,  28,  32)
_DR = _c(115, 22,  22)
_DS = _c(88,  88,  98)
_DRE= _c(225, 35,  35)

DARK_KNIGHT_PIXELS: list[list[tuple]] = [
    [_,   _DK, _DK, _DK, _DK, _DK, _DK,  _ ],
    [_DK, _DK, _DK, _DK, _DK, _DK, _DK, _DK],
    [_DK, _DS, _DS, _DS, _DS, _DS, _DS, _DK],
    [_DK, _DS, _DRE,_DS, _DS, _DRE,_DS, _DK],
    [_DK, _DS, _DS, _DS, _DS, _DS, _DS, _DK],
    [_,   _DR, _DR, _DR, _DR, _DR, _DR,  _ ],
    [_DR, _DR, _DR, _DR, _DR, _DR, _DR, _DR],
    [_DR, _DR, _DR, _DR, _DR, _DR, _DR, _DR],
    [_DS, _DR, _DR, _DR, _DR, _DR, _DR, _DS],
    [_,   _DR, _DR, _DR, _DR, _DR, _DR,  _ ],
    [_,   _,   _DR, _DR, _DR, _DR,  _,   _ ],
    [_DK, _DK, _DK,  _,   _,  _DK, _DK, _DK],
    [_DR, _DR, _DR,  _,   _,  _DR, _DR, _DR],
    [_DK, _DK, _DK,  _,   _,  _DK, _DK, _DK],
]

# ── Ancient Golem (boss — stone giant) ───────────────────────────────────────
_AG = _c(105, 100, 90)
_AL = _c(148, 142, 128)
_AD = _c(62,  58,  50)
_AC = _c(38,  34,  28)
_AOE= _c(222, 128,  28)

ANCIENT_GOLEM_PIXELS: list[list[tuple]] = [
    [_,   _AG, _AG, _AG, _AG, _AG, _AG,  _ ],
    [_AG, _AL, _AL, _AG, _AG, _AL, _AL, _AG],
    [_AG, _AG, _AOE,_AG, _AG, _AOE,_AG, _AG],
    [_AG, _AC, _AC, _AG, _AG, _AC, _AC, _AG],
    [_,   _AG, _AG, _AG, _AG, _AG, _AG,  _ ],
    [_AG, _AG, _AG, _AG, _AG, _AG, _AG, _AG],
    [_AL, _AG, _AG, _AG, _AG, _AG, _AG, _AL],
    [_AG, _AG, _AG, _AG, _AG, _AG, _AG, _AG],
    [_,   _AG, _AD, _AG, _AG, _AD, _AG,  _ ],
    [_,   _AG, _AG, _AG, _AG, _AG, _AG,  _ ],
    [_,   _,   _AG, _AG, _AG, _AG,  _,   _ ],
    [_,   _,   _AD, _AG, _AG, _AD,  _,   _ ],
    [_,   _,   _AG, _AG, _AG, _AG,  _,   _ ],
]

# ── Texture builder ──────────────────────────────────────────────────────────

def _build_texture(pixels: list[list[tuple]], scale: int = 6) -> Texture:
    rows = len(pixels)
    cols = max(len(r) for r in pixels)
    W, H = cols * scale, rows * scale
    img = PNMImage(W, H)
    img.addAlpha()
    img.fill(0.0, 0.0, 0.0)
    img.alphaFill(0.0)
    for row_i, row in enumerate(pixels):
        for col_i, rgba in enumerate(row):
            if not rgba or rgba[3] == 0:
                continue
            r, g, b, a = rgba
            for dy in range(scale):
                for dx in range(scale):
                    px = col_i * scale + dx
                    py = row_i * scale + dy
                    img.setXel(px, py, r / 255.0, g / 255.0, b / 255.0)
                    img.setAlpha(px, py, a / 255.0)
    tex = Texture()
    tex.load(img)
    tex.setMagfilter(Texture.FTNearest)
    tex.setMinfilter(Texture.FTNearest)
    return tex


_TEX_CACHE: dict[str, Texture] = {}

_CHAR_DIMS: dict[str, tuple[float, float]] = {
    "hero":          (1.18, 2.00),
    "goblin":        (1.05, 1.72),
    "slime_a":       (1.10, 1.18),
    "slime_b":       (1.10, 1.18),
    "blob_small":    (0.90, 0.82),
    "bat":           (1.30, 0.80),
    "mushroom":      (1.10, 1.32),
    "orc":           (1.12, 2.10),
    "witch":         (1.05, 1.80),
    "slime_king":    (1.35, 1.48),
    "goblin_chief":  (1.10, 1.98),
    "dark_knight":   (1.15, 2.28),
    "ancient_golem": (1.20, 2.18),
}

_CHAR_PIXELS: dict[str, list] = {
    "hero":          HERO_PIXELS,
    "goblin":        GOBLIN_PIXELS,
    "slime_a":       SLIME_A_PIXELS,
    "slime_b":       SLIME_B_PIXELS,
    "blob_small":    BLOB_SMALL_PIXELS,
    "bat":           BAT_PIXELS,
    "mushroom":      MUSHROOM_PIXELS,
    "orc":           ORC_PIXELS,
    "witch":         WITCH_PIXELS,
    "slime_king":    SLIME_KING_PIXELS,
    "goblin_chief":  GOBLIN_CHIEF_PIXELS,
    "dark_knight":   DARK_KNIGHT_PIXELS,
    "ancient_golem": ANCIENT_GOLEM_PIXELS,
}


def make_char_sprite(parent, unit_id: str) -> tuple[float, float]:
    """
    Attach a pixel-art billboard sprite to parent.
    Returns (width, height) in game units for HP-bar / label placement.
    """
    base_id = unit_id
    if "_" in unit_id:
        parts = unit_id.rsplit("_", 1)
        if parts[-1].isdigit():
            base_id = parts[0]

    key = base_id if base_id in _CHAR_PIXELS else "slime_a"
    pixels = _CHAR_PIXELS[key]
    w, h = _CHAR_DIMS.get(key, (1.0, 1.2))

    if key not in _TEX_CACHE:
        _TEX_CACHE[key] = _build_texture(pixels, scale=6)

    tex = _TEX_CACHE[key]
    cm = CardMaker("sprite")
    cm.setFrame(-w / 2, w / 2, 0.0, h)
    card = parent.attachNewNode(cm.generate())
    card.setTexture(tex)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setBillboardPointEye()

    return w, h
