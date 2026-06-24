> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · **日本語** · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**西洋占星術、人類圖（Human Design）、紫微斗數の3つの人生チャートシステムを、単一の出生記録からネイティブで決定論的に計算。**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` は、小型でオフラインのコマンドラインツールです。1人の出生データ — 日付、時刻、タイムゾーン、地点座標 — を与えると、3つの独立したチャートシステムを1回のパスで計算し、人間が読める Markdown レポート、またはプログラムと AI エージェント向けの構造化 JSON オブジェクトとして出力します。

ブラックボックスの Web アプリではなく、**再現可能で検証可能な**チャート計算が必要な人 — 実務家、セルフ認識ツールを構築する開発者、純粋な計算ステップが必要な AI エージェント — 向けに構築されています。すべての数値は、リモートサービスからでもキャッシュ検索からでも、ネットワーク経由でもなく、本物の天文計算（Swiss Ephemeris）と本物の紫微斗數ライブラリ（iztro）から来ています。

---

## 計算対象

エンジンは**同じ出生時刻**に対して3つのシステムを実行するため、その出力は互いに相互検証できます。各システムは異なる種類の質問に答えます：

| システム | 説明（平文） | エンジンが出力する内容 |
|---------|-----------|-------------------|
| **西洋占星術**（熱帯座標 / プラシダス） | 古典的な西洋占星術 — あなたの出生時に惑星が黄道帯に対してどこに位置していたか、12つのハウスに分割。 | アセンダント + ミッドヘブン、12個の惑星/ポイント（太陽 → 南交点）（サイン、度数、ハウス、逆行フラグ付き）、全12ハウスのカスプ、および検出されたすべてのアスペクト（コンジャンクション/セクスタイル/スクエア/トライン/オポジション）（オーブで整列）。 |
| **人類圖（Human Design）** | 占星術、易経、チャクラシステムの現代的合成。エネルギーがゲート、チャネル、センターを通じて「配線」されている方法を説明します。 | タイプ、オーソリティ、プロフィール、ディフィニション、インカーネーションクロス、88度前の設計日、定義されたセンター/開放センター、定義されたチャネル、パーソナリティと設計チャートの両方の惑星ごとのゲート.ラインアクティベーション。 |
| **紫微斗數** | 運命を12宮盤にマッピングする伝統的な中国占星術システム、名前付きの星で満たされている。 | 五行局、命主（ソウル）/ 身主（ボディ）、時辰インデックス、および宮ごとのデータ — 干支、命/身フラグ、10年年齢範囲、主星/副星/修正星（明度と四化付き）。オプションで最善努力の大限/流年ホロスコープ。 |

Human Design のタイプ、オーソリティ、ディフィニションは**ハードコーディングされていません** — 定義されたセンターの接続グラフから導出されています。

---

## ネイティブ計算をする理由

このエンジンは、近似や外部サービス呼び出しの代わりに実際の数学を行います。この選択により、深刻なチャートツール向けに重要な3つの性質が得られます：

- **決定論的。** 同じ出生入力は常に同じ出力を、バイト単位で正確に生成します。ランダムさ、モデル、実行間のラウンディングドリフトはありません。
- **再現可能。** リポジトリと同じ入力を持つ誰もが、あなたの正確なチャートを再生成できます。計算は、天空用に Swiss Ephemeris（Moshier モデル）を、紫微斗數用に iztro を使用します — どちらも決定論的です。
- **相互検証可能。** 1つの出生時刻から3つの独立したシステムが計算されるため、三角測量ができます。**3つのシステムすべてが同じシグナルを指すとき、それを高い信頼度として扱います。1つのシステムだけが詳細を示すとき、それを参照ポイントとして扱い、結論ではなく。** これがエンジンの中核設計原則です — 単一の評決ではなく、相互に読むべき事実を生成します。

---

## クイックスタート

### ワンラインインストール（推奨）

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

`~/.life-chart-engine` にインストールします（`LIFE_CHART_DIR` で上書き可能）。`sudo` 不要、システム全体への変更なし — リポジトリを clone し、分離された CPython 3.12 venv を作成し、固定された iztro Node バンドルを生成するだけです。`git`、[`uv`](https://docs.astral.sh/uv/)、Node.js/npm が必要です。最新版へ更新するにはいつでも再実行してください。

### ソースからのインストール

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` の動作

`set -euo pipefail` の下で実行され、6 つのステップを行います:

