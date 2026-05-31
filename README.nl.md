> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · **Nederlands** · [Polski](./README.pl.md)

# life-chart-engine

**Deterministische native berekening van drie levensgrafiek-systemen — Western astrologie, Human Design (人類圖) en Zi Wei Dou Shu (紫微斗數) — vanuit één geboortegegevens.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` is een klein, offline opdrachtregelgereedschap. Je geeft het de geboortegegevens van één persoon — datum, tijd, tijdzone en plaatscoördinaten — en het berekent drie onafhankelijke grafiek-systemen in één keer, vervolgens genereert het óf een leesbaar Markdown-rapport óf een gestructureerd JSON-object voor programma's en AI-agents.

Het is gebouwd voor mensen die **reproduceerbare, verifieerbare** grafiekberekeningen willen in plaats van een ondoorzichtige web-app: beoefenaars, ontwikkelaars die zelf-bewustzijnshulpmiddelen bouwen, en AI-agents die een pure rekenstap nodig hebben. Elk getal komt uit echte astronomische berekening (Swiss Ephemeris) en een echte Zi Wei Dou Shu-bibliotheek (py-iztro) — niet van een remote service, niet van gecachede opzoekingen, en nooit via het netwerk.

---

## Wat het berekent

De engine voert drie systemen uit tegen **hetzelfde geboortemoment**, zodat hun uitvoer elkaar kan corroboreren. Elk systeem beantwoordt een ander soort vraag:

| Systeem | Wat het is (duidelijk Nederlands) | Wat de engine oplevert |
|---------|-----------------------------------|------------------------|
| **Western natal** (Tropical / Placidus) | Klassieke westerse astrologie — waar de planeten tegen de dierenriem stonden op het moment van uw geboorte, verdeeld in 12 huizen. | Ascendant + Midheaven, 12 planeten/punten (太陽 → 南交點) met teken, graad, huis en retrograde-vlag, alle 12 huiscuspden, en elk gedetecteerd aspect (合相/六分/四分/三分/對分) gesorteerd op nauwheid. |
| **Human Design** (人類圖) | Een moderne synthese van astrologie, de I-Ching en het chakra-systeem. Beschrijft hoe uw energie via poorten, kanalen en centra is "bedrading". | Type, Authority, Profile, Definition, Incarnation Cross, de 88°-eerdere Design-datum, gedefinieerde/open centra, gedefinieerde kanalen, en per-planeet poort.lijn-activeringen voor zowel de Personality- als Design-grafieken. |
| **Zi Wei Dou Shu** (紫微斗數) | Een traditioneel Chinees astrologiesysteem dat lot op een 12-paleis-bord in kaart brengt, bevolkt door benoemde sterren. | 五行局 (Five Elements Class), 命主 (ziel) / 身主 (lichaam), de 時辰 uur-index, en per-paleis-gegevens — ganzhi, 命/身-vlaggen, decennium-leeftijdsbereik, en hoofd-/neven-/bijvoeglijk sterren (met helderheid en 四化). Optioneel een best-effort 大限/流年 horoscoop. |

Type, Authority en Definition in Human Design zijn **niet hardgecodeerd** — zij worden afgeleid uit de connectiviteitsgrafiek van de gedefinieerde centra.

---

## Waarom native berekening

Deze engine doet de echte wiskunde in plaats van benadering of het aanroepen van een service. Die keuze levert drie eigenschappen op die belangrijk zijn voor elk serieus grafiek-hulpmiddel:

- **Deterministisch.** Dezelfde geboorte-invoer levert altijd dezelfde uitvoer op, byte-voor-byte. Er is geen willekeur, geen model, geen afrondings-drift tussen runs.
- **Reproduceerbaar.** Iedereen met de repository en dezelfde invoer kan uw exacte grafiek opnieuw genereren. Berekeningen gebruiken Swiss Ephemeris (Moshier-model) voor de lucht en py-iztro voor Zi Wei Dou Shu — beide deterministisch.
- **Kruislings verifieerbaar.** Omdat drie onafhankelijke systemen worden berekend vanuit één geboortemoment, kun je trianguleren. **Wanneer alle drie systemen naar hetzelfde signaal wijzen, beschouw het als hoog vertrouwen. Wanneer slechts één systeem een detail toont, beschouw het als een referentiepunt, geen conclusie.** Dit is het kernontwerp-principe van de engine — het levert feiten op om kruislings te lezen, niet één vonnis.

---

## Snelstart

### Eenregelige installatie (aanbevolen)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Installeert in `~/.life-chart-engine` (overschrijf met `LIFE_CHART_DIR`). Geen `sudo`, geen systeembrede wijzigingen — het klont alleen de repo en bouwt een geïsoleerde CPython 3.12 venv. Vereist `git` en [`uv`](https://docs.astral.sh/uv/). Voer op elk moment opnieuw uit om bij te werken naar de nieuwste versie.

### Van bron

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Wat `setup.sh` doet

Het draait onder `set -euo pipefail` en voert vijf stappen uit:

1. **Lost de venv-locatie op** — `${LIFE_VENV:-<repo>/.venv}`. Stel de `LIFE_VENV` omgevingsvariabele in om te overschrijven; de standaard `.venv/` wordt genegeerd door git.
2. **Voorflight: vereist [`uv`](https://docs.astral.sh/uv/)** — als `uv` niet op `PATH` staat, wordt het met exit `1` beëindigd en afdrukken de installatiehint:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Creëert een CPython 3.12 venv** — `uv venv --python 3.12 "$VENV"` (zie [Waarom CPython 3.12](#why-cpython-312-specifically)).
4. **Installeert vastgestelde afhankelijkheden** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Voert een smoke test uit** — voert de engine eenmaal uit met vaste voorbeeld-invoer (stdout negeren) en drukt `OK — engine runs.` af bij succes. Het drukt ook gebruikshints af voor beide modi.

### Handmatige `uv` stappen (geen `setup.sh`)

```bash
# 1. Creëer CPython 3.12 venv (standaard <repo>/.venv; overschrijf met LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Installeer vastgestelde deps
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (Optioneel) smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

