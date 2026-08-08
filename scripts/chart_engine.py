#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三系統完整盤面引擎 v1
西洋星盤(astronomy-engine) + 人類圖 + 紫微斗數(iztro)
改 INPUT 區塊即可為任何人計算。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from . import ephemeris as eph
    from .validation import validate_input
except ImportError:
    import ephemeris as eph
    from validation import validate_input

# ====================== INPUT（改這裡即可） ======================
INPUT = {
    "name":      "範例",
    "gender":    "女",          # '男' / '女'（紫微用）
    "date":      (2000, 1, 1),  # 西曆 年,月,日
    "time":      (12, 0),       # 24h 時,分（本地時鐘時間）
    "tz_offset": 8.0,           # 出生地當時 UTC 時差（含夏令時！台灣1980後=+8）
    "lat":       25.0330,       # Taipei 101 (public landmark)
    "lon":       121.5654,
    "target":    "2025-01-01",
    "ziwei_day_divide": "forward",  # 晚子時: forward=算次日, current=算當日
}
# ===============================================================

FLG = eph.FLG
SIGNS = ['牡羊','金牛','雙子','巨蟹','獅子','處女','天秤','天蠍','射手','摩羯','水瓶','雙魚']

def fmt(lon):
    lon %= 360; s = int(lon//30); d = lon-s*30; dd=int(d); mm=int(round((d-dd)*60))
    if mm==60: mm=0; dd+=1
    return f"{SIGNS[s]} {dd:02d}\u00b0{mm:02d}'"

def _pos_obj(lon):
    lon %= 360; s = int(lon//30); d = lon-s*30; dd=int(d); mm=int(round((d-dd)*60))
    if mm==60: mm=0; dd+=1
    return dict(lon=round(lon,4), sign=SIGNS[s], deg=dd, min=mm, label=fmt(lon))

def _safe(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)): return obj
    if isinstance(obj, (list, tuple, set)): return [_safe(x) for x in obj]
    if isinstance(obj, dict): return {str(k): _safe(v) for k,v in obj.items()}
    if hasattr(obj, 'model_dump'):
        try: return _safe(obj.model_dump())
        except Exception: pass
    if hasattr(obj, '__dict__'):
        try: return _safe(obj.__dict__)
        except Exception: pass
    return str(obj)

def jd_of(date, time, tz):
    y,mo,d = date; h,mi = time
    return eph.julday(y,mo,d, h+mi/60 - tz)

# ---------- 西洋星盤 ----------
def western(inp):
    jd = jd_of(inp["date"], inp["time"], inp["tz_offset"])
    P = ['太陽','月亮','水星','金星','火星','木星','土星','天王星','海王星','冥王星','北交點']
    pos={}; retro={}
    for n in P:
        pos[n],speed=eph.body_lon_speed(jd,n); retro[n]=speed<0
    pos['南交點']=(pos['北交點']+180)%360; retro['南交點']=False
    cusps,asc,mc = eph.houses_asc_mc(jd, inp["lat"], inp["lon"])
    def house_of(lon):
        lon%=360
        for i in range(12):
            a=cusps[i]; b=cusps[(i+1)%12]
            if a<b:
                if a<=lon<b: return i+1
            else:
                if lon>=a or lon<b: return i+1
        return 12
    return jd,pos,retro,cusps,asc,mc,house_of

def aspects(pos, asc, mc):
    pts=dict(pos); pts['上升']=asc; pts['天頂']=mc
    A={0:('合相',8),60:('六分',5),90:('四分',7),120:('三分',7),180:('對分',8)}
    out=[]; keys=list(pts)
    for i in range(len(keys)):
        for j in range(i+1,len(keys)):
            a,b=keys[i],keys[j]; d=abs(pts[a]-pts[b])%360; d=min(d,360-d)
            for ang,(nm,orb) in A.items():
                if abs(d-ang)<=orb: out.append((a,b,nm,abs(d-ang)))
    return sorted(out,key=lambda x:x[3])

# ---------- 人類圖 ----------
SEQ=[25,17,21,51,42,3,27,24,2,23,8,20,16,35,45,12,15,52,39,53,62,56,31,33,7,4,29,59,40,64,
     47,6,46,18,48,57,32,50,28,44,1,43,14,34,9,5,26,11,10,58,38,54,61,60,41,19,13,49,30,55,37,63,22,36]
OFFSET=-1.375
GATE_CENTER={ # 閘門->中心
 64:'頭',61:'頭',63:'頭', 47:'邏輯',24:'邏輯',4:'邏輯',17:'邏輯',43:'邏輯',11:'邏輯',
 62:'喉',23:'喉',56:'喉',35:'喉',12:'喉',45:'喉',33:'喉',8:'喉',31:'喉',20:'喉',16:'喉',
 7:'G',1:'G',13:'G',25:'G',46:'G',2:'G',15:'G',10:'G',
 21:'意志',40:'意志',26:'意志',51:'意志',
 6:'情緒',37:'情緒',22:'情緒',36:'情緒',30:'情緒',55:'情緒',49:'情緒',19:'情緒',
 34:'薦骨',5:'薦骨',14:'薦骨',29:'薦骨',59:'薦骨',9:'薦骨',3:'薦骨',42:'薦骨',27:'薦骨',
 48:'脾',57:'脾',44:'脾',50:'脾',32:'脾',28:'脾',18:'脾',
 53:'根',60:'根',52:'根',39:'根',41:'根',58:'根',38:'根',54:'根'}
CHANNELS={(1,8),(2,14),(3,60),(4,63),(5,15),(6,59),(7,31),(9,52),(10,20),(10,34),(10,57),
 (11,56),(12,22),(13,33),(16,48),(17,62),(18,58),(19,49),(20,34),(20,57),(21,45),(23,43),
 (24,61),(25,51),(26,44),(27,50),(28,38),(29,46),(30,41),(32,54),(34,57),(35,36),(37,40),
 (39,55),(42,53),(47,64)}
MOTORS={'薦骨','情緒','意志','根'}

def gate_line(lon):
    w=(lon-OFFSET)%360; idx=int(w//5.625); g=SEQ[idx]
    line=int((w-idx*5.625)//0.9375)+1
    return g,line

def human_design(inp, sun_lon):
    jd_b = jd_of(inp["date"], inp["time"], inp["tz_offset"])
    # design = Sun 88° earlier
    target=(sun_lon-88)%360; lo,hi=jd_b-100,jd_b-80
    for _ in range(60):
        mid=(lo+hi)/2; s=eph.body_lon_speed(mid,'太陽')[0]
        diff=(s-target+180)%360-180
        if diff<0: lo=mid
        else: hi=mid
    jd_d=(lo+hi)/2
    dY,dM,dD,_=eph.revjul(jd_d+inp["tz_offset"]/24)
    B=['☉','☾','☿','♀','♂','♃','♄','♅','♆','♇','☊']
    def acts(jd):
        o={}
        for n in B: o[n]=eph.body_lon_speed(jd,n)[0]
        o['⊕']=(o['☉']+180)%360; o['☋']=(o['☊']+180)%360
        return o
    Pp=acts(jd_b); Dd=acts(jd_d)
    order=['☉','⊕','☊','☋','☾','☿','♀','♂','♃','♄','♅','♆','♇']
    rows=[]; gates=set()
    for n in order:
        gp,lp=gate_line(Pp[n]); gd,ld=gate_line(Dd[n])
        rows.append((n,gp,lp,gd,ld)); gates.add(gp); gates.add(gd)
    # channels & centers
    chans=[]; defined=set()
    for a,b in CHANNELS:
        if a in gates and b in gates:
            chans.append((a,b)); defined.add(GATE_CENTER[a]); defined.add(GATE_CENTER[b])
    # connectivity graph among defined centers
    adj={c:set() for c in defined}
    for a,b in chans:
        c1,c2=GATE_CENTER[a],GATE_CENTER[b]
        if c1!=c2: adj[c1].add(c2); adj[c2].add(c1)
    # components
    seen=set(); comps=0
    for c in defined:
        if c not in seen:
            comps+=1; stack=[c]
            while stack:
                x=stack.pop(); seen.add(x); stack+=[y for y in adj[x] if y not in seen]
    defn={0:'無定義',1:'一分人(單一定義)',2:'二分人',3:'三分人',4:'四分人'}.get(comps,f'{comps}組')
    # motor to throat?
    def reach(start,goal):
        if start not in defined or goal not in defined: return False
        st=[start]; vis=set()
        while st:
            x=st.pop()
            if x==goal: return True
            vis.add(x); st+=[y for y in adj[x] if y not in vis]
        return False
    m2t = any(reach(m,'喉') for m in MOTORS if m in defined)
    sacral = '薦骨' in defined
    if not defined: htype='反映者'
    elif sacral and m2t: htype='顯示生產者'
    elif sacral: htype='生產者'
    elif m2t: htype='顯示者'
    else: htype='投射者'
    if '情緒' in defined: auth='情緒型權威'
    elif sacral: auth='薦骨型權威'
    elif '脾' in defined: auth='直覺型(脾)權威'
    elif '意志' in defined: auth='意志力(心)權威'
    elif 'G' in defined: auth='自我投射型權威'
    else: auth='無內在權威(心智投射/月亮)'
    prof=f"{rows[0][2]}/{rows[0][4]}"
    RIGHT={(1,3),(1,4),(2,4),(2,5),(3,5),(3,6),(4,6)}; LEFT={(5,1),(5,2),(6,2),(6,3)}; JUX={(4,1)}
    pr=(rows[0][2],rows[0][4])
    angle='右角度交叉' if pr in RIGHT else ('左角度交叉' if pr in LEFT else ('並列交叉' if pr in JUX else '?'))
    cross=f"{angle}（{rows[0][1]}/{rows[1][1]} | {[r for r in rows if r[0]=='☉'][0][3]}/{rows[1][3]}）"
    allc=set(GATE_CENTER.values())
    return dict(design=(int(dY),int(dM),int(dD)),rows=rows,chans=sorted(chans),
                defined=sorted(defined),open=sorted(allc-defined),htype=htype,auth=auth,
                profile=prof,definition=defn,cross=cross)

# ---------- 紫微斗數 ----------
def ziwei(inp):
    # 時辰 index: 子0,丑1,寅2,卯3,辰4,巳5,午6,未7,申8,酉9,戌10,亥11,晚子12
    h=inp["time"][0]
    ti = ((h+1)//2)%12 if h!=23 else 12
    # 早子(0-1)算0; 23點為晚子12
    day_divide = inp.get("ziwei_day_divide", "forward")
    if day_divide not in {"forward", "current"}:
        raise ValueError("ziwei_day_divide must be forward or current")
    ds=f'{inp["date"][0]}-{inp["date"][1]}-{inp["date"][2]}'
    req=dict(date=ds,timeIndex=ti,gender=inp["gender"],fixLeap=True,language='zh-TW',
             target=inp["target"],dayDivide=day_divide)
    sidecar=Path(__file__).resolve().with_name("ziwei_iztro.cjs")
    # Node ≥ 18 is the supported/tested runtime; any sidecar failure converges
    # to one loud error path (no partial chart on any surface).
    NODE_HINT = "this engine requires Node.js >= 18 on PATH for 紫微斗數"
    try:
        timeout_s = float(os.environ.get("LIFE_ZIWEI_TIMEOUT", "15"))
    except ValueError:
        timeout_s = 15.0  # invalid override: fall back rather than crash
    try:
        proc=subprocess.run(["node", str(sidecar)], input=json.dumps(req, ensure_ascii=False),
                            capture_output=True, text=True, encoding="utf-8", timeout=timeout_s)
    except OSError as exc:  # FileNotFoundError, PermissionError, exec-format errors …
        raise RuntimeError(f"紫微斗數 sidecar failed to launch node ({exc}) — {NODE_HINT}") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"紫微斗數 sidecar timed out after {timeout_s:g}s — {NODE_HINT}") from None
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "ziwei iztro sidecar failed"
        raise RuntimeError(f"{detail} — {NODE_HINT}")
    r=json.loads(proc.stdout)
    palaces=[]
    def star_str(lst):
        o=[]
        for s in (lst or []):
            m=s.get('mutagen') or None; br=s.get('brightness','') or ''
            name=s['name']
            o.append(f"{name}({br}){'['+m+']' if m else ''}" if br else f"{name}{'['+m+']' if m else ''}")
        return o
    for p in r["palaces"]:
        flag=('命' if p['isOriginalPalace'] else '')+('身' if p['isBodyPalace'] else '')
        decadal_range=p['decadal']['range']
        palaces.append(dict(name=p['name'],gz=f"{p['heavenlyStem']}{p['earthlyBranch']}",flag=flag,
            major=star_str(p['majorStars']),minor=star_str(p['minorStars']),
            adj=[s['name'] for s in (p['adjectiveStars'] or [])],
            decadal=f"{decadal_range[0]}-{decadal_range[1]}"))
    h2=r.get("horoscope") or {}
    return dict(five=r["fiveElementsClass"],soul=r["soul"],body=r["body"],palaces=palaces,
                dec=h2.get("decadal"),yr=h2.get("yearly"),age=h2.get("age"),ti=ti)

# ====================== 執行與輸出 ======================
def run(inp):
    print(f"### {inp['name']}｜{inp['gender']}｜{inp['date'][0]}-{inp['date'][1]:02d}-{inp['date'][2]:02d} "
          f"{inp['time'][0]:02d}:{inp['time'][1]:02d} (UTC+{inp['tz_offset']:g})\n")
    jd,pos,retro,cusps,asc,mc,house_of = western(inp)
    print("【西洋星盤 Tropical/Placidus】")
    print(f"上升 {fmt(asc)} ｜ 天頂 {fmt(mc)}")
    for n in ['太陽','月亮','水星','金星','火星','木星','土星','天王星','海王星','冥王星','北交點','南交點']:
        print(f"  {n:4s} {fmt(pos[n])}{' ℞' if retro[n] else ''}  {house_of(pos[n])}宮")
    print("  宮頭:", " ".join(f"{i+1}={fmt(cusps[i])}" for i in range(12)))
    asp=aspects(pos,asc,mc)
    print("  主要相位:", "；".join(f"{a}-{b}{nm}({d:.1f}\u00b0)" for a,b,nm,d in asp[:10]))

    print("\n【人類圖 Human Design】")
    hd=human_design(inp,pos['太陽'])
    print(f"類型 {hd['htype']} ｜ 權威 {hd['auth']} ｜ 角色 {hd['profile']} ｜ 定義 {hd['definition']}")
    print(f"輪迴交叉 {hd['cross']}")
    print(f"定義中心 {','.join(hd['defined'])} ｜ 開放中心 {','.join(hd['open'])}")
    print(f"設計日期 {hd['design'][0]}-{hd['design'][1]:02d}-{hd['design'][2]:02d}")
    print(f"通道 {['-'.join(map(str,c)) for c in hd['chans']]}")
    print("  26閘門(體|個性|設計):")
    for n,gp,lp,gd,ld in hd['rows']:
        print(f"    {n}  {gp}.{lp}  |  {gd}.{ld}")

    print("\n【紫微斗數 iztro】")
    zw=ziwei(inp)
    print(f"五行局 {zw['five']} ｜ 命主 {zw['soul']} ｜ 身主 {zw['body']}")
    for p in zw['palaces']:
        stars=" ".join(p['major']) if p['major'] else "空宮"
        extra=("｜"+" ".join(p['minor']+p['adj'])) if (p['minor'] or p['adj']) else ""
        print(f"  {p['name']:4s} {p['gz']}{p['flag']:2s}({p['decadal']}): {stars}{extra}")
    def _sihua(sec):
        return " ".join(f"{m['star']}化{m['type']}" for m in (sec.get('mutagenTyped') or []))
    if zw.get('dec'):
        d=zw['dec']; ar=d.get('ageRange')
        span=f"（{ar[0]}-{ar[1]}歲）" if ar else ""
        print(f"  ── 大限 {d.get('heavenlyStem','')}{d.get('earthlyBranch','')}{span} 四化：{_sihua(d)}")
    if zw.get('yr'):
        y=zw['yr']
        print(f"  ── 流年 {y.get('heavenlyStem','')}{y.get('earthlyBranch','')}（{inp['target']}）四化：{_sihua(y)}")


def compose_markdown(inp):
    from contextlib import redirect_stdout
    from io import StringIO

    buffer = StringIO()
    with redirect_stdout(buffer):
        run(inp)
    return buffer.getvalue()


def build_json(inp):
    jd,pos,retro,cusps,asc,mc,house_of = western(inp)
    asp=aspects(pos,asc,mc)
    hd=human_design(inp,pos['太陽'])
    zw=ziwei(inp)
    order=['太陽','月亮','水星','金星','火星','木星','土星','天王星','海王星','冥王星','北交點','南交點']
    # all-or-nothing: horoscope construction failure fails the whole request
    # loudly (--json envelope / HTTP 500) — never an "ok": true partial result.
    horoscope=dict(decadal=_safe(zw['dec']), yearly=_safe(zw['yr']), age=_safe(zw['age']))
    return {
        "ok": True,
        "schema_version": "1.2",
        "input": {
            "name": inp["name"],
            "gender": inp["gender"],
            "date": f"{inp['date'][0]:04d}-{inp['date'][1]:02d}-{inp['date'][2]:02d}",
            "time": f"{inp['time'][0]:02d}:{inp['time'][1]:02d}",
            "tz_offset": inp["tz_offset"],
            "lat": inp["lat"],
            "lon": inp["lon"],
            "target": inp["target"],
        },
        "western": {
            "system": "Tropical / Placidus / astronomy-engine",
            "ascendant": _pos_obj(asc),
            "midheaven": _pos_obj(mc),
            "planets": [
                dict(name=n, retrograde=retro[n], house=house_of(pos[n]), **_pos_obj(pos[n]))
                for n in order
            ],
            "houses": [
                {"house": i+1, "lon": round(cusps[i]%360,4), "label": fmt(cusps[i])}
                for i in range(12)
            ],
            "aspects": [
                {"a": a, "b": b, "type": nm, "orb": round(d,4)}
                for a,b,nm,d in asp
            ],
        },
        "human_design": {
            "type": hd["htype"],
            "authority": hd["auth"],
            "profile": hd["profile"],
            "definition": hd["definition"],
            "incarnation_cross": hd["cross"],
            "design_date": f"{hd['design'][0]:04d}-{hd['design'][1]:02d}-{hd['design'][2]:02d}",
            "defined_centers": hd["defined"],
            "open_centers": hd["open"],
            "channels": ['-'.join(map(str,c)) for c in hd['chans']],
            "gates": [
                {
                    "planet": n,
                    "personality": {"gate": gp, "line": lp},
                    "design": {"gate": gd, "line": ld},
                }
                for n,gp,lp,gd,ld in hd['rows']
            ],
        },
        "ziwei": {
            "five_elements_class": _safe(zw["five"]),
            "soul": _safe(zw["soul"]),
            "body": _safe(zw["body"]),
            "hour_index": zw["ti"],
            "palaces": [
                {
                    "name": p["name"],
                    "ganzhi": p["gz"],
                    "flags": p["flag"],
                    "decadal_range": p["decadal"],
                    "major_stars": p["major"],
                    "minor_stars": p["minor"],
                    "adjective_stars": p["adj"],
                }
                for p in zw["palaces"]
            ],
            "horoscope": horoscope,
        },
        "meta": {"engine": "life-chart-engine", "version": "1.0", "ephemeris": "astronomy-engine"},
    }

def to_json_text(envelope):
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def build_synastry_json(inp_a, inp_b):
    """Re-export; implementation lives in ``scripts/synastry.py`` (no cycle).

    Choose relative vs absolute import by ``__package__`` — do not use
    try/except ImportError as a fallback (that would swallow real ImportErrors
    raised while loading synastry's dependencies and hide the root cause).
    """
    if __package__:
        from .synastry import build_synastry_json as _impl
    else:
        from synastry import build_synastry_json as _impl
    return _impl(inp_a, inp_b)


_B_FLAG_ATTRS = ("date_b", "time_b", "tz_b", "lat_b", "lon_b", "gender_b")
_B_REQUIRED_ATTRS = ("date_b", "tz_b", "lat_b", "lon_b", "gender_b")


def _parse_args(argv=None):
    import argparse
    p=argparse.ArgumentParser(description="三系統完整盤面引擎（西洋星盤+人類圖+紫微）")
    p.add_argument('--name', default=INPUT['name'])
    p.add_argument('--gender', choices=['男','女'])
    p.add_argument('--date', help='西曆 YYYY-MM-DD')
    p.add_argument('--time', help='本地時鐘時間 HH:MM (24h)；synastry 模式可省略或 unknown')
    p.add_argument('--tz', help='出生地當時 UTC 時差（含夏令時，如台灣=8）')
    p.add_argument('--lat', help='緯度')
    p.add_argument('--lon', help='經度')
    p.add_argument('--target', default=INPUT['target'], help='紫微運限參考日 YYYY-MM-DD')
    p.add_argument('--ziwei-day-divide', default=INPUT['ziwei_day_divide'],
                   choices=['forward','current'], help='晚子時規則：forward=算次日, current=算當日')
    p.add_argument('--example', action='store_true', help='使用內建範例出生資料')
    p.add_argument('--json', action='store_true', default=False)
    # Person B (synastry mode): any -b flag enters dual-person mode
    p.add_argument('--name-b', dest='name_b', default='B',
                   help='Person B 顯示名稱（synastry 輸出不 echo 輸入，預設 B）')
    p.add_argument('--date-b', dest='date_b', help='Person B 西曆 YYYY-MM-DD')
    p.add_argument('--time-b', dest='time_b', help='Person B 本地時鐘 HH:MM 或 unknown')
    p.add_argument('--tz-b', dest='tz_b', help='Person B UTC 時差')
    p.add_argument('--lat-b', dest='lat_b', help='Person B 緯度')
    p.add_argument('--lon-b', dest='lon_b', help='Person B 經度')
    p.add_argument('--gender-b', dest='gender_b', choices=['男', '女'], help='Person B 性別')
    a=p.parse_args(argv)

    synastry_mode = any(getattr(a, attr) is not None for attr in _B_FLAG_ATTRS)

    if a.example and synastry_mode:
        supplied_b = [f"--{attr.replace('_', '-')}" for attr in _B_FLAG_ATTRS
                      if getattr(a, attr) is not None]
        p.error(
            f"--example is mutually exclusive with synastry -b flags "
            f"({', '.join(supplied_b)})"
        )

    birth_fields = ('gender', 'date', 'time', 'tz', 'lat', 'lon')
    supplied_birth_fields = [field for field in birth_fields if getattr(a, field) is not None]
    if a.example and supplied_birth_fields:
        flags = ', '.join(f"--{field}" for field in supplied_birth_fields)
        p.error(f"--example cannot be combined with birth flags: {flags}")

    if synastry_mode:
        if not a.json:
            p.error("synastry mode only supports --json")
        missing_b = [f"--{attr.replace('_', '-')}" for attr in _B_REQUIRED_ATTRS
                     if getattr(a, attr) is None]
        # A-side required fields in synastry mode: time is optional (unknown allowed)
        a_required = ('gender', 'date', 'tz', 'lat', 'lon')
        missing_a = [f"--{field}" for field in a_required if getattr(a, field) is None]
        missing = missing_a + missing_b
        if missing:
            p.error("the following arguments are required: " + ', '.join(missing))

        raw_a = {
            'name': a.name, 'gender': a.gender, 'date': a.date, 'time': a.time,
            'tz': a.tz, 'lat': a.lat, 'lon': a.lon, 'target': a.target,
            'ziwei_day_divide': a.ziwei_day_divide,
        }
        raw_b = {
            'name': a.name_b, 'gender': a.gender_b, 'date': a.date_b, 'time': a.time_b,
            'tz': a.tz_b, 'lat': a.lat_b, 'lon': a.lon_b, 'target': a.target,
            'ziwei_day_divide': a.ziwei_day_divide,
        }
        try:
            inp_a = validate_input(raw_a, allow_unknown_time=True)
        except ValueError as exc:
            field, separator, detail = str(exc).partition(':')
            p.error(f"--{field}:{detail}" if separator else str(exc))
        try:
            inp_b = validate_input(raw_b, allow_unknown_time=True)
        except ValueError as exc:
            # B-side validation errors must name the -b flag so callers can
            # tell which person failed (e.g. --lat-b, not --lat).
            field, separator, detail = str(exc).partition(':')
            p.error(f"--{field}-b:{detail}" if separator else str(exc))
        return {"mode": "synastry", "inp_a": inp_a, "inp_b": inp_b, "json": True}

    if not a.example:
        missing = [field for field in birth_fields if getattr(a, field) is None]
        if missing:
            p.error("the following arguments are required: " + ', '.join(f"--{field}" for field in missing))

    if a.example:
        date_value = '-'.join(map(str, INPUT['date']))
        time_value = ':'.join(map(str, INPUT['time']))
        gender, tz, lat, lon = INPUT['gender'], INPUT['tz_offset'], INPUT['lat'], INPUT['lon']
    else:
        date_value, time_value = a.date, a.time
        gender, tz, lat, lon = a.gender, a.tz, a.lat, a.lon
    raw = {
        'name': a.name, 'gender': gender, 'date': date_value, 'time': time_value,
        'tz': tz, 'lat': lat, 'lon': lon, 'target': a.target,
        'ziwei_day_divide': a.ziwei_day_divide,
    }
    try:
        inp = validate_input(raw)
    except ValueError as exc:
        field, separator, detail = str(exc).partition(':')
        p.error(f"--{field}:{detail}" if separator else str(exc))
    return {"mode": "single", "inp": inp, "json": a.json}


def main(argv=None):
    parsed = _parse_args(argv)
    if parsed["mode"] == "synastry":
        if __package__:
            from .synastry import (
                ERROR_COMPUTATION_UNSUPPORTED,
                ERROR_INTERNAL,
                MESSAGE_COMPUTATION_UNSUPPORTED,
                MESSAGE_INTERNAL,
            )
        else:
            from synastry import (
                ERROR_COMPUTATION_UNSUPPORTED,
                ERROR_INTERNAL,
                MESSAGE_COMPUTATION_UNSUPPORTED,
                MESSAGE_INTERNAL,
            )
        try:
            sys.stdout.write(
                to_json_text(build_synastry_json(parsed["inp_a"], parsed["inp_b"])) + "\n"
            )
        except eph.ComputationUnsupportedError:
            # Fixed dual-mode error shape; do not leak str(exc) (see design §CLI 雙人輸出).
            error, message = ERROR_COMPUTATION_UNSUPPORTED, MESSAGE_COMPUTATION_UNSUPPORTED
        except Exception:
            error, message = ERROR_INTERNAL, MESSAGE_INTERNAL
        else:
            return 0
        envelope = {
            "ok": False,
            "error": error,
            "message": message,
            "schema_version": "1.2",
        }
        sys.stdout.write(to_json_text(envelope) + "\n")
        return 1

    inp, json_mode = parsed["inp"], parsed["json"]
    if json_mode:
        try:
            sys.stdout.write(to_json_text(build_json(inp)) + "\n")
        except Exception as e:
            envelope = {"ok": False, "error": str(e), "schema_version": "1.2"}
            sys.stdout.write(to_json_text(envelope) + "\n")
            return 1
    else:
        try:
            sys.stdout.write(compose_markdown(inp))
        except Exception as e:
            # runtime failure in Markdown mode: nothing on stdout (the buffer is
            # discarded), one clean line on stderr, exit 1 — no traceback.
            sys.stderr.write(f"error: {e}\n")
            return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
