> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · **Polski**

# life-chart-engine

**Deterministyczne natywne obliczenia trzech systemów wykresów życia — zachodnia astrologia natalna, 人類圖 (Human Design) i 紫微斗數 (Zi Wei Dou Shu) — z jednego rekordu urodzeniowego.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` to mały, działający w trybie offline narzędzie wiersza poleceń. Dajesz mu dane urodzeniowe jednej osoby — datę, godzinę, strefę czasową i współrzędne miejsca — i oblicza trzy niezależne systemy wykresów w jednym przejściu, a następnie emituje albo czytelny raport Markdown, albo strukturalny obiekt JSON, który mogą przetwarzać programy i agenci AI.

Jest zbudowany dla osób, które chcą **powtarzalnych, weryfikowalnych** obliczeń wykresów zamiast aplikacji internetowej typu czarna skrzynka: praktyków, deweloperów tworzących narzędzia do samowiedzy i agentów AI, którzy potrzebują czystego kroku obliczeniowego. Każda liczba pochodzi z rzeczywistych obliczeń astronomicznych (Swiss Ephemeris) i rzeczywistej biblioteki 紫微斗數 (iztro) — nie ze zdalnej usługi, nie z buforowanych wyszukiwań i nigdy przez sieć.

---

## Co oblicza

Silnik uruchamia trzy systemy względem **tego samego momentu urodzenia**, aby ich wyniki mogły się wzajemnie potwierdzać. Każdy system odpowiada na inny rodzaj pytania:

| System | Co to jest (zwykły angielski) | Co silnik produkuje |
|--------|-------------------------------|-------------------|
| **Zachodnia natalna** (Tropical / Placidus) | Klasyczna zachodnia astrologia — gdzie planety siedziały względem zodiaku w momencie twojego urodzenia, podzielone na 12 domów. | Ascendent + Środek Nieba, 12 planet/punktów (太陽 → Południowy Węzeł) ze znakiem, stopniem, domem i flagą retrogradacyjną, wszystkie 12 krawędzi domów i każdy wykryty aspekt (koniunkcja/sextile/kwadrat/trygonum/opozycja) posortowane według ścisłości. |
| **人類圖 Human Design** | Nowoczesna synteza astrologii, I-Ching i systemu czakr. Opisuje, jak twoja energia jest „połączona" poprzez bramy, kanały i centra. | Typ, Autorytet, Profil, Definicja, Kopa Reinkarnacji, wcześniejsza o 88° data Projektu, zdefiniowane/otwarte centra, zdefiniowane kanały i aktywacje bramy/linii dla każdej planety dla obu wykresów Osobowości i Projektu. |
| **紫微斗數 Zi Wei Dou Shu** | Tradycyjny chiński system astrologiczny, który mapuje los na 12-pałacową tablicę, zaludnioną nazwanymi gwiazdami. | 五行局 (Klasa Pięciu Elementów), 命主 (dusza) / 身主 (ciało), indeks 時辰 (godzina) i dane dla każdego pałacu — ganzhi, flagi 命/身, dekadowy zakres wieku i główne/drugorzędne/przymiotnikowe gwiazdy (z jasnością i 四化). Opcjonalnie prognoza 大限/流年 na najlepszy wysiłek. |

Typ, Autorytet i Definicja w Human Design **nie są sztywno zakodowane** — są wyprowadzane z grafu łączności zdefiniowanych centrów.

---

## Dlaczego obliczenia natywne

Ten silnik wykonuje rzeczywistą matematykę zamiast przybliżać lub wywoływać usługę. Ten wybór daje trzy właściwości, które mają znaczenie dla każdego poważnego narzędzia do wykresów:

- **Deterministyczne.** To samo wejście urodzeniowe zawsze produkuje to samo wyjście, bajt po bajcie. Nie ma losowości, modelu, ani dryfu zaokrąglania między przebiegami.
- **Powtarzalne.** Każdy, kto ma repozytorium i te same dane wejściowe, może regenerować twój dokładny wykres. Obliczenia używają Swiss Ephemeris (model Moshiera) dla nieba i iztro dla 紫微斗數 — oba deterministyczne.
- **Krzyżowo weryfikowalne.** Ponieważ trzy niezależne systemy są obliczane z jednego momentu urodzenia, możesz triangulować. **Gdy wszystkie trzy systemy wskazują na ten sam sygnał, traktuj go jako wysoką pewność. Gdy tylko jeden system pokazuje szczegół, traktuj go jako punkt odniesienia, nie jako wniosek.** To jest główna zasada projektowania silnika — produkuje fakty do krzyżowego czytania, nie pojedynczy werdykt.

---

## Szybki start

### Instalacja w jednej linii (rekomendowane)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Instaluje do `~/.life-chart-engine` (można zmienić przez `LIFE_CHART_DIR`). Bez `sudo`, bez zmian w całym systemie — tylko klonuje repo, buduje izolowany venv CPython 3.12 i generuje przypięty bundle Node iztro. Wymaga `git`, [`uv`](https://docs.astral.sh/uv/) oraz Node.js/npm. Uruchom ponownie w dowolnym momencie, aby zaktualizować do najnowszej wersji.

### Ze źródła

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Co robi `setup.sh`

Działa pod `set -euo pipefail` i wykonuje sześć kroków:

1. **Rozwiązuje lokalizację venv** — `${LIFE_VENV:-<repo>/.venv}`. Ustaw zmienną `LIFE_VENV`, aby przesłonić; domyślnie `.venv/` jest ignorowane w git.
2. **Sprawdzenie wstępne: wymaga [`uv`](https://docs.astral.sh/uv/)** — jeśli `uv` nie jest w `PATH`, wychodzi z kodem `1` i drukuje wskazówkę instalacji:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Tworzy venv CPython 3.12** — `uv venv --python 3.12 "$VENV"` (zobacz [Dlaczego CPython 3.12](#why-cpython-312-specifically)).
4. **Instaluje przypisuone zależności** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Buduje przypięty bundle iztro** — uruchamia `scripts/build-iztro-bundle.sh`, który instaluje `iztro@2.5.8` w tymczasowym katalogu build i tworzy `vendor/iztro.cjs`.
6. **Uruchamia smoke test** — uruchamia silnik raz ze stałymi danymi przykładowymi (odrzucając stdout) i przy sukcesie wypisuje `OK — engine runs.`. Wypisuje też wskazówki użycia dla obu trybów.

### Ręczne kroki `uv` (bez `setup.sh`)

```bash
# 1. Utwórz venv CPython 3.12 (domyślnie <repo>/.venv; przesłoń zmienną LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Zainstaluj przypisuone zależności
uv pip install --python .venv/bin/python -r requirements.txt

