> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · **Italiano** · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Calcolo determinístico nativo di tre sistemi di carte astrologiche — astrologia natale occidentale, 人類圖 (Human Design) e 紫微斗數 (Zi Wei Dou Shu) — a partire da un singolo dato di nascita.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` è uno strumento da riga di comando piccolo e offline. Si fornisce un dato di nascita — data, ora, fuso orario e coordinate del luogo — e calcola tre sistemi di carte indipendenti in una sola passata, quindi emette un rapporto Markdown leggibile o un oggetto JSON strutturato che programmi e agenti IA possono consumare.

È costruito per persone che desiderano calcoli di carte **riproducibili e verificabili** piuttosto che un'app web a scatola nera: praticanti, sviluppatori che costruiscono strumenti di consapevolezza di sé, e agenti IA che hanno bisogno di un puro passo computazionale. Ogni numero proviene da veri calcoli astronomici e da una vera libreria 紫微斗數 (iztro) — non da un servizio remoto, non da ricerche in cache, e mai sulla rete.

---

## Cosa calcola

Il motore esegue tre sistemi sullo **stesso momento di nascita**, quindi i loro output possono corroborarsi a vicenda. Ogni sistema risponde a un tipo diverso di domanda:

| Sistema | Che cos'è (in semplici parole) | Cosa produce il motore |
|---------|--------------------------------|------------------------|
| **Astrologia natale occidentale** (Tropicale / Placidus) | L'astrologia occidentale classica — dove erano i pianeti contro lo zodiaco alla tua nascita, divisi in 12 case. | Ascendente + Medio Cielo, 12 pianeti/punti (太陽 → Nodo Sud) con segno, grado, casa e indicatore di retrogradazione, tutte le 12 cuspidi delle case, e ogni aspetto rilevato (coniuzione/sestile/quadrato/trigono/opposizione) ordinati per stretta orb. |
| **人類圖 Human Design** | Una sintesi moderna di astrologia, l'I Ching e il sistema dei chakra. Descrive come la tua energia è "cablata" via porte, canali e centri. | Tipo, Autorità, Profilo, Definizione, Croce di Incarnazione, la data di Design 88° precedente, centri definiti/aperti, canali definiti, e attivazioni gate.line per pianeta sia per la carta di Personalità che quella di Design. |
| **紫微斗數 Zi Wei Dou Shu** | Un tradizionale sistema di astrologia cinese che mappa il destino su una tavola a 12 palazzi, popolata da stelle nominate. | 五行局 (Classe dei Cinque Elementi), 命主 (anima) / 身主 (corpo), l'indice 時辰 dell'ora, e dati per palazzo — ganzhi, bandiere 命/身, intervallo di età decennale, e stelle maggiori/minori/aggettivali (con luminosità e 四化). Opzionalmente un oroscopo 大限/流年 best-effort. |

Tipo, Autorità e Definizione in Human Design **non sono hardcoded** — sono derivati dal grafo di connettività dei centri definiti.

---

## Perché il calcolo nativo

Questo motore fa la vera matematica invece di approssimare o chiamare un servizio. Quella scelta compra tre proprietà che importano per qualsiasi strumento di carta serio:

- **Deterministico.** Lo stesso input di nascita produce sempre lo stesso output, byte per byte. Non c'è casualità, nessun modello, nessuna deriva di arrotondamento tra le esecuzioni.
- **Riproducibile.** Chiunque con il repository e gli stessi input può rigenerare la tua carta esatta. I calcoli usano astronomy-engine per il cielo e iztro per 紫微斗數 — entrambi deterministici.
- **Verificabile trasversalmente.** Perché tre sistemi indipendenti sono calcolati da un momento di nascita, puoi triangolare. **Quando tutti e tre i sistemi puntano allo stesso segnale, trattalo come alta fiducia. Quando solo un sistema mostra un dettaglio, trattalo come un punto di riferimento, non una conclusione.** Questo è il principio di design core del motore — produce fatti da leggere trasversalmente, non un unico verdetto.

---

## Inizio rapido

### Installazione in una riga (consigliata)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Installa in `~/.life-chart-engine` (sovrascrivibile con `LIFE_CHART_DIR`). Nessun `sudo`, nessuna modifica di sistema — clona solo il repo, crea un venv CPython 3.12 isolato e genera il bundle Node iztro fissato. Richiede `git`, [`uv`](https://docs.astral.sh/uv/) e Node.js/npm. Riesegui in qualsiasi momento per aggiornare all'ultima versione.

### Dal sorgente

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Cosa fa `setup.sh`

Esegue sotto `set -euo pipefail` e svolge sei passaggi:

1. **Risolve la posizione del venv** — `${LIFE_VENV:-<repo>/.venv}`. Imposta la variabile d'ambiente `LIFE_VENV` per sovrascrivere; il `.venv/` predefinito è git-ignored.
2. **Preflight: richiede [`uv`](https://docs.astral.sh/uv/)** — se `uv` non è su `PATH` esce con `1` e stampa l'hint di installazione:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Crea un venv di CPython 3.12** — `uv venv --python 3.12 "$VENV"` (vedi [Perché CPython 3.12](#why-cpython-312-specifically)).
4. **Installa dipendenze pinned** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Costruisce il bundle iztro fissato** — esegue `scripts/build-iztro-bundle.sh`, che installa `iztro@2.5.8` in una directory di build temporanea e produce `vendor/iztro.cjs`.
6. **Esegue uno smoke test** — avvia il motore una volta con input di esempio fissi (scartando stdout) e stampa `OK — engine runs.` in caso di successo. Stampa anche suggerimenti d'uso per entrambe le modalità.

### Passaggi `uv` manuali (niente `setup.sh`)

```bash
# 1. Crea venv di CPython 3.12 (predefinito <repo>/.venv; sovrascrivi con LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Installa dipendenze pinned
uv pip install --python .venv/bin/python -r requirements.txt

