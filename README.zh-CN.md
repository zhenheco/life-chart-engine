> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · **简体中文** · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**一个确定性本地计算引擎，支持三种生命图表系统 —— 西方本命星盘、人类图 (Human Design) 和紫微斗数 —— 从单一出生记录生成。**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` 是一个小型、离线的命令行工具。给它一个人的出生数据 —— 日期、时间、时区和地点坐标 —— 它将在一次运行中计算三个独立的图表系统，然后输出易读的 Markdown 报告或结构化的 JSON 对象供程序和 AI 代理使用。

它专为那些想要**可重现、可验证**的图表计算（而不是黑箱 Web 应用）的用户而设计：实践者、构建自我意识工具的开发者，以及需要纯计算步骤的 AI 代理。每个数字都来自真实的天文计算（Swiss Ephemeris）和真实的紫微斗数库（py-iztro）—— 不来自远程服务、不来自缓存查询，永远不经过网络。

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
- **可重现性。** 任何拥有仓库和相同输入的人都能重新生成你的精确图表。计算使用 Swiss Ephemeris（Moshier 模型）用于天空，py-iztro 用于紫微斗数 —— 两者都是确定性的。
- **跨系统可验证性。** 因为三个独立的系统是从一个出生时刻计算的，你可以三角验证。**当所有三个系统都指向同一个信号时，将其视为高信心。当只有一个系统显示一个细节时，将其视为参考点，而非结论。** 这是该引擎的核心设计原则 —— 它产生供交叉阅读的事实，而不是单一的判决。

---

## 快速开始

### 一行命令安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

安装到 `~/.life-chart-engine`（使用 `LIFE_CHART_DIR` 覆盖）。无需 `sudo`、无系统范围的更改 —— 它只是克隆仓库并构建一个隔离的 CPython 3.12 venv。需要 `git` 和 [`uv`](https://docs.astral.sh/uv/)。任何时候重新运行以更新到最新版本。

### 从源代码

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` 做什么

它在 `set -euo pipefail` 下运行，执行五个步骤：

