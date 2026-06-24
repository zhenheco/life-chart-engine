> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · **Español** · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Computación nativa determinista de tres sistemas de cartas astrológicas — astrología natal occidental, 人類圖 (Human Design), y 紫微斗數 (Zi Wei Dou Shu) — a partir de un único registro de nacimiento.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#por-qué-cpython-312-específicamente)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#preguntas-frecuentes)

`life-chart-engine` es una pequeña herramienta de línea de comandos, sin conexión. Le suministras los datos de nacimiento de una persona — fecha, hora, zona horaria, y coordenadas del lugar — y calcula tres sistemas de cartas independientes en una sola pasada, emitiendo después un informe legible en Markdown o un objeto JSON estructurado para que programas y agentes de IA lo consuman.

Está construido para las personas que desean cálculos de cartas **reproducibles y verificables** en lugar de una aplicación web de caja negra: practicantes, desarrolladores que construyen herramientas de autoconocimiento, y agentes de IA que necesitan un paso de cómputo puro. Cada número procede de cálculos astronómicos reales (Swiss Ephemeris) y de una biblioteca 紫微斗數 real (iztro) — no de un servicio remoto, no de búsquedas en caché, y nunca a través de la red.

---

## Qué calcula

El motor ejecuta tres sistemas contra el **mismo momento de nacimiento**, de modo que sus resultados pueden corroborarse mutuamente. Cada sistema responde a un tipo diferente de pregunta:

| Sistema | Qué es (en lenguaje común) | Qué genera el motor |
|---------|---------------------------|----------------------|
| **Astrología natal occidental** (Tropical / Placidus) | Astrología clásica occidental — dónde estaban los planetas contra el zodíaco en tu nacimiento, divididos en 12 casas. | Ascendente + Medio Cielo, 12 planetas/puntos (太陽 → 南交點) con signo, grado, casa y marcador de retrogradación, las 12 cúspides de casa, y todos los aspectos detectados (合相/六分/四分/三分/對分) ordenados por precisión. |
| **人類圖 Human Design** | Una síntesis moderna de astrología, el I-Ching, y el sistema de chakras. Describe cómo tu energía está "conectada" a través de puertas, canales y centros. | Tipo, Autoridad, Perfil, Definición, Cruz de Encarnación, la fecha de Diseño 88° anterior, centros definidos/abiertos, canales definidos, y activaciones de puerta.línea por planeta tanto para la carta de Personalidad como de Diseño. |
| **紫微斗數 Zi Wei Dou Shu** | Un sistema de astrología tradicional chino que proyecta el destino en un tablero de 12 palacios, poblado de estrellas nombradas. | Clase de 五行局 (Cinco Elementos), 命主 (alma) / 身主 (cuerpo), el índice de hora 時辰, y datos por palacio — ganzhi, marcadores de 命/身, rango de edad decadal, y estrellas mayores/menores/adjetivales (con brillo y 四化). Opcionalmente un horóscopo de esfuerzo máximo 大限/流年. |

Tipo, Autoridad, y Definición en Human Design **no están codificados en duro** — se derivan del gráfico de conectividad de los centros definidos.

---

## Por qué cálculo nativo

Este motor realiza las matemáticas reales en lugar de aproximar o llamar a un servicio. Esa elección aporta tres propiedades que importan para cualquier herramienta seria de cartas:

- **Determinista.** La misma entrada de nacimiento siempre produce la misma salida, byte por byte. No hay aleatoriedad, no hay modelo, sin fluctuación de redondeo entre ejecuciones.
- **Reproducible.** Cualquiera con el repositorio y las mismas entradas puede regenerar tu carta exacta. Los cálculos utilizan Swiss Ephemeris (modelo Moshier) para el cielo y iztro para 紫微斗數 — ambos deterministas.
- **Verificable transversalmente.** Porque se calculan tres sistemas independientes desde un único momento de nacimiento, puedes triangular. **Cuando los tres sistemas apuntan a la misma señal, trátalo como confianza alta. Cuando solo un sistema muestra un detalle, trátalo como punto de referencia, no como conclusión.** Este es el principio de diseño central del motor — produce hechos para leer transversalmente, no un único veredicto.

---

## Inicio rápido