# 3. Costruisci il bundle iztro fissato
bash scripts/build-iztro-bundle.sh

# 4. (Opzionale) smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Le dipendenze dirette Python sono fissate in `requirements.txt`:

```
astronomy-engine>=2.1.19
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei usa un bundle Node generato e fissato da `scripts/build-iztro-bundle.sh`:

```
iztro@2.5.8
```

---

## Perché CPython 3.12 nello specifico

Il motore attualmente gira sul runtime verificato **CPython 3.12**. Il motivo è dichiarato allo stesso modo in `requirements.txt` e `setup.sh`:

> CPython 3.12 resta bloccato per questa modifica. Il vecchio vincolo di dipendenza nativa Python per Zi Wei è sparito, quindi potrà essere rivalutato dopo aver controllato le dipendenze rimanenti e l'immagine di deploy.

In breve: 3.12 è ancora il runtime testato per questa release. La dipendenza Zi Wei non impone più quel blocco, quindi un bump della versione Python è un controllo di compatibilità successivo, non parte di questo refactor.

---

## Utilizzo

Il motore ha due modalità, selezionate dalla presenza del flag `--json`.

### Modalità umana (Markdown)

Ometti `--json` per ottenere un rapporto di console leggibile. Usa il Python del tuo venv:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Esempio reale ritagliato (gli aspetti sono limitati a top-10 in modalità Markdown):

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

### Modalità agente (JSON)

Aggiungi `--json` per ottenere un oggetto JSON su stdout e niente altro — ideale per programmi e agenti IA:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Esempio reale ritagliato (array troncati a 1–2 elementi; valori verbatim):

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

## Riferimento ai flag della CLI

Non ci sono **flag `required=True`** — argparse non errori mai su uno mancante. Omettere `--date`/`--time`/`--tz`/`--lat`/`--lon` fallback silenziosamente a una persona di esempio incorporata (`範例`, nata `2000-01-01 12:00`, UTC+8, Taipei 101). Quindi per una carta corretta, forniscili tutti.

| Flag | Tipo | Richiesto per un uso corretto? | Predefinito | Formato / regola |
|------|------|------|----------|---------------|
| `--name` | string | No (cosmetico) | `"範例"` | Testo libero; ecoato solo nell'output. |
| `--gender` | string | Solo per 紫微 | `"女"` | Deve essere esattamente `男` o `女` (argparse `choices`; qualsiasi altro → esci `2`). |
| `--date` | string | **Sì** | fallback a `2000-01-01` | `YYYY-MM-DD`, diviso su `-`. Nessun requisito di zero-pad. |
| `--time` | string | **Sì** | fallback a `12:00` | `HH:MM`, orologio locale a 24 ore, diviso su `:`. |
| `--tz` | float | **Sì** | fallback a `8.0` | Offset UTC incluso DST (Taiwan = `8`). Scritto nella chiave input `tz_offset`. |
| `--lat` | float | **Sì** | fallback a `25.0330` | Latitudine in gradi decimali (case occidentali/Asc/MC). |
| `--lon` | float | **Sì** | fallback a `121.5654` | Longitudine in gradi decimali. |
| `--target` | string | No | `"2025-01-01"` | `YYYY-MM-DD`; data di riferimento del periodo fortunato 紫微 (運限參考日). |
| `--json` | flag | No | `False` (Markdown) | Presenza → modalità JSON; assenza → Markdown. Non prende valore. |

> Il motore **non** geocodifica i luoghi o cerca i fusi orari. Chi chiama deve convertire luogo → `lat`/`lon`/`tz` da sé — e il fuso orario/DST è la fonte di errore più comune, quindi verifica l'offset UTC che si applicava al luogo di nascita e alla data di nascita.

---

## Riferimento output

L'envelope `--json` ha sette chiavi di livello superiore, in questo ordine:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Blocco | Sintesi |
|-------|---------|
| `ok` | `true` al successo (`false` nell'envelope di errore). |
| `schema_version` | `"1.1"`. |
| `input` | Echo degli input normalizzati: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (nota `tz_offset`, non `tz`). |
| `western` | Stringa `system`, oggetti di posizione `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (oggetto o `null`). |
| `meta` | `{ engine, version, ephemeris }` — tutti letterali (`ephemeris: "astronomy-engine"`). |

