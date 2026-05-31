> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · **ไทย** · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**การคำนวณเนทีฟแบบกำหนดได้ของระบบแผนภูมิชีวิต 3 ระบบ — ดาราศาสตร์ตะวันตกแบบเนทีฟ ห้องแบบ Human Design (人類圖) และ Zi Wei Dou Shu (紫微斗數) — จากบันทึกการเกิดพอด**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` เป็นเครื่องมือบรรทัดคำสั่งขนาดเล็กและออฟไลน์ คุณให้ข้อมูลการเกิดของบุคคลคนเดียว — วันที่ เวลา โซนเวลา และพิกัดสถานที่ — และมันจะคำนวณระบบแผนภูมิ 3 ระบบในการทำงานเดียวกัน จากนั้นเสมอหรือรายงาน Markdown ที่อ่านง่ายหรือวัตถุ JSON เชิงโครงสร้างสำหรับโปรแกรมและตัวแทน AI ที่จะใช้

สร้างขึ้นสำหรับผู้ที่ต้องการการคำนวณแผนภูมิที่ **ทำซ้ำได้ยืนยันได้** มากกว่าแอปเว็บกล่องดำ: ผู้เชี่ยวชาญ นักพัฒนาที่สร้างเครื่องมือการรับรู้ตัวเอง และตัวแทน AI ที่ต้องการขั้นตอนการคำนวณบริสุทธิ์ ตัวเลขทุกตัวมาจากการคำนวณดาราศาสตร์จริง (Swiss Ephemeris) และไลบรารี Zi Wei Dou Shu จริง (py-iztro) — ไม่ใช่จากบริการระยะไกล ไม่ใช่จากการค้นหากรณี และไม่เคยผ่านเครือข่าย

---

## ระบบคำนวณ

เครื่องมือทำงานกับระบบ 3 ระบบต่อต้าน **ช่วงเวลาการเกิดเดียวกัน** เพื่อให้ผลลัพธ์ของระบบสามารถยืนยันซึ่งกันและกัน ระบบแต่ละระบบตอบคำถามประเภทต่างกัน:

| ระบบ | มันคืออะไร (ภาษาอังกฤษธรรมชาติ) | ระบบเครื่องมือสร้าง |
|--------|----------------------------|------------------------|
| **Western natal** (Tropical / Placidus) | ดาราศาสตร์ตะวันตกแบบคลาสสิก — ที่ดาวเคราะห์นั่งเทียบกับจักรราศี ณ วัยเกิดของคุณ หารด้วยบ้าน 12 หลัง | Ascendant + Midheaven ดาวเคราะห์/จุด 12 ดวง (พระอาทิตย์ → โหนดใต้) ที่มีลักษณะ องศา บ้าน และสัญญาณ retrograde ลัอบอลแนน บ้านทั้ง 12 หลัง และด้านที่ตรวจพบทุกอย่าง (ผสม/หกเหลี่ยม/สี่เหลี่ยม/สามเหลี่ยม/ตรงข้าม) เรียงลำดับตามความเป็นไปได้ |
| **Human Design (人類圖)** | การสังเคราะห์สมัยใหม่ของดาราศาสตร์ I Ching และระบบจักรเปิด อธิบายว่า "สายไฟ" พลังงานของคุณผ่านเกต ช่องทาง และศูนย์ | ประเภท อำนาจ โปรไฟล์ คำจำกัดความ Incarnation Cross วันที่ Design ที่เร็วกว่า 88° ศูนย์กำหนด/เปิด ช่องทางกำหนด และเกต activation ของดาวเคราะห์ต่อ personality และแผนภูมิ Design |
| **Zi Wei Dou Shu (紫微斗數)** | ระบบดาราศาสตร์จีนดั้งเดิมที่จับคู่โชคชะตา ลงบน 12 พระราชวัง เต็มไปด้วยดาวชื่อ | Five Elements Class (五行局) Soul (命主) / Body (身主) ดัชนี hour (時辰) และข้อมูลต่อพระราชวัง — ganzhi, Soul/Body flags ช่วงอายุ decade และ stars หลัก/รอง/สมณฑ (ที่มีความเจิ่ม และ 四化) ตัวเลือกที่ดีที่สุด horoscope ทศวรรษ/ประจำปี |

Type Authority และ Definition ใน Human Design **ไม่ได้รหัสแบบ hardcode** — ได้มาจากกราฟการเชื่อมต่อของศูนย์กำหนด

---

## เหตุผลการคำนวณเนทีฟ

เครื่องมือนี้ทำคณิตศาสตร์จริงแทนการประมาณหรือการโทรไปยังบริการ ตัวเลือกนั้นซื้อ 3 คุณสมบัติที่สำคัญสำหรับเครื่องมือแผนภูมิเสบียงใด ๆ:

- **กำหนดได้** ข้อมูลการเกิดเดียวกันมักสร้างผลลัพธ์เดียวกัน ไบต์สำหรับไบต์ ไม่มีการสุ่ม ไม่มีแบบจำลอง ไม่มีการเบี่ยงเบนการปัดเศษระหว่างการทำงาน
- **ทำซ้ำได้** ใครก็ได้ที่มี repo และเนื้อหาเดียวกันสามารถสร้างแผนภูมิที่แม่นยำของคุณใหม่ได้ การคำนวณใช้ Swiss Ephemeris (Moshier model) สำหรับท้องฟ้า และ py-iztro สำหรับ Zi Wei Dou Shu — ทั้งคู่กำหนดได้
- **ข้ามตรวจสอบได้** เพราะระบบ 3 ระบบอิสระถูกคำนวณจากเวลาการเกิดเดียว คุณสามารถสามเหลี่ยม **เมื่อระบบ 3 ระบบชี้ไปที่สัญญาณเดียวกัน ให้ถือว่ามีความเชื่อมั่นสูง เมื่อระบบเดียวเท่านั้นแสดงรายละเอียด ให้ถือว่ามันเป็นจุดอ้างอิง ไม่ใช่ข้อสรุป** นี่คือหลักการออกแบบหลักของเครื่องมือ — มันสร้างข้อเท็จจริงเพื่อข้ามอ่าน ไม่ใช่คำตัดสินเดียว

---

## เริ่มต้นอย่างรวดเร็ว

### การติดตั้ง One-line (แนะนำ)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

ติดตั้งเข้า `~/.life-chart-engine` (แทนที่ด้วย `LIFE_CHART_DIR`) ไม่มี `sudo` ไม่มีการเปลี่ยนแปลงระดับระบบ — มันเพียงจำลอง repo และสร้าง CPython 3.12 venv แยก ต้องใช้ `git` และ [`uv`](https://docs.astral.sh/uv/) เรียกใช้ใหม่ทุกครั้งเพื่ออัปเดตเป็นเวอร์ชันล่าสุด

### จากแหล่ง

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### สิ่งที่ `setup.sh` ทำ

มันทำงานภายใต้ `set -euo pipefail` และดำเนิน 5 ขั้นตอน:

1. **แก้ไขสถานที่ venv** — `${LIFE_VENV:-<repo>/.venv}` ตั้งค่าตัวแปร env `LIFE_VENV` เพื่อแทนที่; ค่าเริ่มต้น `.venv/` คือ git-ignored
2. **Preflight: ต้องใช้ [`uv`](https://docs.astral.sh/uv/)** — ถ้า `uv` ไม่อยู่ใน `PATH` มันออก `1` และพิมพ์คำแนะนำการติดตั้ง:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **สร้าง CPython 3.12 venv** — `uv venv --python 3.12 "$VENV"` (ดู [เหตุใด CPython 3.12](#why-cpython-312-specifically))
4. **ติดตั้งการพึ่งพาที่ปักหมุด** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`
5. **ทำสอบเลือก** — ดำเนิน execute เครื่องมือครั้งเดียวด้วยข้อมูลตัวอย่างคงที่ (ทิ้ง stdout) และพิมพ์ `OK — engine runs.` ความสำเร็จ มันพิมพ์คำแนะนำการใช้งานสำหรับทั้งสองโหมด