De enige twee directe afhankelijkheden worden vastgesteld in `requirements.txt`:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## Waarom CPython 3.12 specifiek

Je moet de engine op **CPython 3.12** uitvoeren — niet 3.13, niet 3.14. De reden wordt identiek gesteld in `requirements.txt` en `setup.sh`:

> py-iztro's native afhankelijkheden (**pythonmonkey / pydantic-core**) hebben **geen wheels voor 3.13+/3.14 en slagen niet om uit bron te bouwen**. Fixeer op 3.12.

Kort gezegd: `py-iztro` hangt af van native extensies (`pythonmonkey`, `pydantic-core`) waarvan de voorgegenereerde wheels stoppen bij 3.12. Op 3.13/3.14 zijn er geen wheels en de bron-build slaagt niet. Dat is precies waarom `setup.sh` `uv venv --python 3.12` aanroept, en waarom je de engine altijd moet aanroepen met de project venv's Python (`<repo>/.venv/bin/python`), nooit het systeem `python3`.

---

## Gebruik

De engine heeft twee modi, geselecteerd door de aanwezigheid van de `--json`-vlag.

### Menselijke modus (Markdown)

Laat `--json` weg om een leesbaar consolerapport te krijgen. Gebruik uw venv's Python:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Ingekort reëel voorbeeld (aspecten zijn beperkt tot top-10 in Markdown-modus):

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

### Agent-modus (JSON)

Voeg `--json` toe om één JSON-object op stdout en niets anders — ideaal voor programma's en AI-agents:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Ingekort reëel voorbeeld (arrays afgekapt tot 1–2 invoer; waarden woordelijk):

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

## CLI-vlaggen referentie

