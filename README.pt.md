> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · **Português** · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Cálculo nativo determinístico de três sistemas de carta astrológica — astrologia natal ocidental, 人類圖 (Human Design) e 紫微斗數 (Zi Wei Dou Shu) — a partir de um único registro de nascimento.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` é uma pequena ferramenta de linha de comando offline. Você fornece os dados de nascimento de uma pessoa — data, hora, fuso horário e coordenadas do local — e ela calcula três sistemas de carta independentes em uma única passagem, emitindo um relatório legível em Markdown ou um objeto JSON estruturado para programas e agentes de IA consumirem.

É construída para pessoas que desejam cálculos de carta **reproduzíveis e verificáveis** em vez de um aplicativo web em caixa preta: praticantes, desenvolvedores criando ferramentas de autoconhecimento e agentes de IA que precisam de uma etapa pura de computação. Cada número vem do cálculo astronômico real (Swiss Ephemeris) e de uma biblioteca real de 紫微斗數 (py-iztro) — não de um serviço remoto, não de buscas em cache e nunca pela rede.

---

## O que ela calcula

O motor executa três sistemas contra o **mesmo momento de nascimento**, para que suas saídas possam corroborar uma à outra. Cada sistema responde a um tipo diferente de pergunta:

| Sistema | O que é (em linguagem simples) | O que o motor produz |
|---------|-------------------------------|---------------------|
| **Ocidental natal** (Tropical / Placidus) | Astrologia ocidental clássica — onde os planetas estavam contra o zodíaco no seu nascimento, divididos em 12 casas. | Ascendente + Meio do Céu, 12 planetas/pontos (太陽 → 南交點) com signo, grau, casa e indicador de retrógrado, todas as 12 cúspides das casas e cada aspecto detectado (合相/六分/四分/三分/對分) classificado por precisão. |
| **人類圖 Human Design** | Uma síntese moderna de astrologia, o I-Ching e o sistema de chakras. Descreve como sua energia está "fiada" através de portões, canais e centros. | Tipo, Autoridade, Perfil, Definição, Cruz da Encarnação, a data de Design 88° anterior, centros definidos/abertos, canais definidos e ativações de porta.linha por planeta para ambas as cartas de Personalidade e Design. |
| **紫微斗數 Zi Wei Dou Shu** | Um sistema tradicional de astrologia chinesa que mapeia o destino em um tabuleiro de 12 palácios, preenchido por estrelas nomeadas. | 五行局 (Classe dos Cinco Elementos), 命主 (alma) / 身主 (corpo), índice de hora 時辰, e dados por palácio — ganzhi, sinalizadores 命/身, faixa etária decadal e estrelas maiores/menores/adjetivas (com brilho e 四化). Opcionalmente um horóscopo 大限/流年 de melhor esforço. |

Type, Authority e Definition em Human Design **não são codificados** — são derivados do grafo de conectividade dos centros definidos.

---

## Por que cálculo nativo

Este motor faz a matemática real em vez de aproximar ou chamar um serviço. Essa escolha oferece três propriedades que importam para qualquer ferramenta de carta séria:

- **Determinístico.** A mesma entrada de nascimento sempre produz a mesma saída, byte por byte. Não há aleatoriedade, nenhum modelo, nenhuma oscilação de arredondamento entre execuções.
- **Reproduzível.** Qualquer pessoa com o repositório e as mesmas entradas pode regenerar sua carta exata. Os cálculos usam Swiss Ephemeris (modelo Moshier) para o céu e py-iztro para 紫微斗數 — ambos determinísticos.
- **Verificável cruzadamente.** Como três sistemas independentes são calculados a partir de um único momento de nascimento, você pode triangular. **Quando todos os três sistemas apontam para o mesmo sinal, trate como alta confiança. Quando apenas um sistema mostra um detalhe, trate como um ponto de referência, não uma conclusão.** Este é o princípio central de design do motor — produz fatos para ler cruzadamente, não um único veredicto.

---

## Início rápido

### Instalação em uma linha (recomendada)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Instala em `~/.life-chart-engine` (substitua com `LIFE_CHART_DIR`). Sem `sudo`, sem alterações em todo o sistema — apenas clona o repositório e constrói um venv CPython 3.12 isolado. Requer `git` e [`uv`](https://docs.astral.sh/uv/). Execute novamente a qualquer momento para atualizar para a versão mais recente.

### Do source

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### O que `setup.sh` faz

Ele é executado sob `set -euo pipefail` e realiza cinco etapas:

1. **Resolve a localização do venv** — `${LIFE_VENV:-<repo>/.venv}`. Defina a variável de ambiente `LIFE_VENV` para substituir; o padrão `.venv/` é ignorado pelo git.
2. **Verificação preliminar: requer [`uv`](https://docs.astral.sh/uv/)** — se `uv` não estiver em `PATH` ele sai com `1` e imprime a dica de instalação:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Cria um venv CPython 3.12** — `uv venv --python 3.12 "$VENV"` (veja [Por que CPython 3.12](#why-cpython-312-specifically)).
4. **Instala dependências fixas** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Executa um teste de smoke** — executa o motor uma vez com entradas de amostra fixas (descartando stdout) e imprime `OK — engine runs.` no sucesso. Também imprime dicas de uso para ambos os modos.

### Etapas manuais do `uv` (sem `setup.sh`)

```bash
# 1. Criar venv CPython 3.12 (padrão <repo>/.venv; substitua com LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Instalar deps fixos
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (Opcional) teste de smoke
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