Per il contratto di campo completo — ogni chiave, tipo, e il protocollo di invocazione dell'agente — vedi **[AGENTS.md](./AGENTS.md)**.

### Peculiarità di campo che vale la pena sapere

- **`aspects` NON sono limitati in JSON.** Il percorso JSON restituisce *ogni* aspetto rilevato, ordinato ascendente per orb (più stretto per primo). Il limite di 10 elementi esiste solo nel rapporto Markdown.
- **`ziwei.horoscope` è best-effort e può essere `null`.** È racchiuso in `try/except`; su qualsiasi eccezione viene serializzato come `null`. Quando presente è `{ decadal, yearly }`. (Quegli sotto-oggetti espongono struttura interna extra — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, ecc. — oltre il placeholder documentato.)
- **Le stringhe delle stelle codificano luminosità + 四化.** Il formato è `name(brightness)[mutagen]`, con ogni parte opzionale — es. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, o semplice `天機`. `adjective_stars` sono solo nomi (nessuna luminosità/mutagen).

---

## Livelli di accuratezza

Non ogni output ha la stessa fiducia. Leggi ogni livello di conseguenza:

| Livello | Cosa copre | Fiducia |
|--------|------------|---------|
| **Più alto** | Longitudini planetarie, segni, retrogradazione, più posizionamento stelle 紫微 / 命宮·身宮 / 五行局 — pura matematica efemeridica e di calendario. | Esatta dal punto di vista astronomico/calendariale. |
| **Alto, dipendente dal tempo** | Ascendente, Medio Cielo, tutte le 12 cuspidi delle case, la casa dove ogni pianeta cade, linee di Human Design, e l'indice 時辰 di 紫微. | Esatta *dato* un tempo di nascita accurato; sensibile ai minuti. |
| **Verificato** | Luminosità delle stelle 紫微斗數 — allineato agli output della libreria iztro. | Verificato contro la libreria. |
| **Confine del flag ±0.3°** | Qualsiasi pianeta / gate / linea seduto entro ±0.3° di un confine. | Tratta come provvisorio e nota l'impatto — ±0.3° può capovolgilo oltre la linea. |

---

## Limitazioni note

- **Niente Chirone / corpi minori.** L'adapter espone solo i 10 pianeti classici più i nodi lunari.
- **紫微斗數 usa una scuola predefinita.** iztro viene chiamato con opzioni fisse (`bySolar(..., True, 'zh-TW')`); la scuola di posizionamento delle stelle e 四化 sono qualsiasi iztro prepara. Se normalmente usi 飛星 o un'altra scuola, la struttura principale è invariata ma alcuni dettagli possono differire.
- **L'ora di nascita approssimativa degrada il livello dipendente dal tempo.** Se l'ora di nascita è incerta, le assegnazioni di Ascendente/MC/casa, le linee di Human Design, e 時辰 — e qualsiasi cosa derivata da loro — diventano inaffidabili. In quel caso, **tratta i campi dipendenti dal tempo come provvisori** e considera **rettificazione basata su eventi** (corrispondendo eventi di vita noti al timing della carta) prima di fare affidamento su di loro.

---

## Usalo da un agente IA / Hermes

Il modello di integrazione inteso è **auto-installazione**, non SaaS.

Un utente copia l'URL di questo repository, e **il suo proprio** agente o CLI (Claude Code, Hermes, uno script, ecc.) lo clona e lo esegue **localmente sulla macchina dell'utente**. Il calcolo avviene dal lato dell'utente. Non c'è endpoint ospitato da chiamare, nessun account, e **nessun integrazione SaaS richiesta** — il motore è un subprocess stateless, deterministico, offline.

