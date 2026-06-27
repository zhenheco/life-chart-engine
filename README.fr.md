> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · **Français** · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Calcul natif déterministe de trois systèmes de graphiques de vie — astrologie natale occidentale, 人類圖 (Human Design) et 紫微斗數 (Zi Wei Dou Shu) — à partir d'un seul enregistrement de naissance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` est un petit outil en ligne de commande hors ligne. Vous lui fournissez les données de naissance d'une personne — date, heure, fuseau horaire et coordonnées du lieu — et il calcule trois systèmes de graphiques indépendants en une seule passe, puis émet soit un rapport Markdown lisible, soit un objet JSON structuré destiné à la consommation par les programmes et les agents IA.

Il est conçu pour les personnes qui veulent des calculs de graphiques **reproductibles et vérifiables** plutôt qu'une application web en boîte noire : praticiens, développeurs construisant des outils d'autosensibilisation, et agents IA qui ont besoin d'une étape de calcul pur. Chaque nombre provient d'un véritable calcul astronomique et d'une véritable bibliothèque 紫微斗數 (iztro) — pas d'un service distant, pas de recherches en cache, et jamais sur le réseau.

---

## Ce qu'il calcule

Le moteur exécute trois systèmes contre le **même moment de naissance**, de sorte que leurs résultats peuvent se corroborer mutuellement. Chaque système répond à un type de question différent :

| Système | Ce que c'est (en français courant) | Ce que le moteur produit |
|---------|----------------------------------|------------------------|
| **Astrologie natale occidentale** (Tropical / Placidus) | L'astrologie occidentale classique — où se tenaient les planètes face au zodiaque à votre naissance, divisées en 12 maisons. | Ascendant + Milieu du ciel, 12 planètes/points (Soleil → Nœud sud) avec signe, degré, maison et indicateur rétrograde, les 12 cuspides de maison, et tous les aspects détectés (conjonction/sextile/carré/trigone/opposition) triés par précision. |
| **人類圖 Human Design** | Une synthèse moderne de l'astrologie, du Yijing et du système des chakras. Décrit comment votre énergie est « câblée » via des portes, des canaux et des centres. | Type, Autorité, Profil, Définition, Croix d'Incarnation, la date Design datée 88° plus tôt, centres définis/ouverts, canaux définis, et activations de porte.ligne par planète pour les cartes Personnalité et Design. |
| **紫微斗數 Zi Wei Dou Shu** | Un système d'astrologie chinoise traditionnel qui mappe le destin sur un plateau à 12 palais, peuplé d'étoiles nommées. | Classe des cinq éléments, Âme du destin / Corps du destin, index d'heure, et données par palais — ganzhi, indicateurs Âme/Corps, plage d'âge décennal, et étoiles majeure/mineure/adjectif (avec luminosité et mutations). Optionnellement un horoscope décennal/annuel au mieux-effort. |

Type, Autorité et Définition dans Human Design ne sont **pas codés en dur** — ils sont dérivés du graphe de connectivité des centres définis.

---

## Pourquoi le calcul natif

Ce moteur fait les vraies maths au lieu d'approximer ou d'appeler un service. Ce choix achète trois propriétés qui importent pour tout outil de graphique sérieux :

- **Déterministe.** Les mêmes entrées de naissance produisent toujours la même sortie, octet pour octet. Il n'y a pas d'aléatoire, pas de modèle, pas de dérive d'arrondi entre les exécutions.
- **Reproductible.** N'importe qui avec le repo et les mêmes entrées peut régénérer votre graphique exact. Les calculs utilisent astronomy-engine pour le ciel et iztro pour 紫微斗數 — tous deux déterministes.
- **Transvérifiable.** Parce que trois systèmes indépendants sont calculés à partir d'un même moment de naissance, vous pouvez trianguler. **Quand les trois systèmes pointent vers le même signal, traitez-le comme une confiance élevée. Quand un seul système montre un détail, traitez-le comme un point de référence, pas une conclusion.** C'est le principe de conception fondamental du moteur — il produit des faits à lire de manière croisée, pas un seul verdict.

---

## Démarrage rapide

### Installation en une ligne (recommandée)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

S'installe dans `~/.life-chart-engine` (modifiable avec `LIFE_CHART_DIR`). Pas de `sudo`, pas de changement système global — il clone seulement le dépôt, crée un venv CPython 3.12 isolé et génère le bundle Node iztro épinglé. Nécessite `git`, [`uv`](https://docs.astral.sh/uv/) et Node.js/npm. Relancez à tout moment pour mettre à jour vers la dernière version.

### À partir de la source

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Ce que fait `setup.sh`

Il s'exécute sous `set -euo pipefail` et effectue six étapes :