As únicas duas dependências diretas estão fixadas em `requirements.txt`:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## Por que CPython 3.12 especificamente

Você deve executar o motor em **CPython 3.12** — não 3.13, não 3.14. A razão é declarada de forma idêntica em `requirements.txt` e `setup.sh`:

> As dependências nativas do py-iztro (**pythonmonkey / pydantic-core**) **não têm wheels para 3.13+/3.14 e falham ao construir a partir do source**. Fixe em 3.12.

Em resumo: `py-iztro` depende de extensões nativas (`pythonmonkey`, `pydantic-core`) cujos wheels pré-construídos param em 3.12. Em 3.13/3.14 não há wheels e a construção do source falha. É exatamente por isso que `setup.sh` chama `uv venv --python 3.12`, e por isso você deve sempre invocar o motor com o Python do venv do projeto (`<repo>/.venv/bin/python`), nunca o `python3` do sistema.

---

## Uso

O motor tem dois modos, selecionados pela presença da flag `--json`.

### Modo humano (Markdown)

Omita `--json` para obter um relatório de console legível. Use o Python do seu venv:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Amostra real aparada (aspectos são limitados aos 10 principais no modo Markdown):

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

### Modo agente (JSON)

Adicione `--json` para obter um objeto JSON em stdout e nada mais — ideal para programas e agentes de IA:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Amostra real aparada (arrays truncados para 1–2 entradas; valores verbatim):

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

## Referência de flags da CLI

Não há **flags `required=True`** — argparse nunca gera erro em uma ausente. Omitir `--date`/`--time`/`--tz`/`--lat`/`--lon` retorna silenciosamente a uma pessoa de exemplo integrada (`範例`, nascida em `2000-01-01 12:00`, UTC+8, Taipei 101). Então, para uma carta correta, forneça todas elas.

| Flag | Tipo | Obrigatório para uso correto? | Padrão | Formato / regra |
|------|------|-------------------------------|--------|-----------------|
| `--name` | string | Não (cosmético) | `"範例"` | Texto livre; ecoado apenas na saída. |
| `--gender` | string | Apenas para 紫微 | `"女"` | Deve ser exatamente `男` ou `女` (argparse `choices`; qualquer outra coisa → sai com `2`). |
| `--date` | string | **Sim** | retorna a `2000-01-01` | `YYYY-MM-DD`, dividido em `-`. Sem requisito de zero-pad. |
| `--time` | string | **Sim** | retorna a `12:00` | `HH:MM`, relógio local 24 horas, dividido em `:`. |
| `--tz` | float | **Sim** | retorna a `8.0` | Deslocamento UTC incluindo DST (Taiwan = `8`). Escrito na chave de entrada `tz_offset`. |
| `--lat` | float | **Sim** | retorna a `25.0330` | Latitude em graus decimais (casas ocidentais/Asc/MC). |
| `--lon` | float | **Sim** | retorna a `121.5654` | Longitude em graus decimais. |
| `--target` | string | Não | `"2025-01-01"` | `YYYY-MM-DD`; data de referência do período de sorte 紫微 (運限參考日). |
| `--json` | flag | Não | `False` (Markdown) | Presença → modo JSON; ausência → Markdown. Sem valor. |

