"""
Anime-style pixel art sprites — 14-16 px wide, cel-shading outline, 3-tone shading.
PNMImage procedural generation, scale 5 (no external assets needed).
"""
from __future__ import annotations

from panda3d.core import CardMaker, LColor, PNMImage, Texture, TransparencyAttrib

def _c(r: int, g: int, b: int, a: int = 255) -> tuple:
    return (r, g, b, a)

_ = (0, 0, 0, 0)  # transparent

# ═══════════════════════════════════════════════════════════
# HERO  14 × 24  — spiky dark-blue hair, cyan eyes, red scarf
# ═══════════════════════════════════════════════════════════
_HO  = _c( 18, 14, 28)
_HSK = _c(245,210,162)
_HSS = _c(205,165,112)
_HSH = _c(255,232,195)
_HHA = _c( 35, 28, 88)
_HHB = _c( 62, 52,138)
_HHC = _c( 98, 82,182)
_HEY = _c( 55,198,242)
_HED = _c( 28,122,165)
_HEH = _c(195,242,255)
_HSF = _c(218, 42, 42)
_HSD = _c(148, 22, 22)
_HAM = _c(148,172,215)
_HAD = _c( 85,105,152)
_HAH = _c(215,228,248)
_HGL = _c( 38, 32, 58)
_HBL = _c( 88, 72, 42)
_HPN = _c( 52, 62, 92)
_HPD = _c( 32, 40, 65)
_HBT = _c( 28, 22, 18)
_HBM = _c( 60, 48, 32)

HERO_PIXELS = [
 [_,   _,   _HHA,_HHC,_HHA,_HHC,_HHA,_HHC,_HHA, _,   _,   _,   _,   _  ],
 [_,   _HHA,_HHB,_HHA,_HHB,_HHC,_HHB,_HHA,_HHB,_HHA, _,   _,   _,   _  ],
 [_,   _HHA,_HHB,_HHC,_HHB,_HHB,_HHB,_HHB,_HHC,_HHB,_HHA, _,   _,   _  ],
 [_HO, _HHA,_HHB,_HSK,_HSK,_HSH,_HSK,_HSK,_HSH,_HSK,_HHB,_HHA,_HO,  _  ],
 [_HO, _HSK,_HSK,_HO, _HO, _HO, _HSK,_HO, _HO, _HO, _HSK,_HSK,_HO,  _  ],
 [_HO, _HSK,_HSS,_HED,_HEY,_HEY,_HSK,_HED,_HEY,_HEY,_HSS,_HSK,_HO,  _  ],
 [_HO, _HSK,_HSK,_HEH,_HEY,_HED,_HSK,_HEH,_HEY,_HED,_HSK,_HSK,_HO,  _  ],
 [_,   _HO, _HSK,_HSK,_HSK,_HSS,_HSS,_HSS,_HSK,_HSK,_HSK,_HO,  _,   _  ],
 [_,   _HO, _HSK,_HSK,_HSK,_HSK,_HSK,_HSK,_HSK,_HSK,_HSK,_HO,  _,   _  ],
 [_,   _HSF,_HSD,_HSF,_HSF,_HSF,_HSF,_HSF,_HSF,_HSD,_HSF,_HSF, _,   _  ],
 [_HAD,_HAM,_HSF,_HSF,_HAM,_HAM,_HAM,_HAM,_HSF,_HSF,_HAM,_HAM,_HAD, _  ],
 [_HAM,_HAH,_HAM,_HGL,_HAM,_HAM,_HAM,_HAM,_HAM,_HGL,_HAM,_HAH,_HAM, _  ],
 [_HAD,_HAM,_HAM,_HGL,_HAH,_HAM,_HAM,_HAM,_HAH,_HGL,_HAM,_HAM,_HAD, _  ],
 [_,   _HAM,_HAM,_HAD,_HAM,_HAM,_HAM,_HAM,_HAM,_HAD,_HAM,_HAM, _,   _  ],
 [_,   _HGL,_HBL,_HBL,_HBL,_HBL,_HBL,_HBL,_HBL,_HBL,_HBL,_HGL, _,   _  ],
 [_,   _,   _HPN,_HPD,_HPN,_HPN,_HPN,_HPN,_HPN,_HPD,_HPN, _,   _,   _  ],
 [_,   _,   _HPN,_HPN,_HPN,_HPD, _,   _,   _HPD,_HPN,_HPN,_HPN, _,   _  ],
 [_,   _,   _HPD,_HPN,_HPN, _,   _,   _,   _,   _HPN,_HPN,_HPD, _,   _  ],
 [_,   _,   _HPN,_HPN,_HPN, _,   _,   _,   _,   _HPN,_HPN,_HPN, _,   _  ],
 [_,   _,   _HPD,_HPN,_HPD, _,   _,   _,   _,   _HPD,_HPN,_HPD, _,   _  ],
 [_,   _HBT,_HBT,_HBM,_HBT, _,   _,   _,   _,   _HBT,_HBM,_HBT,_HBT, _  ],
 [_HBT,_HBT,_HBM,_HBM,_HBT,_HBT, _,   _HBT,_HBT,_HBM,_HBM,_HBT,_HBT, _  ],
 [_HBT,_HBM,_HBM,_HBM,_HBT,_HBT, _,   _HBT,_HBT,_HBM,_HBM,_HBM,_HBT, _  ],
 [_HBT,_HBT,_HBM,_HBT,_HBT,_HBT, _,   _HBT,_HBT,_HBT,_HBM,_HBT,_HBT, _  ],
]

