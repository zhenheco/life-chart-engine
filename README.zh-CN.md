> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · **简体中文** · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**一个确定性本地计算引擎，支持三种生命图表系统 —— 西方本命星盘、人类图 (Human Design) 和紫微斗数 —— 从单一出生记录生成。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` 是一个小型、离线的命令行工具。给它一个人的出生数据 —— 日期、时间、时区和地点坐标 —— 它将在一次运行中计算三个独立的图表系统，然后输出易读的 Markdown 报告或结构化的 JSON 对象供程序和 AI 代理使用。

它专为那些想要**可重现、可验证**的图表计算（而不是黑箱 Web 应用）的用户而设计：实践者、构建自我意识工具的开发者，以及需要纯计算步骤的 AI 代理。每个数字都来自真实的天文计算和真实的紫微斗数库（iztro）—— 不来自远程服务、不来自缓存查询，永远不经过网络。

---

## 它计算什么

该引擎针对**同一个出生时刻**运行三个系统，因此它们的输出可以相互印证。每个系统回答不同类型的问题：

| 系统 | 定义（通俗语言） | 引擎输出 |
|--------|----------------------------|------------------------|
| **西方本命星盘** (热带/Placidus) | 古典西方占星学 —— 你出生时行星在黄道带对比的位置，分为 12 个宫。 | 上升点 + 中天，12 个行星/点（太阳 → 南交点）的星座、度数、宫位和逆行标志、全部 12 个宫头，以及每个检测到的相位（合相/六分/四分/三分/对分）按紧密度排序。 |
| **人类图** (Human Design) | 占星学、易经和脉轮系统的现代综合。描述你的能量如何通过门、通道和中心进行"接线"。 | 类型、权威、角色、定义、轮回交叉、88°较早的设计日期、已定义/开放的中心、已定义的通道，以及人格和设计两个图表的每个行星门.线激活。 |
| **紫微斗数** | 一个传统中国占星术系统，将命运映射到 12 宫盘，由命名的星曜填充。 | 五行局、命主 / 身主、时辰指数，以及每个宫的数据 —— 干支、命/身标志、十年年龄范围，和主星/副星/辅星（带亮度和四化）。可选的最佳效果大限/流年运势。 |

人类图中的类型、权威和定义**不是硬编码的** —— 它们是从已定义中心的连接图推导出来的。

---

## 为什么选择本地计算

该引擎进行真实的数学计算而不是近似或调用服务。这个选择为任何严肃的图表工具带来三个重要属性：

- **确定性。** 相同的出生输入总是产生相同的输出，字节对字节。没有随机性、没有模型、没有运行之间的舍入漂移。
- **可重现性。** 任何拥有仓库和相同输入的人都能重新生成你的精确图表。计算使用 astronomy-engine用于天空，iztro 用于紫微斗数 —— 两者都是确定性的。
- **跨系统可验证性。** 因为三个独立的系统是从一个出生时刻计算的，你可以三角验证。**当所有三个系统都指向同一个信号时，将其视为高信心。当只有一个系统显示一个细节时，将其视为参考点，而非结论。** 这是该引擎的核心设计原则 —— 它产生供交叉阅读的事实，而不是单一的判决。

---

## 快速开始

### 一行命令安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

安装到 `~/.life-chart-engine`（可用 `LIFE_CHART_DIR` 覆盖）。不需要 `sudo`，不做系统级更改 —— 它只会克隆仓库、构建隔离的 CPython 3.12 venv，并生成固定版本的 iztro Node bundle。需要 `git`、[`uv`](https://docs.astral.sh/uv/) 和 Node.js/npm。可随时重新运行以更新到最新版本。

### 从源代码

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` 做什么

它在 `set -euo pipefail` 下运行并执行六个步骤：