Il publisher non lo gestisce come servizio di rete. Con MIT, uso locale, modifica, distribuzione e uso in hosting sono consentiti secondo `LICENSE`.

Per gli agenti, il contratto è semplice: dispatch il subprocess `--json` con il Python del venv nel workdir del repo, analizza stdout come JSON, fa branching su `ok` (e il codice di uscita), quindi consegna l'oggetto strutturato. Non è necessaria pulizia — è stateless. Il contratto CLI + JSON completo vive in **[AGENTS.md](./AGENTS.md)**.

### Configurazione copy-paste per il tuo agente IA

Incolla questo blocco direttamente in Claude Code, ChatGPT, o qualsiasi agente di codifica — dice all'agente come installare e chiamare lo strumento:

```text
Configura e usa "life-chart-engine" — una CLI che calcola una carta natale occidentale +
Human Design + Zi Wei Dou Shu (紫微斗數) dai dati di nascita.

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Calcola una carta e leggi stdout come JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Regole:
   - TU risolvi la città di nascita in --lat/--lon e il corretto offset UTC storico
     (consapevole di DST). Lo strumento non geocodifica.
   - Conferma se l'ora di nascita è esatta prima di fidarti dell'ascendente,
     delle case, delle linee di Human Design, o del pilastro dell'ora di Zi Wei.
   - Non fabbricare mai valori di carta — chiama sempre lo strumento.
   - Schema di output completo, codici di uscita, e il contratto dell'agente: ~/.life-chart-engine/AGENTS.md
```

---

## Licenza

Questo repository è concesso in licenza **[MIT](./LICENSE)**.

Il motore usa **astronomy-engine (MIT)** per i calcoli astronomici e **iztro (MIT)** per Zi Wei Dou Shu. Le formule delle case Placidus e il riferimento a Meeus sono accreditati in [CREDITS.md](./CREDITS.md).

Puoi usare, copiare, modificare, distribuire, sublicenziare e vendere copie secondo i termini MIT. Conserva copyright e permission notice nelle parti sostanziali del software.

Vedi **[CREDITS.md](./CREDITS.md)** per attribuzione completa e licenze delle dipendenze.

---

## FAQ

**Posso inserire una data lunare?**
No. Gli input sono una data solare gregoriana (`--date YYYY-MM-DD`) e l'ora dell'orologio (`--time HH:MM`). Se hai solo una data lunare, convertila prima. 紫微斗數 viene calcolato tramite l'entry point solare di iztro (`bySolar`).

**Il mio tempo di nascita è solo approssimativo — è un problema?**
Le posizioni planetarie vanno bene, ma l'Ascendente, il Medio Cielo, le cuspidi delle case, la casa dove ogni pianeta sta, le linee di Human Design, e il 時辰 sono tutti sensibili al tempo. Tratta quelli come provvisori e considera la rettificazione basata su eventi prima di fidarti di loro.

**Dov'è Chirone / asteroidi / corpi minori?**
Non incluso. L'adapter espone solo i 10 pianeti classici più i nodi lunari.

**Quale scuola 紫微斗數 usa?**
La scuola predefinita come implementata da iztro (`bySolar(..., True, 'zh-TW')`). La scuola non è selezionabile dall'utente.

**Fa il "phoning home" / usa la rete?**
No. Il motore è completamente offline — nessuna telemetria, nessuna chiamata di rete, nessun effetto collaterale. È un subprocess stateless, deterministico, una sola volta.

**Posso usarlo in un prodotto closed-source?**
Sì. Il repository è concesso in licenza MIT. Conserva copyright e permission notice nelle parti sostanziali del software.

---

## Disclaimer

`life-chart-engine` è un **framework di auto-consapevolezza interpretativa, non predizione o fatalismo**. Gli output sono punti di riferimento strutturati per la riflessione — non prevedono eventi e non determinano risultati. Usali come calibrazione, con la tua esperienza vissuta come autorità finale. Niente qui è consiglio medico, legale, psicologico o finanziario. Per decisioni in quei domini, consulta un professionista qualificato.

---

## Crediti e licenza

- **astronomy-engine** — Don Cross, MIT; calcoli astronomici.
- **Meeus, Astronomical Algorithms** — riferimento per le formule delle case Placidus.
- **iztro** — MIT, per Zi Wei Dou Shu.
- Attribuzione completa: **[CREDITS.md](./CREDITS.md)**.
- **Licenza:** [MIT](./LICENSE).
- **Contratto agent / JSON:** [AGENTS.md](./AGENTS.md).
