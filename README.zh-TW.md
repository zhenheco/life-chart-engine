> 🌐 [English](./README.md) · **繁體中文** · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**確定性原生計算三個生命圖表系統 — 西洋本命星盤、人類圖 (Human Design) 和紫微斗數 — 從單一出生資料中計算。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#為什麼特別需要-cpython-312)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#常見問題)

`life-chart-engine` 是一個小型、離線的命令列工具。你給它一個人的出生資料 — 日期、時間、時區和地點座標 — 它就會在一次執行中計算三個獨立的圖表系統，然後輸出人類可讀的 Markdown 報告或結構化的 JSON 物件供程式和 AI 代理使用。

它是為想要**可重現、可驗證**的圖表計算的人設計的，而不是黑盒網頁應用：從業者、開發自我認知工具的開發者，以及需要純計算步驟的 AI 代理。每個數字都來自真實的天文計算 和真實的紫微斗數程式庫 (iztro) — 不來自遠端服務、不來自快取查詢，也從不透過網路。

---

## 它計算什麼

引擎針對**同一個出生時刻**執行三個系統，所以它們的輸出可以相互驗證。每個系統回答一種不同的問題：

| 系統 | 它是什麼（平白易懂的說法） | 引擎產出 |
|--------|--------------------------|---------|
| **西洋本命** (Tropical / Placidus) | 經典西洋星座占星學 — 你出生時行星相對於黃道帶的位置，分為 12 宮。 | 上升點 + 中天，12 個行星/重要點 (太陽 → 南交點) 附帶星座、度數、宮位和逆行旗標，所有 12 個宮位尖度，以及每個偵測到的相位 (合相/六分/四分/三分/對分) 按精度排序。 |
| **人類圖 Human Design** | 占星學、易經和脈輪系統的現代綜合。描述你的能量如何透過閘門、通道和能量中心「連接」。 | 類型、權威、角色、定義、輪迴交叉、88° 之前的設計日期、已定義/開放的能量中心、已定義的通道，以及人格圖和設計圖的每顆行星閘門.線啟動。 |
| **紫微斗數 Zi Wei Dou Shu** | 傳統中式占星系統，將命運映射到一個 12 宮盤上，填入具名星曜。 | 五行局、命主/身主、時辰指數，以及每宮的資料 — 天干地支、命/身旗標、年代範圍、主星/次星/輔星 (附帶廟陷和四化)。選擇性提供盡力而為的大限/流年運勢。 |

人類圖中的類型、權威和定義**不是硬編碼的** — 它們來自已定義能量中心的連接圖。

---

## 為什麼是原生計算

這個引擎做真實的數學而不是近似或呼叫服務。這個選擇帶來三個對任何嚴肅圖表工具都重要的特性：

- **確定性。** 同樣的出生輸入總是產生同樣的輸出，逐位元組相同。沒有隨機性、沒有模型、沒有執行間的舍入誤差。
- **可重現。** 任何人拿著這個倉庫和相同的輸入都可以重新生成你的確切圖表。計算使用 astronomy-engine 作為天空資料，用 iztro 作為紫微斗數 — 兩個都是確定性的。
- **可交叉驗證。** 因為三個獨立系統都從一個出生時刻計算，你可以三角測量。**當所有三個系統指向同一個信號時，視之為高度信心。當只有一個系統顯示一個細節時，視之為參考點，不是結論。** 這是引擎的核心設計原則 — 它產出交叉閱讀的事實，不是單一裁決。

---

## 快速開始

### 一行安裝 (推薦)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