> O motor **não** localiza lugares nem busca fusos horários. O chamador deve converter lugar → `lat`/`lon`/`tz` por si mesmo — e fuso horário/DST é a fonte mais comum de erro, então verifique o deslocamento UTC que se aplicava ao local de nascimento e à data de nascimento.

---

## Referência de saída

O envelope `--json` tem sete chaves de nível superior, nesta ordem:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Bloco | Resumo |
|-------|--------|
| `ok` | `true` em sucesso (`false` no envelope de erro). |
| `schema_version` | `"1.0"`. |
| `input` | Eco das entradas normalizadas: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (note `tz_offset`, não `tz`). |
| `western` | String `system`, objetos de posição `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (objeto ou `null`). |
| `meta` | `{ engine, version, ephemeris }` — todos literais (`ephemeris: "Moshier"`). |

Para o contrato de campo completo — cada chave, tipo e o protocolo de invocação de agente — veja **[AGENTS.md](./AGENTS.md)**.

### Quirks de campo que vale saber

- **`aspects` NÃO são limitados em JSON.** O caminho JSON retorna *cada* aspecto detectado, classificado em ordem crescente por orb (mais apertado primeiro). O limite de 10 itens existe apenas no relatório Markdown.
- **`ziwei.horoscope` é de melhor esforço e pode ser `null`.** É envolvido em `try/except`; em qualquer exceção é serializado como `null`. Quando presente é `{ decadal, yearly }`. (Esses sub-objetos expõem estrutura interna extra — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, etc. — além do placeholder documentado.)
- **Strings de estrela codificam brilho + 四化.** Formato é `name(brightness)[mutagen]`, com cada parte opcional — por ex., `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]` ou simples `天機`. `adjective_stars` são apenas nomes (sem brilho/mutagen).

---

## Níveis de precisão

Nem toda saída carrega a mesma confiança. Leia cada nível de acordo:

| Nível | O que cobre | Confiança |
|-------|-------------|-----------|
| **Mais alta** | Longitudes planetárias, signos, retrógrado, mais colocação de estrela 紫微 / 命宮·身宮 / 五行局 — matemática pura de efemérides e calendário. | Astronomicamente/calendricamente exata. |
| **Alta, dependente de tempo** | Ascendente, Meio do Céu, todas as 12 cúspides das casas, a casa em que cada planeta cai, linhas de Human Design e o índice de hora 時辰 de 紫微. | Exata *dada* uma hora de nascimento precisa; sensível a minutos. |
| **Verificada** | Brilho de estrela 紫微斗數 — alinhado com as saídas da biblioteca py-iztro. | Verificada contra a biblioteca. |
| **Flag de limite ±0.3°** | Qualquer planeta / portão / linha sentado dentro de ±0.3° de um limite. | Trate como provisório e note o impacto — ±0.3° pode inverter através da linha. |

---

## Limitações conhecidas

- **Sem Quíron / corpos menores.** A compilação usa a efeméride Moshier (`swe.FLG_MOSEPH`, sem arquivos de dados), que não fornece Quíron ou outros corpos menores. Apenas os 10 planetas clássicos mais os nós lunares são computados.
- **紫微斗數 usa uma escola padrão.** py-iztro é chamado com opções fixas (`by_solar(..., True, 'zh-TW')`); a escola de colocação de estrela e 四化 são o que py-iztro padrão é. Se você normalmente usa 飛星 ou outra escola, a estrutura principal é inalterada mas alguns detalhes podem diferir.
- **Hora de nascimento aproximada degrada o nível dependente de tempo.** Se a hora de nascimento é incerta, as atribuições de Ascendente/MC/casa, linhas de Human Design e 時辰 — e qualquer coisa derivada delas — tornam-se não confiáveis. Nesse caso, **trate os campos dependentes de tempo como provisórios** e considere **retificação baseada em eventos** (combinando eventos de vida conhecidos com tempo de carta) antes de confiar neles.

---

## Use-o de um agente de IA / Hermes

O modelo de integração pretendido é **auto-instalar**, não SaaS.

Um usuário copia a URL deste repositório, e **seu próprio** agente ou CLI (Claude Code, Hermes, um script, etc.) o clona e executa **localmente na máquina do usuário**. A computação acontece do lado do usuário. Não há endpoint hospedado para chamar, nenhuma conta, e **nenhuma integração SaaS necessária** — o motor é um subprocess offline, estateless e determinístico.

Como o editor não o opera como um serviço de rede, nenhuma obrigação §13 incide sobre o editor por autossinstalação de outro — separadamente, §13 obriga apenas um operador que executa uma versão *modificada* acessível pela rede — não uso local não modificado.

Para agentes, o contrato é simples: despache o subprocess `--json` com o Python do venv no workdir do repositório, analise stdout como JSON, ramifique em `ok` (e o código de saída), depois passe o objeto estruturado. Nenhuma limpeza necessária — é stateless. O contrato CLI + JSON completo vive em **[AGENTS.md](./AGENTS.md)**.

### Copiar-colar setup para seu agente de IA

Cole este bloco direto em Claude Code, ChatGPT ou qualquer agente de codificação — ele diz ao agente como instalar e chamar a ferramenta:

```text
Configurar e usar "life-chart-engine" — uma CLI que calcula uma carta natal ocidental +
Human Design + Zi Wei Dou Shu (紫微斗數) a partir de dados de nascimento.