### ขั้นตอน `uv` ด้วยตนเอง (ไม่มี `setup.sh`)

```bash
# 1. Create CPython 3.12 venv (default <repo>/.venv; override with LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Install pinned deps
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (Optional) smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

โฟลว์การพึ่งพาโดยตรงเพียงสอง pin ใน `requirements.txt`:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## เหตุใด CPython 3.12 โดยเฉพาะ

คุณต้องเรียกใช้เครื่องมือบน **CPython 3.12** — ไม่ใช่ 3.13 ไม่ใช่ 3.14 เหตุผลระบุว่าเหมือนกันใน `requirements.txt` และ `setup.sh`:

> deps เนทีฟ py-iztro (**pythonmonkey / pydantic-core**) **ไม่มี wheels สำหรับ 3.13+/3.14 และไม่สามารถสร้างจากแหล่ง** ปักหมุด 3.12

โดยสรุป: `py-iztro` ขึ้นอยู่กับส่วนขยายเนทีฟ (`pythonmonkey`, `pydantic-core`) ซึ่งล้วง prebuilt wheels หยุดที่ 3.12 บน 3.13/3.14 ไม่มี wheels และการสร้างแหล่งล้มเหลว นี่คือเหตุผลที่ `setup.sh` เรียก `uv venv --python 3.12` ว่าทำไมคุณควรเรียกใช้เครื่องมือด้วย repo venv Python (`<repo>/.venv/bin/python`) ไม่ใช่ระบบ `python3`

---

## การใช้งาน

เครื่องมือมี 2 โหมด เลือกตามการปรากฏตัวของแฟล็ก `--json`

### โหมด Human (Markdown)

ละเว้น `--json` เพื่อรับรายงาน console ที่อ่านได้ ใช้ Python ของ venv ของคุณ:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

ตัดแต่ง sample จริง (ด้านเหลือเพื่อศูนย์สุด-10 ในโหมด Markdown):

```
### Sample｜女｜1990-06-15 08:30 (UTC+8)

