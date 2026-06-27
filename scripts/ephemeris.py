"""Internal ephemeris adapter.

This module is intentionally backed only by pyswisseph for now.
"""

import swisseph as swe

FLG = swe.FLG_MOSEPH | swe.FLG_SPEED

_BODIES = {
    "太陽": swe.SUN,
    "月亮": swe.MOON,
    "水星": swe.MERCURY,
    "金星": swe.VENUS,
    "火星": swe.MARS,
    "木星": swe.JUPITER,
    "土星": swe.SATURN,
    "天王星": swe.URANUS,
    "海王星": swe.NEPTUNE,
    "冥王星": swe.PLUTO,
    "北交點": swe.TRUE_NODE,
    "☉": swe.SUN,
    "☾": swe.MOON,
    "☿": swe.MERCURY,
    "♀": swe.VENUS,
    "♂": swe.MARS,
    "♃": swe.JUPITER,
    "♄": swe.SATURN,
    "♅": swe.URANUS,
    "♆": swe.NEPTUNE,
    "♇": swe.PLUTO,
    "☊": swe.TRUE_NODE,
}


def julday(y, mo, d, hour):
    return swe.julday(y, mo, d, hour, swe.GREG_CAL)


def revjul(jd):
    return swe.revjul(jd)


def body_lon_speed(jd, body_key):
    values = swe.calc_ut(jd, _BODIES[body_key], FLG)[0]
    return values[0], values[3]


def houses_asc_mc(jd, lat, lon):
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", FLG)
    return cusps, ascmc[0], ascmc[1]
