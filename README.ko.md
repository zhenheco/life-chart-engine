> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · **한국어** · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**세 가지 인생 차트 시스템의 결정론적 네이티브 계산 — 서양 태생학(Western natal astrology), 인류도(Human Design), 그리고 자미두수(紫微斗數 Zi Wei Dou Shu) — 단일 출생 기록에서.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine`은 작고 오프라인 명령줄 도구입니다. 한 사람의 출생 데이터 — 날짜, 시간, 시간대, 장소 좌표 — 를 입력하면 세 개의 독립적인 차트 시스템을 한 번에 계산한 후, 읽기 쉬운 마크다운 리포트 또는 프로그램과 AI 에이전트가 사용할 수 있는 구조화된 JSON 객체를 생성합니다.

이 도구는 **재현 가능하고 검증 가능한** 차트 계산을 원하는 사람들 — 실무자, 자기인식 도구를 구축하는 개발자, 순수 계산 단계가 필요한 AI 에이전트 — 을 위해 만들어졌습니다. 모든 수치는 실제 천문 계산(Swiss Ephemeris)과 실제 자미두수 라이브러리(iztro)에서 나오며, 원격 서비스나 캐시된 조회, 네트워크 통신은 전혀 사용하지 않습니다.

---

## 계산 대상

엔진은 **동일한 출생 시점**에 대해 세 시스템을 실행하므로, 그들의 결과가 서로 상호 검증될 수 있습니다. 각 시스템은 다양한 종류의 질문에 답변합니다:

| 시스템 | 정의(평문) | 엔진의 산출물 |
|--------|-----------|------------|
| **서양 태생학**(Tropical / Placidus) | 고전 서양 점성학 — 출생 시점에 황도대에 대한 행성의 위치, 12 궁(하우스)로 나뉨. | 상승점(Ascendant) + 천정점(Midheaven), 12개 행성/포인트(태양 → 남교점)의 별자리, 각도, 궁 및 역행 플래그, 12개 궁 쿠스프 전체, 그리고 검출된 모든 상(合相/六分/四分/三分/對分) — 긴밀도로 정렬됨. |
| **인류도(Human Design)** | 점성학, 주역, 차크라 시스템의 현대적 합성. 게이트, 채널, 센터를 통한 에너지 "배선" 방식을 설명. | 유형, 권위, 프로필, 정의, 환생 십자가, 88° 이전의 설계 날짜, 정의된/개방된 센터, 정의된 채널, 및 성격 및 설계 차트 모두에 대한 행성별 게이트.라인 활성화. |
| **자미두수(Zi Wei Dou Shu)** | 12궁판에 운명을 매핑하는 전통 중국 점성학. 명명된 별들로 채워짐. | 오행국(五行局), 명주(命主, 영혼) / 신주(身主, 신체), 시진(時辰) 시간 인덱스, 그리고 궁별 데이터 — 간지, 명/신 플래그, 10년 나이 범위, 주요/부차/형용사 별들(밝기 및 사화(四化) 포함). 선택적으로 최선의 노력으로 한 대한(大限)/유년(流年) 운세. |

Human Design의 유형, 권위, 정의는 **하드코딩되지 않음** — 정의된 센터의 연결 그래프에서 유래됩니다.

---

## 네이티브 계산을 하는 이유

이 엔진은 근사 계산이나 외부 서비스 호출 대신 실제 수학을 계산합니다. 이러한 선택은 모든 진지한 차트 도구에 중요한 세 가지 특성을 제공합니다:

- **결정론적.** 동일한 출생 입력은 항상 동일한 결과를 바이트 단위로 정확히 생성합니다. 무작위성, 모델, 실행 간 반올림 편차가 없습니다.
- **재현 가능.** 리포지토리와 동일한 입력을 가지고 있는 누구나 정확한 차트를 재생성할 수 있습니다. 계산은 하늘을 위해 Swiss Ephemeris(Moshier 모델)를, 자미두수를 위해 iztro를 사용 — 둘 다 결정론적입니다.
- **교차 검증 가능.** 한 출생 시점에서 세 개의 독립적인 시스템이 계산되므로 삼각측량이 가능합니다. **세 시스템이 모두 동일한 신호를 가리킬 때, 높은 신뢰도로 취급하세요. 한 시스템만 세부 사항을 보여줄 때, 결론이 아닌 참고 포인트로 취급하세요.** 이것이 엔진의 핵심 설계 원리입니다 — 단일 판단이 아닌 교차 읽기를 위한 사실을 생성합니다.

---

## 빠른 시작

### 한 줄 설치(권장)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

`~/.life-chart-engine`에 설치합니다(`LIFE_CHART_DIR`로 재정의 가능). `sudo`도, 시스템 전체 변경도 없습니다 — repo를 clone하고 격리된 CPython 3.12 venv를 만들며 고정된 iztro Node 번들을 생성할 뿐입니다. `git`, [`uv`](https://docs.astral.sh/uv/), Node.js/npm이 필요합니다. 최신 버전으로 업데이트하려면 언제든 다시 실행하세요.

### 소스에서

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh`의 역할

