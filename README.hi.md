> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · **हिन्दी** · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**तीन जीवन-चार्ट प्रणालियों की नियतात्मक मूल-गणना — पश्चिमी जन्म ज्योतिष, 人類圖 (Human Design), और 紫微斗數 (Zi Wei Dou Shu) — एक एकल जन्म रिकॉर्ड से।**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` एक छोटा, ऑफ़लाइन कमांड-लाइन टूल है। आप इसे किसी व्यक्ति का जन्म डेटा देते हैं — तारीख, समय, समय क्षेत्र, और स्थान निर्देशांक — और यह एक ही पास में तीन स्वतंत्र चार्ट प्रणालियों की गणना करता है, फिर या तो एक मानव-पठनीय Markdown रिपोर्ट या प्रोग्राम और AI एजेंटों के लिए एक संरचित JSON ऑब्जेक्ट उत्सर्जित करता है।

यह उन लोगों के लिए बनाया गया है जो **पुनरुत्पादक, सत्यापन योग्य** चार्ट गणना चाहते हैं, न कि काले-डिब्बे वाली वेब ऐप: व्यवसायी, आत्म-जागरूकता उपकरण बनाने वाले डेवलपर, और AI एजेंट जिन्हें शुद्ध गणना चरण की आवश्यकता है। प्रत्येक संख्या वास्तविक खगोलीय गणना (Swiss Ephemeris) और एक वास्तविक 紫微斗數 लाइब्रेरी (py-iztro) से आती है — किसी रिमोट सेवा से नहीं, कैश्ड लुकअप से नहीं, और कभी नेटवर्क पर नहीं।

---

## यह क्या गणना करता है

इंजन **एक ही जन्म क्षण** के विरुद्ध तीन प्रणालियां चलाता है, इसलिए उनके आउटपुट एक दूसरे को पुष्ट कर सकते हैं। प्रत्येक प्रणाली एक अलग प्रकार के प्रश्न का उत्तर देती है:

| प्रणाली | यह क्या है (साधारण अंग्रेजी में) | इंजन क्या देता है |
|--------|---------------------------|------------------------|
| **पश्चिमी जन्म** (उष्णकटिबंधीय / Placidus) | शास्त्रीय पश्चिमी ज्योतिष — आपके जन्म के समय ग्रह राशि के विरुद्ध कहाँ थे, 12 भावों में विभाजित। | उदय (Ascendant) + मध्य आकाश (Midheaven), 12 ग्रह/बिंदु (太陽 → 南交點) के साथ राशि, डिग्री, भाव और वक्र (retrograde) झंडा, सभी 12 भाव कुस्पी, और हर खोजा गया पहलू (合相/六分/四分/三分/對分) कसाई द्वारा क्रमबद्ध। |
| **人類圖 Human Design** | ज्योतिष, I-Ching, और चक्र प्रणाली का एक आधुनिक संश्लेषण। वर्णन करता है कि आपकी ऊर्जा गेटों, चैनलों, और केंद्रों के माध्यम से कैसे "तार" है। | प्रकार, प्राधिकार, प्रोफाइल, परिभाषा, अवतार क्रॉस, 88°-पहले डिज़ाइन तारीख, परिभाषित/खुले केंद्र, परिभाषित चैनल, और प्रति-ग्रह गेट.लाइन सक्रियताएं व्यक्तित्व और डिज़ाइन दोनों चार्टों के लिए। |
| **紫微斗數 Zi Wei Dou Shu** | एक पारंपरिक चीनी ज्योतिष प्रणाली जो भाग्य को एक 12-महल बोर्ड पर मैप करती है, नामित तारों से भरी हुई। | 五行局 (पाँच तत्व वर्ग), 命主 (आत्मा) / 身主 (शरीर), 時辰 घंटा सूचकांक, और प्रति-महल डेटा — गणज़ी, 命/身 झंडे, दशक आयु सीमा, और प्रमुख/मामूली/विशेषण तारे (चमक और 四化 के साथ)। वैकल्पिक रूप से एक सर्वोत्तम-प्रयास 大限/流年 भविष्यवाणी। |

Human Design में प्रकार, प्राधिकार, और परिभाषा **कठोर-कोडित नहीं** हैं — वे परिभाषित केंद्रों के कनेक्टिविटी ग्राफ से व्युत्पन्न हैं।

---

## मूल गणना क्यों

यह इंजन वास्तविक गणित करता है, अनुमान लगाने या सेवा कॉल करने के बजाय। वह पसंद तीन गुण खरीदता है जो किसी भी गंभीर चार्ट टूल के लिए महत्वपूर्ण हैं:

- **नियतात्मक।** एक ही जन्म इनपुट हमेशा एक ही आउटपुट देता है, बाइट-दर-बाइट। कोई यादृच्छिकता नहीं है, कोई मॉडल नहीं है, रन के बीच कोई गोलाई बहाव नहीं है।
- **पुनरुत्पादक।** रिपो और एक ही इनपुट के साथ कोई भी आपके सटीक चार्ट को पुनः उत्पन्न कर सकता है। गणना आकाश के लिए Swiss Ephemeris (Moshier मॉडल) और 紫微斗數 के लिए py-iztro का उपयोग करती है — दोनों नियतात्मक हैं।
- **क्रॉस-सत्यापन योग्य।** क्योंकि तीन स्वतंत्र प्रणालियों की गणना एक जन्म क्षण से की जाती है, आप त्रिकोणीकरण कर सकते हैं। **जब सभी तीन प्रणालियां एक ही संकेत पर इशारा करती हैं, इसे उच्च आत्मविश्वास के रूप में व्यवहार करें। जब केवल एक प्रणाली विवरण दिखाती है, इसे एक संदर्भ बिंदु के रूप में व्यवहार करें, निष्कर्ष के रूप में नहीं।** यह इंजन का मूल डिज़ाइन सिद्धांत है — यह एक एकल निर्णय नहीं, बल्कि क्रॉस-रीड करने के लिए तथ्य उत्पन्न करता है।

---

## त्वरित प्रारंभ

### एक-पंक्ति स्थापना (अनुशंसित)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

`~/.life-chart-engine` में स्थापित करता है (`LIFE_CHART_DIR` से अधिलेखित करें)। कोई `sudo` नहीं, कोई सिस्टम-व्यापी परिवर्तन नहीं — यह केवल रिपो को क्लोन करता है और एक अलग CPython 3.12 venv बनाता है। `git` और [`uv`](https://docs.astral.sh/uv/) की आवश्यकता है। नवीनतम संस्करण में अपडेट करने के लिए कभी भी पुनः चलाएं।

### स्रोत से

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` क्या करता है