1. **venv の場所を解決** — `${LIFE_VENV:-<repo>/.venv}`。`LIFE_VENV` env 変数を設定してオーバーライド可能。デフォルト `.venv/` は git-ignored。
2. **プリフライト：[`uv`](https://docs.astral.sh/uv/) が必要** — `uv` が `PATH` にない場合は `1` で終了し、インストールヒントを出力：
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **CPython 3.12 venv を作成** — `uv venv --python 3.12 "$VENV"`（[なぜ CPython 3.12](#why-cpython-312-specifically) を参照）。
4. **ピン留めされた依存関係をインストール** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`。
5. **固定された iztro バンドルをビルド** — `scripts/build-iztro-bundle.sh` を実行し、`iztro@2.5.8` を一時ビルドディレクトリにインストールして `vendor/iztro.cjs` を生成します。
6. **スモークテストを実行** — 固定サンプル入力でエンジンを一度実行し（stdout は破棄）、成功時に `OK — engine runs.` を出力します。両モードの使用ヒントも出力します。

### 手動 `uv` ステップ（`setup.sh` なし）

```bash
# 1. CPython 3.12 venv を作成（デフォルト <repo>/.venv、LIFE_VENV でオーバーライド可能）
uv venv --python 3.12 .venv

# 2. ピン留めされた deps をインストール
uv pip install --python .venv/bin/python -r requirements.txt

# 3. 固定された iztro バンドルをビルド
bash scripts/build-iztro-bundle.sh

# 4. (任意) スモークテスト
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Python の直接依存関係は `requirements.txt` に固定されています:

```
pyswisseph==2.10.3.2
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei は `scripts/build-iztro-bundle.sh` によって固定された生成済み Node バンドルを使用します:

```
iztro@2.5.8
```

---

## なぜ CPython 3.12 なのか

エンジンは現在、検証済みの **CPython 3.12** ランタイムで実行されます。その理由は `requirements.txt` と `setup.sh` に同じ内容で記載されています:

> この変更では CPython 3.12 は固定のままです。古い Python Zi Wei ネイティブ依存の制約はなくなったため、残りの依存関係とデプロイイメージを確認した後で再検討できます。

要するに、3.12 はこのリリースで引き続きテスト済みのランタイムです。Zi Wei 依存関係はもはやこの固定を強制しないため、Python バージョンの引き上げはこのリファクタの一部ではなく、後続の互換性確認です。

---

## 使用方法

エンジンは2つのモードを持ち、`--json` フラグの有無で選択されます。

### ヒューマンモード（Markdown）

`--json` を省略して読みやすいコンソールレポートを取得。venv の Python を使用：

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

削減された実際のサンプル（アスペクトは Markdown モードでは上位10に制限）：

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

### エージェントモード（JSON）

`--json` を追加して stdout に1つの JSON オブジェクトを取得 — プログラムと AI エージェント向けに理想的：

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

削減された実際のサンプル（配列は1〜2エントリに切り詰められ、値は逐語的）：

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

## CLI フラグリファレンス

**`required=True` フラグはありません** — argparse は欠落しているフラグでエラーを出しません。`--date`/`--time`/`--tz`/`--lat`/`--lon` を省略するとサイレントに組み込みサンプル人物（`範例`、生年月日 `2000-01-01 12:00`、UTC+8、台北101）にフォールバックします。正確なチャートのためには、すべてを指定してください。

| フラグ | 型 | 正しい使用に必須？ | デフォルト | 形式 / ルール |
|-------|----|--------------------|-----------|------------|
| `--name` | 文字列 | いいえ（装飾） | `"範例"` | 自由テキスト。出力にのみエコーされます。 |
| `--gender` | 文字列 | 紫微のみ必須 | `"女"` | 正確に `男` または `女` である必要があります（argparse `choices`；その他 → 終了 `2`）。 |
| `--date` | 文字列 | **はい** | `2000-01-01` にフォールバック | `YYYY-MM-DD`、`-` で分割。ゼロパッド要件なし。 |
| `--time` | 文字列 | **はい** | `12:00` にフォールバック | `HH:MM`、24時間ローカルクロック時刻、`:` で分割。 |
| `--tz` | float | **はい** | `8.0` にフォールバック | UTC オフセット（夏時間を含む）（台湾 = `8`）。入力キー `tz_offset` に書き込まれます。 |
| `--lat` | float | **はい** | `25.0330` にフォールバック | 十進法の緯度（西洋ハウス/Asc/MC）。 |
| `--lon` | float | **はい** | `121.5654` にフォールバック | 十進法の経度。 |
| `--target` | 文字列 | いいえ | `"2025-01-01"` | `YYYY-MM-DD`；紫微運限参考日。 |
| `--json` | フラグ | いいえ | `False`（Markdown） | 存在 → JSON モード；非存在 → Markdown。値を取得しません。 |

> エンジンは地名のジオコーディングやタイムゾーン検索を**行いません**。呼び出し元が地名 → `lat`/`lon`/`tz` に変換する必要があります — タイムゾーン/DST が最も一般的なエラーの原因であるため、出生地と出生日に適用された UTC オフセットを確認してください。

---

## 出力リファレンス

`--json` エンベロープには、この順序で7つのトップレベルキーがあります：

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| ブロック | 概要 |
|---------|------|
| `ok` | 成功時 `true`（エラーエンベロープでは `false`）。 |
| `schema_version` | `"1.0"`。 |
| `input` | 正規化された入力のエコー：`name`、`gender`、`date`、`time`、`tz_offset`、`lat`、`lon`、`target`（`tz` ではなく `tz_offset` に注意）。 |
| `western` | `system` 文字列、`ascendant`/`midheaven` ポジションオブジェクト、`planets[]`、`houses[]`（×12）、`aspects[]`。 |
| `human_design` | `type`、`authority`、`profile`、`definition`、`incarnation_cross`、`design_date`、`defined_centers[]`、`open_centers[]`、`channels[]`、`gates[]`。 |
| `ziwei` | `five_elements_class`、`soul`、`body`、`hour_index`、`palaces[]`、`horoscope`（オブジェクトまたは `null`）。 |
| `meta` | `{ engine, version, ephemeris }` — すべてリテラル（`ephemeris: "Moshier"`）。 |

完全なフィールド契約 — すべてのキー、型、およびエージェント呼び出しプロトコル — については、**[AGENTS.md](./AGENTS.md)** を参照してください。

### 知る価値があるフィールドの癖

- **`aspects` は JSON でキャップされていません。** JSON パスはすべての検出されたアスペクトを返し、オーブで昇順に並列（最もきつい順）。10項目キャップは Markdown レポートにのみ存在します。
- **`ziwei.horoscope` はベストエフォートで `null` の可能性があります。** `try/except` でラップされています；任意の例外時は `null` としてシリアライズされます。存在する場合は `{ decadal, yearly }`です。（これらのサブオブジェクトはドキュメント化されたプレースホルダーを超えた追加の内部構造 — `index`、`mutagen[]`、`stars[][]`、`yearly_dec_star` など — を公開します。）
- **スター文字列は明度 + 四化をエンコードします。** 形式は `name(brightness)[mutagen]` で、各部分はオプション — 例：`紫微(廟)[祿]`、`紫微(廟)`、`天機[祿]`、またはプレーン `天機`。`adjective_stars` はプレーン名のみ（明度/mutagen なし）。

---

## 精度ティア

すべての出力が同じ信頼度を持つわけではありません。各ティアに応じて読んでください：

| ティア | 対象範囲 | 信頼度 |
|-------|---------|------|
| **最高** | 惑星の黄経、サイン、逆行、プラス紫微スター配置 / 命宮·身宮 / 五行局 — 純粋なエフェメリスと暦の数学。 | 天文学的/暦的に正確。 |
| **高、時間依存** | アセンダント、ミッドヘブン、全12ハウスカスプ、各惑星が属するハウス、Human Design ラインおよび紫微時辰インデックス。 | 正確な*出生時刻が与えられた場合*；分に敏感。 |
| **検証済み** | 紫微斗數スター明度 — iztro ライブラリの出力に整合。 | ライブラリに対して検証済み。 |
| **フラグ境界 ±0.3°** | 境界の ±0.3° 内にある任意の惑星 / ゲート / ライン。 | 仮設として扱い、影響をメモ — ±0.3° はそれを線を超えてフリップできます。 |

---

## 既知の制限

- **Chiron / 小惑星はありません。** ビルドは Moshier エフェメリス（`swe.FLG_MOSEPH`、データファイルなし）を使用し、Chiron または他の小惑星を提供しません。古典的な10惑星とルナノードのみが計算されます。
- **紫微斗數は1つのデフォルトスクールを使用します。** iztro は固定オプション（`bySolar(..., True, 'zh-TW')`）で呼び出されます；スター配置スクールと四化は iztro のデフォルトです。通常、飛星またはその他のスクールを使用する場合、メイン構造は変わりませんが、一部の詳細は異なる可能性があります。
- **近似出生時刻は時間依存ティアを低下させます。** 出生時刻が不確定である場合、アセンダント/MC/ハウス割り当て、Human Design ライン、および時辰 — およびそれらから導出されたもの — は信頼性が低くなります。その場合、**時間依存フィールドを仮設として扱い**、それらに依存する前に**事象ベースの是正**（既知の人生イベントをチャートタイミングと照合）を検討してください。

---

## AI エージェント / Hermes から使用

意図された統合モデルは **SaaS ではなく自己インストール**です。

ユーザーがこのリポジトリの URL をコピーし、**彼ら自身の**エージェント、CLI（Claude Code、Hermes、スクリプト等）が**ユーザーのマシンでローカルに**それをクローンして実行します。計算はユーザー側で発生します。呼び出すホストされたエンドポイント、アカウント、**SaaS 統合は不要です** — エンジンはステートレス、決定論的、オフラインのサブプロセスです。

パブリッシャーがそれをネットワークサービスとして操作しないため、誰かが自己インストールする場合、パブリッシャーに §13 義務は生じません。（別途、§13 は*修正された*ネットワーク到達可能バージョンを実行するオペレータのみに義務付けます — 修正されていないローカル使用は対象外です。）

エージェントの場合、契約は単純です：リポジトリの venv Python で `--json` サブプロセスをディスパッチし、stdout を JSON として解析し、`ok`（および終了コード）で分岐し、構造化オブジェクトを引き渡します。クリーンアップは不要です — ステートレスです。完全な CLI + JSON 契約は **[AGENTS.md](./AGENTS.md)** に記載されています。

### AI エージェント向けコピー・ペーストセットアップ

このブロックを Claude Code、ChatGPT、または任意のコーディングエージェントに直接貼り付けます — これはツールをインストールして呼び出す方法をエージェントに指示します：

```text
Set up and use "life-chart-engine" — a CLI that computes a Western natal chart +
Human Design + Zi Wei Dou Shu (紫微斗數) from birth data.

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
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

## ライセンス

このリポジトリは **[AGPL-3.0](./LICENSE)** でライセンスされています。

**AGPL-3.0 を平文で。** それは GNU GPL-3.0（強力なコピーレフトライセンス：ソフトウェアを配布する場合、同じライセンスの下で完全な対応するソースをリリースする必要があります）**プラス1つの追加句、第13条**です。§13 は「SaaS ループホール」を閉じます：GPL の*配布*トリガーを超えて、プログラムを*修正*してユーザーがネットワーク経由であなたの修正版と相互作用できるようにする場合、それらのリモートユーザーに対応するソースを提供する必要があります。（修正されていないアップストリームをネットワークサービスとして実行することは、それ自体では §13 をトリガーしません。）AGPL は相互的ですが、無限にウイルス的ではありません — AGPL コードから派生した、または AGPL コードでリンクされたコードのみに到達します。

**このリポジトリが AGPL である理由。** エンジンは **Swiss Ephemeris**（`pyswisseph` 経由）を惑星位置とハウスカスプ用にリンクします。Astrodienst は **AGPL-3.0 OR 商業ライセンス**として Swiss Ephemeris をデュアルライセンスしており、そのコードはより許容的なものとしてリライセンスできません。AGPL がコピーレフトで、このプロジェクトがそれをリンクするため、結合された全体の作品は AGPL である必要があります。（`iztro` は MIT で、コピーレフト非要件；Swiss Ephemeris が AGPL をここで強制する唯一のコンポーネントです。）

**実践での意味。**

| あなたがしていること | AGPL 義務 |
|------------------|----------|
| **自己インストール**（ローカルで自分自身のため実行） | §13 は*トリガーされません* — リモートユーザーがいないため、すでにソースがあります。クリーン。 |
| **ネットワークサービスとして*修正*バージョンを実行** | §13 は*トリガーされます* — それらのリモートユーザーにあなたのデプロイされたバージョンの完全な対応するソースを、修正を含めて AGPL でオファーする必要があります。注：§13 のソースオファー義務は修正に条件付けられます — 修正されていないアップストリームをネットワークサービスとして実行することは、それ自体では §13 をトリガーしません、ただしソースはすでに公開です。 |

**ネットワークソース義務があなたの使用事例に合わない場合の3つのオプション：**

1. **AGPL を保持** — 完全な対応するソース（修正を含む）をネットワーク経由を含む誰にでも公開します（§13 に従い）。無料、交渉なし。
2. **[Astrodienst](https://www.astro.com/swisseph/) から Swiss Ephemeris 商業ライセンスを購入** — これは Swiss Ephemeris 部分の AGPL 義務を解除し、あなた自身のコードをリライセンスして閉じたビルドを出荷/ホストできます。（これは Astrodienst のデュアルライセンシングモデルです。）
3. **エフェメリスを交換** — `pyswisseph` を許容的にライセンスされた天文学ソース（例えば **Skyfield（MIT）** プラス公開ドメイン **JPL DE440** エフェメリス — 説明例、唯一のオプションではない）で置き換えます。Swiss Ephemeris がなくなると、残りのスタック（iztro MIT、プラス MPL-2.0/MIT/Apache deps）は AGPL を強制しなくなり、全リポジトリは MIT である可能性があります。これは本物のエンジニアリング作業です：現在 Swiss Ephemeris から取得されているすべてを再実装する必要があります — 惑星黄経、逆行フラグ、Asc/MC、プラシダスハウスカスプ、および Human Design 88° 設計ソルバーへの入力。

**[CREDITS.md](./CREDITS.md)** で完全な帰属と依存ごとのライセンスを参照してください。

---

## FAQ

**太陰暦の日付を入力できますか？**
いいえ。入力は、グレゴリオ太陽暦の日付（`--date YYYY-MM-DD`）と時刻（`--time HH:MM`）です。太陰暦の日付しかない場合は、最初に変換してください。紫微斗數は iztro の太陽入力エンドポイント（`bySolar`）経由で計算されます。

**出生時刻が近似値のみですが、問題ですか？**
惑星位置は大丈夫ですが、アセンダント、ミッドヘブン、ハウスカスプ、各惑星が属するハウス、Human Design ライン、および時辰はすべて時間に敏感です。それらを仮設として扱い、それらに依存する前に事象ベースの是正を検討してください。

**Chiron / 小惑星 / 小惑星体はどこですか？**
含まれていません。ここで使用される Moshier エフェメリスはそれらを提供しません；古典的な10惑星とルナノードのみが計算されます。

**どの紫微斗數スクールを使用しますか？**
iztro（`bySolar(..., True, 'zh-TW')`）で実装されたデフォルトスクール。スクールはユーザーが選択可能ではありません。

**ホームに電話をかけます / ネットワークを使用しますか？**
いいえ。エンジンは完全にオフライン — テレメトリなし、ネットワーク呼び出しなし、副作用なし。ステートレス、決定論的なワンショットサブプロセスです。

**クローズドソース製品内で使用できますか？**
AGPL-3.0 では、個人的/ローカルな使用のためにはい。ビルドの配布は GPL 移譲/ソース義務をトリガーし、*修正*ビルドのネットワーク提供は AGPL §13 をトリガーします — どちらにしても対応するソースをオファーする必要があります。完全にクローズドソースに進むには、Astrodienst から Swiss Ephemeris 商業ライセンスを購入するか、エフェメリスを Skyfield + JPL DE440 に交換してください（[ライセンス](#ライセンス) を参照）。

---

## 免責事項

`life-chart-engine` は**解釈的自己認識フレームワークであり、予測や運命ではありません**。出力は反省のための構造化参照ポイント — イベントを予測せず、結果を決定しません。キャリブレーションとして使用し、あなた自身の生活経験を最終的な権威とします。ここには医学的、法的、心理的、または財務的なアドバイスはありません。これらの領域での決定については、資格のある専門家に相談してください。

---

## クレジット & ライセンス

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG、デュアルライセンス AGPL-3.0 / 商用（<https://www.astro.com/swisseph/>）。
- **iztro** — MIT、紫微斗數用。
- 完全な帰属：**[CREDITS.md](./CREDITS.md)**。
- **ライセンス：** [AGPL-3.0](./LICENSE)。
- **エージェント / JSON 契約：** [AGENTS.md](./AGENTS.md)。
