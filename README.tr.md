> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · **Türkçe** · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Üç yaşam haritası sisteminin deterministik yerel hesaplaması — Batı doğum haritacılığı (Western natal astrology), 人類圖 (Human Design) ve 紫微斗數 (Zi Wei Dou Shu) — tek bir doğum kaydından.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` küçük ve çevrimdışı bir komut satırı aracıdır. Bir kişinin doğum verilerini — tarih, zaman, saat dilimi ve yer koordinatlarını — girin; araç üç bağımsız harita sistemini tek seferde hesaplar ve insan tarafından okunabilir bir Markdown raporu ya da programlar ve yapay zeka ajanları tarafından tüketilecek yapılandırılmış bir JSON nesnesi yayınlar.

Gerçek astronomik hesaplamayı (Swiss Ephemeris) ve gerçek bir 紫微斗數 kütüphanesini (iztro) kullanan **üretebilir ve doğrulanabilir** harita hesaplamaları isteyen insanlar için tasarlanmıştır — bir kara kutu web uygulaması değil, uzak bir hizmet değil, hiçbir zaman ağ üzerinden değil. Her sayı gerçek astronomik hesaplamadan (Swiss Ephemeris) ve gerçek bir 紫微斗數 kütüphanesinden (iztro) gelir — uzak bir hizmet, önbelleğe alınmış arama veya ağ üzerinde hiçbir şey olmaz.

---

## Neler hesaplandığı

Motor, **aynı doğum anına** karşı üç sistemi çalıştırır; böylece çıktıları birbirini doğrulayabilir. Her sistem farklı bir soruyu yanıtlar:

| Sistem | Ne olduğu (basit İngilizce) | Motorun sunduğu sonuç |
|--------|---------------------------|----------------------|
| **Batı doğum haritacılığı** (Tropical / Placidus) | Klasik Batı yıldız bilimi — doğumunuzda gezegenlerin burç karşısında nerede olduğu, 12 eve bölünmüş. | Yükselen Burç + Orta Gök, 12 gezegen/nokta (太陽 → Güney Düğümü) işaret, derece, ev ve geriye dönüş işareti, tüm 12 ev ucu ve algılanan tüm yönler (konjunksiyon/sekstil/kare/trigon/karşıt) sıkılığa göre sıralanmış. |
| **人類圖 Human Design** | Yıldız bilimi, I-Ching ve çakra sisteminin modern sentezi. Enerjinizin kapılar, kanallar ve merkezler aracılığıyla nasıl "kablolu" olduğunu açıklar. | Tip, Yetki, Profil, Tanım, İlahiyat Haçı, 88° önceki Tasarım tarihi, tanımlanan/açık merkezler, tanımlanan kanallar ve hem Kişilik hem de Tasarım haritaları için gezegen başına kapı.satır aktivasyonları. |
| **紫微斗數 Zi Wei Dou Shu** | Kaderini 12 saraydaki bir tahtaya eşleyen geleneksel Çin yıldız bilimi sistemi, adlandırılmış yıldızlarla doldurulmuş. | 五行局 (Beş Element Sınıfı), 命主 (ruh) / 身主 (beden), 時辰 saat dizini ve saray başına veri — ganzhi, 命/身 işaretleri, onlu yaş aralığı ve ana/yan/sıfat yıldızlar (parlaklık ve 四化 ile). İsteğe bağlı olarak en iyi çaba 大限/流年 horoskopu. |

Human Design'da Tip, Yetki ve Tanım **sabit kodlanmamıştır** — tanımlanan merkezlerin bağlantı grafiğinden türetilir.

---

## Neden yerel hesaplama

Bu motor yaklaşımcılık yapmak veya bir hizmeti çağırmak yerine gerçek matematik yapar. Bu seçim, ciddi bir harita aracı için önemli olan üç özellik getirir:

- **Deterministik.** Aynı doğum girdisi her zaman aynı çıktıyı, bayt-bayt aynı şekilde üretir. Rastgelelik yok, model yok, çalıştırmalar arasında yuvarlama sapması yok.
- **Üretilebilir.** Depoyu ve aynı girdileri olan herkes, tam haritanızı yeniden oluşturabilir. Hesaplamalar gökyüzü için Swiss Ephemeris (Moshier modeli) ve 紫微斗數 için iztro kullanır — ikisi de deterministiktir.
- **Çapraz doğrulanabilir.** Üç bağımsız sistem tek bir doğum anından hesaplandığı için, üçgenlenebilirsiniz. **Üç sistem de aynı sinyale işaret ettiğinde, bunu yüksek güven olarak değerlendirin. Sadece bir sistem bir ayrıntı gösterdiğinde, bunu bir referans noktası olarak değerlendirin, sonuç olarak değil.** Bu, motorun temel tasarım ilkesidir — çapraz okunacak gerçekler üretir, tek bir karar değil.

---

## Hızlı başlangıç

### Tek satırlık kurulum (önerilir)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

`~/.life-chart-engine` içine kurar (`LIFE_CHART_DIR` ile geçersiz kılınabilir). `sudo` yok, sistem genelinde değişiklik yok — yalnızca repoyu klonlar, izole bir CPython 3.12 venv oluşturur ve sabitlenmiş iztro Node paketini üretir. `git`, [`uv`](https://docs.astral.sh/uv/) ve Node.js/npm gerektirir. En son sürüme güncellemek için istediğiniz zaman tekrar çalıştırın.

### Kaynaktan

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` neler yapar

