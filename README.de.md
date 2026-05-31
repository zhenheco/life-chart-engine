> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · **Deutsch** · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Deterministische native Berechnung von drei Life-Chart-Systemen — Western-Astrologie, 人類圖 (Human Design) und 紫微斗數 (Zi Wei Dou Shu) — aus einem einzelnen Geburtsrekord.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` ist ein kleines, offlines Kommandozeilentool. Man gibt ihm die Geburtsdaten einer Person — Datum, Uhrzeit, Zeitzone und Ortskoordinaten — und es berechnet in einem Durchgang drei unabhängige Chartsysteme, danach wird entweder ein für Menschen lesbarer Markdown-Bericht oder ein strukturiertes JSON-Objekt für Programme und KI-Agenten ausgegeben.

Es ist für Menschen gedacht, die **reproduzierbare, verifiable** Chartberechnungen wünschen, statt einer Black-Box-Web-App: Praktiker, Entwickler von Selbstbewusstseinskenntnistools und KI-Agenten, die einen reinen Rechenschritt benötigen. Jede Zahl stammt aus echter astronomischer Berechnung (Swiss Ephemeris) und einer echten 紫微斗數-Bibliothek (py-iztro) — nicht von einem Remote-Dienst, nicht aus zwischengespeicherten Abfragen und niemals über das Netzwerk.

---

## Was es berechnet

Das Engine läuft gegen alle drei Systeme zum **gleichen Geburtsmoment**, damit ihre Ausgaben sich gegenseitig bestätigen können. Jedes System beantwortet eine andere Art von Frage:

| System | Was es ist (Umgangssprache) | Was das Engine ergibt |
|--------|-------|--------|
| **Western natal** (Tropical / Placidus) | Klassische westliche Astrologie — wo die Planeten gegen den Tierkreis bei deiner Geburt standen, aufgeteilt in 12 Häuser. | Aszendent + Mittelhimmel, 12 Planeten/Punkte (太陽 → Südknoten) mit Zeichen, Grad, Haus und Retrogradenflag, alle 12 Hauscuspiden und jeder erkannte Aspekt (Konjunktion/Sextil/Quadrat/Trigon/Opposition) sortiert nach Enge. |
| **人類圖 Human Design** | Eine moderne Synthese von Astrologie, dem I-Ging und dem Chakra-System. Beschreibt, wie deine Energie via Gates, Kanäle und Zentren „verdrahtet" ist. | Typ, Autorität, Profil, Definition, Incarnation Cross, das 88°-frühere Design-Datum, definierte/offene Zentren, definierte Kanäle und pro-Planetengateline-Aktivierungen für sowohl Persönlichkeits- als auch Design-Charts. |
| **紫微斗數 Zi Wei Dou Shu** | Ein traditionelles chinesisches Astrologiesystem, das Schicksal auf ein 12-Paläste-Brett abbildet, bevölkert von benannten Sternen. | 五行局 (Fünf-Elemente-Klasse), 命主 (Seele) / 身主 (Körper), der 時辰-Stundenindex und pro-Paläste-Daten — Ganzhi, 命/身-Flags, dezennale Altersbereichs und major/minor/Adjektiv-Sterne (mit Helligkeit und 四化). Optional ein besonderer Versuch 大限/流年-Horoskop. |

Typ, Autorität und Definition im Human Design sind **nicht hardcodiert** — sie werden aus dem Konnektivitätsgraph der definierten Zentren abgeleitet.

---

## Warum native Berechnung

Dieses Engine erledigt die echte Mathematik statt zu approximieren oder einen Dienst aufzurufen. Diese Wahl sichert drei Eigenschaften, die für jedes ernsthafte Chart-Tool wichtig sind:

- **Deterministisch.** Die gleiche Geburtsangabe erzeugt immer die gleiche Ausgabe, Byte für Byte. Es gibt keine Zufälligkeit, kein Modell, keine Rundungsdrift zwischen Läufen.
- **Reproduzierbar.** Jeder mit dem Repo und den gleichen Eingaben kann dein exaktes Chart regenerieren. Berechnungen nutzen Swiss Ephemeris (Moshier-Modell) für den Himmel und py-iztro für 紫微斗數 — beide deterministisch.
- **Cross-verifiable.** Da drei unabhängige Systeme aus einem Geburtsmoment berechnet werden, kannst du triangulieren. **Wenn alle drei Systeme auf das gleiche Signal zeigen, behandle es als hohes Vertrauen. Wenn nur ein System ein Detail zeigt, behandle es als einen Referenzpunkt, nicht als eine Schlussfolgerung.** Das ist das Kerndesignprinzip des Engines — es erzeugt Fakten zum Cross-Lesen, nicht ein einzelnes Urteil.

---

## Quick Start

### One-Line-Installation (empfohlen)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Installiert in `~/.life-chart-engine` (mit `LIFE_CHART_DIR` überschreibbar). Kein `sudo`, keine systemweiten Änderungen — es klont nur das Repo und erstellt ein isoliertes CPython-3.12-venv. Benötigt `git` und [`uv`](https://docs.astral.sh/uv/). Jederzeit erneut ausführen, um auf die neueste Version zu aktualisieren.

### Aus Quellen

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Was `setup.sh` tut

Es läuft unter `set -euo pipefail` und führt fünf Schritte aus:

1. **Resolves the venv location** — `${LIFE_VENV:-<repo>/.venv}`. Setze die `LIFE_VENV` env var, um zu überschreiben; der Standardwert `.venv/` ist git-ignoriert.
2. **Preflight: benötigt [`uv`](https://docs.astral.sh/uv/)** — wenn `uv` nicht auf `PATH` ist, beendet es sich mit `1` und gibt den Install-Hinweis:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Erstellt ein CPython-3.12-venv** — `uv venv --python 3.12 "$VENV"` (siehe [Warum CPython 3.12](#why-cpython-312-specifically)).
4. **Installiert gepin­nte Abhängigkeiten** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Führt einen Smoke Test durch** — führt das Engine einmal mit festgelegten Beispieleingaben aus (verwirft stdout) und gibt `OK — engine runs.` bei Erfolg aus. Es druckt auch Nutzungshinweise für beide Modi.

### Manuelle `uv`-Schritte (ohne `setup.sh`)

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

Die einzigen zwei direkten Abhängigkeiten sind gepin­nt in `requirements.txt`:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## Warum CPython 3.12 speziell

Du musst das Engine auf **CPython 3.12** ausführen — nicht 3.13, nicht 3.14. Der Grund wird identisch angegeben in `requirements.txt` und `setup.sh`:

> py-iztro's native deps (**pythonmonkey / pydantic-core**) have **no wheels for 3.13+/3.14 and fail to build from source**. Pin to 3.12.

Kurz gesagt: `py-iztro` hängt von nativen Erweiterungen ab (`pythonmonkey`, `pydantic-core`), deren vorgefertigte Wheels bei 3.12 enden. Auf 3.13/3.14 gibt es keine Wheels und der Source-Build schlägt fehl. Das ist genau der Grund, warum `setup.sh` `uv venv --python 3.12` aufruft, und warum du das Engine immer mit dem Project-venv's Python aufrufen solltest (`<repo>/.venv/bin/python`), niemals das System-`python3`.

---

## Verwendung

Das Engine hat zwei Modi, ausgewählt durch die Präsenz des `--json`-Flags.

### Human-Modus (Markdown)

Weglassen von `--json` ergibt einen lesbaren Console-Bericht. Nutze dein venv's Python:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Gekürzte echte Probe (Aspekte sind in Markdown-Modus auf Top-10 begrenzt):

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

### Agent-Modus (JSON)

Füge `--json` hinzu, um ein einzelnes JSON-Objekt auf stdout und nichts sonst — ideal für Programme und KI-Agenten:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Gekürzte echte Probe (Arrays auf 1–2 Einträge gekürzt; Werte wörtlich):

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

## CLI-Flags-Referenz

Es gibt **keine `required=True` Flags** — argparse gibt nie einen Fehler bei einem fehlenden aus. Auslassen von `--date`/`--time`/`--tz`/`--lat`/`--lon` fällt stillschweigend auf eine eingebaute Beispielperson zurück (`範例`, geboren `2000-01-01 12:00`, UTC+8, Taipei 101). Also gib für ein korrektes Chart alle an.

| Flag | Typ | Erforderlich für korrekten Einsatz? | Standard | Format / Regel |
|------|------|---------------------------|---------|---------------|
| `--name` | string | Nein (kosmetisch) | `"範例"` | Freitext; wird nur in die Ausgabe echoed. |
| `--gender` | string | Nur für 紫微 | `"女"` | Muss genau `男` oder `女` sein (argparse `choices`; alles andere → exit `2`). |
| `--date` | string | **Ja** | fällt auf `2000-01-01` zurück | `YYYY-MM-DD`, auf `-` geteilt. Keine Zero-Pad-Anforderung. |
| `--time` | string | **Ja** | fällt auf `12:00` zurück | `HH:MM`, 24-Stunden-Ortsuhr, auf `:` geteilt. |
| `--tz` | float | **Ja** | fällt auf `8.0` zurück | UTC-Offset einschließlich DST (Taiwan = `8`). Geschrieben zum Input-Schlüssel `tz_offset`. |
| `--lat` | float | **Ja** | fällt auf `25.0330` zurück | Breitengrad in Dezimalgraden (westliche Häuser/Asc/MC). |
| `--lon` | float | **Ja** | fällt auf `121.5654` zurück | Längengrad in Dezimalgraden. |
| `--target` | string | Nein | `"2025-01-01"` | `YYYY-MM-DD`; 紫微-Glücksperioden-Referenzdatum (運限參考日). |
| `--json` | flag | Nein | `False` (Markdown) | Präsenz → JSON-Modus; Abwesenheit → Markdown. Nimmt keinen Wert an. |

> Das Engine **geocodiert nicht** oder schlägt Zeitzonen nach. Der Aufrufer muss Ort → `lat`/`lon`/`tz` selbst umrechnen — und Zeitzone/DST ist die häufigste Fehlerquelle, also stelle sicher, dass der UTC-Offset verifiziert ist, der am Geburtsort und am Geburtsdatum galt.

---

## Output-Referenz

Die `--json`-Envelope hat sieben Top-Level-Schlüssel in dieser Reihenfolge:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Block | Zusammenfassung |
|-------|---------|
| `ok` | `true` bei Erfolg (`false` in der Fehler-Envelope). |
| `schema_version` | `"1.0"`. |
| `input` | Echo der normalisierten Eingaben: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (beachte `tz_offset`, nicht `tz`). |
| `western` | `system`-String, `ascendant`/`midheaven`-Positionsobjekte, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (Objekt oder `null`). |
| `meta` | `{ engine, version, ephemeris }` — alle Literale (`ephemeris: "Moshier"`). |

Für den vollständigen Feldvertrag — jeden Schlüssel, jeden Typ und das Agent-Aufrufsprotokoll — siehe **[AGENTS.md](./AGENTS.md)**.

### Feldbesonderheiten, die wissenswert sind

- **`aspects` sind NICHT in JSON begrenzt.** Der JSON-Pfad gibt *jeden* erkannten Aspekt zurück, sortiert aufsteigend nach Orb (am engsten zuerst). Die 10-Item-Grenze existiert nur im Markdown-Bericht.
- **`ziwei.horoscope` ist ein bester Versuch und kann `null` sein.** Es ist in `try/except` eingewickelt; bei jeder Ausnahme wird es als `null` serialisiert. Wenn vorhanden ist es `{ decadal, yearly }`. (Diese Teil-Objekte enthüllen zusätzliche interne Struktur — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star` etc. — über den dokumentierten Platzhalter hinaus.)
- **Star-Strings codieren Helligkeit + 四化.** Das Format ist `name(brightness)[mutagen]`, wobei jeder Teil optional ist — z.B. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]` oder einfach `天機`. `adjective_stars` sind nur Namen (keine Helligkeit/Mutagen).

---

## Accuracy-Stufen

Nicht jede Ausgabe trägt das gleiche Vertrauen. Lies jede Stufe entsprechend:

| Stufe | Was sie abdeckt | Vertrauen |
|------|----------------|------------|
| **Höchste** | Planetenlängen, Zeichen, Retrograd plus 紫微-Sternplatzierung / 命宮·身宮 / 五行局 — reine Ephemeris und Kalendermathe. | Astronomisch/kalendarisch exakt. |
| **Hoch, zeitabhängig** | Aszendent, Mittelhimmel, alle 12 Hauscuspiden, das Haus, in dem jeder Planet sitzt, Human-Design-Linien und der 紫微-時辰-Index. | Exakt *mit* einer genauen Geburtszeit; empfindlich gegenüber Minuten. |
| **Verifiziert** | 紫微斗數-Sternhelligkeit — auf die Ausgaben der py-iztro-Bibliothek ausgerichtet. | Gegen die Bibliothek verifiziert. |
| **Flaggrenze ±0,3°** | Jeder Planet / Gate / Linie, der innerhalb ±0,3° einer Grenze sitzt. | Behandle als vorläufig und notiere die Auswirkung — ±0,3° kann es über die Linie kippen. |

---

## Bekannte Einschränkungen

- **Kein Chiron / Nebenkörper.** Der Build verwendet die Moshier-Ephemeris (`swe.FLG_MOSEPH`, keine Datendateien), die Chiron oder andere Nebenkörper nicht bereitstellt. Nur die 10 klassischen Planeten plus die Mondknoten werden berechnet.
- **紫微斗數 nutzt eine Standardschule.** py-iztro wird mit festen Optionen aufgerufen (`by_solar(..., True, 'zh-TW')`); die Stern-Platzierungsschule und 四化 sind, was py-iztro standardmäßig nutzt. Wenn du normalerweise 飛星 oder eine andere Schule nutzt, ist die Hauptstruktur unverändert, aber einige Details können unterscheiden.
- **Ungenaue Geburtszeit degradiert die zeitabhängige Stufe.** Wenn die Geburtszeit unsicher ist, werden die Aszendent/MC/Haus-Zuweisungen, Human-Design-Linien und 時辰 — und alles, was davon abgeleitet ist — unzuverlässig. In diesem Fall **behandle die zeitabhängigen Felder als provisorisch** und erwäge **ereignisbasierte Rektifikation** (Abgleich bekannter Lebenereignisse mit Chart-Timing), bevor du dich darauf verlässt.

---

## Nutze es von einem KI-Agent / Hermes

Das beabsichtigte Integrationmodell ist **Self-Install**, nicht SaaS.

Ein Benutzer kopiert die URL dieses Repos und **sein eigener** Agent oder CLI (Claude Code, Hermes, ein Skript etc.) klont es und führt es **lokal auf der Maschine des Benutzers** aus. Die Berechnung findet auf der Seite des Benutzers statt. Es gibt keinen gehosteten Endpoint aufzurufen, keinen Account und **keine SaaS-Integration erforderlich** — das Engine ist ein zustandsloses, deterministisches, offlines Subprocess.

Da der Herausgeber es nicht als Netzwerkdienst betreibt, fällt §13 für niemanden, der es selbst installiert, auf den Herausgeber. (Separat obligiert §13 nur einen Betreiber, der eine *modifizierte* netzwerkerreichbare Version läuft — nicht unmodifizierte lokale Nutzung.)

Für Agenten ist der Vertrag einfach: dispatch den `--json` Subprocess mit dem venv Python im Repo-Workdir, parse stdout als JSON, verzweige auf `ok` (und den Exit-Code), dann übergebe das strukturierte Objekt. Keine Bereinigung erforderlich — es ist zustandslos. Der vollständige CLI + JSON-Vertrag lebt in **[AGENTS.md](./AGENTS.md)**.

### Copy-Paste-Setup für deinen KI-Agent

Kopiere diesen Block direkt in Claude Code, ChatGPT oder jeden Coding-Agent — es sagt dem Agent, wie das Werkzeug installiert und aufgerufen wird:

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

## Lizenzierung

Dieses Repository ist unter **[AGPL-3.0](./LICENSE)** lizenziert.

**AGPL-3.0 in einfachem Englisch.** Es ist GNU GPL-3.0 (eine starke Copyleft-Lizenz: wenn du die Software verbreitest, musst du deine komplette korrespondierende Quelle unter derselben Lizenz freigeben) **plus eine zusätzliche Klausel, Abschnitt 13**. §13 schließt das „SaaS-Schlupfloch": über den GPL's *Verbreitungs*-Trigger hinaus, fügt es hinzu, dass wenn du das Programm *änderst* und Benutzer deine modifizierte Version über ein Netzwerk verwenden lässt, du diesen Remote-Benutzern deine korrespondierende Quelle anbieten musst. (Das Ausführen eines unmodifizierten Upstream als Netzwerkdienst triggert §13 nicht von sich selbst heraus.) AGPL ist gegenseitig, aber nicht grenzenlos viral — es erreicht nur Code, der ein Derivat von oder mit dem AGPL-Code verlinkt ist.

**Warum dieses Repo AGPL ist.** Das Engine verlinkt **Swiss Ephemeris** (via `pyswisseph`) für Planetenpositionen und Hauscuspiden. Astrodienst **dual-lizenziert** Swiss Ephemeris als **AGPL-3.0 ODER eine kommerzielle Lizenz**, und sein Code kann nicht als etwas Permissiveres neu lizenziert werden. Weil AGPL Copyleft ist und dieses Projekt es verlinkt, muss die ganze kombinierte Arbeit AGPL sein. (`py-iztro` ist MIT und erzwingt keine Copyleft; Swiss Ephemeris ist die einzige Komponente, die hier AGPL erzwingt.)

**Was es praktisch bedeutet.**

| Was du tust | AGPL-Verpflichtung |
|--------|-----------------|
| **Self-Install** (führe es lokal für dich selbst aus) | §13 wird *nicht* getriggert — es gibt keine Remote-Benutzer zu servieren, und du hast bereits die Quelle. Sauber. |
| **Führe eine *modifizierte* Version als Netzwerkdienst aus** | §13 wird *getriggert* — du musst diesen Remote-Benutzern die komplette korrespondierende Quelle deiner eingesetzten Version, unter AGPL, einschließlich deiner Modifikationen anbieten. Beachte: §13's Quellen-Angebots-Verpflichtung ist an Modifikation bedingt — das Ausführen des unmodifizierten Upstream als Netzwerkdienst triggert §13 nicht von sich aus, obwohl die Quelle ohnehin schon öffentlich ist. |

**Deine drei Optionen**, wenn die Netzwerk-Quellen-Verpflichtung nicht zu deinem Anwendungsfall passt:

1. **Behalte AGPL** — veröffentliche deine komplette korrespondierende Quelle (einschließlich Modifikationen) an jeden, der sie nutzt, einschließlich über ein Netzwerk pro §13. Kostenlos, keine Verhandlung.
2. **Kaufe eine Swiss-Ephemeris-Kommerziallizenz von [Astrodienst](https://www.astro.com/swisseph/)** — dies hebt die AGPL-Verpflichtung für den Swiss-Ephemeris-Teil auf, dein eigenes Code neu zu lizenzieren und einen geschlossenen Build zu versenden/hosten. (Das ist Astrodiensts Dual-Lizenzierungsmodell.)
3. **Tausche die Ephemeris aus** — ersetze `pyswisseph` mit einer permissiv-lizenzierten Astronomie-Quelle (zum Beispiel **Skyfield (MIT)** plus die öffentliche Domäne **JPL DE440**-Ephemeris — illustrative Alternativen, nicht die einzige Option). Ohne Swiss Ephemeris erzwingt der verbleibende Stack (py-iztro MIT, plus die MPL-2.0/MIT/Apache-Deps) nicht mehr AGPL und das ganze Repo könnte MIT sein. Das ist echte technische Arbeit: du musst alles neu implementieren, das derzeit von Swiss Ephemeris stammt — Planetenlängen, Retrograden-Flags, Asc/MC, Placidus-Hauscuspiden und die Eingaben für den Human-Design-88°-Design-Solver.

Siehe **[CREDITS.md](./CREDITS.md)** für vollständige Zurechnung und pro-Abhängigkeits-Lizenzen.

---

## FAQ

**Kann ich ein Mondatum eingeben?**
Nein. Eingaben sind ein gregorianisches Sonnendatum (`--date YYYY-MM-DD`) und Tageszeit (`--time HH:MM`). Wenn du nur ein Mondatum hast, konvertiere es zuerst. 紫微斗數 wird via py-iztro's Sonnen-Einstiegspunkt berechnet (`by_solar`).

**Meine Geburtszeit ist nur ungefähr — ist das ein Problem?**
Die Planetenpositionen sind okay, aber der Aszendent, Mittelhimmel, Hauscuspiden, das Haus, in dem jeder Planet sitzt, Human-Design-Linien und die 時辰 sind alle zeitabhängig. Behandle sie als provisorisch und erwäge ereignisbasierte Rektifikation, bevor du dich darauf verlässt.

**Wo sind Chiron / Asteroiden / Nebenkörper?**
Nicht enthalten. Die hier verwendete Moshier-Ephemeris liefert sie nicht; nur die 10 klassischen Planeten und die Mondknoten werden berechnet.

**Welche 紫微斗數-Schule nutzt es?**
Die Standardschule wie von py-iztro implementiert (`by_solar(..., True, 'zh-TW')`). Die Schule ist nicht vom Benutzer wählbar.

**Phont es nach Hause / nutzt das Netzwerk?**
Nein. Das Engine ist vollständig offline — keine Telemetrie, keine Netzwerkanrufe, keine Nebenwirkungen. Es ist ein zustandsloses, deterministisches One-Shot-Subprocess.

**Kann ich es in ein closed-source-Produkt nutzen?**
Unter AGPL-3.0, ja für private/lokale Nutzung. Ein Build verbreiten triggert die GPL konveying/Quellen-Verpflichtungen, und einen *modifizierten* Build netzwerk-servieren triggert AGPL §13 — immer muss du korrespondierende Quelle anbieten. Um vollständig closed-source zu werden, kaufe entweder eine Swiss-Ephemeris-Kommerziallizenz von Astrodienst oder tausche die Ephemeris zu Skyfield + JPL DE440 aus (siehe [Lizenzierung](#licensing)).

---

## Haftungsausschluss

`life-chart-engine` ist ein **interpretives Selbstbewusstsein-Rahmenwerk, keine Vorhersage oder Fatalismus**. Die Ausgaben sind strukturierte Referenzpunkte für Reflexion — sie sagen Ereignisse nicht voraus und bestimmen keine Ergebnisse. Nutze sie als Kalibrierung, mit deinem eigenen gelebten Erlebnis als letzte Autorität. Nichts hier ist medizinischer, juristischer, psychologischer oder finanzieller Rat. Für Entscheidungen in diesen Bereichen konsultiere einen qualifizierten Fachmann.

---

## Guthaben & Lizenz

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, dual-lizenziert AGPL-3.0 / kommerziell (<https://www.astro.com/swisseph/>).
- **py-iztro** (und upstream `iztro`) — MIT, für 紫微斗數.
- Vollständige Zurechnung: **[CREDITS.md](./CREDITS.md)**.
- **Lizenz:** [AGPL-3.0](./LICENSE).
- **Agent / JSON-Vertrag:** [AGENTS.md](./AGENTS.md).