यह `set -euo pipefail` के तहत चलता है और पाँच चरण करता है:

1. **venv स्थान को हल करता है** — `${LIFE_VENV:-<repo>/.venv}`। अधिलेखन करने के लिए `LIFE_VENV` env var सेट करें; डिफ़ॉल्ट `.venv/` git-ignore है।
2. **प्रीफ्लाइट: [`uv`](https://docs.astral.sh/uv/) की आवश्यकता है** — यदि `uv` `PATH` पर नहीं है तो यह `1` को exit करता है और इंस्टॉल हिंट प्रिंट करता है:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **एक CPython 3.12 venv बनाता है** — `uv venv --python 3.12 "$VENV"` (देखें [Why CPython 3.12](#why-cpython-312-specifically))।
4. **पिन किए गए डिपेंडेंसी को इंस्टॉल करता है** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`।
5. **एक स्मोक टेस्ट चलाता है** — निश्चित नमूना इनपुट के साथ इंजन को एक बार निष्पादित करता है (stdout को छोड़ देता है) और सफलता पर `OK — engine runs.` प्रिंट करता है। यह दोनों मोड के लिए उपयोग संकेत भी प्रिंट करता है।

### मैनुअल `uv` चरण (कोई `setup.sh` नहीं)

```bash
# 1. CPython 3.12 venv बनाएं (डिफ़ॉल्ट <repo>/.venv; LIFE_VENV से अधिलेखित करें)
uv venv --python 3.12 .venv

# 2. पिन किए गए deps को इंस्टॉल करें
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (वैकल्पिक) स्मोक टेस्ट
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

केवल दो प्रत्यक्ष डिपेंडेंसी `requirements.txt` में पिन की गई हैं:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## CPython 3.12 विशेष रूप से क्यों

आपको इंजन को **CPython 3.12** पर चलाना चाहिए — 3.13 नहीं, 3.14 नहीं। कारण `requirements.txt` और `setup.sh` दोनों में समान रूप से कहा गया है:

> py-iztro की मूल deps (**pythonmonkey / pydantic-core**) के पास **3.13+/3.14 के लिए कोई wheels नहीं हैं और स्रोत से बनने में विफल हैं**। 3.12 को पिन करें।

संक्षेप में: `py-iztro` देशी विस्तार पर निर्भर करता है (`pythonmonkey`, `pydantic-core`) जिनके पूर्वनिर्मित wheels 3.12 पर रुकते हैं। 3.13/3.14 पर कोई wheels नहीं हैं और स्रोत बिल्ड विफल होता है। यही ठीक है कि `setup.sh` `uv venv --python 3.12` कहता है, और आपको हमेशा प्रोजेक्ट venv के Python (`<repo>/.venv/bin/python`) के साथ इंजन को invoke करना चाहिए, कभी सिस्टम `python3` नहीं।

---

## उपयोग

इंजन के दो मोड हैं, जिन्हें `--json` झंडे की उपस्थिति से चुना जाता है।

### मानव मोड (Markdown)

पठनीय कंसोल रिपोर्ट प्राप्त करने के लिए `--json` को छोड़ें। अपने venv के Python का उपयोग करें:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

ट्रिम किया गया वास्तविक नमूना (पहलू Markdown मोड में शीर्ष-10 तक सीमित हैं):

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

### एजेंट मोड (JSON)

`--json` जोड़ें ताकि stdout पर एक JSON ऑब्जेक्ट और कुछ नहीं — प्रोग्राम और AI एजेंटों के लिए आदर्श:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

ट्रिम किया गया वास्तविक नमूना (arrays को 1–2 entries तक ट्रिम किया गया; मान शाब्दिक):

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

## CLI झंडे संदर्भ

**कोई `required=True` झंडे नहीं** हैं — argparse कभी एक लापता पर error नहीं करता। `--date`/`--time`/`--tz`/`--lat`/`--lon` को छोड़ने से चुप्पी से एक बिल्ट-इन उदाहरण व्यक्ति में fallback होता है (`範例`, जन्म `2000-01-01 12:00`, UTC+8, Taipei 101)। तो एक सही चार्ट के लिए, उन सभी को आपूर्ति करें।

| झंडा | प्रकार | सही उपयोग के लिए आवश्यक? | डिफ़ॉल्ट | प्रारूप / नियम |
|------|--------|------------------------|---------|-------------|
| `--name` | string | नहीं (cosmetic) | `"範例"` | मुक्त पाठ; आउटपुट में केवल प्रतिध्वनि। |
| `--gender` | string | केवल 紫微 के लिए | `"女"` | बिल्कुल `男` या `女` होना चाहिए (argparse `choices`; कुछ और → exit `2`)। |
| `--date` | string | **हाँ** | `2000-01-01` को fallback करता है | `YYYY-MM-DD`, `-` पर विभाजन। शून्य-पैड की आवश्यकता नहीं। |
| `--time` | string | **हाँ** | `12:00` को fallback करता है | `HH:MM`, 24-घंटे स्थानीय घड़ी समय, `:` पर विभाजन। |
| `--tz` | float | **हाँ** | `8.0` को fallback करता है | DST सहित UTC offset (Taiwan = `8`)। Input key `tz_offset` में लिखा गया। |
| `--lat` | float | **हाँ** | `25.0330` को fallback करता है | दशमलव डिग्री में अक्षांश (पश्चिमी भाव/Asc/MC)। |
| `--lon` | float | **हाँ** | `121.5654` को fallback करता है | दशमलव डिग्री में देशांतर। |
| `--target` | string | नहीं | `"2025-01-01"` | `YYYY-MM-DD`; 紫微 luck-period संदर्भ तारीख (運限參考日)। |
| `--json` | झंडा | नहीं | `False` (Markdown) | उपस्थिति → JSON मोड; अनुपस्थिति → Markdown। कोई मान नहीं लेता। |

> इंजन स्थानों को geocode नहीं करता है या समय क्षेत्र को look up नहीं करता है। कॉलर को स्वयं स्थान → `lat`/`lon`/`tz` को convert करना चाहिए — और timezone/DST सबसे सामान्य error स्रोत है, इसलिए UTC offset को verify करें जो जन्म स्थान और जन्म तारीख पर लागू था।

---

## आउटपुट संदर्भ

`--json` envelope के सात top-level कुंजियां हैं, इस क्रम में:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| ब्लॉक | सारांश |
|-------|---------|
| `ok` | सफलता पर `true` (`false` error envelope में)। |
| `schema_version` | `"1.0"`। |
| `input` | सामान्यीकृत इनपुट की प्रतिध्वनि: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (ध्यान दें `tz_offset`, `tz` नहीं)। |
| `western` | `system` string, `ascendant`/`midheaven` position objects, `planets[]`, `houses[]` (×12), `aspects[]`। |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`। |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (object या `null`)। |
| `meta` | `{ engine, version, ephemeris }` — सभी literals (`ephemeris: "Moshier"`)। |

पूर्ण field contract के लिए — हर key, प्रकार, और एजेंट invocation protocol — देखें **[AGENTS.md](./AGENTS.md)**।

### ध्यान देने योग्य फील्ड विशेषताएं

- **`aspects` JSON में capped नहीं हैं।** JSON पथ *हर* खोजा गया पहलू देता है, orb द्वारा восходящих क्रम में सॉर्ट किया गया (सबसे तंग पहले)। 10-item cap केवल Markdown रिपोर्ट में मौजूद है।
- **`ziwei.horoscope` best-effort है और `null` हो सकता है।** यह `try/except` में लपेटा गया है; किसी भी exception पर यह `null` के रूप में serializes करता है। जब मौजूद हो तो यह `{ decadal, yearly }` है। (वे sub-objects प्रलेखित placeholder से परे अतिरिक्त आंतरिक संरचना expose करते हैं — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, आदि।)
- **तारा strings brightness + 四化 को encode करते हैं।** प्रारूप है `name(brightness)[mutagen]`, प्रत्येक भाग optional — उदा. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, या plain `天機`। `adjective_stars` केवल plain names हैं (कोई brightness/mutagen नहीं)।

---

## शुद्धता स्तर

प्रत्येक आउटपुट समान आत्मविश्वास नहीं रखता। प्रत्येक स्तर को तदनुसार पढ़ें:

| स्तर | यह क्या कवर करता है | आत्मविश्वास |
|------|------------|---------|
| **सर्वोच्च** | ग्रहीय देशांतर, राशि, वक्र, साथ ही 紫微 तारा placement / 命宮·身宮 / 五行局 — शुद्ध ephemeris और calendar गणित। | खगोलीय रूप से/calendrically exact। |
| **उच्च, समय-निर्भर** | उदय (Ascendant), मध्य आकाश (Midheaven), सभी 12 भाव कुस्पी, वह भाव प्रत्येक ग्रह में पड़ता है, Human Design लाइनें, और 紫微 時辰 index। | Exact *एक सटीक जन्म समय दिया गया*; मिनटों के प्रति संवेदनशील। |
| **सत्यापित** | 紫微斗數 तारा brightness — py-iztro लाइब्रेरी के आउटपुट के साथ संरेखित। | लाइब्रेरी के विरुद्ध सत्यापित। |
| **झंडा सीमा ±0.3°** | कोई भी ग्रह / गेट / लाइन एक सीमा के ±0.3° के भीतर बैठता है। | अनंतिम के रूप में व्यवहार करें और प्रभाव को नोट करें — ±0.3° इसे सीमा के पार flip कर सकता है। |

---

## ज्ञात सीमाएं

- **कोई Chiron / मामूली निकाय नहीं।** बिल्ड Moshier ephemeris (`swe.FLG_MOSEPH`, कोई data files नहीं) का उपयोग करता है, जो Chiron या अन्य मामूली निकाय प्रदान नहीं करता है। केवल 10 शास्त्रीय ग्रह साथ चंद्र nodes की गणना की जाती है।
- **紫微斗數 एक डिफ़ॉल्ट स्कूल का उपयोग करता है।** py-iztro को निश्चित विकल्पों (`by_solar(..., True, 'zh-TW')`) के साथ कॉल किया जाता है; तारा-placement स्कूल और 四化 जो भी py-iztro डिफ़ॉल्ट है। यदि आप सामान्यतः 飛星 या किसी अन्य स्कूल का उपयोग करते हैं, तो मुख्य संरचना अपरिवर्तित है लेकिन कुछ विवरण भिन्न हो सकते हैं।
- **अनुमानित जन्म समय समय-निर्भर स्तर को degrade करता है।** यदि जन्म समय अनिश्चित है, तो उदय/MC/भाव assignments, Human Design लाइनें, और 時辰 — और उनसे व्युत्पन्न कुछ भी — unreliable हो जाते हैं। उस स्थिति में, **समय-निर्भर फील्ड को अनंतिम के रूप में व्यवहार करें** और उन पर भरोसा करने से पहले **event-based rectification** (ज्ञात जीवन events को चार्ट timing से मिलान) पर विचार करें।

---

## इसे एक AI एजेंट / Hermes से उपयोग करें

इच्छित integration मॉडल है **self-install**, SaaS नहीं।

एक उपयोगकर्ता इस रिपो की URL कॉपी करता है, और **उनके स्वयं के** एजेंट या CLI (Claude Code, Hermes, एक script, आदि) इसे क्लोन करता है और इसे **स्थानीय रूप से उपयोगकर्ता की machine पर चलाता है**। compute उपयोगकर्ता की ओर से होता है। कॉल करने के लिए कोई hosted endpoint नहीं है, कोई account नहीं है, और **कोई SaaS integration आवश्यक नहीं है** — इंजन एक stateless, deterministic, offline subprocess है।

क्योंकि प्रकाशक इसे नेटवर्क सेवा के रूप में संचालित नहीं करता है, किसी और के self-install के लिए प्रकाशक पर कोई §13 obligation नहीं पड़ता। (अलग से, §13 केवल एक ऑपरेटर को obligate करता है जो एक *modified* network-reachable संस्करण चलाता है — अपरिवर्तित स्थानीय उपयोग नहीं।)

एजेंटों के लिए, contract सरल है: workerdir में रिपो वenv Python के साथ `--json` subprocess को dispatch करें, stdout को JSON के रूप में parse करें, `ok` (और exit code) पर branch करें, फिर structured ऑब्जेक्ट को hand off करें। कोई cleanup आवश्यक नहीं — यह stateless है। पूर्ण CLI + JSON contract **[AGENTS.md](./AGENTS.md)** में रहता है।

### अपने AI एजेंट के लिए कॉपी-पेस्ट सेटअप

यह ब्लॉक सीधे Claude Code, ChatGPT, या किसी भी coding एजेंट में पेस्ट करें — यह एजेंट को बताता है कि टूल को कैसे install और कॉल करें:

```text
"life-chart-engine" को सेट अप और उपयोग करें — एक CLI जो जन्म डेटा से एक पश्चिमी जन्म चार्ट + Human Design + Zi Wei Dou Shu (紫微斗數) की गणना करता है।

1. Install करें (को `git` और `uv` की आवश्यकता है; यदि uv गायब है: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. एक चार्ट की गणना करें और stdout को JSON के रूप में पढ़ें:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. नियम:
   - आप जन्म शहर को --lat/--lon और सही ऐतिहासिक UTC offset (DST-aware) को resolve करते हैं। टूल geocode नहीं करता है।
   - पुष्टि करें कि जन्म समय सटीक है उदय, भाव, Human Design लाइनें, या Zi Wei घंटे pillar पर विश्वास करने से पहले।
   - कभी चार्ट मानों को fake न करें — हमेशा टूल को कॉल करें।
   - पूर्ण आउटपुट schema, exit codes, और एजेंट contract: ~/.life-chart-engine/AGENTS.md
```

---

## लाइसेंसिंग

यह रिपॉजिटरी **[AGPL-3.0](./LICENSE)** के तहत लाइसेंस प्राप्त है।

**AGPL-3.0 सादी अंग्रेजी में।** यह GNU GPL-3.0 है (एक मजबूत copyleft लाइसेंस: यदि आप सॉफ्टवेयर को distribute करते हैं, तो आपको अपने complete corresponding source को एक ही लाइसेंस के तहत release करना चाहिए) **साथ ही एक अतिरिक्त clause, Section 13**। §13 "SaaS loophole" को बंद करता है: GPL के *distribution* trigger से परे, यह जोड़ता है कि यदि आप प्रोग्राम को *modify* करते हैं और users को आपके modified version के साथ नेटवर्क पर interact करने देते हैं, तो आपको उन remote users को अपने corresponding source प्रदान करना चाहिए। (अपरिवर्तित upstream को नेटवर्क service के रूप में चलाना स्वयं में §13 को trigger नहीं करता है।) AGPL reciprocal है लेकिन boundlessly viral नहीं — यह केवल code तक पहुंचता है जो AGPL code का derivative है, या उसके साथ linked है।

**यह रिपो AGPL क्यों है।** इंजन **Swiss Ephemeris** (via `pyswisseph`) को ग्रहीय positions और भाव cusps के लिए link करता है। Astrodienst **dual-licenses** Swiss Ephemeris को **AGPL-3.0 OR एक commercial license** के रूप में, और इसके code को कुछ भी अधिक permissive के रूप में relicense नहीं किया जा सकता। क्योंकि AGPL copyleft है और यह project इसे link करता है, पूरा combined work अवश्य AGPL होना चाहिए। (`py-iztro` MIT है और कोई copyleft impose नहीं करता; Swiss Ephemeris यहां पूरे AGPL को force करने वाला एकमात्र component है।)

**व्यवहार में इसका क्या मतलब है।**

| आप करते हैं | AGPL obligation |
|----------|-----------------|
| **Self-install** (इसे स्वयं के लिए locally चलाएं) | §13 *नहीं* triggered है — कोई remote users नहीं हैं serve करने के लिए, और आपके पास पहले से source है। Clean। |
| **एक *modified* version को एक नेटवर्क service के रूप में चलाएं** | §13 *है* triggered — आपको उन remote users को अपने deployed version के complete corresponding source प्रदान करना चाहिए, AGPL के तहत, आपके modifications सहित। नोट: §13 का source-offer duty modification पर conditioned है — अपरिवर्तित upstream को नेटवर्क service के रूप में चलाना स्वयं में §13 को trigger नहीं करता, हालांकि source पहले से ही public है। |

**यदि नेटवर्क-source obligation आपके use case में fit नहीं करता:**

1. **AGPL रखें** — अपने complete corresponding source (modifications सहित) को किसी को भी publish करें जो इसे use करता है, नेटवर्क के over से per §13। मुफ्त, कोई negotiation नहीं।
2. **[Astrodienst](https://www.astro.com/swisseph/) से एक Swiss Ephemeris commercial license खरीदें** — यह Swiss Ephemeris portion के लिए AGPL obligation को lift करता है, आपको अपने code को relicense करने और एक closed build को ship/host करने देता है। (यह Astrodienst का dual-licensing मॉडल है।)
3. **ephemeris को swap करें** — `pyswisseph` को एक permissively licensed astronomy source से replace करें (उदा. **Skyfield (MIT)** plus public-domain **JPL DE440** ephemeris — illustrative alternatives, एकमात्र विकल्प नहीं)। Swiss Ephemeris gone के साथ, बाकी stack (py-iztro MIT, plus MPL-2.0/MIT/Apache deps) अब AGPL को force नहीं करता और पूरा repo MIT हो सकता है। यह real engineering प्रयास है: आपको Swiss Ephemeris से currently sourced हर चीज को reimplement करना चाहिए — ग्रहीय देशांतर, retrograde flags, Asc/MC, Placidus भाव cusps, और Human Design 88° design solver के inputs।

देखें **[CREDITS.md](./CREDITS.md)** पूर्ण attribution और per-dependency licenses के लिए।

---

## FAQ

**क्या मैं एक lunar date दर्ज कर सकता हूँ?**
नहीं। Inputs एक Gregorian solar date (`--date YYYY-MM-DD`) और घड़ी समय (`--time HH:MM`) हैं। यदि आपके पास केवल एक lunar date है, तो पहले इसे convert करें। 紫微斗數 py-iztro के solar entry point (`by_solar`) के via computed है।

**मेरा जन्म समय केवल अनुमानित है — क्या यह एक समस्या है?**
ग्रहीय positions ठीक हैं, लेकिन उदय, मध्य आकाश, भाव cusps, वह भाव प्रत्येक ग्रह में बैठता है, Human Design लाइनें, और 時辰 सभी समय-संवेदनशील हैं। इन्हें अनंतिम के रूप में व्यवहार करें और event-based rectification पर विचार करें उन पर भरोसा करने से पहले।

**Chiron / asteroids / मामूली निकाय कहाँ हैं?**
शामिल नहीं हैं। यहाँ उपयोग किया गया Moshier ephemeris उन्हें प्रदान नहीं करता है; केवल 10 शास्त्रीय ग्रह और चंद्र nodes की गणना की जाती है।

**कौन सा 紫微斗數 स्कूल यह उपयोग करता है?**
py-iztro द्वारा implemented default स्कूल (`by_solar(..., True, 'zh-TW')`)। स्कूल user-selectable नहीं है।

**क्या यह phone home करता है / नेटवर्क का उपयोग करता है?**
नहीं। इंजन पूरी तरह से offline है — कोई telemetry नहीं, कोई नेटवर्क calls नहीं, कोई side effects नहीं। यह एक stateless, deterministic one-shot subprocess है।

**क्या मैं इसे एक closed-source product के अंदर उपयोग कर सकता हूँ?**
AGPL-3.0 के तहत, हाँ private/local use के लिए। एक build को distribute करना GPL conveying/source obligations को trigger करता है, और एक *modified* build को नेटवर्क-serve करना AGPL §13 को trigger करता है — किसी भी तरह से आपको corresponding source प्रदान करना चाहिए। पूरी तरह से closed-source जाने के लिए, या तो Astrodienst से एक Swiss Ephemeris commercial license खरीदें या ephemeris को Skyfield + JPL DE440 पर swap करें (देखें [Licensing](#licensing))।

---

## अस्वीकरण

`life-chart-engine` एक **interpretive self-awareness framework है, prediction या fatalism नहीं**। आउटपुट reflection के लिए structured reference बिंदु हैं — वे events को foretell नहीं करते हैं और outcomes को determine नहीं करते हैं। इन्हें calibration के रूप में उपयोग करें, आपके स्वयं के lived experience को final authority के रूप में। यहाँ कुछ भी medical, legal, psychological, या financial सलाह नहीं है। उन domains में decisions के लिए, एक qualified professional से consult करें।

---

## Credits & License

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, dual-licensed AGPL-3.0 / commercial (<https://www.astro.com/swisseph/>).
- **py-iztro** (and upstream `iztro`) — MIT, for 紫微斗數.
- पूर्ण attribution: **[CREDITS.md](./CREDITS.md)**.
- **License:** [AGPL-3.0](./LICENSE).
- **Agent / JSON contract:** [AGENTS.md](./AGENTS.md).