# 3. Zbuduj przypięty bundle iztro
bash scripts/build-iztro-bundle.sh

# 4. (Opcjonalnie) smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Bezpośrednie zależności Pythona są przypięte w `requirements.txt`:

```
pyswisseph==2.10.3.2
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei używa wygenerowanego bundla Node przypiętego przez `scripts/build-iztro-bundle.sh`:

```
iztro@2.5.8
```

---

## Dlaczego dokładnie CPython 3.12

Silnik działa obecnie na zweryfikowanym runtime **CPython 3.12**. Powód jest zapisany identycznie w `requirements.txt` i `setup.sh`:

> CPython 3.12 pozostaje zablokowany dla tej zmiany. Stare ograniczenie natywnej zależności Python Zi Wei zniknęło, więc można do tego wrócić po sprawdzeniu pozostałych zależności i obrazu wdrożeniowego.

Krótko: 3.12 nadal jest testowanym runtime dla tego wydania. Zależność Zi Wei nie wymusza już tej blokady, więc podbicie wersji Pythona to późniejszy test zgodności, a nie część tego refaktoru.

---

## Użycie

Silnik ma dwa tryby, wybierane przez obecność flagi `--json`.

### Tryb człowieka (Markdown)

Pomiń `--json`, aby otrzymać czytelny raport konsoli. Użyj Pythona z venv:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Przycięty przykład ze świata rzeczywistego (aspekty są ograniczone do 10 pierwszych w trybie Markdown):

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

### Tryb agenta (JSON)

Dodaj `--json`, aby otrzymać jeden obiekt JSON na stdout i nic więcej — idealnie dla programów i agentów AI:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Przycięty przykład ze świata rzeczywistego (tablice skrócone do 1–2 wpisów; wartości dosłownie):

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

## Odnośnik flag CLI

Nie ma **flag `required=True`** — argparse nigdy nie zgłasza błędu na brakującą. Pominięcie `--date`/`--time`/`--tz`/`--lat`/`--lon` wycicho wraca do osoby z wbudowanego przykładu (`範例`, urodzonej `2000-01-01 12:00`, UTC+8, Taipei 101). Aby uzyskać prawidłowy wykres, podaj je wszystkie.

| Flaga | Typ | Wymagana do prawidłowego użytku? | Domyślnie | Format / reguła |
|-------|-----|----------------------------------|----------|-----------------|
| `--name` | string | Nie (kosmetyczne) | `"範例"` | Dowolny tekst; echowany tylko do wyjścia. |
| `--gender` | string | Tylko dla 紫微 | `"女"` | Musi być dokładnie `男` lub `女` (argparse `choices`; cokolwiek innego → exit `2`). |
| `--date` | string | **Tak** | wraca do `2000-01-01` | `YYYY-MM-DD`, podzielone na `-`. Bez wymogu dopełniania zerami. |
| `--time` | string | **Tak** | wraca do `12:00` | `HH:MM`, 24-godzinowy czas zegara lokalnego, podzielony na `:`. |
| `--tz` | float | **Tak** | wraca do `8.0` | Przesunięcie UTC włączając DST (Tajwan = `8`). Zapisane do klucza wejścia `tz_offset`. |
| `--lat` | float | **Tak** | wraca do `25.0330` | Szerokość geograficzna w stopniach dziesiętnych (zachodnie domy/Asc/MC). |
| `--lon` | float | **Tak** | wraca do `121.5654` | Długość geograficzna w stopniach dziesiętnych. |
| `--target` | string | Nie | `"2025-01-01"` | `YYYY-MM-DD`; data referencji dla okresu szczęścia 紫微 (運限參考日). |
| `--json` | flaga | Nie | `False` (Markdown) | Obecność → tryb JSON; brak → Markdown. Bierze brak wartości. |

> Silnik **nie** geokoduje miejsc ani nie przeszukuje stref czasowych. Osoba dzwoniąca musi sama konwertować miejsce → `lat`/`lon`/`tz` — a strefa czasowa/DST to najczęstsza źródła błędu, więc sprawdź przesunięcie UTC, które obowiązywało w miejscu urodzenia i dniu urodzenia.

---

## Odnośnik wyjścia

Koperta `--json` ma siedem kluczy najwyższego poziomu, w tej kolejności:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Blok | Streszczenie |
|------|-------------|
| `ok` | `true` po powodzeniu (`false` w kopercie błędu). |
| `schema_version` | `"1.1"`. |
| `input` | Echo znormalizowanych wejść: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (zwróć uwagę na `tz_offset`, nie `tz`). |
| `western` | String `system`, obiekty pozycji `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (obiekt lub `null`). |
| `meta` | `{ engine, version, ephemeris }` — wszystkie literały (`ephemeris: "Moshier"`). |