`set -euo pipefail` altında çalışır ve altı adım gerçekleştirir:

1. **Venv konumunu çözer** — `${LIFE_VENV:-<repo>/.venv}`. Geçersiz kılmak için `LIFE_VENV` ortam değişkenini ayarlayın; varsayılan `.venv/` git tarafından yoksayılır.
2. **Ön kontrol: [`uv`](https://docs.astral.sh/uv/) gerektirir** — `uv` `PATH` üzerinde değilse çıkış `1` ile çıkar ve kurulum ipucunu yazdırır:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **CPython 3.12 venv oluşturur** — `uv venv --python 3.12 "$VENV"` ([Neden CPython 3.12](#why-cpython-312-specifically) bölümüne bakın).
4. **Sabitlenmiş bağımlılıkları yükler** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Sabitlenmiş iztro paketini oluşturur** — `scripts/build-iztro-bundle.sh` çalıştırır; bu betik `iztro@2.5.8` paketini geçici bir build dizinine kurar ve `vendor/iztro.cjs` üretir.
6. **Smoke test çalıştırır** — motoru sabit örnek girdilerle bir kez çalıştırır (stdout atılır) ve başarıda `OK — engine runs.` yazar. Ayrıca iki mod için kullanım ipuçları yazar.

### Manuel `uv` adımları (`setup.sh` olmadan)

```bash
# 1. CPython 3.12 venv oluştur (varsayılan <repo>/.venv; LIFE_VENV ile geçersiz kıl)
uv venv --python 3.12 .venv

# 2. Sabitlenmiş bağımlılıkları yükle
uv pip install --python .venv/bin/python -r requirements.txt

# 3. Sabitlenmiş iztro paketini oluştur
bash scripts/build-iztro-bundle.sh

# 4. (İsteğe bağlı) smoke test
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Python doğrudan bağımlılıkları `requirements.txt` içinde sabitlenmiştir:

```
pyswisseph==2.10.3.2
fastapi==0.128.8
uvicorn==0.39.0
httpx==0.28.1
```

Zi Wei, `scripts/build-iztro-bundle.sh` tarafından sabitlenmiş üretilen bir Node paketi kullanır:

```
iztro@2.5.8
```

---

## Neden özel olarak CPython 3.12

Motor şu anda doğrulanmış **CPython 3.12** runtime üzerinde çalışır. Bunun nedeni `requirements.txt` ve `setup.sh` içinde aynı şekilde belirtilir:

> CPython 3.12 bu değişiklik için kilitli kalır. Eski Python Zi Wei native bağımlılık kısıtı kalktı; bu yüzden kalan bağımlılıklar ve deployment imajı kontrol edildikten sonra yeniden değerlendirilebilir.

Kısaca: 3.12 bu sürüm için hâlâ test edilen runtime'dır. Zi Wei bağımlılığı artık bu kilidi zorlamıyor; dolayısıyla Python sürümünü yükseltmek bu refactor'ın parçası değil, sonraki bir uyumluluk kontrolüdür.

---

## Kullanım

Motorun iki modu vardır, `--json` işaretinin varlığıyla seçilir.

### İnsan modu (Markdown)

Okunabilir bir konsol raporu almak için `--json` atlayın. Venv'inizin Python'unu kullanın:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Kesilmiş gerçek örnek (yönler Markdown modunda ilk 10 ile sınırlıdır):

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

### Ajan modu (JSON)

Bir JSON nesnesi almak ve başka hiçbir şey almamak için `--json` ekleyin — programlar ve yapay zeka ajanları için ideal:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Kesilmiş gerçek örnek (diziler 1–2 giriş ile kesilmiş; değerler olduğu gibi):

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

## CLI işaretleri başvurusu

**Zorunlu işaret yok** — argparse eksik bir işarette asla hata vermez. `--date`/`--time`/`--tz`/`--lat`/`--lon` atlamamak, sessizce yerleşik bir örnek kişiye (`範例`, doğum `2000-01-01 12:00`, UTC+8, Taipei 101) geri döner. Doğru bir harita için hepsini sağlayın.

| İşaret | Tür | Doğru kullanım için gerekli? | Varsayılan | Biçim / kural |
|--------|-----|-----------------------------|---------|-|
| `--name` | dize | Hayır (kozmetik) | `"範例"` | Serbest metin; sadece çıktıya yankılanır. |
| `--gender` | dize | Sadece 紫微 için | `"女"` | Kesinlikle `男` ya da `女` olmalıdır (argparse `choices`; başka bir şey → çıkış `2`). |
| `--date` | dize | **Evet** | `2000-01-01`'e geri döner | `YYYY-MM-DD`, `-` üzerinde bölün. Sıfır doldurma gerekli değil. |
| `--time` | dize | **Evet** | `12:00`'ye geri döner | `HH:MM`, 24 saat yerel saat, `:` üzerinde bölün. |
| `--tz` | kayan | **Evet** | `8.0`'ye geri döner | UTC kaydırması DST dahil (Tayvan = `8`). Giriş anahtarı `tz_offset` yazılır. |
| `--lat` | kayan | **Evet** | `25.0330`'ye geri döner | Ondalık derece cinsinden enlem (Batı evleri/Asc/MC). |
| `--lon` | kayan | **Evet** | `121.5654`'ye geri döner | Ondalık derece cinsinden boylam. |
| `--target` | dize | Hayır | `"2025-01-01"` | `YYYY-MM-DD`; 紫微 şans dönemi referans tarihi (運限參考日). |
| `--json` | işaret | Hayır | `False` (Markdown) | Varlık → JSON modu; yokluk → Markdown. Değer almaz. |

> Motor yerler coğrafya kodlaması yapmaz veya saat dilimlerini aramaz. Arayan, yeri → `lat`/`lon`/`tz` kendileri dönüştürmelidir — ve saat dilimi/DST en yaygın hata kaynağıdır; bu nedenle doğum yerinde ve doğum tarihinde geçerli olan UTC kaydırmasını doğrulayın.

---

## Çıkış başvurusu

`--json` zarfı yedi üst düzey anahtara sahiptir, bu sırada:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Blok | Özet |
|------|------|
| `ok` | Başarı üzerine `true` (hata zarfında `false`). |
| `schema_version` | `"1.0"`. |
| `input` | Normalleştirilmiş girdilerin yankısı: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (`tz` değil `tz_offset` not). |
| `western` | `system` dizesi, `ascendant`/`midheaven` konum nesneleri, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (nesne ya da `null`). |
| `meta` | `{ engine, version, ephemeris }` — tümü değişmezler (`ephemeris: "Moshier"`). |

Tam alan sözleşmesi için — her anahtar, tür ve ajan çağırma protokolü — bkz. **[AGENTS.md](./AGENTS.md)**.

### Bilmekte değer olan alan tuhafları

- **`aspects` JSON'da SINIRLANDI DEĞİL.** JSON yolu *her* algılanan yönü döndürür, orba göre artan sırada sıralanır (en sıkı ilk). 10 öğe sınırı yalnızca Markdown raporda vardır.
- **`ziwei.horoscope` en iyi çaba ve `null` olabilir.** `try/except` ile sarılmıştır; herhangi bir istisna üzerine `null` olarak serileştirilir. Mevcut olduğunda `{ decadal, yearly }` dir. (Bu alt nesneler, belgelenen yer tutucuyu aşan ek iç yapıyı ortaya koyan — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star` vb.)
- **Yıldız dizgileri parlaklık + 四化 kodlar.** Biçim `name(brightness)[mutagen]`, her parça isteğe bağlı — örn. `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, ya da düz `天機`. `adjective_stars` sadece düz isimlerdir (parlaklık/mutagen yok).

---

## Doğruluk katmanları

Her çıkış aynı güvene sahip değildir. Her katmanı uygun şekilde okuyun:

| Katman | Neyi kapsar | Güven |
|--------|----------|--------|
| **En yüksek** | Gezegen boylamı, işaretler, geriye dönüş, artı 紫微 yıldız yerleşimi / 命宮·身宮 / 五行局 — saf efemeris ve takvim matematik. | Astronomik/takvim açısından tam doğru. |
| **Yüksek, zamana bağlı** | Yükselen Burç, Orta Gök, tüm 12 ev ucu, her gezegen hangi eve düşer, Human Design çizgileri ve 紫微 時辰 indeksi. | *Verilen* doğru doğum zamanı olduğunda tam; dakikalara duyarlı. |
| **Doğrulanmış** | 紫微斗數 yıldız parlaklığı — iztro kütüphanesinin çıktılarına hizalanmış. | Kütüphaneye karşı doğrulanmış. |
| **Bayrak sınırı ±0.3°** | Sınırın ±0.3° içinde oturan herhangi bir gezegen / kapı / çizgi. | Geçici olarak ele alın ve etkisine not edin — ±0.3° sınırı karşısında çevirmek olabilir. |

---

## Bilinen sınırlamalar

- **Chiron / küçük cisimler yok.** Yapı Moshier efemerisini (`swe.FLG_MOSEPH`, veri dosyası yok) kullanır; bu da Chiron veya diğer küçük cisimleri sağlamaz. Sadece 10 klasik gezegen ve ay düğümleri hesaplanır.
- **紫微斗數 bir varsayılan okulu kullanır.** iztro sabit seçeneklerle çağrılır (`bySolar(..., True, 'zh-TW')`); yıldız yerleşimi okulu ve 四化 iztro'nun varsayılanlarıdır. Normalde 飛星 veya başka bir okul kullanıyorsanız, ana yapı değişmez ancak bazı ayrıntılar farklı olabilir.
- **Yaklaşık doğum zamanı zamana bağlı katmanı bozar.** Doğum zamanı belirsizse, Yükselen Burç/MC/ev atamaları, Human Design çizgileri ve 時辰 — ve onlardan türetilen her şey — güvenilmez olur. Bu durumda, **zamana bağlı alanları geçici olarak ele alın** ve **olaya dayalı düzeltmeyi göz önünde bulundurun** (bilinen yaşam olaylarını harita zamanlamasıyla eşleştirmek) bunlara güvenmeden önce.

---

## Bir yapay zeka ajanı / Hermes'ten kullanın

Amaçlanan entegrasyon modeli SaaS değil, **self-install**dir.

Bir kullanıcı bu depoyu URL'sini kopyalar ve **kendi** ajanı veya CLI'si (Claude Code, Hermes, bir komut dosyası vb.) bunu klonlar ve **kullanıcının makinesinde yerel olarak çalıştırır**. Hesaplama, kullanıcı tarafında gerçekleşir. Çağrılacak barındırılan bir uç nokta yok, hesap yok ve **SaaS entegrasyonu gerekli değil** — motor, durumsuz, deterministik, çevrimdışı bir alt süreçtir.

Yayıncı bunu bir ağ hizmeti olarak işletmediği için, başka birinin self-install'ı için §13 yükümlülüğü yayıncıya düşmez. (Ayrıca, §13 sadece *değiştirilmiş* bir ağ erişimine açık sürümü çalıştıran bir operatörü yükümlü kılar — değiştirilmemiş yerel kullanımı değil.)

Ajanlar için, sözleşme basittir: `--json` alt işlemini venv Python'u repo çalışma dizininde gönderin, stdout'u JSON olarak ayrıştırın, `ok` (ve çıkış kodu) üzerinde dal ve yapılandırılmış nesneyi devraleçin. Temizlik gerekli değil — durumsuz. Tam CLI + JSON sözleşmesi **[AGENTS.md](./AGENTS.md)** içinde yaşar.

### Yapay zeka ajanınız için kopyala-yapıştır kurulumu

Bu bloku doğrudan Claude Code, ChatGPT veya herhangi bir kodlama ajanına yapıştırın — araç nasıl yükleyeceğini ve çağıracağını ajanı bilgilendirir:

```text
"life-chart-engine" — doğum verilerinden Batı doğum haritası + Human Design +
紫微斗數 (Zi Wei Dou Shu) hesaplayan bir CLI'yi kurun ve kullanın.