`set -euo pipefail` 아래에서 실행되며 여섯 단계를 수행합니다:

1. **venv 위치 결정** — `${LIFE_VENV:-<repo>/.venv}`. `LIFE_VENV` 환경 변수를 설정하여 재정의하세요. 기본값 `.venv/`는 git-ignored입니다.
2. **사전 검사: [`uv`](https://docs.astral.sh/uv/) 필요** — `uv`가 `PATH`에 없으면 `1`을 종료하고 설치 힌트를 출력합니다:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **CPython 3.12 venv 생성** — `uv venv --python 3.12 "$VENV"` ([왜 CPython 3.12?](#why-cpython-312-specifically) 참조).
4. **고정된 의존성 설치** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **고정된 iztro 번들을 빌드** — `scripts/build-iztro-bundle.sh`를 실행해 `iztro@2.5.8`을 임시 빌드 디렉터리에 설치하고 `vendor/iztro.cjs`를 생성합니다.
6. **스모크 테스트 실행** — 고정된 샘플 입력으로 엔진을 한 번 실행(stdout 폐기)하고 성공 시 `OK — engine runs.`를 출력합니다. 두 모드의 사용 힌트도 출력합니다.

### 수동 `uv` 단계 (`setup.sh` 없음)

```bash
# 1. CPython 3.12 venv 생성 (기본값 <repo>/.venv; LIFE_VENV로 재정의)
uv venv --python 3.12 .venv

# 2. 고정된 의존성 설치
uv pip install --python .venv/bin/python -r requirements.txt

# 3. 고정된 iztro 번들 빌드
bash scripts/build-iztro-bundle.sh

# 4. (선택) 스모크 테스트
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Python 직접 의존성은 `requirements.txt`에 고정되어 있습니다:

```
pyswisseph==2.10.3.2
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei는 `scripts/build-iztro-bundle.sh`가 고정한 생성된 Node 번들을 사용합니다:

```
iztro@2.5.8
```

---

## CPython 3.12를 특정하는 이유

엔진은 현재 검증된 **CPython 3.12** 런타임에서 실행됩니다. 그 이유는 `requirements.txt`와 `setup.sh`에 동일하게 명시되어 있습니다:

> 이번 변경에서는 CPython 3.12가 계속 고정됩니다. 예전 Python Zi Wei 네이티브 의존성 제약은 사라졌으므로, 남은 의존성과 배포 이미지를 확인한 뒤 다시 검토할 수 있습니다.

요약하면: 3.12는 이 릴리스에서 여전히 테스트된 런타임입니다. Zi Wei 의존성이 더 이상 그 고정을 강제하지 않으므로, Python 버전 상향은 이 리팩터의 일부가 아니라 후속 호환성 확인입니다.

---

## 사용법

엔진에는 두 가지 모드가 있으며, `--json` 플래그의 존재로 선택됩니다.

### 인간 모드(마크다운)

`--json`을 생략하여 읽기 쉬운 콘솔 리포트를 얻습니다. venv의 Python을 사용하세요:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

정제된 실제 샘플(상(相)은 마크다운 모드에서 상위 10개로 제한):

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

### 에이전트 모드(JSON)

`--json`을 추가하여 stdout의 단일 JSON 객체를 얻습니다 — 프로그램 및 AI 에이전트에 이상적입니다:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

정제된 실제 샘플(배열은 1–2개 항목으로 자르고 값은 그대로):

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
  "meta": { "engine": "life-chart-engine", "version": "1.0", "ephemeris": "Moshier" }
}
```

---

## CLI 플래그 레퍼런스

**`required=True` 플래그가 없습니다** — argparse는 누락된 항목에 대해 오류를 발생시키지 않습니다. `--date`/`--time`/`--tz`/`--lat`/`--lon`을 생략하면 기본 제공 예제 인물(`범례`, 출생 `2000-01-01 12:00`, UTC+8, Taipei 101)로 무음 폴백됩니다. 정확한 차트를 위해 모두 제공하세요.

| 플래그 | 유형 | 올바른 사용에 필수인가? | 기본값 | 형식 / 규칙 |
|--------|------|------------------------|----|-----------|
| `--name` | 문자열 | 아니오(미용) | `"範例"` | 자유 텍스트. 출력에만 에코됩니다. |
| `--gender` | 문자열 | 자미두수에만 필요 | `"女"` | 정확히 `男` 또는 `女`여야 함(argparse `choices`; 다른 것 → exit `2`). |
| `--date` | 문자열 | **예** | falls back to `2000-01-01` | `YYYY-MM-DD`, `-`로 분할. 0 패딩 요구 사항 없음. |
| `--time` | 문자열 | **예** | falls back to `12:00` | `HH:MM`, 24시간 로컬 시계 시간, `:`로 분할. |
| `--tz` | 부동 소수점 | **예** | falls back to `8.0` | DST 포함 UTC 오프셋(대만 = `8`). 입력 키 `tz_offset`에 기록됨. |
| `--lat` | 부동 소수점 | **예** | falls back to `25.0330` | 10진 도 단위 위도(서양 궁/상승점/천정점). |
| `--lon` | 부동 소수점 | **예** | falls back to `121.5654` | 10진 도 단위 경도. |
| `--target` | 문자열 | 아니오 | `"2025-01-01"` | `YYYY-MM-DD`; 자미두수 운한 참고 날짜(運限參考日). |
| `--json` | 플래그 | 아니오 | `False`(마크다운) | 존재 → JSON 모드; 부재 → 마크다운. 값을 취하지 않음. |

> 엔진은 **장소를 지오코딩하거나 시간대를 조회하지 않습니다**. 호출자는 장소 → `lat`/`lon`/`tz`를 직접 변환해야 합니다 — 그리고 시간대/DST는 가장 일반적인 오류 소스이므로 출생지 및 출생일에 적용된 UTC 오프셋을 확인하세요.

---

## 출력 레퍼런스

`--json` 봉투는 7개의 최상위 키를 이 순서대로 가집니다:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| 블록 | 요약 |
|------|-----|
| `ok` | 성공 시 `true`(`false` in error envelope). |
| `schema_version` | `"1.1"`. |
| `input` | 정규화된 입력의 에코: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (note `tz_offset`, not `tz`). |
| `western` | `system` 문자열, `ascendant`/`midheaven` 위치 객체, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (object or `null`). |
| `meta` | `{ engine, version, ephemeris }` — 모두 리터럴(`ephemeris: "Moshier"`). |

완전한 필드 계약 — 모든 키, 유형, 에이전트 호출 프로토콜 — 은 **[AGENTS.md](./AGENTS.md)**를 참조하세요.

### 알아야 할 필드 특이성

- **`aspects`는 JSON에서 제한되지 않습니다.** JSON 경로는 *모든* 검출된 상을 반환하며, orb로 오름차순으로 정렬됩니다(가장 긴밀함부터). 10항목 제한은 마크다운 리포트에만 존재합니다.
- **`ziwei.horoscope`는 최선의 노력이며 `null`일 수 있습니다.** try/except으로 감싸짐; 예외 발생 시 `null`로 직렬화됩니다. 존재할 때 `{ decadal, yearly }`입니다. (이 하위 객체는 문서화된 자리 표시자를 넘어서는 추가 내부 구조 — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star` 등을 노출합니다.)
- **별 문자열은 밝기 + 사화를 인코딩합니다.** 형식은 `name(brightness)[mutagen]`이며, 각 부분은 선택 사항입니다 — 예: `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, 또는 plain `天機`. `adjective_stars`는 plain names만 (밝기/사화 없음).

---

## 정확도 계층

모든 출력이 동일한 신뢰도를 가지지는 않습니다. 각 계층을 그에 따라 읽으세요:

| 계층 | 적용 범위 | 신뢰도 |
|------|---------|-------|
| **최고** | 행성 황경도, 별자리, 역행, 플러스 자미두수 별 위치 / 명궁·신궁 / 오행국 — 순수 ephemeris 및 달력 수학. | 천문학적/역법적으로 정확. |
| **높음, 시간 의존** | 상승점, 천정점, 12개 모든 궁 쿠스프, 각 행성이 속하는 궁, 인류도 라인, 자미두수 시진 인덱스. | 정확한 *출생 시간이 정확할 경우*; 분(minute)에 민감. |
| **검증됨** | 자미두수 별 밝기 — iztro 라이브러리의 출력과 정렬됨. | 라이브러리에 대해 검증됨. |
| **플래그 경계 ±0.3°** | 경계 내 ±0.3°에 있는 모든 행성 / 게이트 / 라인. | 잠정적으로 취급하고 영향을 주목하세요 — ±0.3°는 경계를 넘게 할 수 있습니다. |

---

## 알려진 제한 사항

- **Chiron / 소행성 없음.** 빌드는 Moshier ephemeris(`swe.FLG_MOSEPH`, 데이터 파일 없음)를 사용하는데, Chiron이나 다른 소행성을 제공하지 않습니다. 10개의 고전 행성과 달의 교점만 계산됩니다.
- **자미두수는 하나의 기본 학파를 사용합니다.** iztro는 고정된 옵션(`bySolar(..., True, 'zh-TW')`)으로 호출되며, 별 배치 학파와 사화는 iztro의 기본값입니다. 보통 비성(飛星) 또는 다른 학파를 사용한다면, 주요 구조는 변경되지 않지만 일부 세부 사항은 다를 수 있습니다.
- **대략적인 출생 시간은 시간 의존 계층을 악화시킵니다.** 출생 시간이 불확실한 경우, 상승점/MC/궁 할당, 인류도 라인, 시진 — 그리고 그들에서 유래된 모든 것 — 신뢰할 수 없게 됩니다. 그 경우 **시간 의존 필드를 잠정적으로 취급하세요** 그리고 **사건 기반 직경(event-based rectification)**을 고려하세요(알려진 삶의 사건을 차트 타이밍과 매칭). 신뢰하기 전에.

---

## AI 에이전트 / Hermes에서 사용

의도된 통합 모델은 **자체 설치**이지, SaaS가 아닙니다.

사용자는 이 리포지토리의 URL을 복사하고, **자신의** 에이전트 또는 CLI(Claude Code, Hermes, 스크립트 등)가 **사용자의 머신에서 로컬로** 클론하고 실행합니다. 계산은 사용자 측에서 발생합니다. 호출할 호스팅된 엔드포인트가 없고, 계정도 없으며, **SaaS 통합이 필요하지 않습니다** — 엔진은 상태 비저장, 결정론적, 오프라인 서브프로세스입니다.

퍼블리셔가 이를 네트워크 서비스로 운영하지 않으므로, 다른 사람의 자체 설치에 대해 퍼블리셔에 대해 §13 의무가 발생하지 않습니다. (별개로, §13은 수정되지 않은 로컬 사용이 아니라 네트워크 도달 가능한 *수정된* 버전을 실행하는 운영자만 의무화합니다.)

에이전트의 경우, 계약은 간단합니다: 리포지토리 workdir의 venv Python으로 `--json` 서브프로세스를 전달하고, stdout을 JSON으로 파싱하고, `ok`에서 분기하고(exit 코드 포함), 그 다음 구조화된 객체를 전달합니다. 정리가 필요 없습니다 — 상태 비저장입니다. 완전한 CLI + JSON 계약은 **[AGENTS.md](./AGENTS.md)**에 있습니다.

### AI 에이전트를 위한 복사-붙여넣기 설정

이 블록을 Claude Code, ChatGPT 또는 다른 코딩 에이전트에 바로 붙여넣으세요 — 에이전트에게 도구를 설치하고 호출하는 방법을 알려줍니다:

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

## 라이선싱

이 리포지토리는 **[AGPL-3.0](./LICENSE)** 아래 라이선싱됩니다.

**평문 AGPL-3.0.** GNU GPL-3.0(강력한 카피레프트 라이선스: 소프트웨어를 배포하면 완전한 해당 소스를 동일한 라이선스 아래 릴리스해야 함)에 하나의 추가 조항인 **Section 13**을 더한 것입니다. §13은 "SaaS 허점"을 닫습니다: GPL의 *배포* 트리거를 넘어서, 프로그램을 *수정*하고 수정된 버전과 상호 작용하게 하는 경우 네트워크를 통해, 원격 사용자에게 해당 소스를 제공해야 한다고 추가합니다. (수정되지 않은 업스트림을 네트워크 서비스로 실행하는 것만으로는 §13을 트리거하지 않습니다.) AGPL은 상호주의이지만 무한정 바이러스성이 아닙니다 — AGPL 코드의 파생 또는 연결된 코드에만 도달합니다.

**이 리포지토리가 AGPL인 이유.** 엔진은 **Swiss Ephemeris**(`pyswisseph`을 통해)를 행성 위치 및 궁 쿠스프와 연결합니다. Astrodienst는 Swiss Ephemeris를 **AGPL-3.0 OR a commercial license**로 이중 라이선싱하며, 그 코드는 더 허용적인 것으로 재라이선싱될 수 없습니다. AGPL은 카피레프트이고 이 프로젝트가 링크하므로, 전체 결합 작업은 AGPL이어야 합니다. (`iztro`는 MIT이고 카피레프트를 강제하지 않음; Swiss Ephemeris가 여기서 AGPL을 강제하는 유일한 구성 요소입니다.)

**실제로 의미하는 바.**

| 당신의 행위 | AGPL 의무 |
|-----------|---------|
| **자체 설치**(로컬로 실행) | §13은 *트리거되지 않습니다* — 원격 사용자가 없고, 소스가 이미 있습니다. 깔끔함. |
| **네트워크 서비스로 *수정된* 버전 실행** | §13은 *트리거됩니다* — 원격 사용자에게 배포된 버전의 완전한 해당 소스를 AGPL 아래 제공해야 하며, 수정 사항 포함. 참고: §13의 source-offer 의무는 수정에 따라 조건부입니다 — 수정되지 않은 업스트림을 네트워크 서비스로 실행하는 것만으로는 §13을 트리거하지 않지만, 소스는 어쨌든 공개됩니다. |

**사용 사례가 네트워크 소스 의무에 맞지 않는 경우, 세 가지 옵션:**

1. **AGPL 유지** — 완전한 해당 소스(수정 사항 포함)를 anyone who uses it에게 발행하세요(AGPL 아래 §13에 따라 네트워크 포함). 무료, 협상 없음.
2. **[Astrodienst](https://www.astro.com/swisseph/)에서 Swiss Ephemeris 상용 라이선스 구입** — 이것은 Swiss Ephemeris 부분의 AGPL 의무를 해제하여, 자신의 코드를 재라이선싱하고 닫힌 빌드를 배포/호스팅할 수 있게 합니다. (이것은 Astrodienst의 이중 라이선싱 모델입니다.)
3. **ephemeris 교체** — `pyswisseph`을 허용적으로 라이선싱된 천문 소스로 교체합니다(예: **Skyfield (MIT)** plus the public-domain **JPL DE440** ephemeris — 예시 대안, 유일한 옵션 아님). Swiss Ephemeris가 없으면, 나머지 스택(iztro MIT, plus MPL-2.0/MIT/Apache deps)은 더 이상 AGPL을 강제하지 않으며 전체 리포지토리는 MIT가 될 수 있습니다. 이것은 실제 엔지니어링 작업입니다: 현재 Swiss Ephemeris에서 소스된 모든 것을 재구현해야 합니다 — 행성 황경도, 역행 플래그, Asc/MC, Placidus 궁 쿠스프, 그리고 Human Design 88° design solver의 입력.

전체 저작자 표시 및 의존성당 라이선스는 **[CREDITS.md](./CREDITS.md)**를 참조하세요.

---

## FAQ

**음력을 입력할 수 있나요?**
아니요. 입력은 그레고리력 태양 날짜(`--date YYYY-MM-DD`)와 시계 시간(`--time HH:MM`)입니다. 음력 날짜만 있는 경우, 먼저 변환하세요. 자미두수는 iztro의 태양 진입점(`bySolar`)을 통해 계산됩니다.

**제 출생 시간은 대략적일 뿐입니다 — 문제가 되나요?**
행성 위치는 좋지만, 상승점, 천정점, 궁 쿠스프, 각 행성이 있는 궁, 인류도 라인, 시진은 모두 시간에 민감합니다. 이들을 잠정적으로 취급하세요 그리고 신뢰하기 전에 사건 기반 직경을 고려하세요.

**Chiron / 소행성 / 소행성은 어디에?**
포함되지 않음. 여기서 사용된 Moshier ephemeris는 이들을 제공하지 않습니다. 10개의 고전 행성과 달의 교점만 계산됩니다.

**어느 자미두수 학파를 사용합니까?**
iztro에서 구현한 기본 학파(`bySolar(..., True, 'zh-TW')`). 학파는 사용자 선택 불가.

**전화를 집으로 보내나요 / 네트워크를 사용합니까?**
아니요. 엔진은 완전히 오프라인입니다 — 원격 측정, 네트워크 호출, 부작용 없음. 상태 비저장, 결정론적 일회 서브프로세스입니다.

**닫힌 소스 제품 내에서 사용할 수 있나요?**
AGPL-3.0 아래, 비공개/로컬 사용에는 예. 빌드 배포는 GPL 이송/소스 의무를 트리거하고, *수정된* 빌드를 네트워크 제공하면 AGPL §13을 트리거합니다 — 어느 경우든 해당 소스를 제공해야 합니다. 완전히 폐쇄 소스로 하려면, Astrodienst에서 Swiss Ephemeris 상용 라이선스를 구입하거나 Skyfield + JPL DE440으로 ephemeris를 교체하세요([라이선싱](#licensing) 참조).

---

## 면책 조항

`life-chart-engine`은 **해석적 자기인식 프레임워크이지, 예측 또는 숙명론이 아닙니다**. 출력은 성찰을 위한 구조화된 참고 포인트입니다 — 이들은 사건을 예고하지 않으며 결과를 결정하지 않습니다. 이들을 보정으로 사용하고, 자신의 살아있는 경험을 최종 권위로 사용하세요. 여기의 아무것도 의료, 법률, 심리학 또는 재정 조언이 아닙니다. 이 영역의 결정의 경우, 자격이 있는 전문가와 상담하세요.

---

## 저작자 표시 및 라이선스

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, dual-licensed AGPL-3.0 / commercial (<https://www.astro.com/swisseph/>).
- **iztro** — MIT, 紫微斗數용.
- Full attribution: **[CREDITS.md](./CREDITS.md)**.
- **License:** [AGPL-3.0](./LICENSE).
- **Agent / JSON contract:** [AGENTS.md](./AGENTS.md).