### Instalación de una línea (recomendado)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Se instala en `~/.life-chart-engine` (anular con `LIFE_CHART_DIR`). Sin `sudo`, sin cambios en todo el sistema — solo clona el repositorio, construye un venv CPython 3.12 aislado, y genera el bundle Node de iztro fijado. Requiere `git`, [`uv`](https://docs.astral.sh/uv/), y Node.js/npm. Vuelve a ejecutar en cualquier momento para actualizar a la última versión.

### Desde la fuente

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Qué hace `setup.sh`

Se ejecuta bajo `set -euo pipefail` y realiza seis pasos:

1. **Resuelve la ubicación del venv** — `${LIFE_VENV:-<repo>/.venv}`. Establece la variable de entorno `LIFE_VENV` para anular; el valor predeterminado `.venv/` está en .gitignore.
2. **Verificación previa: requiere [`uv`](https://docs.astral.sh/uv/)** — si `uv` no está en `PATH` sale con `1` e imprime la sugerencia de instalación:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Crea un venv CPython 3.12** — `uv venv --python 3.12 "$VENV"` (véase [Por qué CPython 3.12](#por-qué-cpython-312-específicamente)).
4. **Instala dependencias fijas** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Construye el bundle iztro fijado** — ejecuta `scripts/build-iztro-bundle.sh`, que instala `iztro@2.5.8` en un directorio temporal de compilación y emite `vendor/iztro.cjs`.
6. **Ejecuta una prueba de humo** — ejecuta el motor una vez con entradas de ejemplo fijas (descartando stdout) e imprime `OK — engine runs.` en caso de éxito. También imprime sugerencias de uso para ambos modos.

### Pasos `uv` manuales (sin `setup.sh`)

```bash
# 1. Crear venv CPython 3.12 (por defecto <repo>/.venv; anular con LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Instalar dependencias fijas
uv pip install --python .venv/bin/python -r requirements.txt

# 3. Construir el bundle iztro fijado
bash scripts/build-iztro-bundle.sh

# 4. (Opcional) prueba de humo
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Las dependencias directas de Python están fijadas en `requirements.txt`:

```
pyswisseph==2.10.3.2
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei usa un bundle Node generado y fijado por `scripts/build-iztro-bundle.sh`:

```
iztro@2.5.8
```

---

## Por qué CPython 3.12 específicamente

Actualmente el motor se ejecuta sobre el runtime verificado **CPython 3.12**. La razón se declara de forma idéntica en `requirements.txt` y `setup.sh`:

> CPython 3.12 permanece bloqueado para este cambio. La antigua restricción de dependencia nativa de Python para Zi Wei ya no existe, así que puede revisarse después de comprobar las dependencias restantes y la imagen de despliegue.

En resumen: 3.12 sigue siendo el runtime probado para esta versión. La dependencia de Zi Wei ya no fuerza ese bloqueo, así que subir la versión de Python es una comprobación de compatibilidad posterior, no parte de este refactor.

---

## Uso

El motor tiene dos modos, seleccionados por la presencia de la bandera `--json`.

### Modo humano (Markdown)

Omite `--json` para obtener un informe de consola legible. Usa el Python de tu venv:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Muestra real recortada (los aspectos se limitan a los 10 mejores en modo Markdown):

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

### Modo agente (JSON)

Añade `--json` para obtener un único objeto JSON en stdout y nada más — ideal para programas y agentes de IA:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Muestra real recortada (matrices truncadas a 1–2 entradas; valores literales):

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

## Referencia de banderas CLI

No hay **banderas `required=True`** — argparse nunca emite error en una falta. Omitir `--date`/`--time`/`--tz`/`--lat`/`--lon` silenciosamente recurre a una persona de ejemplo incorporada (`範例`, nacida `2000-01-01 12:00`, UTC+8, Taipei 101). Por tanto, para una carta correcta, suministra todas.

| Bandera | Tipo | ¿Requerida para uso correcto? | Valor por defecto | Formato / regla |
|---------|------|-------------------------------|-------------------|-----------------|
| `--name` | string | No (cosmético) | `"範例"` | Texto libre; solo reflejado en la salida. |
| `--gender` | string | Solo para 紫微 | `"女"` | Debe ser exactamente `男` o `女` (argparse `choices`; cualquier otra cosa → salida `2`). |
| `--date` | string | **Sí** | recurre a `2000-01-01` | `YYYY-MM-DD`, dividido en `-`. Sin requisito de relleno de ceros. |
| `--time` | string | **Sí** | recurre a `12:00` | `HH:MM`, reloj local de 24 horas, dividido en `:`. |
| `--tz` | float | **Sí** | recurre a `8.0` | Desplazamiento UTC incluyendo horario de verano (Taiwán = `8`). Escrito en clave `tz_offset`. |
| `--lat` | float | **Sí** | recurre a `25.0330` | Latitud en grados decimales (casas occidentales/Asc/MC). |
| `--lon` | float | **Sí** | recurre a `121.5654` | Longitud en grados decimales. |
| `--target` | string | No | `"2025-01-01"` | `YYYY-MM-DD`; fecha de referencia de período de suerte 紫微 (運限參考日). |
| `--json` | bandera | No | `False` (Markdown) | Presencia → modo JSON; ausencia → Markdown. No toma valor. |

> El motor **no** geocodifica lugares ni consulta zonas horarias. El llamador debe convertir lugar → `lat`/`lon`/`tz` por sí mismo — y la zona horaria/horario de verano es la fuente más común de error, así que verifica el desplazamiento UTC que se aplicaba en el lugar de nacimiento y la fecha de nacimiento.

---

## Referencia de salida

La envoltura `--json` tiene siete claves de nivel superior, en este orden:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Bloque | Resumen |
|--------|---------|
| `ok` | `true` en caso de éxito (`false` en la envoltura de error). |
| `schema_version` | `"1.1"`. |
| `input` | Eco de entradas normalizadas: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (nota `tz_offset`, no `tz`). |
| `western` | cadena `system`, objetos de posición `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (objeto o `null`). |
| `meta` | `{ engine, version, ephemeris }` — todos literales (`ephemeris: "Moshier"`). |

Para el contrato de campo completo — cada clave, tipo, y el protocolo de invocación de agente — véase **[AGENTS.md](./AGENTS.md)**.

### Particularidades de campo que vale la pena conocer

- **`aspects` NO están limitados en JSON.** La ruta JSON devuelve *todos* los aspectos detectados, ordenados ascendentemente por orb (más ajustados primero). El límite de 10 elementos existe solo en el informe Markdown.
- **`ziwei.horoscope` es esfuerzo máximo y puede ser `null`.** Está envuelto en `try/except`; en cualquier excepción se serializa como `null`. Cuando está presente es `{ decadal, yearly }`. (Esos subobjetos exponen estructura interna adicional — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, etc. — más allá del marcador documentado.)
- **Cadenas de estrellas codifican brillo + 四化.** El formato es `name(brightness)[mutagen]`, con cada parte opcional — p. ej. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, o simple `天機`. `adjective_stars` son solo nombres (sin brillo/mutagen).

---

## Niveles de precisión

No todas las salidas llevan la misma confianza. Lee cada nivel en consecuencia:

| Nivel | Qué cubre | Confianza |
|-------|-----------|-----------|
| **Más alto** | Longitudes de planetas, signos, retrogradación, más ubicación de estrellas 紫微 / 命宮·身宮 / 五行局 — pura matemática de efemérides y calendario. | Astronómica/calendarialmente exacta. |
| **Alto, dependiente del tiempo** | Ascendente, Medio Cielo, las 12 cúspides de casa, la casa en la que cae cada planeta, líneas de Human Design, e índice 紫微 時辰. | Exacto *dada* una hora de nacimiento precisa; sensible a minutos. |
| **Verificado** | Brillo de estrellas 紫微斗數 — alineado con las salidas de la biblioteca iztro. | Verificado contra la biblioteca. |
| **Límite de bandera ±0,3°** | Cualquier planeta / puerta / línea sentada dentro de ±0,3° de un límite. | Trata como provisional y nota el impacto — ±0,3° puede voltearlo a través de la línea. |

---

## Limitaciones conocidas

- **Sin Quirón / cuerpos menores.** La compilación utiliza la efemérides Moshier (`swe.FLG_MOSEPH`, sin archivos de datos), que no proporciona Quirón u otros cuerpos menores. Solo se calculan los 10 planetas clásicos más los nodos lunares.
- **紫微斗數 utiliza una escuela predeterminada.** iztro se invoca con opciones fijas (`bySolar(..., True, 'zh-TW')`); la escuela de colocación de estrellas y 四化 son lo que iztro predetermina. Si normalmente usas 飛星 u otra escuela, la estructura principal es inalterada pero algunos detalles pueden diferir.
- **Hora de nacimiento aproximada degrada el nivel dependiente del tiempo.** Si la hora de nacimiento es incierta, el Ascendente/MC/asignaciones de casa, líneas de Human Design, y 時辰 — y cualquier cosa derivada de ellas — se vuelven poco confiables. En ese caso, **trata los campos dependientes del tiempo como provisionales** y considera **rectificación basada en eventos** (correspondencia de eventos de vida conocidos con el tiempo de la carta) antes de confiar en ellos.

---

## Úsalo desde un agente de IA / Hermes

El modelo de integración previsto es **autoinstalación**, no SaaS.

Un usuario copia la URL de este repositorio, y **su propio** agente o CLI (Claude Code, Hermes, un script, etc.) lo clona y lo ejecuta **localmente en la máquina del usuario**. El cómputo sucede en el lado del usuario. No hay punto final alojado para llamar, sin cuenta, y **no se requiere integración SaaS** — el motor es un subproceso sin estado, determinista, sin conexión.

Porque el editor no lo opera como un servicio de red, ninguna obligación §13 recae en el editor para la autoinstalación de otro — únicamente §13 obliga a un operador que ejecuta una versión de red *modificada* — no uso local sin modificar.

Para agentes, el contrato es simple: envía el subproceso `--json` con el Python del venv en el directorio de trabajo del repositorio, analiza stdout como JSON, rama en `ok` (y el código de salida), entonces entrega el objeto estructurado. No se necesita limpieza — es sin estado. El contrato CLI + JSON completo vive en **[AGENTS.md](./AGENTS.md)**.

### Configuración copiar-pegar para tu agente de IA

Pega este bloque directamente en Claude Code, ChatGPT, o cualquier agente de codificación — le dice al agente cómo instalar y llamar la herramienta:

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

## Licencia

Este repositorio está licenciado bajo **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 en inglés plano.** Es la GPL-3.0 de GNU (una licencia copyleft fuerte: si distribuyes el software, debes liberar tu fuente completa correspondiente bajo la misma licencia) **más una cláusula adicional, Sección 13**. §13 cierra la "brecha SaaS": más allá del disparador de *distribución* de GPL, añade que si *modificas* el programa y dejas que usuarios interactúen con tu versión modificada sobre una red, debes ofrecer a esos usuarios remotos tu fuente correspondiente. (Ejecutar un servicio de red sin modificar el canal ascendente no dispara por sí solo §13.) AGPL es recíproca pero no indefinidamente viral — solo alcanza código que es derivativo de, o vinculado con, el código AGPL.

**Por qué este repositorio es AGPL.** El motor vincula **Swiss Ephemeris** (a través de `pyswisseph`) para posiciones de planetas y cúspides de casa. Astrodienst **licencia dual** Swiss Ephemeris como **AGPL-3.0 O una licencia comercial**, y su código no puede ser relicenciado como algo más permisivo. Porque AGPL es copyleft y este proyecto lo vincula, la obra combinada completa debe ser AGPL. (`iztro` es MIT y no impone copyleft; Swiss Ephemeris es el único componente que fuerza AGPL aquí.)

**Qué significa en la práctica.**

| Lo que haces | Obligación AGPL |
|--------------|-----------------|
| **Autoinstalación** (ejecutarlo localmente para ti) | §13 *no* se dispara — no hay usuarios remotos a servir, y ya tienes la fuente. Limpio. |
| **Ejecutar una versión *modificada* como servicio de red** | §13 *se dispara* — debes ofrecer a esos usuarios remotos la fuente completa correspondiente de tu versión desplegada, bajo AGPL, incluyendo tus modificaciones. Nota: el deber de ofrecer fuente de §13 está condicionado por modificación — ejecutar el ascendente sin modificar como servicio de red no dispara por sí solo §13, aunque la fuente ya sea pública de todos modos. |

**Tus tres opciones** si la obligación de fuente de red no se ajusta a tu caso de uso:

1. **Mantén AGPL** — publica tu fuente completa correspondiente (incluyendo modificaciones) a cualquiera que la use, incluyendo sobre una red per §13. Gratis, sin negociación.
2. **Compra una licencia comercial de Swiss Ephemeris de [Astrodienst](https://www.astro.com/swisseph/)** — esto levanta la obligación AGPL para la porción Swiss Ephemeris, permitiéndote relicenciar tu propio código y enviar/alojar una compilación cerrada. (Este es el modelo de licencia dual de Astrodienst.)
3. **Intercambia la efemérides** — reemplaza `pyswisseph` con una fuente de astronomía bajo licencia permisiva (por ejemplo **Skyfield (MIT)** más la efemérides de dominio público **JPL DE440** — alternativas ilustrativas, no la única opción). Con Swiss Ephemeris desaparecido, la pila restante (iztro MIT, más las dependencias MPL-2.0/MIT/Apache) ya no fuerza AGPL y el repositorio completo podría ser MIT. Este es esfuerzo de ingeniería real: debes reimplementar todo actualmente originado de Swiss Ephemeris — longitudes de planetas, marcadores de retrogradación, Asc/MC, cúspides de casa Placidus, e entradas al solucionador de diseño 88° de Human Design.

Véase **[CREDITS.md](./CREDITS.md)** para atribución completa y licencias por dependencia.

---

## Preguntas frecuentes

**¿Puedo introducir una fecha lunar?**
No. Las entradas son una fecha solar gregoriana (`--date YYYY-MM-DD`) y hora de reloj (`--time HH:MM`). Si solo tienes una fecha lunar, conviértela primero. 紫微斗數 se calcula a través del punto de entrada solar de iztro (`bySolar`).

**Mi hora de nacimiento es solo aproximada — ¿es un problema?**
Las posiciones de planetas están bien, pero el Ascendente, Medio Cielo, cúspides de casa, la casa en la que se sienta cada planeta, líneas de Human Design, y 時辰 son todos sensibles al tiempo. Trata esos como provisionales y considera rectificación basada en eventos antes de confiar en ellos.

**¿Dónde están Quirón / asteroides / cuerpos menores?**
No incluidos. La efemérides Moshier utilizada aquí no los proporciona; solo se calculan los 10 planetas clásicos y los nodos lunares.

**¿Qué escuela de 紫微斗數 usa?**
La escuela predeterminada como se implementa en iztro (`bySolar(..., True, 'zh-TW')`). La escuela no es seleccionable por el usuario.

**¿Marca el teléfono a casa / usa la red?**
No. El motor es totalmente sin conexión — sin telemetría, sin llamadas de red, sin efectos secundarios. Es un subproceso sin estado, determinista, de una sola pasada.

**¿Puedo usarlo dentro de un producto cerrado?**
Bajo AGPL-3.0, sí para uso privado/local. Distribuir una compilación dispara las obligaciones de conveyo/fuente de GPL, y servir una compilación *modificada* sobre la red dispara AGPL §13 — de cualquier forma debes ofrecer fuente correspondiente. Para ir completamente cerrado, compra una licencia comercial de Swiss Ephemeris de Astrodienst o intercambia la efemérides a Skyfield + JPL DE440 (véase [Licencia](#licencia)).

---

## Aviso de limitación de responsabilidad

`life-chart-engine` es un **marco de autoconocimiento interpretativo, no predicción ni fatalismo**. Las salidas son puntos de referencia estructurados para reflexión — no pronostican eventos y no determinan resultados. Úsalos como calibración, con tu propia experiencia vivida como autoridad final. Nada aquí es consejo médico, legal, psicológico, o financiero. Para decisiones en esos ámbitos, consulta a un profesional calificado.

---

## Créditos y Licencia

- **Swiss Ephemeris** a través de `pyswisseph` — © Astrodienst AG, licencia dual AGPL-3.0 / comercial (<https://www.astro.com/swisseph/>).
- **iztro** — MIT, para 紫微斗數.
- Atribución completa: **[CREDITS.md](./CREDITS.md)**.
- **Licencia:** [AGPL-3.0](./LICENSE).
- **Contrato de agente / JSON:** [AGENTS.md](./AGENTS.md).