【西洋星盤 Tropical/Placidus】
上升 獅子 08°29' ｜ 天頂 金牛 04°22'
  太陽   雙子 23°40'  11宮
  月亮   雙魚 09°00'  8宮
  ...
  主要相位: 北交點-南交點對分(0.0°)；北交點-上升對分(0.4°)；南交點-上升合相(0.4°)；木星-冥王星三分(0.4°)；月亮-天王星六分(0.8°)…

【人類圖 Human Design】
類型 投射者 ｜ 權威 自我投射型權威 ｜ 角色 1/3 ｜ 定義 一分人(單一定義)
輪迴交叉 右角度交叉（12/11 | 36/6）
定義中心 G,喉 ｜ 開放中心 情緒,意志,根,脾,薦骨,邏輯,頭
設計日期 1990-03-16
通道 ['13-33']

【紫微斗數 py-iztro】
五行局 土五局 ｜ 命主 祿存 ｜ 身主 火星
  命宮   戊寅  (5-14): 七殺(廟)｜天廚 蜚廉
  父母   己卯  (115-124): 天同(平)[忌]｜地劫 天喜 咸池 恩光 天德
  ...
```

### โหมด Agent (JSON)

เพิ่ม `--json` เพื่อรับวัตถุ JSON หนึ่งชิ้นบน stdout และไม่มีอะไรเลย — อุดมคติสำหรับโปรแกรมและตัวแทน AI:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

ตัดแต่ง sample จริง (อาร์เรย์ตัดเป็น 1–2 entry; ค่า verbatim):

```json
{
  "ok": true,
  "schema_version": "1.0",
  "input": {
    "name": "小明", "gender": "女",
    "date": "1990-06-15", "time": "08:30",
    "tz_offset": 8.0, "lat": 25.033, "lon": 121.5654,
    "target": "2025-01-01"
  },
  "western": {
    "system": "Tropical / Placidus / Moshier",
    "ascendant": { "lon": 128.483, "sign": "獅子", "deg": 8, "min": 29, "label": "獅子 08°29'" },
    "midheaven": { "lon": 34.3665, "sign": "金牛", "deg": 4, "min": 22, "label": "金牛 04°22'" },
    "planets": [
      { "name": "太陽", "retrograde": false, "house": 11, "lon": 83.6719, "sign": "雙子", "deg": 23, "min": 40, "label": "雙子 23°40'" }
    ],
    "houses": [
      { "house": 1, "lon": 128.483, "label": "獅子 08°29'" }
    ],
    "aspects": [
      { "a": "北交點", "b": "南交點", "type": "對分", "orb": 0.0 },
      { "a": "木星", "b": "冥王星", "type": "三分", "orb": 0.3744 }
    ]
  },
  "human_design": {
    "type": "投射者",
    "authority": "自我投射型權威",
    "profile": "1/3",
    "definition": "一分人(單一定義)",
    "incarnation_cross": "右角度交叉（12/11 | 36/6）",
    "design_date": "1990-03-16",
    "defined_centers": ["G", "喉"],
    "open_centers": ["情緒", "意志", "根", "脾", "薦骨", "邏輯", "頭"],
    "channels": ["13-33"],
    "gates": [
      { "planet": "☉", "personality": { "gate": 12, "line": 1 }, "design": { "gate": 36, "line": 3 } }
    ]
  },
  "ziwei": {
    "five_elements_class": "土五局",
    "soul": "祿存",
    "body": "火星",
    "hour_index": 4,
    "palaces": [
      {
        "name": "命宮", "ganzhi": "戊寅", "flags": "", "decadal_range": "5-14",
        "major_stars": ["七殺(廟)"], "minor_stars": [], "adjective_stars": ["天廚", "蜚廉"]
      }
    ],
    "horoscope": { "decadal": { "...": "best-effort, may be null" } }
  },
  "meta": { "engine": "life-chart-engine", "version": "1.0", "ephemeris": "Moshier" }
}
```

---

## ข้อมูลอ้างอิง CLI flags

ไม่มี `required=True` flags — argparse ไม่เคยผิดพลาดหากไม่มี ละเว้น `--date`/`--time`/`--tz`/`--lat`/`--lon` silently fall back ไปที่บุคคลตัวอย่าง built-in (`範例` เกิด `2000-01-01 12:00` UTC+8 Taipei 101) ดังนั้นสำหรับแผนภูมิที่ถูกต้อง ให้จัดหาทั้งหมด

| Flag | ประเภท | ต้องใช้สำหรับการใช้งานที่ถูกต้องหรือไม่ | ค่าเริ่มต้น | รูปแบบ / กฎ |
|------|------|---------------------------|---------|---------------|
| `--name` | string | ไม่ (cosmetic) | `"範例"` | ข้อความฟรี; echo เข้าสู่เอาต์พุตเท่านั้น |
| `--gender` | string | เพียง Zi Wei เท่านั้น | `"女"` | ต้องถูกต้องแน่นอน `男` หรือ `女` (argparse `choices`; อื่น ๆ → ออก `2`) |
| `--date` | string | **ใช่** | fall back ไปที่ `2000-01-01` | `YYYY-MM-DD` แยก `-` ไม่จำเป็น zero-pad |
| `--time` | string | **ใช่** | fall back ไปที่ `12:00` | `HH:MM` 24-hour local clock time แยก `:` |
| `--tz` | float | **ใช่** | fall back ไปที่ `8.0` | UTC offset รวม DST (Taiwan = `8`) เขียนไปที่ input key `tz_offset` |
| `--lat` | float | **ใช่** | fall back ไปที่ `25.0330` | Latitude ในองศาทศนิยม (Western houses/Asc/MC) |
| `--lon` | float | **ใช่** | fall back ไปที่ `121.5654` | Longitude ในองศาทศนิยม |
| `--target` | string | ไม่ | `"2025-01-01"` | `YYYY-MM-DD`; Zi Wei luck-period reference date (運限參考日) |
| `--json` | flag | ไม่ | `False` (Markdown) | Presence → JSON mode; absence → Markdown ไม่ใช้ค่า |

> เครื่องมือทำ **ไม่** geocode สถานที่หรือค้นหาเขตเวลา ผู้เรียกต้องแปลง place → `lat`/`lon`/`tz` ตัวเอง — และเขตเวลา/DST คือแหล่งข้อผิดพลาดทั่วไปที่สุด ดังนั้นตรวจสอบ UTC offset ที่ใช้ที่สถานที่เกิด และวันเกิด

---

## ข้อมูลอ้างอิงเอาต์พุต

ซองจดหมาย `--json` มี 7 keys ระดับบนสุด ในการสั่งนี้:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| บล็อก | สรุป |
|-------|---------|
| `ok` | `true` ความสำเร็จ (`false` ในซองจดหมายข้อผิดพลาด) |
| `schema_version` | `"1.0"` |
| `input` | Echo ของเนื้อหาที่ปกติ: `name` `gender` `date` `time` `tz_offset` `lat` `lon` `target` (หมายเหตุ `tz_offset` ไม่ใช่ `tz`) |
| `western` | `system` string `ascendant`/`midheaven` position objects `planets[]` `houses[]` (×12) `aspects[]` |
| `human_design` | `type` `authority` `profile` `definition` `incarnation_cross` `design_date` `defined_centers[]` `open_centers[]` `channels[]` `gates[]` |
| `ziwei` | `five_elements_class` `soul` `body` `hour_index` `palaces[]` `horoscope` (วัตถุหรือ `null`) |
| `meta` | `{ engine, version, ephemeris }` — ตัวอักษร (`ephemeris: "Moshier"`) |

สำหรับสัญญาฟิลด์เต็ม — ทุก key ประเภท และโปรโตคอลการเรียกใช้ตัวแทน — ดู **[AGENTS.md](./AGENTS.md)**

### Field quirks น่ารู้

- **`aspects` ไม่ได้ capped ใน JSON** path JSON ส่งคืน *ทุก* ด้านที่ตรวจพบ เรียงลำดับจากน้อยไปมากตามหมอบ (แน่นที่สุดที่สาม) cap 10-item มีเพียงในรายงาน Markdown
- **`ziwei.horoscope` คือ best-effort และอาจเป็น `null`** มันถูก wrap ใน `try/except`; ในข้อยกเว้นใด ๆ มันเป็นอนุกรม `null` เมื่อมีอยู่ มันคือ `{ decadal, yearly }` (sub-objects เหล่านั้นเปิดโครงสร้างภายในพิเศษ — `index` `mutagen[]` `stars[][]` `yearly_dec_star` ฯลฯ — เกินกว่าตัวจำหน่ายที่บันทึกไว้)
- **สตริง Star เข้ารหัสความเจิ่ม + 四化** รูปแบบคือ `name(brightness)[mutagen]` กับแต่ละส่วน optional — เช่น `紫微(廟)[祿]` `紫微(廟)` `天機[祿]` หรือแค่ `天機` `adjective_stars` เป็นชื่อเรียบร้อยเท่านั้น (ไม่มีความเจิ่ม/mutagen)

---

## ชั้นความแม่นยำ

ไม่ใช่ทุกเอาต์พุตเข้ารับเชื่อมั่น อ่านแต่ละชั้นตามลำดับ:

| ชั้น | สิ่งที่มันครอบคลุม | ความเชื่อมั่น |
|------|----------------|------------|
| **สูงสุด** | ลองจิจูดดาวเคราะห์ สัญญาณ retrograde และ Zi Wei star placement / 命宮·身宮 / 五行局 — pure ephemeris และคณิตศาสตร์ปฏิทิน | ศาสตร์ดาราศาสตร์/ปฏิทินที่แม่นยำ |
| **สูง ต้องอาศัยเวลา** | Ascendant Midheaven ทั้ง 12 house cusps บ้านที่ดาวเคราะห์แต่ละดวงตกใน Human Design lines และ Zi Wei 時辰 index | ที่แม่นยำ *ให้* เวลาเกิดที่แม่นยำ; ความไว ต่อนาที |
| **ตรวจสอบแล้ว** | ความเจิ่มดาว Zi Wei Dou Shu — ปรับตามเอาต์พุต py-iztro library | ตรวจสอบกับไลบรารี่ |
| **Flag boundary ±0.3°** | ดาวเคราะห์ / เกต / ไลน์ใด ๆ นั่งภายใน ±0.3° ของขอบเขต | ถือว่า provisional และหมายเหตุผลกระทบ — ±0.3° สามารถ flip มันข้ามไลน์ |

---

## ข้อจำกัดที่ทราบ

- **ไม่มี Chiron / bodies รอง** บิลด์ใช้ ephemeris Moshier (`swe.FLG_MOSEPH` ไม่มี data files) ซึ่งไม่ให้ Chiron หรือ bodies รอง เพียง 10 ดาวเคราะห์คลาสสิกบวก lunar nodes จึงถูกคำนวณ
- **Zi Wei Dou Shu ใช้ school ค่าเริ่มต้นเดียว** py-iztro เรียกด้วยตัวเลือก fixed (`by_solar(..., True, 'zh-TW')`); star-placement school และ 四化 เป็น whatever py-iztro defaults ไป ถ้าปกติคุณใช้ 飛星 หรือ school อื่น โครงสร้าง principal ไม่เปลี่ยนแปลง แต่รายละเอียดบาง อาจแตกต่าง
- **เวลาเกิดประมาณลดระดับความสำคัญ time-dependent** ถ้าเวลาเกิด uncertain Ascendant/MC/house assignments Human Design lines และ 時辰 — และสิ่งใด ๆ derived จากพวกเขา — กลายเป็น unreliable ในกรณีนั้น **ถือว่า time-dependent fields เป็น provisional** และพิจารณา **event-based rectification** (matching known life events เพื่อ chart timing) ก่อน relying บน them

---

## ใช้มันจาก AI agent / Hermes

การรวมแบบ intended ถูก **self-install** ไม่ใช่ SaaS

ผู้ใช้คัดลอก repo URL นี้ และ **ของตัวเอง** agent หรือ CLI (Claude Code Hermes a script ฯลฯ) clones มัน และรัน มัน **locally บนเครื่องของผู้ใช้** การคำนวณเกิดขึ้นบนด้านผู้ใช้ ไม่มี hosted endpoint ไป call ไม่มี account และ **ไม่จำเป็นต้องมี SaaS integration** — เครื่องมือเป็น stateless กำหนดได้ offline subprocess

เนื่องจากสำนักพิมพ์ไม่ดำเนินการเป็นบริการเครือข่าย ไม่มี §13 obligation ตกบน publisher สำหรับ self-install ของใครก็ได้ (แยกต่างหาก §13 เพียง obligates operator ที่รัน *modified* network-reachable version — ไม่ unmodified local use)

สำหรับตัวแทน สัญญาเรียบง่าย: dispatch subprocess `--json` กับ venv Python ใน repo workdir parse stdout เป็น JSON branch บน `ok` (และ exit code) จากนั้นส่งต่อ object ที่ได้รับการจัดโครงสร้าง ไม่ต้องการการทำความสะอาด — มันเป็น stateless สัญญา CLI + JSON เต็มอยู่ใน **[AGENTS.md](./AGENTS.md)**

### Copy-paste setup สำหรับ AI agent ของคุณ

วาง block นี้โดยตรงลงใน Claude Code ChatGPT หรือ coding agent ใด ๆ — มันบอก agent วิธีการติดตั้ง และเรียกใช้เครื่องมือ:

```text
Set up and use "life-chart-engine" — a CLI that computes a Western natal chart +
Human Design + Zi Wei Dou Shu (紫微斗數) from birth data.