Er zijn **geen `required=True` vlaggen** — argparse geeft nooit een fout op een ontbrekende. Het weglaten van `--date`/`--time`/`--tz`/`--lat`/`--lon` valt stilzwijgend terug op een ingebouwde voorbeeldpersoon (`範例`, geboren `2000-01-01 12:00`, UTC+8, Taipei 101). Voor een correct diagram moet je ze allemaal opgeven.

| Vlag | Type | Vereist voor correct gebruik? | Standaard | Indeling / regel |
|------|------|------|---------|---------------|
| `--name` | string | Nee (cosmetisch) | `"範例"` | Vrije tekst; alleen in uitvoer weergegeven. |
| `--gender` | string | Alleen voor Zi Wei | `"女"` | Moet exact `男` of `女` zijn (argparse `choices`; iets anders → exit `2`). |
| `--date` | string | **Ja** | valt terug op `2000-01-01` | `YYYY-MM-DD`, gesplitst op `-`. Geen nul-pad vereist. |
| `--time` | string | **Ja** | valt terug op `12:00` | `HH:MM`, 24-uurs lokale klok, gesplitst op `:`. |
| `--tz` | float | **Ja** | valt terug op `8.0` | UTC-offset inclusief zomeruur (Taiwan = `8`). Geschreven naar invoersleutel `tz_offset`. |
| `--lat` | float | **Ja** | valt terug op `25.0330` | Breedtegraad in decimale graden (westerse huizen/Asc/MC). |
| `--lon` | float | **Ja** | valt terug op `121.5654` | Lengtegraad in decimale graden. |
| `--target` | string | Nee | `"2025-01-01"` | `YYYY-MM-DD`; Zi Wei geluk-periode referentiedatum (運限參考日). |
| `--json` | vlag | Nee | `False` (Markdown) | Aanwezigheid → JSON-modus; afwezigheid → Markdown. Neemt geen waarde. |

> De engine voert **geen** geocodering uit of slaat tijdzones op. De oproeper moet plaats → `lat`/`lon`/`tz` zelf omzetten — en tijdzone/zomeruur is de meest voorkomende foutbron, dus verifieer de UTC-offset die van toepassing was op de geboorteplek en geboortedatum.

---

## Uitvoerreferentie

De `--json` envelop heeft zeven top-level sleutels, in deze volgorde:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Blok | Samenvatting |
|------|---------|
| `ok` | `true` bij succes (`false` in fout-envelop). |
| `schema_version` | `"1.0"`. |
| `input` | Echo van genormaliseerde invoer: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (merk op `tz_offset`, niet `tz`). |
| `western` | `system` string, `ascendant`/`midheaven` positieobjecten, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (object of `null`). |
| `meta` | `{ engine, version, ephemeris }` — allemaal letterlijke waarden (`ephemeris: "Moshier"`). |

Voor het volledige veldcontract — elke sleutel, type en het agent-oproep-protocol — zie **[AGENTS.md](./AGENTS.md)**.

### Veldbijzonderheden die het waard zijn om te kennen

- **`aspects` zijn NIET beperkt in JSON.** Het JSON-pad retourneert *elk* gedetecteerd aspect, oplopend gesorteerd op orb (strakst eerst). De 10-item-limiet bestaat alleen in het Markdown-rapport.
- **`ziwei.horoscope` is best-effort en kan `null` zijn.** Het wordt ingesloten in `try/except`; bij uitzondering wordt het geserialiseerd als `null`. Wanneer aanwezig is het `{ decadal, yearly }`. (Die sub-objecten stellen extra interne structuur bloot — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, enz. — voorbij de gedocumenteerde placeholder.)
- **Star-strings coderen helderheid + 四化.** Indeling is `name(brightness)[mutagen]`, met elk onderdeel optioneel — bijv. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, of gewoon `天機`. `adjective_stars` zijn alleen namen (geen helderheid/mutagen).

---