1. **解析 venv 位置** —— `${LIFE_VENV:-<repo>/.venv}`。设置 `LIFE_VENV` 环境变量以覆盖；默认 `.venv/` 被 git 忽略。
2. **预检：需要 [`uv`](https://docs.astral.sh/uv/)** —— 如果 `uv` 不在 `PATH` 上，它退出 `1` 并打印安装提示：
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **创建 CPython 3.12 venv** —— `uv venv --python 3.12 "$VENV"`（见 [为什么是 CPython 3.12](#why-cpython-312-specifically)）。
4. **安装固定依赖** —— `uv pip install --python "$VENV/bin/python" -r requirements.txt`。
5. **构建固定版本的 iztro bundle** —— 运行 `scripts/build-iztro-bundle.sh`，它会把 `iztro@2.5.8` 安装到临时构建目录，并输出 `vendor/iztro.cjs`。
6. **运行冒烟测试** —— 使用固定示例输入执行一次引擎（丢弃 stdout），成功时打印 `OK — engine runs.`。它还会打印两种模式的使用提示。

### 手动 `uv` 步骤（无 `setup.sh`）

```bash
# 1. 创建 CPython 3.12 venv（默认 <repo>/.venv；使用 LIFE_VENV 覆盖）
uv venv --python 3.12 .venv

# 2. 安装固定依赖
uv pip install --python .venv/bin/python -r requirements.txt

# 3. 构建固定版本的 iztro bundle
bash scripts/build-iztro-bundle.sh

# 4.（可选）冒烟测试
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Python 直接依赖固定在 `requirements.txt` 中：

```
astronomy-engine>=2.1.19
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei 使用由 `scripts/build-iztro-bundle.sh` 生成并固定版本的 Node bundle：

```
iztro@2.5.8
```

---

## 为什么特别选择 CPython 3.12

引擎目前运行在已验证的 **CPython 3.12** runtime 上。原因在 `requirements.txt` 和 `setup.sh` 中的描述相同：

> 此更改仍锁定 CPython 3.12。旧的 Python Zi Wei 本地依赖约束已经消失，因此可在检查剩余依赖和部署镜像后重新评估。

简单来说：3.12 仍是此版本已测试的 runtime。Zi Wei 依赖不再强制这个锁定，因此升级 Python 版本是后续兼容性检查，而不是此次重构的一部分。

---

## 使用

引擎有两种模式，由 `--json` 标志的存在选择。

### 人类模式（Markdown）

省略 `--json` 获得可读的控制台报告。使用你的 venv Python：

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

修剪的真实示例（相位在 Markdown 模式中上限为前 10 个）：

```
### Sample｜女｜1990-06-15 08:30 (UTC+8)

【西洋星盘 Tropical/Placidus】
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

### 代理模式（JSON）

添加 `--json` 获得一个 JSON 对象在 stdout 上，其他无 —— 理想用于程序和 AI 代理：

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

修剪的真实示例（数组截断为 1-2 项；值按原样）：

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

## CLI 标志参考

**没有 `required=True` 标志** —— argparse 在遗漏时从不出错。省略 `--date`/`--time`/`--tz`/`--lat`/`--lon` 会默认回退到内置示例人物（`範例`，出生 `2000-01-01 12:00`，UTC+8，台北 101）。因此为了正确的图表，提供全部标志。

| 标志 | 类型 | 正确使用时必需？ | 默认值 | 格式 / 规则 |
|------|------|---------------------------|---------|---------------|
| `--name` | string | 否（仅美观） | `"範例"` | 自由文本；仅回显到输出。 |
| `--gender` | string | 仅紫微需要 | `"女"` | 必须恰好是 `男` 或 `女`（argparse `choices`；其他 → 退出 `2`）。 |
| `--date` | string | **是** | 回退到 `2000-01-01` | `YYYY-MM-DD`，用 `-` 分割。不需要补零。 |
| `--time` | string | **是** | 回退到 `12:00` | `HH:MM`，24 小时本地时钟时间，用 `:` 分割。 |
| `--tz` | float | **是** | 回退到 `8.0` | UTC 偏移包括夏令时（台湾 = `8`）。写入输入键 `tz_offset`。 |
| `--lat` | float | **是** | 回退到 `25.0330` | 十进制度的纬度（西方宫位/上升点/中天）。 |
| `--lon` | float | **是** | 回退到 `121.5654` | 十进制度的经度。 |
| `--target` | string | 否 | `"2025-01-01"` | `YYYY-MM-DD`；紫微运限参考日期。 |
| `--json` | flag | 否 | `False`（Markdown） | 存在 → JSON 模式；不存在 → Markdown。不接受值。 |

> 引擎**不**进行地理编码或查询时区。调用者必须自己转换地点 → `lat`/`lon`/`tz` —— 而且时区/夏令时是最常见的错误来源，所以验证在出生地点和出生日期适用的 UTC 偏移。

---

## 输出参考

`--json` 包装有七个顶级键，按此顺序：

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| 块 | 摘要 |
|-------|---------|
| `ok` | 成功时 `true`（错误包装时 `false`）。 |
| `schema_version` | `"1.1"`。 |
| `input` | 规范化输入的回显：`name`、`gender`、`date`、`time`、`tz_offset`、`lat`、`lon`、`target`（注意 `tz_offset`，不是 `tz`）。 |
| `western` | `system` 字符串、`ascendant`/`midheaven` 位置对象、`planets[]`、`houses[]`（×12）、`aspects[]`。 |
| `human_design` | `type`、`authority`、`profile`、`definition`、`incarnation_cross`、`design_date`、`defined_centers[]`、`open_centers[]`、`channels[]`、`gates[]`。 |
| `ziwei` | `five_elements_class`、`soul`、`body`、`hour_index`、`palaces[]`、`horoscope`（对象或 `null`）。 |
| `meta` | `{ engine, version, ephemeris }` —— 全部字面值 (`ephemeris: "astronomy-engine"`). |

完整字段合约 —— 每个键、类型和代理调用协议 —— 见 **[AGENTS.md](./AGENTS.md)**。

### 值得了解的字段怪癖

- **`aspects` 在 JSON 中不受限制。** JSON 路径返回*每个*检测到的相位，按幅度升序排序（最紧密优先）。10 项上限仅存在于 Markdown 报告中。
- **`ziwei.horoscope` 是尽力而为的，可能是 `null`。** 它被包装在 `try/except` 中；任何异常时它序列化为 `null`。存在时是 `{ decadal, yearly }`。（这些子对象暴露额外的内部结构 —— `index`、`mutagen[]`、`stars[][]`、`yearly_dec_star` 等 —— 超出记录的占位符。）
- **星曜字符串编码亮度 + 四化。** 格式是 `name(brightness)[mutagen]`，每部分可选 —— 例如 `紫微(廟)[祿]`、`紫微(廟)`、`天機[祿]` 或纯 `天機`。`adjective_stars` 仅为纯名称（无亮度/四化）。

---

## 准确性层级

并非每个输出都有相同的信心。根据每个层级相应阅读：

| 层级 | 涵盖内容 | 信心 |
|------|----------------|------------|
| **最高** | 行星黄经、星座、逆行，加上紫微星曜位置 / 命宫·身宫 / 五行局 —— 纯天文和历法数学。 | 天文/历法精确。 |
| **高，时间依赖** | 上升点、中天、全部 12 个宫头、每颗行星所在的宫、人类图线，以及紫微时辰指数。 | 精确*给定*准确的出生时间；对分钟敏感。 |
| **已验证** | 紫微星曜亮度 —— 与 iztro 库的输出对齐。 | 已针对库验证。 |
| **标志边界 ±0.3°** | 任何行星 / 门 / 线坐在边界的 ±0.3° 内。 | 视为暂定，注意影响 —— ±0.3° 可以跨越界线翻转。 |

---

## 已知限制

- **无 Chiron / 小天体。** 当前 adapter 只输出 10 颗古典行星加月球节点。
- **紫微斗数使用一个默认流派。** iztro 被调用时使用固定选项（`bySolar(..., True, 'zh-TW')`）；星曜位置流派和四化是 iztro 的默认值。如果你通常使用飞星或其他流派，主要结构不变但某些细节可能不同。
- **近似出生时间降低时间依赖层级。** 如果出生时间不确定，上升点/中天/宫位分配、人类图线和时辰 —— 以及任何源自它们的东西 —— 变得不可靠。在这种情况下，**将时间依赖字段视为暂定**并在依赖它们之前考虑**基于事件的矫正**（将已知的生活事件与图表时间匹配）。

---

## 从 AI 代理 / Hermes 使用

意图的整合模式是**自安装**，而不是 SaaS。

用户复制此仓库的 URL，**他们自己的**代理或 CLI（Claude Code、Hermes、脚本等）克隆它并**在用户的计算机上本地**运行它。计算发生在用户方。没有托管的端点可调用，没有账户，**不需要 SaaS 整合** —— 引擎是一个无状态的、确定性的、离线的子进程。

发布者不把它作为网络服务运营。按照 MIT 条款，本地使用、修改、分发和托管使用都允许，细节见 `LICENSE`。

对于代理来说，合约很简单：用仓库中的 venv Python 分发 `--json` 子进程，将 stdout 解析为 JSON，在 `ok`（和退出代码）上分支，然后移交结构化对象。不需要清理 —— 它是无状态的。完整的 CLI + JSON 合约存在于 **[AGENTS.md](./AGENTS.md)**。

### 为你的 AI 代理复制粘贴设置

将这个块直接粘贴到 Claude Code、ChatGPT 或任何编码代理 —— 它告诉代理如何安装和调用工具：

```text
设置并使用 "life-chart-engine" —— 一个从出生数据计算西方本命星盘 +
人类图 + 紫微斗数的 CLI。

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. 计算图表并将 stdout 读为 JSON：
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. 规则：
   - 你自己解析出生城市为 --lat/--lon 和正确的历史 UTC
     偏移（考虑夏令时）。工具不进行地理编码。
   - 在信任上升点、宫位、人类图线或紫微时辰柱之前，
     确认出生时间是否准确。
   - 永远不要伪造图表值 —— 总是调用工具。
   - 完整的输出模式、退出代码和代理合约：~/.life-chart-engine/AGENTS.md
```

---

## 许可证

本仓库采用 **[MIT](./LICENSE)** 许可证。

引擎使用 **astronomy-engine (MIT)** 进行天文计算，并使用 **iztro (MIT)** 进行紫微斗数计算。Placidus 宫位公式和 Meeus 参考列在 [CREDITS.md](./CREDITS.md)。

你可以按 MIT 条款使用、复制、修改、分发、再授权和销售副本。请在软件的实质部分保留 copyright 与 permission notice。

完整致谢和依赖许可证见 **[CREDITS.md](./CREDITS.md)**。

---

## 常见问题

**我可以输入农历日期吗？**
不。输入是公历太阳日期（`--date YYYY-MM-DD`）和时钟时间（`--time HH:MM`）。如果你只有农历日期，先转换它。紫微斗数通过 iztro 的太阳入口点（`bySolar`）计算。

**我的出生时间仅仅是近似的 —— 这是问题吗？**
行星位置没问题，但上升点、中天、宫头、每颗行星所在的宫、人类图线和时辰都是时间敏感的。将这些视为暂定，在依赖它们之前考虑基于事件的矫正。

**哪里有 Chiron / 小行星 / 小天体？**
不包括。当前 adapter 只输出 10 颗古典行星和月球节点。

**它使用哪个紫微斗数流派？**
iztro 实现的默认流派（`bySolar(..., True, 'zh-TW')`）。流派不是用户可选的。

**它会对外拨号 / 使用网络吗？**
否。引擎完全离线 —— 没有遥测、没有网络调用、没有副作用。它是一个无状态的、确定性的一次性子进程。

**我可以在闭源产品中使用它吗？**
可以。本仓库采用 MIT 许可证；请在软件的实质部分保留 copyright 与 permission notice。

---

## 免责声明

`life-chart-engine` 是一个**解释性自我意识框架，不是预测或宿命论**。输出是用于反思的结构化参考点 —— 它们不预言事件，不决定结果。用它们作为校准，以你自己的生活经验作为最终权威。这里没有任何内容是医学、法律、心理或财务建议。对于这些领域的决定，咨询合格的专业人士。

---

## 致谢与许可证

- **astronomy-engine** — Don Cross，MIT；天文计算。
- **Meeus, Astronomical Algorithms** — Placidus 宫位公式参考。
- **iztro** — MIT，用于紫微斗数。
- 完整归属：**[CREDITS.md](./CREDITS.md)**。
- **许可证：** [MIT](./LICENSE)。
- **代理 / JSON 合约：** [AGENTS.md](./AGENTS.md)。