1. Install (needs `git` and `uv`; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Compute a chart and read stdout as JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Rules:
   - YOU resolve the birth city to --lat/--lon and the correct historical UTC
     offset (DST-aware). The tool does not geocode.
   - Confirm whether the birth time is exact before trusting the ascendant,
     houses, Human Design lines, or the Zi Wei hour pillar.
   - Never fabricate chart values — always call the tool.
   - Full output schema, exit codes, and the agent contract: ~/.life-chart-engine/AGENTS.md
```

---

## การอนุญาต

repo นี้ได้รับอนุญาตภายใต้ **[AGPL-3.0](./LICENSE)**

**AGPL-3.0 ในภาษาอังกฤษธรรมชาติ** มันคือ GNU GPL-3.0 (copyleft strong license: ถ้าคุณแจกจ่าย software คุณต้องเผยแพร่ complete corresponding source ภายใต้ license เดียวกัน) **บวกอย่างน้อยหนึ่งข้อบัญชี มาตรา 13** §13 ปิด "SaaS loophole": นอกเหนือจาก GPL *distribution* trigger มันเพิ่ม ที่ถ้าคุณ *modify* โปรแกรม และให้ผู้ใช้โต้ตอบกับ modified version ของคุณบนเครือข่าย คุณต้อง offer remote users ของคุณ corresponding source (Running unmodified upstream เป็นบริการเครือข่ายไม่ trigger §13 เอง) AGPL reciprocal แต่ไม่ boundlessly viral — มันเพียง reach code ที่ is a derivative ของ หรือ linked กับ AGPL code

**ทำไม repo นี้ AGPL** เครื่องมือ links **Swiss Ephemeris** (via `pyswisseph`) สำหรับ planetary positions และ house cusps Astrodienst **dual-licenses** Swiss Ephemeris เป็น **AGPL-3.0 OR commercial license** และ code ของ it ไม่สามารถ relicensed เป็นสิ่ง permissive เพิ่มเติม เพราะ AGPL copyleft และ project นี้ links it whole combined work ต้อง AGPL (`py-iztro` MIT และ imposes ไม่มี copyleft; Swiss Ephemeris เท่านั้น component forcing AGPL ที่นี่)

**มันหมายความว่าในทางปฏิบัติ**

| คุณทำ | AGPL obligation |
|--------|-----------------|
| **Self-install** (รัน it locally สำหรับตัวเอง) | §13 คือ *ไม่* triggered — ไม่มี remote users เพื่อให้บริการ และคุณมี source แล้ว ยากจนสะอาด |
| **เรียก *modified* version เป็นบริการเครือข่าย** | §13 *คือ* triggered — คุณต้อง offer remote users ของคุณ complete corresponding source ของ deployed version ของคุณ ภายใต้ AGPL รวม modifications ของคุณ หมายเหตุ: §13 source-offer duty เป็น conditioned ใน modification — running unmodified upstream เป็นบริการเครือข่าย ไม่ trigger §13 เอง แม้ว่า source ยังเป็น public อยู่แล้ว |

**ตัวเลือก 3 ของคุณ** ถ้า network-source obligation ไม่พอดี use case ของคุณ:

1. **Keep AGPL** — เผยแพร่ complete corresponding source ของคุณ (รวม modifications) ให้ใครก็ได้ที่ใช้ it รวมบนเครือข่ายต่อ §13 ฟรี ไม่มีการเจรจา
2. **ซื้อ Swiss Ephemeris commercial license จาก [Astrodienst](https://www.astro.com/swisseph/)** — นี้ยก AGPL obligation สำหรับ Swiss Ephemeris portion ให้ relicense code ของคุณเอง และ ship/host a closed build (นี้ Astrodienst dual-licensing model)
3. **สลับ ephemeris** — แทนที่ `pyswisseph` ด้วย permissively licensed astronomy source (เช่น **Skyfield (MIT)** บวก public-domain **JPL DE440** ephemeris — illustrative alternatives ไม่ใช่ option เดียว) ด้วย Swiss Ephemeris ไป stack ที่เหลือ (py-iztro MIT บวก MPL-2.0/MIT/Apache deps) ยังคงบังคับ AGPL และ whole repo สามารถถูก MIT นี้คือ real engineering effort: คุณต้อง reimplement ทั้งหมด currently sourced จาก Swiss Ephemeris — planetary longitudes retrograde flags Asc/MC Placidus house cusps และ inputs ไปยัง Human Design 88° design solver

ดู **[CREDITS.md](./CREDITS.md)** สำหรับ full attribution และ per-dependency licenses

---

## FAQ

**ฉันสามารถป้อนวันที่อักษรจันทรคติได้หรือไม่?**
ไม่ใช่ เนื้อหาเป็นวันที่สุริยะแบบ Gregorian (`--date YYYY-MM-DD`) และเวลานาฬิกา (`--time HH:MM`) ถ้าคุณมีเพียงวันที่อักษรจันทรคติ ให้แปลง it first Zi Wei Dou Shu ถูกคำนวณผ่าน py-iztro solar entry point (`by_solar`)

**เวลาเกิดของฉันเพียง approximate — นี่คือปัญหาหรือไม่?**
Planetary positions ดีแต่ Ascendant Midheaven house cusps บ้านที่ดาวเคราะห์นั่ง Human Design lines และ 時辰 ทั้งหมด time-sensitive ถือว่า those เป็น provisional และพิจารณา event-based rectification ก่อน relying บน them

**ที่ไหน Chiron / asteroids / bodies รอง?**
ไม่รวม Moshier ephemeris ที่ใช้ที่นี่ไม่ให้ them; เพียง 10 classical planets และ lunar nodes จึงถูกคำนวณ

**ไหน Zi Wei Dou Shu school ไป?**
Default school เช่น implemented โดย py-iztro (`by_solar(..., True, 'zh-TW')`). School ไม่ user-selectable

**มันโทรศัพท์บ้าน / ใช้เครือข่าย?**
ไม่ใช่ เครื่องมือเป็นลูกอ้ย offline — ไม่มี telemetry ไม่มี network calls ไม่มี side effects มันเป็น stateless กำหนดได้ one-shot subprocess

**ฉันสามารถใช้มัน inside closed-source product?**
ภายใต้ AGPL-3.0 ใช่สำหรับ private/local use Distributing a build triggers GPL conveying/source obligations และ network-serving a *modified* build triggers AGPL §13 — ทั้งสองวิธี คุณต้อง offer corresponding source ไปไปปิดแหล่ง either ซื้อ Swiss Ephemeris commercial license จาก Astrodienst หรือสลับ ephemeris ไปยัง Skyfield + JPL DE440 (ดู [Licensing](#licensing))

---

## ปฏิเสธ

`life-chart-engine` คือ **self-awareness framework interpretive ไม่ prediction หรือ fatalism** เอาต์พุตเป็น structured reference points สำหรับ reflection — พวกเขาไม่คาดหวังเหตุการณ์ และไม่จำหน่าย outcomes มันใช้พวกเขาเป็น calibration กับ lived experience ของคุณเป็นเพื่อน final authority ไม่มีสิ่งใด ที่นี่เป็น medical legal psychological หรือ financial advice สำหรับการตัดสินใจใน domains ที่ consult a qualified professional

---

## Credits & License

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG dual-licensed AGPL-3.0 / commercial (<https://www.astro.com/swisseph/>)
- **py-iztro** (และ upstream `iztro`) — MIT สำหรับ Zi Wei Dou Shu
- Full attribution: **[CREDITS.md](./CREDITS.md)**
- **License:** [AGPL-3.0](./LICENSE)
- **Agent / JSON contract:** [AGENTS.md](./AGENTS.md)