1. **解析 venv 位置** —— `${LIFE_VENV:-<repo>/.venv}`。设置 `LIFE_VENV` 环境变量以覆盖；默认 `.venv/` 被 git 忽略。
2. **预检：需要 [`uv`](https://docs.astral.sh/uv/)** —— 如果 `uv` 不在 `PATH` 上，它退出 `1` 并打印安装提示：
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **创建 CPython 3.12 venv** —— `uv venv --python 3.12 "$VENV"`（见 [为什么是 CPython 3.12](#why-cpython-312-specifically)）。
4. **安装固定依赖** —— `uv pip install --python "$VENV/bin/python" -r requirements.txt`。
5. **运行冒烟测试** —— 用固定示例输入执行引擎一次（丢弃 stdout）并在成功时打印 `OK — engine runs.`。它也为两种模式打印使用提示。

### 手动 `uv` 步骤（无 `setup.sh`）

```bash
# 1. 创建 CPython 3.12 venv（默认 <repo>/.venv；使用 LIFE_VENV 覆盖）
uv venv --python 3.12 .venv

# 2. 安装固定依赖
uv pip install --python .venv/bin/python -r requirements.txt

# 3. （可选）冒烟测试
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

仅有两个直接依赖被固定在 `requirements.txt` 中：

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## 为什么特别选择 CPython 3.12

你必须在 **CPython 3.12** 上运行引擎 —— 不是 3.13，不是 3.14。原因在 `requirements.txt` 和 `setup.sh` 中的描述完全相同：

> py-iztro 的本地依赖（**pythonmonkey / pydantic-core**）**没有 3.13+/3.14 的轮子，从源构建失败**。固定为 3.12。

简单来说：`py-iztro` 依赖本地扩展（`pythonmonkey`、`pydantic-core`），其预构建轮子止步于 3.12。在 3.13/3.14 上没有轮子，源构建失败。这正是为什么 `setup.sh` 调用 `uv venv --python 3.12`，也是为什么你应该始终用项目 venv 的 Python（`<repo>/.venv/bin/python`）调用引擎，永远不使用系统 `python3`。

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

【紫微斗數 py-iztro】
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
| `schema_version` | `"1.0"`。 |
| `input` | 规范化输入的回显：`name`、`gender`、`date`、`time`、`tz_offset`、`lat`、`lon`、`target`（注意 `tz_offset`，不是 `tz`）。 |
| `western` | `system` 字符串、`ascendant`/`midheaven` 位置对象、`planets[]`、`houses[]`（×12）、`aspects[]`。 |
| `human_design` | `type`、`authority`、`profile`、`definition`、`incarnation_cross`、`design_date`、`defined_centers[]`、`open_centers[]`、`channels[]`、`gates[]`。 |
| `ziwei` | `five_elements_class`、`soul`、`body`、`hour_index`、`palaces[]`、`horoscope`（对象或 `null`）。 |
| `meta` | `{ engine, version, ephemeris }` —— 全部字面值（`ephemeris: "Moshier"`）。 |

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
| **已验证** | 紫微星曜亮度 —— 与 py-iztro 库的输出对齐。 | 已针对库验证。 |
| **标志边界 ±0.3°** | 任何行星 / 门 / 线坐在边界的 ±0.3° 内。 | 视为暂定，注意影响 —— ±0.3° 可以跨越界线翻转。 |

---

## 已知限制

- **无 Chiron / 小天体。** 构建使用 Moshier 黄历（`swe.FLG_MOSEPH`，无数据文件），不提供 Chiron 或其他小天体。仅计算 10 颗古典行星加月球节点。
- **紫微斗数使用一个默认流派。** py-iztro 被调用时使用固定选项（`by_solar(..., True, 'zh-TW')`）；星曜位置流派和四化是 py-iztro 的默认值。如果你通常使用飞星或其他流派，主要结构不变但某些细节可能不同。
- **近似出生时间降低时间依赖层级。** 如果出生时间不确定，上升点/中天/宫位分配、人类图线和时辰 —— 以及任何源自它们的东西 —— 变得不可靠。在这种情况下，**将时间依赖字段视为暂定**并在依赖它们之前考虑**基于事件的矫正**（将已知的生活事件与图表时间匹配）。

---

## 从 AI 代理 / Hermes 使用

意图的整合模式是**自安装**，而不是 SaaS。

用户复制此仓库的 URL，**他们自己的**代理或 CLI（Claude Code、Hermes、脚本等）克隆它并**在用户的计算机上本地**运行它。计算发生在用户方。没有托管的端点可调用，没有账户，**不需要 SaaS 整合** —— 引擎是一个无状态的、确定性的、离线的子进程。

因为发布者不将其作为网络服务运营，第 13 条（§13）的义务对发布者来说不适用于有人自安装的情况。（单独地，§13 仅对运营*修改过的*网络可达版本的运营者强制 —— 不适用于未修改的本地使用。）

对于代理来说，合约很简单：用仓库中的 venv Python 分发 `--json` 子进程，将 stdout 解析为 JSON，在 `ok`（和退出代码）上分支，然后移交结构化对象。不需要清理 —— 它是无状态的。完整的 CLI + JSON 合约存在于 **[AGENTS.md](./AGENTS.md)**。

### 为你的 AI 代理复制粘贴设置

将这个块直接粘贴到 Claude Code、ChatGPT 或任何编码代理 —— 它告诉代理如何安装和调用工具：

```text
设置并使用 "life-chart-engine" —— 一个从出生数据计算西方本命星盘 +
人类图 + 紫微斗数的 CLI。

1. 安装（需要 `git` 和 `uv`；如果 uv 丢失：curl -LsSf https://astral.sh/uv/install.sh | sh）：
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

此仓库在 **[AGPL-3.0](./LICENSE)** 下许可。

**AGPL-3.0 的通俗英文说法。** 它是 GNU GPL-3.0（一个强制性 copyleft 许可证：如果你分发软件，你必须在同一许可证下发布你的完整对应源代码）**加上一个额外条款，第 13 条**。§13 关闭了 "SaaS 漏洞"：超越 GPL 的*分发*触发器，它增加了如果你*修改*程序并让用户通过网络与你的修改版本交互，你必须向那些远程用户提供你的对应源代码。（将未修改的上游作为网络服务运行本身不触发 §13。）AGPL 是相互的但不无限地病毒性 —— 它仅涵盖到是 AGPL 代码的导数或与其链接的代码。

**为什么此仓库是 AGPL。** 引擎链接**Swiss Ephemeris**（通过 `pyswisseph`）用于行星位置和宫头。Astrodienst **双重许可** Swiss Ephemeris 为 **AGPL-3.0 或商业许可证**，其代码不能被重新许可为任何更宽松的东西。因为 AGPL 是 copyleft 且此项目链接它，整个组合工作必须是 AGPL。（`py-iztro` 是 MIT 且不强制 copyleft；Swiss Ephemeris 是这里唯一强制 AGPL 的组件。）

**在实践中意味着什么。**

| 你做 | AGPL 义务 |
|--------|-----------------|
| **自安装**（为自己本地运行） | §13*不*被触发 —— 没有远程用户需要提供，你已经有了源代码。清晰。 |
| **将*修改*版本作为网络服务运行** | §13*被*触发 —— 你必须向那些远程用户提供你的部署版本的完整对应源，在 AGPL 下，包括你的修改。注意：§13 的源代码提供义务以修改为条件 —— 仅仅将未修改的上游作为网络服务运行本身不触发 §13，尽管源代码已经公开了。 |

**你的三个选项**，如果网络源义务不符合你的用例：

1. **保持 AGPL** —— 向任何使用它的人发布你的完整对应源（包括修改），包括通过网络根据 §13。免费，无需协商。
2. **从 [Astrodienst](https://www.astro.com/swisseph/) 购买 Swiss Ephemeris 商业许可证** —— 这解除了 Swiss Ephemeris 部分的 AGPL 义务，让你重新许可自己的代码并发送/主持一个闭源构建。（这是 Astrodienst 的双重许可模式。）
3. **交换黄历** —— 将 `pyswisseph` 替换为有许可许可的天文学源（例如 **Skyfield (MIT)** 加上公共领域 **JPL DE440** 黄历 —— 示意的替代品，不是唯一的选项）。Swiss Ephemeris 消失后，剩余的堆栈（py-iztro MIT，加上 MPL-2.0/MIT/Apache deps）不再强制 AGPL，整个仓库可以是 MIT。这是真实的工程工作：你必须重新实现当前源自 Swiss Ephemeris 的所有东西 —— 行星黄经、逆行标志、上升点/中天、Placidus 宫头，以及人类图 88° 设计求解器的输入。

见 **[CREDITS.md](./CREDITS.md)** 获取完整归属和每个依赖的许可证。

---

## 常见问题

**我可以输入农历日期吗？**
不。输入是公历太阳日期（`--date YYYY-MM-DD`）和时钟时间（`--time HH:MM`）。如果你只有农历日期，先转换它。紫微斗数通过 py-iztro 的太阳入口点（`by_solar`）计算。

**我的出生时间仅仅是近似的 —— 这是问题吗？**
行星位置没问题，但上升点、中天、宫头、每颗行星所在的宫、人类图线和时辰都是时间敏感的。将这些视为暂定，在依赖它们之前考虑基于事件的矫正。

**哪里有 Chiron / 小行星 / 小天体？**
不包括。这里使用的 Moshier 黄历不提供它们；仅计算 10 颗古典行星和月球节点。

**它使用哪个紫微斗数流派？**
py-iztro 实现的默认流派（`by_solar(..., True, 'zh-TW')`）。流派不是用户可选的。

**它会对外拨号 / 使用网络吗？**
否。引擎完全离线 —— 没有遥测、没有网络调用、没有副作用。它是一个无状态的、确定性的一次性子进程。

**我可以在闭源产品中使用它吗？**
根据 AGPL-3.0，是的用于私有/本地使用。分发构建触发 GPL 传达/源义务，网络服务*修改*构建触发 AGPL §13 —— 任意方式你必须提供对应源。为完全闭源，要么从 Astrodienst 购买 Swiss Ephemeris 商业许可证，要么将黄历交换为 Skyfield + JPL DE440（见[许可证](#许可证)）。

---

## 免责声明

`life-chart-engine` 是一个**解释性自我意识框架，不是预测或宿命论**。输出是用于反思的结构化参考点 —— 它们不预言事件，不决定结果。用它们作为校准，以你自己的生活经验作为最终权威。这里没有任何内容是医学、法律、心理或财务建议。对于这些领域的决定，咨询合格的专业人士。

---

## 致谢与许可证

- **Swiss Ephemeris** 通过 `pyswisseph` —— © Astrodienst AG，双重许可 AGPL-3.0 / 商业（<https://www.astro.com/swisseph/>）。
- **py-iztro**（及上游 `iztro`）—— MIT，用于紫微斗数。
- 完整归属：**[CREDITS.md](./CREDITS.md)**。
- **许可证：** [AGPL-3.0](./LICENSE)。
- **代理 / JSON 合约：** [AGENTS.md](./AGENTS.md)。