1. **Résout l'emplacement du venv** — `${LIFE_VENV:-<repo>/.venv}`. Définissez la variable d'environnement `LIFE_VENV` pour surcharger ; la valeur par défaut `.venv/` est dans .gitignore.
2. **Contrôle préalable : nécessite [`uv`](https://docs.astral.sh/uv/)** — si `uv` n'est pas dans `PATH`, il quitte avec code `1` et imprime l'indice d'installation :
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Crée un venv CPython 3.12** — `uv venv --python 3.12 "$VENV"` (voir [Pourquoi CPython 3.12](#why-cpython-312-specifically)).
4. **Installe les dépendances épinglées** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Construit le bundle iztro épinglé** — exécute `scripts/build-iztro-bundle.sh`, qui installe `iztro@2.5.8` dans un répertoire de build temporaire et produit `vendor/iztro.cjs`.
6. **Lance un test fumée** — exécute le moteur une fois avec des entrées d'exemple fixes (stdout ignoré) et imprime `OK — engine runs.` en cas de succès. Il imprime aussi des conseils d'utilisation pour les deux modes.

### Étapes `uv` manuelles (sans `setup.sh`)

```bash
# 1. Créer un venv CPython 3.12 (par défaut <repo>/.venv ; à surcharger avec LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Installer les dépendances épinglées
uv pip install --python .venv/bin/python -r requirements.txt

# 3. Construire le bundle iztro épinglé
bash scripts/build-iztro-bundle.sh

# 4. (Optionnel) test fumée
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Les dépendances Python directes sont épinglées dans `requirements.txt` :

```
astronomy-engine>=2.1.19
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei utilise un bundle Node généré et épinglé par `scripts/build-iztro-bundle.sh` :

```
iztro@2.5.8
```

---

## Pourquoi CPython 3.12 spécifiquement

Le moteur fonctionne actuellement sur le runtime vérifié **CPython 3.12**. La raison est indiquée de façon identique dans `requirements.txt` et `setup.sh` :

> CPython 3.12 reste verrouillé pour ce changement. L'ancienne contrainte de dépendance native Python de Zi Wei a disparu ; cela pourra être réexaminé après vérification des dépendances restantes et de l'image de déploiement.

En bref : 3.12 reste le runtime testé pour cette version. La dépendance Zi Wei n'impose plus ce verrou, donc une montée de version Python est une vérification de compatibilité ultérieure plutôt qu'une partie de ce refactor.

---

## Utilisation

Le moteur a deux modes, sélectionnés par la présence du drapeau `--json`.

### Mode humain (Markdown)

Omettez `--json` pour obtenir un rapport en console lisible. Utilisez le Python de votre venv :

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Exemple réel élagué (les aspects sont plafonnés aux 10 premiers en mode Markdown) :

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

### Mode agent (JSON)

Ajoutez `--json` pour obtenir un objet JSON unique sur stdout et rien d'autre — idéal pour les programmes et les agents IA :

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Exemple réel élagué (les tableaux sont tronqués à 1–2 entrées ; les valeurs sont littérales) :

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

## Référence des drapeaux CLI

Il n'y a **pas de drapeaux `required=True`** — argparse ne génère jamais d'erreur sur un manquant. L'omission de `--date`/`--time`/`--tz`/`--lat`/`--lon` revient silencieusement à une personne exemple intégrée (`範例`, née `2000-01-01 12:00`, UTC+8, Taipei 101). Donc pour un graphique correct, fournissez-les tous.

| Drapeau | Type | Obligatoire pour une utilisation correcte ? | Par défaut | Format / règle |
|---------|------|---------------------------------------------|-----------|-----------------|
| `--name` | chaîne | Non (cosmétique) | `"範例"` | Texte libre ; renvoyé dans la sortie uniquement. |
| `--gender` | chaîne | Seulement pour 紫微 | `"女"` | Doit être exactement `男` ou `女` (choix argparse ; autre chose → quitter `2`). |
| `--date` | chaîne | **Oui** | revient à `2000-01-01` | `YYYY-MM-DD`, divisé sur `-`. Aucune exigence de remplissage zéro. |
| `--time` | chaîne | **Oui** | revient à `12:00` | `HH:MM`, horloge 24 heures en heure locale, divisée sur `:`. |
| `--tz` | float | **Oui** | revient à `8.0` | Décalage UTC incluant DST (Taiwan = `8`). Écrit dans la clé d'entrée `tz_offset`. |
| `--lat` | float | **Oui** | revient à `25.0330` | Latitude en degrés décimaux (maisons occidentales/Asc/MC). |
| `--lon` | float | **Oui** | revient à `121.5654` | Longitude en degrés décimaux. |
| `--target` | chaîne | Non | `"2025-01-01"` | `YYYY-MM-DD` ; date de référence de la période chanceuse 紫微 (date de référence 運限). |
| `--json` | drapeau | Non | `False` (Markdown) | Présence → mode JSON ; absence → Markdown. Ne prend pas de valeur. |

> Le moteur ne géocode **pas** les lieux ni ne recherche les fuseaux horaires. L'appelant doit convertir lui-même lieu → `lat`/`lon`/`tz` — et le fuseau horaire/DST est la source d'erreur la plus courante, donc vérifiez le décalage UTC qui s'appliquait au lieu de naissance et à la date de naissance.

---

## Référence de sortie

L'enveloppe `--json` a sept clés de haut niveau, dans cet ordre :

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Bloc | Résumé |
|------|--------|
| `ok` | `true` en cas de succès (`false` dans l'enveloppe d'erreur). |
| `schema_version` | `"1.1"`. |
| `input` | Écho des entrées normalisées : `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (notez `tz_offset`, pas `tz`). |
| `western` | Chaîne `system`, objets de position `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (objet ou `null`). |
| `meta` | `{ engine, version, ephemeris }` — tous littéraux (`ephemeris: "astronomy-engine"`). |

Pour le contrat complet — chaque clé, type et protocole d'invocation d'agent — voir **[AGENTS.md](./AGENTS.md)**.

### Particularités de champs à connaître

- **`aspects` ne sont PAS plafonnés en JSON.** Le chemin JSON retourne *tous* les aspects détectés, triés par ordre croissant d'orbe (le plus serré d'abord). Le plafond de 10 éléments existe seulement dans le rapport Markdown.
- **`ziwei.horoscope` est au mieux-effort et peut être `null`.** Il est enveloppé dans `try/except` ; en cas d'exception, il se sérialise comme `null`. Quand présent, c'est `{ decadal, yearly }`. (Ces sous-objets exposent une structure interne supplémentaire — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, etc. — au-delà du placeholder documenté.)
- **Les chaînes d'étoiles codent luminosité + mutations.** Le format est `name(luminosité)[mutation]`, avec chaque partie optionnelle — par ex. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, ou simple `天機`. `adjective_stars` sont des noms simples seulement (pas de luminosité/mutation).

---

## Niveaux de précision

Pas chaque sortie ne porte la même confiance. Lisez chaque niveau en conséquence :

| Niveau | Ce qu'il couvre | Confiance |
|--------|-----------------|-----------|
| **Très élevé** | Longitudes planétaires, signes, rétrograde, plus placement d'étoile 紫微 / 命宮·身宮 / 五行局 — pure éphéméride et mathématique calendaire. | Astronomiquement/calendairement exact. |
| **Élevé, dépendant du temps** | Ascendant, Milieu du ciel, les 12 cuspides de maison, la maison dans laquelle tombe chaque planète, lignes Human Design, et index 時辰 紫微. | Exact *à condition* d'une heure de naissance précise ; sensible aux minutes. |
| **Vérifié** | Luminosité d'étoile 紫微斗數 — alignée avec les sorties de la bibliothèque iztro. | Vérifié contre la bibliothèque. |
| **Limite d'indicateur ±0,3°** | Toute planète / porte / ligne se situant dans ±0,3° d'une limite. | Traitez comme provisoire et notez l'impact — ±0,3° peut la renverser de l'autre côté de la ligne. |

---

## Limitations connues

- **Pas de Chiron / corps mineurs.** L'adapter expose seulement les 10 planètes classiques et les nœuds lunaires.
- **紫微斗數 utilise une école par défaut.** iztro est appelé avec des options fixes (`bySolar(..., True, 'zh-TW')`); l'école de placement d'étoile et les mutations sont ce que iztro utilise par défaut. Si vous utilisez normalement la 飛星 ou une autre école, la structure principale est inchangée mais certains détails peuvent différer.
- **Une heure de naissance approximative dégrade le niveau temps-dépendant.** Si l'heure de naissance est incertaine, les assignations d'Ascendant/MC/maison, les lignes Human Design, et 時辰 — et tout ce qui en dérive — deviennent peu fiables. Dans ce cas, **traitez les champs temps-dépendants comme provisoires** et considérez **la rectification basée sur événement** (faire correspondre les événements de vie connus au timing du graphique) avant de vous y fier.

---

## L'utiliser depuis un agent IA / Hermes

Le modèle d'intégration prévu est **l'auto-installation**, pas SaaS.

Un utilisateur copie l'URL du repo, et **son propre** agent ou CLI (Claude Code, Hermes, un script, etc.) le clone et l'exécute **localement sur la machine de l'utilisateur**. Le calcul se fait du côté de l'utilisateur. Il n'y a pas d'endpoint hébergé à appeler, pas de compte, et **aucune intégration SaaS requise** — le moteur est un sous-processus sans état, déterministe, hors ligne.

L'éditeur ne l'exploite pas comme service réseau. Sous MIT, l'usage local, la modification, la distribution et l'usage hébergé sont autorisés selon les termes de `LICENSE`.

Pour les agents, le contrat est simple : dispatcher le sous-processus `--json` avec le Python du venv dans le répertoire du repo, analyser stdout en tant que JSON, bifurquer sur `ok` (et le code de sortie), puis remettre l'objet structuré. Aucun nettoyage nécessaire — c'est sans état. Le contrat CLI + JSON complet se trouve dans **[AGENTS.md](./AGENTS.md)**.

### Configuration copier-coller pour votre agent IA

Collez ce bloc directement dans Claude Code, ChatGPT ou n'importe quel agent de codage — il indique à l'agent comment installer et appeler l'outil :

```text
Configurer et utiliser « life-chart-engine » — une CLI qui calcule un graphique natal occidental +
Human Design + Zi Wei Dou Shu (紫微斗數) à partir de données de naissance.

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Calculer un graphique et lire stdout comme JSON :
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Règles :
   - VOUS résolvez la ville de naissance en --lat/--lon et le décalage UTC historique correct
     (conscient de DST). L'outil ne géocode pas.
   - Confirmez si l'heure de naissance est exacte avant de faire confiance à l'ascendant,
     aux maisons, aux lignes Human Design, ou au pilier d'heure Zi Wei.
   - Ne jamais fabriquer de valeurs de graphique — toujours appeler l'outil.
   - Schéma de sortie complet, codes de sortie et contrat d'agent : ~/.life-chart-engine/AGENTS.md
```

---

## Licence

Ce dépôt est sous licence **[MIT](./LICENSE)**.

Le moteur utilise **astronomy-engine (MIT)** pour les calculs astronomiques et **iztro (MIT)** pour Zi Wei Dou Shu. Les formules de maisons Placidus et la référence à Meeus sont créditées dans [CREDITS.md](./CREDITS.md).

Vous pouvez utiliser, copier, modifier, distribuer, sous-licencier et vendre des copies selon les termes MIT. Conservez le copyright et le permission notice dans les parties substantielles du logiciel.

Voir **[CREDITS.md](./CREDITS.md)** pour l'attribution complète et les licences des dépendances.

---

## FAQ

**Puis-je entrer une date lunaire ?**
Non. Les entrées sont une date solaire grégorienne (`--date YYYY-MM-DD`) et une heure d'horloge (`--time HH:MM`). Si vous n'avez qu'une date lunaire, convertissez-la d'abord. 紫微斗數 est calculée via le point d'entrée solaire de iztro (`bySolar`).

**Mon heure de naissance est seulement approximative — est-ce un problème ?**
Les positions planétaires vont bien, mais l'Ascendant, le Milieu du ciel, les cuspides de maison, la maison dans laquelle se trouve chaque planète, les lignes Human Design, et 時辰 sont tous sensibles au temps. Traitez-les comme provisoires et considérez la rectification basée sur événement avant de vous y fier.

**Où sont Chiron / astéroïdes / corps mineurs ?**
Non inclus. L'adapter expose seulement les 10 planètes classiques et les nœuds lunaires.

**Quelle école 紫微斗數 utilise-t-elle ?**
L'école par défaut telle qu'implémentée par iztro (`bySolar(..., True, 'zh-TW')`). L'école n'est pas configurable par l'utilisateur.

**Est-ce que cela appelle à la maison / utilise le réseau ?**
Non. Le moteur est entièrement hors ligne — pas de télémétrie, pas d'appels réseau, pas d'effets secondaires. C'est un sous-processus sans état, déterministe, à usage unique.

**Puis-je l'utiliser dans un produit propriétaire ?**
Oui. Le dépôt est sous licence MIT. Conservez le copyright et le permission notice dans les parties substantielles du logiciel.

---

## Clause de non-responsabilité

`life-chart-engine` est un **cadre de sensibilisation personnelle interprétative, pas une prédiction ou un fatalisme**. Les résultats sont des points de référence structurés pour la réflexion — ils ne prédisent pas les événements et ne déterminent pas les résultats. Utilisez-les comme étalonnage, votre expérience vécue étant l'autorité finale. Rien ici n'est conseil médical, juridique, psychologique ou financier. Pour les décisions dans ces domaines, consultez un professionnel qualifié.

---

## Crédits & Licence

- **astronomy-engine** — Don Cross, MIT ; calculs astronomiques.
- **Meeus, Astronomical Algorithms** — référence pour les formules de maisons Placidus.
- **iztro** — MIT, pour Zi Wei Dou Shu.
- Attribution complète : **[CREDITS.md](./CREDITS.md)**.
- **Licence :** [MIT](./LICENSE).
- **Contrat agent / JSON :** [AGENTS.md](./AGENTS.md).