Aby uzyskać pełny kontrakt pola — każdy klucz, typ i protokół wywoływania agenta — zobacz **[AGENTS.md](./AGENTS.md)**.

### Dziwactwa pola warte poznania

- **`aspects` NIE są ograniczone w JSON.** Ścieżka JSON zwraca *każdy* wykryty aspekt, posortowany rosnąco po orb (najściślejszy pierwszy). Limit 10 elementów istnieje tylko w raporcie Markdown.
- **`ziwei.horoscope` jest na najlepszy wysiłek i może być `null`.** Jest owinięty w `try/except`; na każdy wyjątek szereguje się jako `null`. Gdy jest obecny, to `{ decadal, yearly }`. (Te podobjekty ujawniają dodatkową wewnętrzną strukturę — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star` itd. — poza udokumentowanym zastępczym symbolem.)
- **Ciągi gwiazd kodują jasność + 四化.** Format to `name(brightness)[mutagen]`, z każdą częścią opcjonalną — np. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]` lub zwykła `天機`. `adjective_stars` to tylko zwykłe nazwy (bez jasności/mutagen).

---

## Poziomy dokładności

Nie każde wyjście ma taką samą pewność. Przeczytaj każdy poziom odpowiednio:

| Poziom | Co obejmuje | Pewność |
|--------|------------|---------|
| **Najwyższa** | Długości geograficzne planet, znaki, retrogradacja plus rozmieszczenie gwiazd 紫微 / 命宮·身宮 / 五行局 — czysta efemerys i matematyka kalendarza. | Astronomicznie/kalendarnie dokładne. |
| **Wysoka, zależna od czasu** | Ascendent, Środek Nieba, wszystkie 12 krawędzi domów, dom, w którym pada każda planeta, linie Human Design i indeks 時辰 紫微. | Dokładne *przy* dokładnym czasie urodzenia; czułe na minuty. |
| **Zweryfikowana** | Jasność gwiazd 紫微斗數 — dostosowana do wyników biblioteki iztro. | Zweryfikowana względem biblioteki. |
| **Granica flagi ±0,3°** | Dowolna planeta / brama / linia siedząca w granicach ±0,3° granicy. | Traktuj jako prowizoryczne i zanotuj wpływ — ±0,3° może ją przeniesć przez linię. |

---

## Znane ograniczenia

- **Brak Chirona / drobnych ciał.** Kompilacja używa efemerysty Moshiera (`swe.FLG_MOSEPH`, brak plików danych), która nie dostarcza Chirona ani innych drobnych ciał. Obliczane są tylko 10 klasycznych planet plus węzły Księżyca.
- **紫微斗數 używa jednej domyślnej szkoły.** iztro jest wywoływane z ustalonymi opcjami (`bySolar(..., True, 'zh-TW')`); szkoła rozmieszczenia gwiazd i 四化 są takie, jakie domyślnie ustawia iztro. Jeśli zwykle używasz 飛星 lub innej szkoły, główna struktura jest niezmieniona, ale niektóre szczegóły mogą się różnić.
- **Przybliżony czas urodzenia pogarsza poziom zależny od czasu.** Jeśli czas urodzenia jest niepewny, przypisania Ascendentu/MC/domów, linie Human Design i 時辰 — i wszystko co od nich pochodzi — stają się zawodne. W takim przypadku **traktuj pola zależne od czasu jako prowizoryczne** i rozważ **prostowanie oparte na zdarzeniach** (dopasowanie znanych zdarzeń życiowych do czasu wykresu) przed poleganiem na nich.

---

## Użyj go od agenta AI / Hermesa

Zamierzonym modelem integracji jest **samodzielna instalacja**, nie SaaS.

Użytkownik kopiuje URL tego repozytorium i **jego własny** agent lub CLI (Claude Code, Hermes, skrypt itp.) klonuje go i uruchamia **lokalnie na maszynie użytkownika**. Obliczenia odbywają się po stronie użytkownika. Nie ma hostowanego punktu końcowego do wywoływania, bez konta i **bez wymaganej integracji SaaS** — silnik jest stateless, deterministycznym, offline'owym podprocesem.

Ponieważ wydawca nie obsługuje go jako usługi sieciowej, na wydawcę nie pada obowiązek §13 w przypadku czyjegoś samodzielnego zainstalowania. (Osobno §13 zobowiązuje operatora, który uruchamia *zmodyfikowaną* wersję dostępną sieciowo — nie niezmodyfikowane lokalne użytko.)

Dla agentów kontrakt jest prosty: wyślij subprocess `--json` z venv Pythonem w katalogi roboczym repozytorium, przeanalizuj stdout jako JSON, rozgałęź na `ok` (i kod wyjścia), a następnie przekaż strukturalny obiekt. Czyszczenie nie jest potrzebne — jest stateless. Pełny kontrakt CLI + JSON znajduje się w **[AGENTS.md](./AGENTS.md)**.

### Kopia kopiuj-wklej setup dla twojego agenta AI

Wklej ten blok bezpośrednio do Claude Code, ChatGPT lub dowolnego agenta kodowania — mówi agentowi, jak zainstalować i wywoływać narzędzie:

```text
Skonfiguruj i użyj "life-chart-engine" — CLI, który oblicza zachodnia wykres narodzenia +
Human Design + Zi Wei Dou Shu (紫微斗數) z danych urodzeniowych.

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Oblicz wykres i czytaj stdout jako JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Reguły:
   - TY rozwiązujesz miasto urodzenia na --lat/--lon i prawidłowe historyczne przesunięcie UTC
     (uwzględniające DST). Narzędzie nie geokoduje.
   - Potwierdź, czy czas urodzenia jest dokładny, zanim będziesz ufać ascendentowi,
     domom, liniom Human Design lub filarowi godziny Zi Wei.
   - Nigdy nie fabrykuj wartości wykresu — zawsze wywoływaj narzędzie.
   - Pełny schemat wyjścia, kody wyjścia i kontrakt agenta: ~/.life-chart-engine/AGENTS.md
```

---

## Licencjowanie

To repozytorium jest licencjonowane na podstawie **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 zwykłym angielskim.** To jest GNU GPL-3.0 (silna licencja copyleft: jeśli rozpowszechniasz oprogramowanie, musisz wydać pełny odpowiadający kod źródłowy na tej samej licencji) **plus jedna dodatkowa klauzula, Sekcja 13**. §13 zamyka „lukę SaaS": poza wyzwalaczem *dystrybucji* GPL, dodaje, że jeśli *zmodyfikujesz* program i pozwolisz użytkownikom wchodzić w interakcję ze swoją zmodyfikowaną wersją przez sieć, musisz oferować tym zddalonym użytkownikom twój odpowiadający kod źródłowy. (Uruchamianie niezmodyfikowanego upstreamu jako usługi sieciowej nie wyzwala samo w sobie §13.) AGPL jest odwzajemniony, ale nie w sposób nieograniczony wirusowy — dociera tylko do kodu, który jest pochodną lub połączony z kodem AGPL.

**Dlaczego to repozytorium to AGPL.** Silnik łączy **Swiss Ephemeris** (przez `pyswisseph`) dla pozycji planet i krawędzi domów. Astrodienst **podwójnie licencjonuje** Swiss Ephemeris jako **AGPL-3.0 LUB licencja komercyjna**, a jego kod nie może być ponownie licencjonowany na coś bardziej permisywnego. Ponieważ AGPL jest copyleft i ten projekt go łączy, całe połączone dzieło musi być AGPL. (`iztro` to MIT i nie nakłada copyleft; Swiss Ephemeris to jedyna składnik wymuszająca AGPL tutaj.)

**Co to oznacza w praktyce.**

| Robisz | Obowiązek AGPL |
|--------|----------------|
| **Samodzielna instalacja** (uruchomienie lokalnie dla siebie) | §13 *nie jest* wyzwolony — nie ma zddalonych użytkowników do obsługi, a ty już masz kod źródłowy. Czyste. |
| **Uruchomienie *zmodyfikowanej* wersji jako usługi sieciowej** | §13 *jest* wyzwolony — musisz oferować tym zddalonym użytkownikom pełny odpowiadający kod źródłowy twojej wdrożonej wersji, na podstawie AGPL, włączając twoje modyfikacje. Uwaga: obowiązek oferty źródła §13 jest uwarunkowany modyfikacją — uruchomienie niezmodyfikowanego upstreamu jako usługi sieciowej nie wyzwala samo w sobie §13, chociaż kod źródłowy jest już publiczny.

**Twoje trzy opcje**, jeśli obowiązek źródła sieciowego nie pasuje do twojego przypadku użytku:

1. **Zachowaj AGPL** — opublikuj pełny odpowiadający kod źródłowy (włączając modyfikacje) wszystkim, którzy go używają, włączając przez sieć zgodnie z §13. Bezpłatnie, bez negocjacji.
2. **Kup komercyjną licencję Swiss Ephemeris od [Astrodienst](https://www.astro.com/swisseph/)** — to znosi obowiązek AGPL dla części Swiss Ephemeris, pozwalając ci ponownie licencjonować twój własny kod i wysyłać/hostować zamknięta kompilację. (To model podwójnego licencjonowania Astrodienstu.)
3. **Zamień efemeryk** — zastąp `pyswisseph` permisywnie licencjonowanym źródłem astronomii (na przykład **Skyfield (MIT)** plus publiczną **JPL DE440** efemeryk — ilustracyjne alternatywy, nie jedyna opcja). Ze zniesionym Swiss Ephemeris, pozostały stos (iztro MIT, plus MPL-2.0/MIT/Apache deps) już nie wymusza AGPL i całe repozytorium mogłoby być MIT. To rzeczywisty wysiłek inżynierski: musisz ponownie wdrożyć wszystko aktualnie pozyskiwane ze Swiss Ephemeris — długości geograficzne planet, flagi retrogradacji, Asc/MC, Placidusowe krawędzie domów i dane wejściowe do solvera projektu Human Design 88°.

Zobacz **[CREDITS.md](./CREDITS.md)** dla pełnego przypisania i licencji na zależność.

---

## FAQ

**Czy mogę wpisać datę księżycową?**
Nie. Dane wejściowe to data gregoriańska słoneczna (`--date YYYY-MM-DD`) i czas zegara (`--time HH:MM`). Jeśli masz tylko datę księżycową, najpierw ją skonwertuj. 紫微斗數 jest obliczany poprzez punkt wejścia słoneczny iztro (`bySolar`).

**Mój czas urodzenia jest tylko przybliżony — czy to problem?**
Pozycje planet są w porządku, ale Ascendent, Środek Nieba, krawędzie domów, dom, w którym siedzi każda planeta, linie Human Design i 時辰 są wszystkie czułe na czas. Traktuj je jako prowizoryczne i rozważ prostowanie oparte na zdarzeniach, zanim na nich polegaj.

**Gdzie Chiron / asteroidy / drobne ciała?**
Nie uwzględnione. Efemerys Moshiera używana tutaj ich nie dostarcza; obliczane są tylko 10 klasycznych planet i węzły Księżyca.

**Którą szkołę 紫微斗數 używa?**
Domyślną szkołę zaimplementowaną przez iztro (`bySolar(..., True, 'zh-TW')`). Szkoła nie jest wybierana przez użytkownika.

**Czy dzwoni do domu / używa sieci?**
Nie. Silnik jest całkowicie offline — bez telemetrii, bez połączeń sieciowych, bez efektów ubocznych. Jest to stateless, deterministyczny jednorazowy subprocess.

**Czy mogę użyć go wewnątrz zamkniętego produktu?**
Na podstawie AGPL-3.0, tak dla prywatnego/lokalnego użytku. Rozpowszechnianie kompilacji wyzwala obowiązki GPL przekazywania/źródła i obsługiwanie sieciowe *zmodyfikowanej* kompilacji wyzwala AGPL §13 — w każdym razie musisz oferować odpowiadający kod źródłowy. Aby zostać całkowicie zamkniętym, kupić komercyjną licencję Swiss Ephemeris od Astrodienstu lub zamienić efemerys na Skyfield + JPL DE440 (zobacz [Licencjowanie](#licensing)).

---

## Zastrzeżenie

`life-chart-engine` jest **interpretacyjnym framework'iem samowiedzy, nie przewidywaniem ani fatalizmem**. Wyjścia są strukturalnymi punktami odniesienia do refleksji — nie przepowiadają zdarzeń i nie określają wyników. Użyj ich jako kalibracji, przy twoim własnym doświadczeniu jako ostatecznym autorytetem. Nic tutaj nie jest poradą medyczną, prawną, psychologiczną ani finansową. W przypadku decyzji w tych dziedzinach, skonsultuj się z kwalifikowanym specjalistą.

---

## Kredyty i licencja

- **Swiss Ephemeris** przez `pyswisseph` — © Astrodienst AG, licencjonowany podwójnie AGPL-3.0 / komercyjna (<https://www.astro.com/swisseph/>).
- **iztro** — MIT, dla 紫微斗數.
- Pełne przypisanie: **[CREDITS.md](./CREDITS.md)**.
- **Licencja:** [AGPL-3.0](./LICENSE).
- **Kontrakt agenta / JSON:** [AGENTS.md](./AGENTS.md).