## Nauwkeurigheid-lagen

Niet elke uitvoer draagt hetzelfde vertrouwen. Lees elke laag dienovereenkomstig:

| Laag | Wat het omvat | Vertrouwen |
|------|----------------|------------|
| **Hoogste** | Planetaire lengtes, tekens, retrograde, plus Zi Wei sterplaatsing / 命宮·身宮 / 五行局 — pure efemerisis en kalender-wiskunde. | Astronomisch/kalendarisch exact. |
| **Hoog, tijd-afhankelijk** | Ascendant, Midheaven, alle 12 huiscuspden, het huis waarin elke planeet valt, Human Design-lijnen, en de Zi Wei 時辰 index. | Exact *gegeven* een nauwkeurig geboortemoment; gevoelig voor minuten. |
| **Geverifieerd** | Zi Wei Dou Shu sterhelderheid — afgestemd op de py-iztro bibliotheekuitvoer. | Geverifieerd tegen de bibliotheek. |
| **Vlaggrens ±0.3°** | Elke planeet / poort / lijn die binnen ±0.3° van een grens zit. | Behandel als voorlopig en noteer de impact — ±0.3° kan het erover heen kantelen. |

---

## Bekende beperkingen

- **Geen Chiron / kleine lichamen.** De bouw gebruikt de Moshier-efemerisis (`swe.FLG_MOSEPH`, geen databestanden), die Chiron of andere kleine lichamen niet levert. Alleen de 10 klassieke planeten plus de maanknooplijnen worden berekend.
- **Zi Wei Dou Shu gebruikt één standaard-school.** py-iztro wordt aangeroe met vaste opties (`by_solar(..., True, 'zh-TW')`); de ster-plaatsingsschool en 四化 zijn wat py-iztro standaard doet. Als je normaal 飛星 of een andere school gebruikt, blijft de hoofdstructuur ongewijzigd maar kunnen sommige details verschillen.
- **Benaderde geboortemoment verslechtert de tijd-afhankelijke laag.** Als het geboortemoment onzeker is, worden de Ascendant/MC/huistoewijzingen, Human Design-lijnen en 時辰 — en alles wat ervan is afgeleid — onbetrouwbaar. In dat geval, **behandel de tijd-afhankelijke velden als voorlopig** en overweeg **event-gebaseerde rectificatie** (bekende levensgebeurtenissen afstemmen op grafiek-timing) voordat je erop vertrouwt.

---

## Gebruik het van een AI-agent / Hermes

Het beoogde integratie-model is **self-install**, niet SaaS.

Een gebruiker kopieert deze repo's URL, en **hun eigen** agent of CLI (Claude Code, Hermes, een script, enz.) klont het en voert het **lokaal op de machine van de gebruiker** uit. De berekening gebeurt aan de zijde van de gebruiker. Er is geen gehoste eindpunt om aan te roepen, geen account, en **geen SaaS-integratie vereist** — de engine is een stateless, deterministisch, offline subproces.

Omdat de uitgever het niet als netwerkservice exploiteert, geldt geen §13-verplichting voor de uitgever voor iemands self-install. (Afzonderlijk is §13 alleen een uitgever verbonden die een *gewijzigde* netwerktoegankelijke versie draait — niet ongewijzigd lokaal gebruik.)

Voor agents is het contract eenvoudig: verzend het `--json` subproces met de venv Python in de repo workdir, parse stdout als JSON, vertakkingen op `ok` (en de exit-code), en geef het gestructureerde object af. Geen opschoning nodig — het is stateless. Het volledige CLI + JSON-contract staat in **[AGENTS.md](./AGENTS.md)**.

### Copy-paste-setup voor uw AI-agent

Plak dit blok rechtstreeks in Claude Code, ChatGPT of een coderingsagent — het vertelt de agent hoe het gereedschap moet worden geïnstalleerd en aangeroepen:

```text
Stel "life-chart-engine" in en gebruik het — een CLI die een Western natal-grafiek +
Human Design + Zi Wei Dou Shu (紫微斗數) berekent uit geboortevgegevens.

1. Installeer (vereist `git` en `uv`; als uv ontbreekt: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Bereken een grafiek en lees stdout als JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Regels:
   - JIJ lost de geboorteplek op naar --lat/--lon en de juiste historische UTC
     offset (zomeruur-bewust). Het gereedschap voert geen geocodering uit.
   - Bevestig of het geboortemoment exact is voordat je het ascendant,
     huizen, Human Design-lijnen of de Zi Wei uurpijler vertrouwt.
   - Maak nooit grafiekwaarden zelf — roep het gereedschap altijd aan.
   - Volledige uitvoerschema, exit-codes en het agent-contract: ~/.life-chart-engine/AGENTS.md
```

---

## Licentie

Deze repository is gelicentieerd onder **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 in duidelijk Nederlands.** Het is de GNU GPL-3.0 (een sterke copyleft-licentie: als je de software distribueert, moet je je volledige overeenkomstige bron onder dezelfde licentie vrijgeven) **plus één extra clausule, Sectie 13**. §13 sluit de "SaaS-uitzondering" af: voorbij de verdeling-trigger van de GPL, voegt het toe dat als je het programma *wijzigt* en gebruikers je gewijzigde versie over een netwerk laat interageren, je die externe gebruikers je overeenkomstige bron moet aanbieden. (Het uitvoeren van een ongewijzigde upstream als netwerkservice triggert §13 op zich niet.) AGPL is wederkerig maar niet grenzeloos viraal — het bereikt alleen code die een derivaat of gekoppeld is met de AGPL-code.

**Waarom deze repo AGPL is.** De engine koppelt **Swiss Ephemeris** (via `pyswisseph`) voor planetaire posities en huiscuspden. Astrodienst **tweevoudig licentieert** Swiss Ephemeris als **AGPL-3.0 OF een commerciële licentie**, en de code kan niet onder iets permissiever opnieuw worden gelicentieerd. Omdat AGPL copyleft is en dit project het koppelt, moet het gehele gecombineerde werk AGPL zijn. (`py-iztro` is MIT en legt geen copyleft op; Swiss Ephemeris is de enige component die AGPL hier forceert.)

**Wat het in de praktijk betekent.**

| Je doet | AGPL-verplichting |
|--------|-----------------|
| **Self-install** (lokaal voor jezelf uitvoeren) | §13 wordt *niet* geactiveerd — er zijn geen externe gebruikers om te bedienen, en je hebt al de bron. Schoon. |
| **Een *gewijzigde* versie als netwerkservice uitvoeren** | §13 *wordt* geactiveerd — je moet die externe gebruikers de volledige overeenkomstige bron van je ingezette versie aanbieden, onder AGPL, inclusief jouw wijzigingen. Opmerking: §13's source-aanbod-plicht is conditioneel op wijziging — het uitvoeren van de ongewijzigde upstream als netwerkservice triggert §13 op zich niet, hoewel de bron toch al openbaar is. |

**Jouw drie opties** als de netwerkbron-verplichting niet past bij jouw geval:

1. **AGPL behouden** — publiceer jouw volledige overeenkomstige bron (inclusief wijzigingen) aan iedereen die het gebruikt, inclusief over een netwerk per §13. Gratis, geen onderhandeling.
2. **Koop een commerciële Swiss Ephemeris-licentie van [Astrodienst](https://www.astro.com/swisseph/)** — dit tilt de AGPL-verplichting voor het Swiss Ephemeris-gedeelte, waardoor je jouw eigen code opnieuw kunt licentiëren en een gesloten bouw/host kunt verzenden. (Dit is Astrodienst's dual-licensing-model.)
3. **Wissel de efemerisis** — vervang `pyswisseph` door een permissief gelicentieerde astronomie-bron (bijv. **Skyfield (MIT)** plus de publiek-domein **JPL DE440** efemerisis — illustratieve alternatieven, niet de enige optie). Met Swiss Ephemeris weg, dwingt de resterende stack (py-iztro MIT, plus de MPL-2.0/MIT/Apache deps) AGPL niet meer af en zou de hele repo MIT kunnen zijn. Dit is echte engineering-inspanning: je moet alles wat momenteel afkomstig is van Swiss Ephemeris opnieuw implementeren — planetaire lengtes, retrograde-vlaggen, Asc/MC, Placidus-huiscuspden en de invoer naar de Human Design 88° design-oplosser.

Zie **[CREDITS.md](./CREDITS.md)** voor volledige attributie en per-afhankelijkheid licenties.

---

## Veelgestelde vragen

**Kan ik een maankalender-datum invoeren?**
Nee. Invoer zijn een Gregoriaanse zonnedatum (`--date YYYY-MM-DD`) en klok-tijd (`--time HH:MM`). Als je alleen een maankalender-datum hebt, zet het eerst om. Zi Wei Dou Shu wordt berekend via py-iztro's zonne-invoerpunt (`by_solar`).

**Mijn geboortemoment is alleen benaderend — is dat een probleem?**
De planetaire posities zijn prima, maar het Ascendant, Midheaven, huiscuspden, het huis waarin elke planeet zit, Human Design-lijnen en de 時辰 zijn allemaal tijd-gevoelig. Behandel die als voorlopig en overweeg event-gebaseerde rectificatie voordat je erop vertrouwt.

**Waar zijn Chiron / asteroïden / kleine lichamen?**
Niet inbegrepen. De Moshier-efemerisis die hier wordt gebruikt, levert ze niet; alleen de 10 klassieke planeten en de maanknooplijnen worden berekend.

**Welke Zi Wei Dou Shu-school gebruikt het?**
De standaard-school zoals geïmplementeerd door py-iztro (`by_solar(..., True, 'zh-TW')`). De school kan niet door de gebruiker worden geselecteerd.

**Telt het huiswaarts / gebruikt het het netwerk?**
Nee. De engine is volledig offline — geen telemetrie, geen netwerkoproepen, geen bijwerkingen. Het is een stateless, deterministisch eenmalig subproces.

**Kan ik het in een gesloten-bron product gebruiken?**
Onder AGPL-3.0, ja voor privé/lokaal gebruik. Het distribueren van een bouw triggert de GPL-vervoerings-/bronverplichtingen, en het netwerkbediening van een *gewijzigde* bouw triggert AGPL §13 — hoe dan ook moet je overeenkomstige bron aanbieden. Om volledig gesloten-bron te gaan, koopt u ofwel een commerciële Swiss Ephemeris-licentie van Astrodienst of verwisselt u de efemerisis voor Skyfield + JPL DE440 (zie [Licentie](#licensing)).

---

## Disclaimer

`life-chart-engine` is een **interpretatief zelf-bewustzijn-raamwerk, geen voorspelling of fatalisme**. De uitvoeren zijn gestructureerde referentiepunten voor bezinning — zij voorzeggen geen gebeurtenissen en bepalen geen resultaten. Gebruik ze als kalibratie, met uw eigen geleefd ervaring als eindautoriteit. Niets hier is medisch, juridisch, psychologisch of financieel advies. Voor beslissingen in die domeinen, raadpleeg een gekwalificeerde professional.

---

## Credits & Licentie

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, tweevoudig gelicentieerd AGPL-3.0 / commercieel (<https://www.astro.com/swisseph/>).
- **py-iztro** (en upstream `iztro`) — MIT, voor Zi Wei Dou Shu.
- Volledige attributie: **[CREDITS.md](./CREDITS.md)**.
- **Licentie:** [AGPL-3.0](./LICENSE).
- **Agent / JSON-contract:** [AGENTS.md](./AGENTS.md).
