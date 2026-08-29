# Gate 19 中心歸屬修正（情緒 → 根）— 影響說明

- 日期：2026-08-30
- 變更：`scripts/chart_engine.py` 的 `GATE_CENTER` 把人類圖閘門 19 由「情緒」（Solar Plexus）改為「根」（Root）
- 影響面：**既有單人盤的已定義/開放中心與 Definition（分人）**，以及合盤的人類圖側

## 機制（一句話）

`human_design()` 在通道完整時用 `GATE_CENTER` 把兩端閘門對應的中心加入連通圖；`CHANNELS` 含 `(19,49)`，
而 19 原本被錯歸「情緒」，使該通道成為「情緒↔情緒」自環，無法把「根」中心定義起來。修正後它是「根↔情緒」。

## 錯誤如何被確認

逐中心點算閘門數。其他八個中心全部符合標準人類圖，只有兩個不符，且剛好差一個：

| 中心 | 修正前 | 修正後 | 標準 |
|---|---|---|---|
| 情緒 Solar Plexus | 8 | 7 | 7 |
| 根 Root | 8 | 9 | 9 |
| 頭 3 / 邏輯 6 / 喉 11 / G 8 / 意志 4 / 薦骨 9 / 脾 7 | 相同 | 相同 | 相同 |

總計 64 個閘門不變，錯位的只有 19 這一個。

## 量化影響（n=5000 隨機出生資料，1940–2010，UTC+8，台北）

| 輸出欄位 | 受影響 | 比例 |
|---|---|---|
| 已定義中心 `defined` | 241 | **4.82%** |
| 開放中心 `open` | 241 | **4.82%** |
| Definition 分人 `definition` | 172 | **3.44%** |
| Type `htype` | 0 | 0% |
| Authority `auth` | 0 | 0% |
| Profile / Cross / 通道 `chans` / Design | 0 | 0% |

變更範例：

- `1995-05-29 06:56` 已定義中心多出「根」
- `1999-01-21 09:36` 三分人 → 二分人（通道 `(3,60) (4,63) (19,49) (27,50)`；已定義中心集合前後相同，
  改變的是 19-49 由自環變成「根↔情緒」的邊，把兩個分量併起來）
- `1950-01-25 06:39` 四分人 → 三分人

## 為什麼含閘門 19 的人多、真正受影響的人少

樣本中 **32.44%（1622/5000）的盤含有閘門 19**，但只有 4.82% 的輸出改變。
改變需要的是**完整的 19-49 通道**，不是單一閘門；只有 19 沒有 49 時，19 仍是懸掛閘門，不定義任何中心。

未受影響的實例（含閘門 19、Definition 與中心完全不變）：

- `1953-04-20 19:16` — 三分人，通道 `(3,60) (4,63) (24,61) (25,51) (27,50)`，不含 19-49
- `1948-11-01 13:01` — 二分人，通道 `(11,56) (26,44)`
- `2003-04-13 14:00` — 三分人，通道 `(12,22) (24,61) (32,54)`

## 為什麼 Type 與 Authority 是 0%（結構上的必然，不是抽樣不足）

修正前，19-49 雖然是「情緒↔情緒」自環，但 `defined.add()` 對通道兩端都執行，所以**情緒中心本來就已被
這條通道定義**、本來就是 motor；自環只是在連通圖上不連任何邊（`adj` 僅在 `c1 != c2` 時加邊）。
修正後多出的是「根↔情緒」這條**邊**，不是多出一個 motor 來源：該連通分量的 motor 集合與對「喉」的
可達性都沒變，而 Authority 階層中情緒最高、該分量本來就含情緒。因此 Type 與 Authority 不動，
真正改變的是中心之間的**連通性**，也就是分人數。

## Golden fixture 為何零差異

`--example`（範例人）與 `examples/sample-input.json`（小明）兩張盤都含閘門 19，但**都沒有完整的 19-49 通道**，
所以修正後 `tests/fixtures/golden_example.json`、`golden_example.md`、`examples/sample-output.json`
重新產生後與既有檔案**位元組完全相同**（並經連續兩次生成驗證決定性）。
`tests/fixtures/golden_example_pre_1_2.json` 是 1.2 bump 的變更前 oracle，本次未重新產生。

## 對既有使用者的意義

線上服務在本修正部署前，對那 4.82% 的使用者回報的已定義/開放中心是錯的，其中 3.44% 的 Definition
（幾分人）也是錯的。部署後這些人的結果會改變；Type 與 Authority 不會變。

## 量測重現方式

以下腳本只在記憶體中把 `GATE_CENTER[19]` 翻回 `'情緒'` 當 before，不修改任何檔案。
存成任意檔名後於 repo 根目錄執行 `.venv/bin/python <檔名>`：

```python
import sys, pathlib, importlib.util, random, datetime, collections
sys.path.insert(0, str(pathlib.Path("scripts").resolve()))
spec = importlib.util.spec_from_file_location("ce", "scripts/chart_engine.py")
ce = importlib.util.module_from_spec(spec); spec.loader.exec_module(ce)
assert ce.GATE_CENTER[19] == '根'

random.seed(19)
cases = []
for _ in range(5000):
    d = datetime.date(1940, 1, 1) + datetime.timedelta(days=random.randrange(0, 25567))
    cases.append({"date": (d.year, d.month, d.day),
                  "time": (random.randrange(24), random.randrange(60)),
                  "tz_offset": 8.0, "lat": 25.033, "lon": 121.5654,
                  "name": "x", "gender": "男"})

def snap():
    out = []
    for inp in cases:
        jd = ce.jd_of(inp["date"], inp["time"], inp["tz_offset"])
        sun, _ = ce.eph.body_lon_speed(jd, '太陽')
        out.append(ce.human_design(inp, sun))
    return out

after = snap()
ce.GATE_CENTER[19] = '情緒'
before = snap()
ce.GATE_CENTER[19] = '根'

diff = collections.Counter()
for b, a in zip(before, after):
    for k in after[0]:
        if b.get(k) != a.get(k):
            diff[k] += 1
for k in after[0]:
    print(f"{k:12s} {diff.get(k, 0):5d}  {100 * diff.get(k, 0) / len(cases):.2f}%")
```