1. Install (needs `git`, `uv`, and Node.js/npm; if uv is missing: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Bir harita hesaplayın ve stdout'u JSON olarak okuyun:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<etiket>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <dst_dahil_utc_kaydırması> --lat <enlem> --lon <boylam> \
     --target <YYYY-MM-DD>

3. Kurallar:
   - DOĞUM ŞEHRİNİ --lat/--lon'a ve doğru tarihsel UTC
     kaydırması (DST duyarlı) olarak ÇÖZERSİNİZ. Araç coğrafya kodlaması yapmaz.
   - Yükselen Burç, evler, Human Design çizgileri veya Zi Wei saat direğine
     güvenmeden önce doğum zamanının tam olup olmadığını onaylayın.
   - Asla harita değerlerini uydurma — her zaman aracı çağırın.
   - Tam çıkış şeması, çıkış kodları ve ajan sözleşmesi: ~/.life-chart-engine/AGENTS.md
```

---

## Lisanslama

Bu depo, **[AGPL-3.0](./LICENSE)** altında lisanslanmıştır.

**AGPL-3.0 sade İngilizce.** GNU GPL-3.0'dır (güçlü bir copyleft lisansı: yazılımı dağıtırsanız, tam ilgili kaynağınızı aynı lisans altında yayınlamalısınız) **artı bir ekstra madde, 13. Bölüm**. §13 "SaaS açığını" kapatır: GPL'nin *dağıtım* tetikleyicisinin ötesinde, programı *değiştirir* ve kullanıcılarınızın değiştirilmiş sürümünüzle bir ağ üzerinden etkileşime girmesine izin verirseniz, bu uzak kullanıcılara ilgili kaynağınızı sunmalısınız. (Değiştirilmemiş üst akışı bir ağ hizmeti olarak çalıştırmak kendisinde §13'ü tetiklemez.) AGPL karşılıklıdır ancak sınırsız viral değil — yalnızca AGPL kodunun türevi veya bağlantılı kodu ulaşır.

**Bu depo neden AGPL'dir.** Motor, gezegen konumları ve ev uçları için **Swiss Ephemeris** (`pyswisseph` aracılığıyla) bağlantı kurar. Astrodienst, Swiss Ephemeris'i **AGPL-3.0 VEYA ticari lisans** olarak çift lisanslı tutar ve kodunun daha izin verici bir şeye lisans değiştirilmesi mümkün değil. AGPL copyleft olduğu ve bu proje bunu bağladığı için, tüm birleştirilmiş iş AGPL olmalı. (`iztro` MIT'dir ve copyleft empoze etmez; Swiss Ephemeris, burada AGPL'yi zorlayan tek bileşendir.)

**Pratikte ne anlama gelir.**

| Bunu yaparsınız | AGPL yükümlülüğü |
|---|---|
| **Self-install** (kendiniz için yerel olarak çalıştırın) | §13 *tetiklenmez* — uzak kullanıcı yok ve kaynağa zaten sahipsiniz. Temiz. |
| **Bir *değiştirilmiş* sürümü ağ hizmeti olarak çalıştırın** | §13 *tetiklenir* — bu uzak kullanıcılara değiştirilmiş sürüm de dahil olmak üzere, tam ilgili kaynağını AGPL altında sunmalısınız. Not: §13'ün kaynak sunma görevi değiştirmeye koşulludur — değiştirilmemiş üst akışı bir ağ hizmeti olarak çalıştırmak kendisinde §13'ü tetiklemez, ancak kaynak zaten kamuya açıktır. |

**Ağ-kaynak yükümlülüğü, kullanım durumunuza uymazsa üç seçeneğiniz vardır:**

1. **AGPL'yi tutun** — tam ilgili kaynağınızı (değişiklikler dahil) ağ üzerinden de dahil olmak üzere kullanan herkese yayınlayın §13 başına. Ücretsiz, müzakere yok.
2. **[Astrodienst](https://www.astro.com/swisseph/) 'den bir Swiss Ephemeris ticari lisansı satın alın** — bu, Swiss Ephemeris kısmı için AGPL yükümlülüğünü kaldırır; kendi kodunuzu yeniden lisanslayabilir ve kapalı bir yapı gönderip barındırabilirsiniz. (Bu, Astrodienst'ın çift lisanslama modelidir.)
3. **Efemeris'i değiştirin** — `pyswisseph`'i izin verici bir şekilde lisanslanan astronomik kaynakla değiştirin (örneğin **Skyfield (MIT)** artı kamu-alan **JPL DE440** efemeris — bilgilendirici alternatifler, tek seçenek değil). Swiss Ephemeris gitti, kalan yığın (iztro MIT, artı MPL-2.0/MIT/Apache bağımlılıkları) artık AGPL'yi zorlamamaz ve tüm depo MIT olabilir. Bu gerçek mühendislik çabasıdır: şu anda Swiss Ephemeris'ten kaynaklanan her şeyi yeniden uygulamanız gerekir — gezegen boylamları, geriye dönüş işaretleri, Asc/MC, Placidus ev uçları ve Human Design 88° tasarım çözücüsüne girdiler.

Tam atıf ve bağımlılık başına lisanslar için **[CREDITS.md](./CREDITS.md)** bölümüne bakın.

---

## SSS

**Ay tarihini girebilir miyim?**
Hayır. Girdiler Gregoryen güneş tarihi (`--date YYYY-MM-DD`) ve saat saatidir (`--time HH:MM`). Sadece bir ay tarihiniz varsa, önce dönüştürün. 紫微斗數, iztro'nun güneş girişi noktası (`bySolar`) aracılığıyla hesaplanır.

**Doğum zamanım sadece yaklaşık — bu bir sorun mu?**
Gezegen konumları tamam, ancak Yükselen Burç, Orta Gök, ev uçları, her gezegenin oturduğu ev, Human Design çizgileri ve 時辰 tümü zamana duyarlıdır. Bunları geçici olarak ele alın ve bunlara güvenmeden önce olaya dayalı düzeltmeyi göz önünde bulundurun.

**Chiron / asteroidler / küçük cisimler nerede?**
Dahil değil. Burada kullanılan Moshier efemeris bunları sağlamaz; sadece 10 klasik gezegen ve ay düğümleri hesaplanır.

**紫微斗數 hangi okulu kullanır?**
iztro (`bySolar(..., True, 'zh-TW')`) tarafından uygulanan varsayılan okul. Okul kullanıcı tarafından seçilebilir değil.

**Telefona ev aramı yapar / ağ kullanır mı?**
Hayır. Motor tamamen çevrimdışı — telemetri yok, ağ çağrısı yok, yan etki yok. Durumsuz, deterministik, tek seferlik bir alt işlemdir.

**Kapalı kaynaklı bir ürünün içinde kullanabilir miyim?**
AGPL-3.0 altında, özel/yerel kullanım için evet. Bir yapıyı dağıtmak GPL iletme/kaynak yükümlülüklerini tetikler ve değiştirilmiş bir yapıyı ağ ile sunmak AGPL §13'ünü tetikler — her iki durumda da ilgili kaynağı sunmalısınız. Tamamen kapalı kaynak olmak için, Astrodienst'den bir Swiss Ephemeris ticari lisansı satın alın veya efemeris'i Skyfield + JPL DE440 olarak değiştirin ([Lisanslama](#licensing) bölümüne bakın).

---

## Feragat

`life-chart-engine`, **yorumsal öz-farkındalık çerçevesi, tahmin veya kadercilik değil**. Çıktılar, düşünme için yapılandırılmış referans noktalarıdır — olayları bildirmazlar ve sonuçları belirlemezler. Bunları, kendi yaşanmış deneyiminizin son otorite olacağı şekilde ayarlamalar olarak kullanın. Buradaki hiçbir şey tıbbi, yasal, psikolojik veya finansal tavsiye değil. Bu alanlardaki kararlar için, nitelikli bir profesyonele danışın.

---

## Jenerik & Lisans

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, çift lisanslı AGPL-3.0 / ticari (<https://www.astro.com/swisseph/>).
- **iztro** — MIT, 紫微斗數 için.
- Tam atıf: **[CREDITS.md](./CREDITS.md)**.
- **Lisans:** [AGPL-3.0](./LICENSE).
- **Ajan / JSON sözleşmesi:** [AGENTS.md](./AGENTS.md).