# ═══════════════════════════════════════════════════════════
# BLOB SMALL  10 × 8  — chibi slime, big highlight eyes
# ═══════════════════════════════════════════════════════════
_BG = _c( 55,195, 70)
_BL = _c(105,230,118)
_BD = _c( 28,130, 45)
_BE = _c( 18, 22, 18)

BLOB_SMALL_PIXELS = [
 [_,   _,   _BG, _BG, _BG, _BG, _BG, _,   _,   _  ],
 [_,   _BG, _BL, _BL, _BG, _BG, _BL, _BG, _,   _  ],
 [_BG, _BG, _BE, _BG, _BG, _BG, _BE, _BG, _BG, _  ],
 [_BG, _BL, _BG, _BG, _BG, _BG, _BG, _BL, _BG, _  ],
 [_BG, _BG, _BG, _BG, _BG, _BG, _BG, _BG, _BG, _  ],
 [_,   _BG, _BL, _BG, _BG, _BL, _BG, _BG, _,   _  ],
 [_,   _,   _BG, _BD, _BD, _BG, _BG, _,   _,   _  ],
 [_,   _,   _,   _BG, _BG, _,   _,   _,   _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# BAT  16 × 8  — wide jagged wings, red eyes, white fangs
# ═══════════════════════════════════════════════════════════
_BAP = _c( 55, 35, 75)
_BAM = _c( 90, 60,115)
_BAL = _c(128, 90,155)
_BAE = _c(205, 35, 35)
_BAF = _c(235,232,218)
_BAB = _c( 40, 25, 55)

BAT_PIXELS = [
 [_BAP, _,   _,   _BAP,_BAM,_BAP,_BAP,_BAM,_BAP,_BAP,_BAP, _,   _,   _,  _BAP, _  ],
 [_BAP,_BAP,_BAM,_BAL,_BAM,_BAP,_BAP,_BAP,_BAM,_BAL,_BAM,_BAP,_BAP, _,   _,   _  ],
 [_,   _BAP,_BAM,_BAM,_BAM,_BAB,_BAB,_BAB,_BAM,_BAM,_BAM,_BAP, _,   _,   _,   _  ],
 [_,   _BAP,_BAM,_BAM,_BAB,_BAE,_BAB,_BAE,_BAB,_BAM,_BAM,_BAP, _,   _,   _,   _  ],
 [_,   _,   _BAP,_BAM,_BAB,_BAF,_BAB,_BAF,_BAB,_BAM,_BAP, _,   _,   _,   _,   _  ],
 [_,   _,   _BAP,_BAM,_BAM,_BAB,_BAB,_BAB,_BAM,_BAM,_BAP, _,   _,   _,   _,   _  ],
 [_,   _,   _,   _BAP,_BAP,_BAP,_BAB,_BAP,_BAP,_BAP, _,   _,   _,   _,   _,   _  ],
 [_,   _,   _,   _,   _BAP,_BAP,_BAB,_BAP,_BAP, _,   _,   _,   _,   _,   _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# MUSHROOM  12 × 14  — huge cap, angry glow eyes, teeth
# ═══════════════════════════════════════════════════════════
_MUR = _c(175, 48, 38)
_MUL = _c(215, 85, 72)
_MUS = _c(112, 28, 22)
_MUW = _c(245,240,225)
_MUT = _c(218,195,152)
_MUSh= _c(178,155,112)
_MUH = _c(238,218,178)
_MUE = _c( 22, 18, 15)
_MUG = _c(125,195, 55)
_MUM = _c( 88, 52, 35)

MUSHROOM_PIXELS = [
 [_,   _MUR,_MUR,_MUR,_MUR,_MUR,_MUR,_MUR,_MUR,_MUR, _,   _  ],
 [_MUR,_MUL,_MUW,_MUR,_MUR,_MUR,_MUR,_MUW,_MUL,_MUR,_MUR, _  ],
 [_MUR,_MUR,_MUR,_MUW,_MUR,_MUR,_MUW,_MUR,_MUR,_MUR,_MUR, _  ],
 [_MUR,_MUL,_MUR,_MUR,_MUR,_MUR,_MUR,_MUR,_MUL,_MUR,_MUR, _  ],
 [_MUS,_MUS,_MUS,_MUS,_MUS,_MUS,_MUS,_MUS,_MUS,_MUS,_MUS, _  ],
 [_,   _,   _MUT,_MUT,_MUT,_MUT,_MUT,_MUT,_MUT, _,   _,   _  ],
 [_,   _,   _MUH,_MUE,_MUE,_MUG,_MUG,_MUE,_MUSh,_,  _,   _  ],
 [_,   _,   _MUT,_MUSh,_MUE,_MUE,_MUE,_MUE,_MUT,_,  _,   _  ],
 [_,   _,   _MUT,_MUH,_MUM,_MUT,_MUM,_MUH,_MUT, _,   _,   _  ],
 [_,   _,   _MUH,_MUT,_MUT,_MUT,_MUT,_MUT,_MUSh,_,  _,   _  ],
 [_,   _,   _MUT,_MUT,_MUT,_MUT,_MUT,_MUT,_MUT, _,   _,   _  ],
 [_,   _,   _MUSh,_MUT,_MUT,_MUT,_MUT,_MUT,_MUSh,_,  _,  _  ],
 [_,   _MUSh,_MUT,_MUSh, _,  _,  _,   _MUSh,_MUT,_MUSh, _,  _  ],
 [_,   _MUSh,_MUSh, _,   _,  _,  _,   _,   _MUSh,_MUSh, _,  _  ],
]

# ═══════════════════════════════════════════════════════════
# GOBLIN  12 × 20  — lime skin, slit red eyes, fang grin
# ═══════════════════════════════════════════════════════════
_GOS = _c( 88,158, 60)
_GOL = _c(122,208, 98)
_GOD = _c( 48,102, 35)
_GOE = _c(212, 45, 42)
_GOF = _c(238,232,215)
_GOB = _c(125, 85, 42)
_GBD = _c( 78, 52, 25)

GOBLIN_PIXELS = [
 [_,   _GOD,_GOD,_GOD,_GOD,_GOD,_GOD,_GOD,_GOD, _,   _,   _  ],
 [_GOD,_GOS,_GOL,_GOS,_GOS,_GOS,_GOS,_GOL,_GOS,_GOD, _,   _  ],
 [_GOD,_GOL,_GOS,_GOS,_GOS,_GOS,_GOS,_GOS,_GOL,_GOD, _,   _  ],
 [_GOD,_GOS,_GOE,_GOE,_GOS,_GOS,_GOE,_GOE,_GOS,_GOD, _,   _  ],
 [_,   _GOD,_GOS,_GOS,_GOD,_GOD,_GOS,_GOS,_GOD, _,   _,   _  ],
 [_,   _GOD,_GOS,_GOF,_GOS,_GOS,_GOF,_GOS,_GOD, _,   _,   _  ],
 [_,   _,   _GOD,_GOS,_GOS,_GOS,_GOS,_GOD, _,   _,   _,   _  ],
 [_,   _GOB,_GBD,_GOB,_GOB,_GOB,_GOB,_GBD,_GOB, _,   _,   _  ],
 [_GOB,_GOB,_GOS,_GOB,_GOB,_GOB,_GOB,_GOS,_GOB,_GOB, _,   _  ],
 [_GOS,_GOB,_GBD,_GOB,_GBD,_GBD,_GOB,_GBD,_GOB,_GOS, _,   _  ],
 [_GOS,_GOB,_GOB,_GBD,_GOB,_GOB,_GBD,_GOB,_GOB,_GOS, _,   _  ],
 [_GOD,_GOS,_GOB,_GOB,_GOB,_GOB,_GOB,_GOB,_GOS,_GOD, _,   _  ],
 [_,   _GBD,_GOB,_GBD,_GBD,_GBD,_GBD,_GOB,_GBD, _,   _,   _  ],
 [_,   _GOS,_GOS,_GOD,_GOS, _,   _,   _GOD,_GOS,_GOS, _,   _  ],
 [_,   _GOD,_GOS,_GOS,_GOS, _,   _,   _GOS,_GOS,_GOD, _,   _  ],
 [_,   _GOS,_GOS,_GOD, _,   _,   _,   _,   _GOD,_GOS, _,   _  ],
 [_,   _GOS,_GOD,_GOS, _,   _,   _,   _,   _GOS,_GOD, _,   _  ],
 [_,   _GOD,_GOS,_GOD,_GOD, _,   _,   _GOD,_GOD,_GOS, _,   _  ],
 [_,   _GOD,_GOS,_GOS,_GOD, _,   _,   _GOD,_GOS,_GOS, _,   _  ],
 [_GOD, _,  _GOD, _,   _,   _,   _,   _,   _,   _GOD,_GOD, _  ],
]

# ═══════════════════════════════════════════════════════════
# ORC  14 × 22  — barrel chest, tusks, iron armor
# ═══════════════════════════════════════════════════════════
_ORS = _c(105,152, 68)
_ORL = _c(142,198, 98)
_ORD = _c( 60,100, 42)
_ORE = _c(205, 38, 38)
_ORT = _c(238,225,205)
_ORA = _c(115, 98, 80)
_OAD = _c( 72, 60, 48)
_OAL = _c(158,142,122)
_ORB = _c( 88, 72, 55)

ORC_PIXELS = [
 [_,   _,   _ORD,_ORD,_ORD,_ORD,_ORD,_ORD,_ORD, _,   _,   _,   _,   _  ],
 [_,   _ORD,_ORS,_ORL,_ORS,_ORS,_ORS,_ORL,_ORS,_ORD, _,   _,   _,   _  ],
 [_ORD,_ORL,_ORS,_ORS,_ORS,_ORS,_ORS,_ORS,_ORL,_ORD, _,   _,   _,   _  ],
 [_ORD,_ORS,_ORD,_ORE,_ORS,_ORS,_ORE,_ORD,_ORS,_ORD, _,   _,   _,   _  ],
 [_,   _ORD,_ORS,_ORS,_ORD,_ORD,_ORS,_ORS,_ORD, _,   _,   _,   _,   _  ],
 [_,   _ORD,_ORT,_ORT,_ORS,_ORS,_ORT,_ORT,_ORD, _,   _,   _,   _,   _  ],
 [_,   _,   _ORD,_ORS,_ORS,_ORS,_ORS,_ORD, _,   _,   _,   _,   _,   _  ],
 [_OAD,_ORA,_OAL,_ORA,_ORA,_ORA,_ORA,_ORA,_ORA,_OAL,_ORA,_OAD, _,   _  ],
 [_ORA,_OAL,_ORA,_ORA,_ORA,_ORA,_ORA,_ORA,_ORA,_ORA,_OAL,_ORA, _,   _  ],
 [_ORS,_ORA,_OAD,_ORA,_OAL,_ORA,_ORA,_OAL,_ORA,_OAD,_ORA,_ORS, _,   _  ],
 [_ORS,_ORS,_OAD,_ORS,_ORS,_ORS,_ORS,_ORS,_OAD,_ORS,_ORS,_ORS, _,   _  ],
 [_ORS,_ORL,_ORS,_ORS,_ORS,_ORS,_ORS,_ORS,_ORS,_ORL,_ORS,_ORS, _,   _  ],
 [_,   _ORB,_ORB,_OAD,_ORB,_ORB,_ORB,_ORB,_OAD,_ORB,_ORB, _,   _,   _  ],
 [_,   _ORA,_OAD,_ORA,_ORA,_ORA,_ORA,_ORA,_ORA,_OAD,_ORA, _,   _,   _  ],
 [_,   _ORS,_ORA,_ORS,_ORS, _,   _,   _ORS,_ORS,_ORA,_ORS, _,   _,   _  ],
 [_,   _ORD,_ORS,_ORS,_ORS, _,   _,   _ORS,_ORS,_ORS,_ORD, _,   _,   _  ],
 [_,   _ORA,_OAD,_ORA,_ORA, _,   _,   _ORA,_ORA,_OAD,_ORA, _,   _,   _  ],
 [_,   _OAD,_ORA,_ORA,_ORA, _,   _,   _ORA,_ORA,_ORA,_OAD, _,   _,   _  ],
 [_OAL,_ORA,_ORA,_OAD,_ORA,_ORA, _,   _ORA,_ORA,_OAD,_ORA,_ORA,_OAL, _  ],
 [_OAD,_ORA,_OAD,_ORA,_ORA,_ORA, _,   _ORA,_ORA,_ORA,_OAD,_ORA,_OAD, _  ],
 [_OAD,_OAD,_ORA,_ORA,_ORA,_ORA, _,   _ORA,_ORA,_ORA,_ORA,_OAD,_OAD, _  ],
 [_OAL,_OAD,_OAD,_ORA,_ORA, _,   _,   _,   _ORA,_ORA,_OAD,_OAD,_OAL, _  ],
]

# ═══════════════════════════════════════════════════════════
# WITCH  12 × 18  — tall hat, glow eyes, flowing robe, staff
# ═══════════════════════════════════════════════════════════
_WHO = _c( 18, 12, 28)
_WHT = _c( 48, 28, 78)
_WHL = _c( 78, 48,118)
_WSK = _c(228,198,158)
_WSS = _c(188,158,118)
_WEY = _c(158,220, 55)
_WED = _c( 92,140, 30)
_WRO = _c(108, 40,150)
_WRL = _c(148, 72,195)
_WRD = _c( 65, 22, 95)
_WST = _c( 88, 70, 45)
_WOM = _c(225,185, 55)
_WOG = _c(255,225,105)

WITCH_PIXELS = [
 [_,   _,   _,   _WHT,_WHL,_WHT,_WHT, _,   _,   _,   _,   _  ],
 [_,   _,   _WHT,_WHL,_WHT,_WHT,_WHT,_WHT, _,   _,   _,   _  ],
 [_,   _WHT,_WHL,_WHT,_WHT,_WHT,_WHT,_WHT,_WHL,_WHT, _,   _  ],
 [_WHT,_WHT,_WHT,_WHT,_WHT,_WHT,_WHT,_WHT,_WHT,_WHT,_WHT, _  ],
 [_,   _,   _WSK,_WSK,_WSK,_WSK,_WSK,_WSK, _,   _,   _,   _  ],
 [_,   _,   _WSK,_WED,_WEY,_WSK,_WED,_WEY, _,   _,   _,   _  ],
 [_,   _,   _WSK,_WEY,_WED,_WSS,_WEY,_WED, _,   _,   _,   _  ],
 [_,   _,   _WSS,_WSK,_WSS,_WSK,_WSK,_WSS, _,   _,   _,   _  ],
 [_,   _WRD,_WRO,_WRO,_WRO,_WRO,_WRO,_WRD, _,   _,   _,   _  ],
 [_WRO,_WRL,_WRO,_WRO,_WRO,_WRO,_WRO,_WRL,_WSK,_WST, _,   _  ],
 [_WRD,_WRO,_WRL,_WRO,_WRO,_WRO,_WRL,_WRO,_WSK,_WST, _,   _  ],
 [_WRO,_WRD,_WRO,_WRO,_WRO,_WRO,_WRO,_WRD,_WST,_WOM, _,   _  ],
 [_WRD,_WRO,_WRO,_WRL,_WRO,_WRO,_WRL,_WRO,_WOG, _,   _,   _  ],
 [_WRO,_WRD,_WRO,_WRO,_WRO,_WRO,_WRO,_WRD, _,   _,   _,   _  ],
 [_WRD,_WRO,_WRL,_WRO,_WRO,_WRL,_WRO,_WRD, _,   _,   _,   _  ],
 [_,   _WRO,_WRO,_WRD, _,   _,   _WRD,_WRO, _,   _,   _,   _  ],
 [_,   _WRD,_WRO,_WRD, _,   _,   _WRD,_WRO, _,   _,   _,   _  ],
 [_,   _WHO,_WRD,_WHO, _,   _,   _WHO,_WRD, _,   _,   _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# SLIME KING  16 × 15  — huge body, crown, 3 eyes, boss
# ═══════════════════════════════════════════════════════════
_SKG = _c( 45,198, 72)
_SKL = _c( 98,235,118)
_SKD = _c( 22,132, 45)
_SKE = _c( 12, 18, 12)
_SKP = _c(205, 42, 42)
_CRW = _c(242,198, 35)
_CRL = _c(255,228, 92)
_CRD = _c(165,130, 18)
_CRJ = _c(215, 40, 40)
_CRB = _c( 40, 80,215)

SLIME_KING_PIXELS = [
 [_,   _CRW,_CRJ,_CRW,_CRD,_CRB,_CRW,_CRW,_CRB,_CRD,_CRW,_CRJ,_CRW, _,   _,   _  ],
 [_,   _CRL,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRL, _,   _,   _  ],
 [_,   _CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD, _,   _,   _  ],
 [_,   _,   _SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG, _,   _,   _,   _,   _  ],
 [_,   _SKG,_SKL,_SKL,_SKG,_SKG,_SKG,_SKG,_SKG,_SKL,_SKL,_SKG, _,   _,   _,   _  ],
 [_SKG,_SKG,_SKE,_SKE,_SKG,_SKG,_SKG,_SKG,_SKE,_SKE,_SKG,_SKG, _,   _,   _,   _  ],
 [_SKG,_SKG,_SKL,_SKE,_SKG,_SKG,_SKG,_SKG,_SKL,_SKE,_SKG,_SKG, _,   _,   _,   _  ],
 [_SKG,_SKG,_SKG,_SKG,_SKP,_SKP,_SKP,_SKP,_SKG,_SKG,_SKG,_SKG, _,   _,   _,   _  ],
 [_SKG,_SKD,_SKD,_SKD,_SKD,_SKD,_SKD,_SKD,_SKD,_SKD,_SKD,_SKG, _,   _,   _,   _  ],
 [_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG, _,   _,   _,   _  ],
 [_SKG,_SKL,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKL,_SKG, _,   _,   _,   _  ],
 [_,   _SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG,_SKG, _,   _,   _,   _,   _  ],
 [_,   _,   _SKG,_SKG,_SKD,_SKD,_SKD,_SKD,_SKG,_SKG, _,   _,   _,   _,   _,   _  ],
 [_,   _,   _,   _SKD,_SKD, _,   _,   _SKD,_SKD, _,   _,   _,   _,   _,   _,   _  ],
 [_,   _,   _,   _SKD, _,   _,   _,   _,   _SKD, _,   _,   _,   _,   _,   _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# GOBLIN CHIEF  14 × 24  — gold armor, crown, massive brawler
# ═══════════════════════════════════════════════════════════
_GCA = _c(195,158, 40)
_GAD = _c(145,108, 22)
_GAL = _c(228,198, 95)

GOBLIN_CHIEF_PIXELS = [
 [_,   _CRW,_CRJ,_CRW,_CRD,_CRB,_CRW,_CRW,_CRB,_CRD,_CRW,_CRJ,_CRW, _  ],
 [_,   _CRL,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRW,_CRL, _  ],
 [_,   _CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD,_CRD, _  ],
 [_,   _GOD,_GOD,_GOD,_GOD,_GOD,_GOD,_GOD,_GOD,_GOD, _,   _,   _,   _  ],
 [_GOD,_GOS,_GOL,_GOS,_GOS,_GOS,_GOS,_GOL,_GOS,_GOD, _,   _,   _,   _  ],
 [_GOD,_GOL,_GOS,_GOS,_GOS,_GOS,_GOS,_GOS,_GOL,_GOD, _,   _,   _,   _  ],
 [_GOD,_GOS,_GOE,_GOE,_GOS,_GOS,_GOE,_GOE,_GOS,_GOD, _,   _,   _,   _  ],
 [_,   _GOD,_GOS,_GOS,_GOD,_GOD,_GOS,_GOS,_GOD, _,   _,   _,   _,   _  ],
 [_,   _GOD,_GOS,_GOF,_GOS,_GOS,_GOF,_GOS,_GOD, _,   _,   _,   _,   _  ],
 [_,   _,   _GCA,_GAD,_GCA,_GCA,_GCA,_GCA,_GAD,_GCA, _,   _,   _,   _  ],
 [_GCA,_GAL,_GCA,_GCA,_GCA,_GCA,_GCA,_GCA,_GCA,_GAL,_GCA, _,   _,   _  ],
 [_GCA,_GCA,_GAD,_GCA,_GAL,_GCA,_GCA,_GAL,_GCA,_GAD,_GCA, _,   _,   _  ],
 [_GOS,_GCA,_GCA,_GAD,_GCA,_GCA,_GCA,_GCA,_GAD,_GCA,_GOS, _,   _,   _  ],
 [_GOS,_GOS,_GCA,_GCA,_GCA,_GCA,_GCA,_GCA,_GCA,_GOS,_GOS, _,   _,   _  ],
 [_,   _GAD,_GCA,_GAD,_GCA,_GCA,_GCA,_GCA,_GAD,_GCA,_GAD, _,   _,   _  ],
 [_,   _GCA,_GCA,_GAD, _,   _,   _,   _,   _GAD,_GCA,_GCA, _,   _,   _  ],
 [_,   _GOS,_GOD,_GCA, _,   _,   _,   _,   _GCA,_GOD,_GOS, _,   _,   _  ],
 [_,   _GOS,_GOS,_GAD, _,   _,   _,   _,   _GAD,_GOS,_GOS, _,   _,   _  ],
 [_,   _GOD,_GOS,_GOS, _,   _,   _,   _,   _GOS,_GOS,_GOD, _,   _,   _  ],
 [_GCA,_GCA,_GAD,_GCA,_GCA, _,   _,   _GCA,_GCA,_GAD,_GCA,_GCA, _,   _  ],
 [_GAD,_GCA,_GAL,_GCA,_GCA, _,   _,   _GCA,_GCA,_GAL,_GCA,_GAD, _,   _  ],
 [_GAD,_GAD,_GCA,_GCA, _,   _,   _,   _,   _GCA,_GCA,_GAD,_GAD, _,   _  ],
 [_GAL,_GAD,_GAD, _,   _,   _,   _,   _,   _,   _GAD,_GAD,_GAL, _,   _  ],
 [_,   _GAL,_GAD, _,   _,   _,   _,   _,   _,   _,   _GAD,_GAL, _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# DARK KNIGHT  14 × 26  — void armor, blood-red eye slit
# ═══════════════════════════════════════════════════════════
_DKA = _c( 22, 20, 28)
_DKM = _c( 42, 38, 52)
_DKL = _c( 75, 70, 90)
_DKR = _c(115, 20, 20)
_DKS = _c( 88, 85, 98)
_DRE = _c(228, 32, 32)
_DRG = _c(255, 88, 60)

DARK_KNIGHT_PIXELS = [
 [_,   _,   _DKA,_DKA,_DKA,_DKA,_DKA,_DKA,_DKA, _,   _,   _,   _,   _  ],
 [_,   _DKA,_DKM,_DKM,_DKM,_DKM,_DKM,_DKM,_DKM,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKS,_DKS,_DKS,_DKS,_DKS,_DKS,_DKS,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKS,_DRE,_DRE,_DRG,_DRG,_DRE,_DRE,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKS,_DKS,_DKS,_DKS,_DKS,_DKS,_DKS,_DKA, _,   _,   _,   _  ],
 [_,   _,   _DKA,_DKM,_DKM,_DKM,_DKM,_DKM,_DKA, _,   _,   _,   _,   _  ],
 [_DKL,_DKA,_DKM,_DKA,_DKA,_DKA,_DKA,_DKA,_DKM,_DKA,_DKL, _,   _,   _  ],
 [_DKA,_DKL,_DKA,_DKA,_DKA,_DKA,_DKA,_DKA,_DKA,_DKL,_DKA, _,   _,   _  ],
 [_,   _DKA,_DKR,_DKM,_DKM,_DKM,_DKM,_DKM,_DKR,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKR,_DKM,_DKS,_DKM,_DKM,_DKS,_DKR,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKR,_DKM,_DKM,_DKM,_DKM,_DKM,_DKR,_DKA, _,   _,   _,   _  ],
 [_DKA,_DKR,_DKR,_DKA,_DKM,_DKM,_DKM,_DKA,_DKR,_DKR,_DKA, _,   _,   _  ],
 [_,   _DKA,_DKM,_DKA,_DKM,_DKM,_DKM,_DKA,_DKM,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKM,_DKM,_DKM,_DKM,_DKM,_DKM,_DKM,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKA,_DKM,_DKM,_DKM,_DKM,_DKM,_DKA,_DKA, _,   _,   _,   _  ],
 [_,   _,   _DKA,_DKR,_DKM,_DKM,_DKM,_DKR,_DKA, _,   _,   _,   _,   _  ],
 [_,   _DKA,_DKM,_DKA, _,   _,   _,   _DKA,_DKM,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKR,_DKA, _,   _,   _,   _DKA,_DKR,_DKA, _,   _,   _,   _  ],
 [_,   _DKA,_DKM,_DKA, _,   _,   _,   _DKA,_DKM,_DKA, _,   _,   _,   _  ],
 [_DKL,_DKA,_DKM,_DKM,_DKA, _,   _,   _DKA,_DKM,_DKM,_DKA,_DKL, _,   _  ],
 [_DKA,_DKL,_DKA,_DKM,_DKA, _,   _,   _DKA,_DKM,_DKA,_DKL,_DKA, _,   _  ],
 [_DKA,_DKA,_DKL,_DKM,_DKA, _,   _,   _DKA,_DKM,_DKL,_DKA,_DKA, _,   _  ],
 [_DKA,_DKA,_DKA,_DKM,_DKM, _,   _,   _DKM,_DKM,_DKA,_DKA,_DKA, _,   _  ],
 [_DKL,_DKA,_DKA,_DKA, _,   _,   _,   _,   _DKA,_DKA,_DKA,_DKL, _,   _  ],
 [_DKL,_DKL,_DKA, _,   _,   _,   _,   _,   _,   _DKA,_DKL,_DKL, _,   _  ],
 [_,   _DKL,_DKL, _,   _,   _,   _,   _,   _,   _,   _DKL,_DKL, _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# ANCIENT GOLEM  16 × 26  — cracked stone, lava veins, runes
# ═══════════════════════════════════════════════════════════
_AGS = _c(105,100, 90)
_AGL = _c(148,142,128)
_AGD = _c( 62, 58, 50)
_AGC = _c( 38, 34, 28)
_AGO = _c(222,128, 28)
_AGR = _c(255,180, 55)
_AGN = _c(195,165, 45)

ANCIENT_GOLEM_PIXELS = [
 [_,   _AGD,_AGD,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGD,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGL,_AGL,_AGS,_AGS,_AGS,_AGS,_AGL,_AGL,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGS,_AGO,_AGR,_AGS,_AGS,_AGR,_AGO,_AGS,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGC,_AGC,_AGS,_AGS,_AGS,_AGS,_AGC,_AGC,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGL,_AGS,_AGN,_AGN,_AGS,_AGS,_AGN,_AGN,_AGS,_AGL,_AGD, _,   _,   _,   _  ],
 [_,   _AGD,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGD, _,   _,   _,   _,   _  ],
 [_AGC,_AGS,_AGD,_AGD,_AGD,_AGD,_AGD,_AGD,_AGD,_AGD,_AGS,_AGC, _,   _,   _,   _  ],
 [_AGS,_AGL,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGL,_AGS, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGS,_AGO,_AGS,_AGN,_AGN,_AGS,_AGO,_AGS,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGL,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGL,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGS,_AGS,_AGC,_AGS,_AGS,_AGC,_AGS,_AGS,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGC,_AGS,_AGD,_AGD,_AGS,_AGS,_AGS,_AGS,_AGD,_AGD,_AGS,_AGC, _,   _,   _,   _  ],
 [_,   _AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS, _,   _,   _,   _,   _  ],
 [_,   _AGL,_AGS,_AGN,_AGO,_AGS,_AGS,_AGO,_AGN,_AGS,_AGL, _,   _,   _,   _,   _  ],
 [_,   _AGD,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGD, _,   _,   _,   _,   _  ],
 [_AGD,_AGS,_AGD, _,   _,   _AGS,_AGS, _,   _,   _AGD,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGS,_AGL,_AGS, _,   _,   _AGS,_AGS, _,   _,   _AGS,_AGL,_AGS, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGC, _,   _,   _AGS,_AGS, _,   _,   _AGC,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGC,_AGS,_AGS, _,   _,   _AGS,_AGS, _,   _,   _AGS,_AGS,_AGC, _,   _,   _,   _  ],
 [_AGD,_AGS,_AGO, _,   _,   _AGS,_AGS, _,   _,   _AGO,_AGS,_AGD, _,   _,   _,   _  ],
 [_AGD,_AGL,_AGS,_AGD, _,   _AGS,_AGS, _,   _AGD,_AGS,_AGL,_AGD, _,   _,   _,   _  ],
 [_AGC,_AGS,_AGD,_AGS, _,   _AGS,_AGS, _,   _AGS,_AGD,_AGS,_AGC, _,   _,   _,   _  ],
 [_AGD,_AGD,_AGS,_AGS,_AGD,_AGS,_AGS,_AGD,_AGS,_AGS,_AGD,_AGD, _,   _,   _,   _  ],
 [_AGL,_AGD,_AGD,_AGS,_AGS,_AGS,_AGS,_AGS,_AGS,_AGD,_AGD,_AGL, _,   _,   _,   _  ],
 [_,   _AGL,_AGD,_AGD,_AGS, _,   _,   _AGS,_AGD,_AGD,_AGL, _,   _,   _,   _,   _  ],
 [_,   _,   _AGL,_AGD,_AGD, _,   _,   _AGD,_AGD,_AGL, _,   _,   _,   _,   _,   _  ],
]

# ═══════════════════════════════════════════════════════════
# Slime A / B  (kept for compatibility)
# ═══════════════════════════════════════════════════════════
_SG = _c(62, 195, 78); _SL = _c(125,232,128); _SD = _c(32,120,48); _SE = _c(12,18,12)
SLIME_A_PIXELS = [
 [_,  _,  _SG,_SG,_SG,_SG, _,  _ ],
 [_,  _SG,_SL,_SG,_SG,_SL,_SG, _ ],
 [_SG,_SG,_SE,_SG,_SG,_SE,_SG,_SG],
 [_SG,_SG,_SG,_SG,_SG,_SG,_SG,_SG],
 [_SG,_SL,_SG,_SG,_SG,_SG,_SL,_SG],
 [_,  _SG,_SG,_SD,_SD,_SG,_SG, _ ],
 [_,  _,  _SG,_SG,_SG,_SG, _,  _ ],
]

_TB = _c(58,95,215); _TL = _c(110,148,245); _TD = _c(28,45,140); _TY = _c(240,225,55)
SLIME_B_PIXELS = [
 [_,  _,  _TB,_TB,_TB,_TB, _,  _ ],
 [_,  _TB,_TL,_TB,_TB,_TL,_TB, _ ],
 [_TB,_TB,_TY,_TB,_TB,_TY,_TB,_TB],
 [_TB,_TB,_TB,_TB,_TB,_TB,_TB,_TB],
 [_TB,_TL,_TB,_TB,_TB,_TB,_TL,_TB],
 [_,  _TB,_TB,_TD,_TD,_TB,_TB, _ ],
 [_,  _,  _TB,_TB,_TB,_TB, _,  _ ],
]

# ═══════════════════════════════════════════════════════════
# Texture builder
# ═══════════════════════════════════════════════════════════

def _build_texture(pixels: list[list[tuple]], scale: int = 5) -> Texture:
    rows = len(pixels)
    cols = max(len(r) for r in pixels)
    img = PNMImage(cols * scale, rows * scale)
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
                    img.setXel(col_i*scale+dx, row_i*scale+dy, r/255.0, g/255.0, b/255.0)
                    img.setAlpha(col_i*scale+dx, row_i*scale+dy, a/255.0)
    tex = Texture()
    tex.load(img)
    tex.setMagfilter(Texture.FTNearest)
    tex.setMinfilter(Texture.FTNearest)
    return tex


_TEX_CACHE: dict[str, Texture] = {}

_CHAR_DIMS: dict[str, tuple[float, float]] = {
    "hero":          (1.40, 2.40),
    "blob_small":    (0.85, 0.72),
    "bat":           (1.55, 0.72),
    "mushroom":      (1.10, 1.42),
    "goblin":        (1.10, 1.95),
    "orc":           (1.25, 2.18),
    "witch":         (1.05, 1.82),
    "slime_a":       (1.05, 1.12),
    "slime_b":       (1.05, 1.12),
    "slime_king":    (1.40, 1.52),
    "goblin_chief":  (1.20, 2.42),
    "dark_knight":   (1.20, 2.62),
    "ancient_golem": (1.38, 2.65),
}

_CHAR_PIXELS: dict[str, list] = {
    "hero":          HERO_PIXELS,
    "blob_small":    BLOB_SMALL_PIXELS,
    "bat":           BAT_PIXELS,
    "mushroom":      MUSHROOM_PIXELS,
    "goblin":        GOBLIN_PIXELS,
    "orc":           ORC_PIXELS,
    "witch":         WITCH_PIXELS,
    "slime_a":       SLIME_A_PIXELS,
    "slime_b":       SLIME_B_PIXELS,
    "slime_king":    SLIME_KING_PIXELS,
    "goblin_chief":  GOBLIN_CHIEF_PIXELS,
    "dark_knight":   DARK_KNIGHT_PIXELS,
    "ancient_golem": ANCIENT_GOLEM_PIXELS,
}


def make_char_sprite(parent, unit_id: str) -> tuple[float, float]:
    """Attach an anime pixel-art billboard sprite to parent.
    Returns (width, height) in game units."""
    base_id = unit_id
    if "_" in unit_id:
        parts = unit_id.rsplit("_", 1)
        if parts[-1].isdigit():
            base_id = parts[0]

    key = base_id if base_id in _CHAR_PIXELS else "slime_a"
    pixels = _CHAR_PIXELS[key]
    w, h = _CHAR_DIMS.get(key, (1.0, 1.2))

    if key not in _TEX_CACHE:
        _TEX_CACHE[key] = _build_texture(pixels, scale=5)

    tex = _TEX_CACHE[key]
    cm = CardMaker("sprite")
    cm.setFrame(-w / 2, w / 2, 0.0, h)
    card = parent.attachNewNode(cm.generate())
    card.setTexture(tex)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setBillboardPointEye()
    return w, h