1. Instalar (precisa de `git` e `uv`; se uv estiver faltando: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Calcular uma carta e ler stdout como JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Regras:
   - VOCÊ resolve a cidade de nascimento para --lat/--lon e o deslocamento UTC histórico correto
     (consciente de DST). A ferramenta não localiza.
   - Confirme se a hora de nascimento é exata antes de confiar no ascendente,
     casas, linhas de Human Design ou o pilar de hora Zi Wei.
   - Nunca fabrique valores de carta — sempre chame a ferramenta.
   - Esquema de saída completo, códigos de saída e o contrato de agente: ~/.life-chart-engine/AGENTS.md
```

---

## Licenciamento

Este repositório é licenciado sob **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 em inglês simples.** É o GNU GPL-3.0 (uma licença copyleft forte: se você distribui o software, deve liberar seu código fonte completo correspondente sob a mesma licença) **mais uma cláusula extra, Seção 13**. §13 fecha a "brecha do SaaS": além do gatilho de *distribuição* do GPL, adiciona que se você *modifica* o programa e deixa usuários interagirem com sua versão modificada pela rede, você deve oferecer àqueles usuários remotos seu código fonte correspondente. (Executar um upstream não modificado como um serviço de rede não dispara §13 por si só.) AGPL é recíproco mas não infinitamente viral — apenas alcança código que é um derivado de, ou vinculado com, o código AGPL.

**Por que este repositório é AGPL.** O motor vincula **Swiss Ephemeris** (via `pyswisseph`) para posições planetárias e cúspides de casas. Astrodienst **dual-licencia** Swiss Ephemeris como **AGPL-3.0 OR uma licença comercial**, e seu código não pode ser relicenciado como algo mais permissivo. Como AGPL é copyleft e este projeto o vincula, a obra combinada inteira deve ser AGPL. (`py-iztro` é MIT e não impõe copyleft; Swiss Ephemeris é o único componente forçando AGPL aqui.)

**O que significa na prática.**

| Você faz | Obrigação AGPL |
|---------|----------------|
| **Auto-instalar** (executar localmente para você) | §13 *não* é disparado — não há usuários remotos a servir, e você já tem o código. Limpo. |
| **Executar uma versão *modificada* como um serviço de rede** | §13 *é* disparado — você deve oferecer àqueles usuários remotos o código fonte correspondente completo de sua versão implantada, sob AGPL, incluindo suas modificações. Nota: o dever de oferta de fonte do §13 é condicionado em modificação — executar o upstream não modificado como um serviço de rede não dispara §13 por si só, embora a fonte já seja pública de qualquer forma. |

**Suas três opções** se a obrigação de fonte de rede não se encaixa em seu caso de uso:

1. **Manter AGPL** — publique seu código fonte correspondente completo (incluindo modificações) para qualquer pessoa que o use, incluindo pela rede por §13. Grátis, sem negociação.
2. **Compre uma licença comercial de Swiss Ephemeris de [Astrodienst](https://www.astro.com/swisseph/)** — isso levanta a obrigação AGPL para a porção Swiss Ephemeris, deixando você relicenciar seu próprio código e enviar/hospedar um build fechado. (Este é o modelo dual-license de Astrodienst.)
3. **Troque a efeméride** — substitua `pyswisseph` por uma fonte de astronomia licenciada permissivamente (por exemplo **Skyfield (MIT)** mais a efeméride de domínio público **JPL DE440** — alternativas ilustrativas, não a única opção). Com Swiss Ephemeris fora, a pilha restante (py-iztro MIT, mais deps MPL-2.0/MIT/Apache) não força mais AGPL e todo o repositório poderia ser MIT. Este é esforço de engenharia real: você deve reimplementar tudo atualmente fornecido por Swiss Ephemeris — longitudes planetárias, sinalizadores retrógrados, Asc/MC, cúspides de casa Placidus e as entradas para o solucionador de design 88° de Human Design.

Veja **[CREDITS.md](./CREDITS.md)** para atribuição completa e licenças por dependência.

---

## FAQ

**Posso inserir uma data lunar?**
Não. As entradas são uma data solar Gregoriana (`--date YYYY-MM-DD`) e hora do relógio (`--time HH:MM`). Se você só tem uma data lunar, converta-a primeiro. 紫微斗數 é calculado via ponto de entrada solar de py-iztro (`by_solar`).

**Minha hora de nascimento é apenas aproximada — isto é um problema?**
As posições planetárias ficam bem, mas o Ascendente, Meio do Céu, cúspides de casas, a casa em que cada planeta se senta, linhas de Human Design e 時辰 são todos sensíveis ao tempo. Trate-os como provisórios e considere retificação baseada em eventos antes de confiar neles.

**Onde está Quíron / asteroides / corpos menores?**
Não incluído. A efeméride Moshier usada aqui não fornece eles; apenas os 10 planetas clássicos e os nós lunares são computados.

**Qual escola de 紫微斗數 ela usa?**
A escola padrão conforme implementada por py-iztro (`by_solar(..., True, 'zh-TW')`). A escola não é selecionável pelo usuário.

**Ela telefona para casa / usa a rede?**
Não. O motor é totalmente offline — sem telemetria, sem chamadas de rede, sem efeitos colaterais. É um subprocess estateless, determinístico e único.

**Posso usá-lo dentro de um produto fechado?**
Sob AGPL-3.0, sim para uso privado/local. Distribuir um build dispara as obrigações de conveyance e código-fonte da GPL, e servir pela rede um build *modificado* dispara AGPL §13 — ou de forma alguma você deve oferecer código fonte correspondente. Para ficar completamente fechado, ou compre uma licença comercial de Swiss Ephemeris de Astrodienst ou troque a efeméride para Skyfield + JPL DE440 (veja [Licenciamento](#licensing)).

---

## Aviso legal

`life-chart-engine` é um **framework de auto-reflexão interpretativa, não predição ou fatalismo**. As saídas são pontos de referência estruturados para reflexão — não predizem eventos e não determinam resultados. Use-os como calibração, com sua própria experiência vivida como a autoridade final. Nada aqui é conselho médico, legal, psicológico ou financeiro. Para decisões nesses domínios, consulte um profissional qualificado.

---

## Créditos e Licença

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, dual-licenciado AGPL-3.0 / comercial (<https://www.astro.com/swisseph/>).
- **py-iztro** (e upstream `iztro`) — MIT, para 紫微斗數.
- Atribuição completa: **[CREDITS.md](./CREDITS.md)**.
- **Licença:** [AGPL-3.0](./LICENSE).
- **Contrato agente / JSON:** [AGENTS.md](./AGENTS.md).
