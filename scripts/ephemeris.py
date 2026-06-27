"""Internal ephemeris adapter backed by astronomy-engine."""

from __future__ import annotations

import math

import astronomy as A


FLG = 0
J2000 = 2451545.0
DELTA_DAYS = 0.5

_BODIES = {
    "太陽": A.Body.Sun,
    "水星": A.Body.Mercury,
    "金星": A.Body.Venus,
    "火星": A.Body.Mars,
    "木星": A.Body.Jupiter,
    "土星": A.Body.Saturn,
    "天王星": A.Body.Uranus,
    "海王星": A.Body.Neptune,
    "冥王星": A.Body.Pluto,
    "☉": A.Body.Sun,
    "☿": A.Body.Mercury,
    "♀": A.Body.Venus,
    "♂": A.Body.Mars,
    "♃": A.Body.Jupiter,
    "♄": A.Body.Saturn,
    "♅": A.Body.Uranus,
    "♆": A.Body.Neptune,
    "♇": A.Body.Pluto,
}


def julday(y, mo, d, hour):
    if mo <= 2:
        y -= 1
        mo += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    return (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (mo + 1))
        + d
        + b
        - 1524.5
        + hour / 24
    )


def revjul(jd):
    z = math.floor(jd + 0.5)
    f = jd + 0.5 - z
    alpha = math.floor((z - 1867216.25) / 36524.25)
    a = z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    dd = math.floor(365.25 * c)
    e = math.floor((b - dd) / 30.6001)
    day = b - dd - math.floor(30.6001 * e) + f
    mo = e - 1 if e < 14 else e - 13
    y = c - 4716 if mo > 2 else c - 4715
    whole_day = math.floor(day)
    return int(y), int(mo), int(whole_day), (day - whole_day) * 24


def body_lon_speed(jd, body_key):
    lon = _lon(jd, body_key)
    before = _lon(jd - DELTA_DAYS, body_key)
    after = _lon(jd + DELTA_DAYS, body_key)
    return lon, _signed_delta(after, before) / (2 * DELTA_DAYS)


def houses_asc_mc(jd, lat, lon):
    time = _time(jd)
    eps = _true_obliquity_rad(time)
    ramc = math.radians((A.SiderealTime(time) * 15 + lon) % 360)
    phi = math.radians(lat)

    mc = _lon_from_ra(ramc, eps)
    asc = (
        math.degrees(
            math.atan2(
                -math.cos(ramc),
                math.sin(eps) * math.tan(phi) + math.cos(eps) * math.sin(ramc),
            )
        )
        + 180
    ) % 360

    cusp11 = _placidus_cusp(ramc, phi, eps, 1 / 3)
    cusp12 = _placidus_cusp(ramc, phi, eps, 2 / 3)
    cusp9 = _placidus_cusp(ramc, phi, eps, -1 / 3)
    cusp8 = _placidus_cusp(ramc, phi, eps, -2 / 3)

    cusps = [0.0] * 12
    cusps[0] = asc
    cusps[1] = (cusp8 + 180) % 360
    cusps[2] = (cusp9 + 180) % 360
    cusps[3] = (mc + 180) % 360
    cusps[4] = (cusp11 + 180) % 360
    cusps[5] = (cusp12 + 180) % 360
    cusps[6] = (asc + 180) % 360
    cusps[7] = cusp8
    cusps[8] = cusp9
    cusps[9] = mc
    cusps[10] = cusp11
    cusps[11] = cusp12
    return cusps, asc, mc


def _time(jd):
    return A.Time(jd - J2000)


def _true_obliquity_rad(time):
    rot = A.Rotation_EQD_ECT(time).rot
    return math.atan2(rot[2][1], rot[1][1])


def _lon_from_ra(ra, eps):
    return math.degrees(math.atan2(math.sin(ra), math.cos(ra) * math.cos(eps))) % 360


def _placidus_cusp(ramc, phi, eps, k):
    ra = (ramc + k * math.pi / 2) % (2 * math.pi)
    tan_phi = math.tan(phi)
    tan_eps = math.tan(eps)
    for _ in range(100):
        arg = -math.sin(ra) * tan_phi * tan_eps
        if abs(arg) > 1:
            raise ValueError("placidus undefined at high latitude")
        nxt = (ramc + k * math.acos(arg)) % (2 * math.pi)
        if abs(_signed_rad_delta(nxt, ra)) < 1e-8:
            return _lon_from_ra(nxt, eps)
        ra = nxt
    raise ValueError("placidus cusp iteration did not converge")


def _signed_rad_delta(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def _lon(jd, body_key):
    time = _time(jd)
    if body_key in ("月亮", "☾"):
        return A.EclipticGeoMoon(time).lon % 360
    if body_key in ("北交點", "☊"):
        return _true_node_lon(time)
    vector = A.GeoVector(_BODIES[body_key], time, aberration=True)
    return A.Ecliptic(vector).elon % 360


def _true_node_lon(time):
    state = A.GeoMoonState(time)
    rot = A.Rotation_EQJ_ECT(time)
    r = A.RotateVector(rot, A.Vector(state.x, state.y, state.z, time))
    v = A.RotateVector(rot, A.Vector(state.vx, state.vy, state.vz, time))
    hx = r.y * v.z - r.z * v.y
    hy = r.z * v.x - r.x * v.z
    return math.degrees(math.atan2(hx, -hy)) % 360


def _signed_delta(a, b):
    diff = (a - b + 180) % 360 - 180
    return diff + 360 if diff <= -180 else diff