安裝到 `~/.life-chart-engine`（可用 `LIFE_CHART_DIR` 覆寫）。不需要 `sudo`，不做系統層級變更 — 它只會 clone repo、建立隔離的 CPython 3.12 venv，並產生固定版本的 iztro Node bundle。需要 `git`、[`uv`](https://docs.astral.sh/uv/) 和 Node.js/npm。可隨時重新執行以更新到最新版本。

### 從原始碼

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` 做什麼

它在 `set -euo pipefail` 下執行並進行六個步驟：

1. **解析虛擬環境位置** — `${LIFE_VENV:-<repo>/.venv}`。設定 `LIFE_VENV` 環境變數以覆蓋；預設 `.venv/` 被 git 忽略。
2. **飛行前檢查：需要 [`uv`](https://docs.astral.sh/uv/)** — 如果 `uv` 不在 `PATH` 上，它會以 `1` 退出並列印安裝提示：
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **建立 CPython 3.12 虛擬環境** — `uv venv --python 3.12 "$VENV"` (參看 [為什麼特別需要 CPython 3.12](#為什麼特別需要-cpython-312))。
4. **安裝固定的依賴項** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`。
5. **建立固定版本的 iztro bundle** — 執行 `scripts/build-iztro-bundle.sh`，它會把 `iztro@2.5.8` 安裝到暫存 build 目錄，並輸出 `vendor/iztro.cjs`。
6. **執行 smoke test** — 用固定範例輸入執行引擎一次（丟棄 stdout），成功時印出 `OK — engine runs.`。它也會印出兩種模式的使用提示。

### 手動 `uv` 步驟 (無 `setup.sh`)

```bash
# 1. 建立 CPython 3.12 虛擬環境 (預設 <repo>/.venv；用 LIFE_VENV 覆蓋)
uv venv --python 3.12 .venv

# 2. 安裝固定的依賴項
uv pip install --python .venv/bin/python -r requirements.txt

# 3. 建立固定版本的 iztro bundle
bash scripts/build-iztro-bundle.sh

# 4.（選用）smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Python 直接依賴項固定在 `requirements.txt` 中：

```
astronomy-engine>=2.1.19
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei 使用由 `scripts/build-iztro-bundle.sh` 產生並固定版本的 Node bundle：

```
iztro@2.5.8
```

---

## 為什麼特別需要 CPython 3.12

引擎目前執行在已驗證的 **CPython 3.12** runtime 上。原因在 `requirements.txt` 和 `setup.sh` 中的敘述相同：

> 此變更仍鎖定 CPython 3.12。舊的 Python Zi Wei 原生依賴限制已經消失，因此可在檢查剩餘依賴與部署映像後重新評估。

簡言之：3.12 仍是此版本已測試的 runtime。Zi Wei 依賴不再強制這個鎖定，因此升級 Python 版本是後續相容性檢查，而不是此次重構的一部分。

---

## 使用方式

引擎有兩種模式，由 `--json` 旗標的有無選擇。

### 人類模式 (Markdown)

省略 `--json` 以取得可讀的主控台報告。使用你的虛擬環境 Python：

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

修剪過的真實範例 (相位在 Markdown 模式中限制在前 10 個)：

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

【紫微斗數 iztro】
五行局 土五局 ｜ 命主 祿存 ｜ 身主 火星
  命宮   戊寅  (5-14): 七殺(廟)｜天廚 蜚廉
  父母   己卯  (115-124): 天同(平)[忌]｜地劫 天喜 咸池 恩光 天德
  ...
```

### 代理模式 (JSON)

加上 `--json` 以在 stdout 上取得一個 JSON 物件，除此之外什麼都沒有 — 適合程式和 AI 代理：

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

修剪過的真實範例 (陣列截斷為 1–2 個項目；值逐字)：

```json
{
  "ok": true,
  "schema_version": "1.1",
  "input": {
    "name": "小明", "gender": "女",
    "date": "1990-06-15", "time": "08:30",
    "tz_offset": 8.0, "lat": 25.033, "lon": 121.5654,
    "target": "2025-01-01"
  },
  "western": {
    "system": "Tropical / Placidus / astronomy-engine",
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
    "horoscope": {
      "decadal": {
        "name": "大限", "heavenlyStem": "丁", "earthlyBranch": "亥",
        "ageRange": [33, 42],
        "palaceNames": ["...12..."],
        "mutagen": ["太陰", "天同", "天機", "巨門"],
        "mutagenTyped": [
          { "star": "太陰", "type": "祿" }, { "star": "天同", "type": "權" },
          { "star": "天機", "type": "科" }, { "star": "巨門", "type": "忌" }
        ]
      },
      "yearly": {
        "name": "流年",
        "mutagen": ["...4, fixed 祿/權/科/忌 order..."],
        "mutagenTyped": [{ "star": "...", "type": "祿|權|科|忌" }, "...4..."]
      },
      "age": {
        "name": "小限", "nominalAge": 26,
        "mutagen": ["...4..."],
        "mutagenTyped": [{ "star": "...", "type": "祿|權|科|忌" }, "...4..."]
      }
    }

  },
  "meta": { "engine": "life-chart-engine", "version": "1.0", "ephemeris": "astronomy-engine" }
}
```

---

## CLI 旗標參考

**沒有 `required=True` 旗標** — argparse 對於缺少的旗標永遠不會出錯。省略 `--date`/`--time`/`--tz`/`--lat`/`--lon` 會無聲地回退到一個內建的範例人 (`範例`，生於 `2000-01-01 12:00`，UTC+8，台北 101)。所以為了正確的圖表，提供所有旗標。

| 旗標 | 型別 | 正確使用必需？ | 預設值 | 格式 / 規則 |
|------|------|-------------|--------|-----------|
| `--name` | 字串 | 否 (裝飾用) | `"範例"` | 自由文字；只回應到輸出中。 |
| `--gender` | 字串 | 僅對紫微 | `"女"` | 必須正好是 `男` 或 `女` (argparse `choices`；其他任何東西 → 退出 `2`)。 |
| `--date` | 字串 | **是** | 回退到 `2000-01-01` | `YYYY-MM-DD`，以 `-` 分割。無零填充要求。 |
| `--time` | 字串 | **是** | 回退到 `12:00` | `HH:MM`，24 小時當地時鐘時間，以 `:` 分割。 |
| `--tz` | 浮點數 | **是** | 回退到 `8.0` | UTC 偏移量包括夏令時 (台灣 = `8`)。寫入輸入鍵 `tz_offset`。 |
| `--lat` | 浮點數 | **是** | 回退到 `25.0330` | 緯度，十進位度 (西洋宮位/上升/中天)。 |
| `--lon` | 浮點數 | **是** | 回退到 `121.5654` | 經度，十進位度。 |
| `--target` | 字串 | 否 | `"2025-01-01"` | `YYYY-MM-DD`；紫微運限參考日期 (運限參考日)。 |
| `--json` | 旗標 | 否 | `False` (Markdown) | 有無 → JSON 模式；無 → Markdown。不帶值。 |

> 引擎**不**進行地理編碼或查詢時區。呼叫者必須自己轉換地點 → `lat`/`lon`/`tz` — 時區/夏令時是最常見的錯誤來源，所以驗證在出生地和出生日期適用的 UTC 偏移量。

---

## 輸出參考

`--json` 信封有七個頂級鍵，按此順序：

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| 區塊 | 摘要 |
|------|------|
| `ok` | 成功時 `true` (`false` 在錯誤信封中)。 |
| `schema_version` | `"1.1"`。 |
| `input` | 標準化輸入的回應：`name`、`gender`、`date`、`time`、`tz_offset`、`lat`、`lon`、`target` (注意 `tz_offset`，不是 `tz`)。 |
| `western` | `system` 字串、`ascendant`/`midheaven` 位置物件、`planets[]`、`houses[]` (×12)、`aspects[]`。 |
| `human_design` | `type`、`authority`、`profile`、`definition`、`incarnation_cross`、`design_date`、`defined_centers[]`、`open_centers[]`、`channels[]`、`gates[]`。 |
| `ziwei` | `five_elements_class`、`soul`、`body`、`hour_index`、`palaces[]`、`horoscope` (物件或 `null`)。 |
| `meta` | `{ engine, version, ephemeris }` — 全部字面值 (`ephemeris: "astronomy-engine"`). |

對於完整欄位合約 — 每個鍵、型別和代理呼叫協議 — 參看 **[AGENTS.md](./AGENTS.md)**。

### 值得知道的欄位怪異性

- **`aspects` 在 JSON 中**不**被限制**。JSON 路徑返回*每個*偵測到的相位，按軌度昇序排序 (最精密優先)。10 項上限僅存在於 Markdown 報告中。
- **`ziwei.horoscope` 是盡力而為的，可能是 `null`**。它被包裝在 `try/except` 中；任何異常時它序列化為 `null`。當存在時它是 `{ decadal, yearly }`。(那些子物件展示額外的內部結構 — `index`、`mutagen[]`、`stars[][]`、`yearly_dec_star` 等 — 超越記錄的佔位符。)
- **星曜字串編碼廟陷 + 四化。** 格式是 `name(brightness)[mutagen]`，每部分可選 — 例如 `紫微(廟)[祿]`、`紫微(廟)`、`天機[祿]` 或普通 `天機`。`adjective_stars` 只是普通名稱 (無廟陷/四化)。

---

## 精度層級

不是每個輸出都帶著相同的信心。據各層級閱讀：

| 層級 | 它涵蓋什麼 | 信心 |
|------|---------|------|
| **最高** | 行星經度、星座、逆行，加上紫微星曜位置/命宮·身宮/五行局 — 純天文和曆法數學。 | 天文/曆法上完全準確。 |
| **高、時間相關** | 上升點、中天、所有 12 個宮位尖度、每顆行星落在的宮位、人類圖線，以及紫微時辰指數。 | 確切*給定*準確的出生時間；對分鐘敏感。 |
| **已驗證** | 紫微斗數星曜廟陷 — 與 iztro 程式庫輸出對齐。 | 根據程式庫驗證。 |
| **旗標邊界 ±0.3°** | 任何行星/閘門/線坐在邊界的 ±0.3° 內。 | 視為暫定，並注意影響 — ±0.3° 可以在邊界上翻轉它。 |

---

## 已知限制

- **沒有凱龍/小行星。** 目前 adapter 只輸出 10 個經典行星加月交點。
- **紫微斗數使用一個預設學派。** iztro 用固定選項呼叫 (`bySolar(..., True, 'zh-TW')`)；星曜位置學派和四化是 iztro 預設的。如果你通常使用飛星或另一個學派，主要結構不變但某些細節可能不同。
- **近似出生時間降級時間相關層級。** 如果出生時間不確定，上升點/中天/宮位指派、人類圖線和時辰 — 以及任何衍生自它們的東西 — 變成不可靠。在那種情況下，**視時間相關欄位為暫定**，並考慮**事件型複調** (將已知的人生事件與圖表時機匹配) 在依賴它們之前。

---

## 從 AI 代理 / Hermes 使用它

預期的整合模型是**自行安裝**，不是 SaaS。

一個使用者複製這個倉庫的 URL，並讓**他們自己的**代理或 CLI (Claude Code、Hermes、一個指令碼等) 在使用者的機器上**本地複製和執行它**。計算發生在使用者一側。沒有託管端點可以呼叫、沒有帳戶、**沒有 SaaS 整合必需** — 引擎是一個無狀態、確定性、離線的子程序。

發佈者不營運此工具作為網路服務。依 MIT 條款，本地使用、修改、散布與託管使用都可以，細節見 `LICENSE`。

對於代理，合約很簡單：在倉庫工作目錄中用虛擬環境 Python 分派 `--json` 子程序，將 stdout 解析為 JSON，根據 `ok` (和退出碼) 分支，然後交付結構化物件。無需清理 — 它是無狀態的。完整的 CLI + JSON 合約在 **[AGENTS.md](./AGENTS.md)** 中。

### 為你的 AI 代理複製貼上設定

直接粘貼這個區塊到 Claude Code、ChatGPT 或任何編碼代理 — 它告訴代理如何安裝和呼叫工具：

```text
設定並使用 "life-chart-engine" — 一個從出生資料計算西洋本命星盤 +
人類圖 + 紫微斗數 (Zi Wei Dou Shu) 的 CLI。

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. 計算一個圖表並將 stdout 讀為 JSON：
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. 規則：
   - 你解析出生城市到 --lat/--lon 和正確的歷史 UTC
     偏移量 (考慮夏令時)。工具不進行地理編碼。
   - 在信任上升點、宮位、人類圖線或紫微時辰柱之前
     確認出生時間是否準確。
   - 永遠不要偽造圖表值 — 總是呼叫工具。
   - 完整的輸出模式、退出碼和代理合約：~/.life-chart-engine/AGENTS.md
```

---

## 授權

此倉庫以 **[MIT](./LICENSE)** 授權。

引擎使用 **astronomy-engine (MIT)** 進行天文計算，並使用 **iztro (MIT)** 進行紫微斗數計算。Placidus 宮位公式與 Meeus 參考書目列在 [CREDITS.md](./CREDITS.md)。

你可以依 MIT 條款使用、複製、修改、散布、再授權和銷售副本。請在軟體的實質部分保留 copyright 與 permission notice。

完整致謝與依賴授權請見 **[CREDITS.md](./CREDITS.md)**。

---

## 常見問題

**我可以輸入陰曆日期嗎？**
否。輸入是格里高曆太陽日期 (`--date YYYY-MM-DD`) 和時鐘時間 (`--time HH:MM`)。如果你只有陰曆日期，先轉換它。紫微斗數透過 iztro 的太陽進入點 (`bySolar`) 計算。

**我的出生時間只是近似的 — 那是問題嗎？**
行星位置沒問題，但上升點、中天、宮位尖度、每顆行星坐在的宮位、人類圖線和時辰都是時間敏感的。視那些為暫定，並在依賴它們之前考慮事件型複調。

**凱龍/小行星/小行星在哪？**
不包括。目前 adapter 只輸出 10 個經典行星和月交點。

**它使用哪個紫微斗數學派？**
iztro 實作的預設學派 (`bySolar(..., True, 'zh-TW')`)。學派不是使用者可選的。

**它會打回家/使用網路嗎？**
否。引擎完全離線 — 無遙測、無網路呼叫、無副作用。它是一個無狀態、確定性的一次性子程序。

**我可以在關閉來源產品中使用它嗎？**
可以。此倉庫以 MIT 授權；請在軟體的實質部分保留 copyright 與 permission notice。

---

## 免責聲明

`life-chart-engine` 是一個**詮釋性自我認知框架，不是預測或命定主義**。輸出是反思的結構化參考點 — 它們不預言事件也不決定結果。用它們作為校準，以你自己的生活經驗為最終權威。這裡的任何東西都不是醫學、法律、心理或財務建議。對於這些領域的決定，請諮詢合格的專業人士。

---

## 認可與授權

- **astronomy-engine** — Don Cross，MIT；天文計算。
- **Meeus, Astronomical Algorithms** — Placidus 宮位公式參考。
- **iztro** — MIT，用於紫微斗數。
- 完整屬性：**[CREDITS.md](./CREDITS.md)**。
- **授權：** [MIT](./LICENSE)。
- **代理 / JSON 合約：** [AGENTS.md](./AGENTS.md)。
