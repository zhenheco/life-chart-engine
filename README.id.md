> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · **Bahasa Indonesia** · [Tiếng Việt](./README.vi.md) · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Komputasi deterministik asli dari tiga sistem bagan kehidupan — astrologi natal Barat, 人類圖 (Human Design), dan 紫微斗數 (Zi Wei Dou Shu) — dari satu catatan kelahiran.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` adalah alat baris perintah kecil dan luring. Anda memberikannya data kelahiran satu orang — tanggal, waktu, zona waktu, dan koordinat tempat — dan alat ini menghitung tiga sistem bagan independen dalam satu lintasan, lalu mengeluarkan laporan Markdown yang mudah dibaca atau objek JSON terstruktur untuk dikonsumsi oleh program dan agen AI.

Ini dibangun untuk orang-orang yang menginginkan **komputasi bagan yang dapat direproduksi dan dapat diverifikasi** daripada aplikasi web kotak hitam: praktisi, pengembang yang membangun alat kesadaran diri, dan agen AI yang membutuhkan langkah komputasi murni. Setiap angka berasal dari komputasi astronomi nyata (Swiss Ephemeris) dan perpustakaan 紫微斗數 nyata (py-iztro) — bukan dari layanan jarak jauh, bukan dari pencarian cache, dan tidak pernah melalui jaringan.

---

## Apa yang dihitung

Mesin menjalankan tiga sistem terhadap **momen kelahiran yang sama**, sehingga keluarannya dapat saling memperkuat. Setiap sistem menjawab jenis pertanyaan yang berbeda:

| Sistem | Apa itu (bahasa sehari-hari) | Apa yang dihasilkan mesin |
|--------|------|------------------------|
| **Western natal** (Tropical / Placidus) | Astrologi Barat klasik — di mana planet-planet duduk melawan zodiak saat kelahiran Anda, dibagi menjadi 12 rumah. | Ascendant + Midheaven, 12 planet/poin (太陽 → 南交點) dengan tanda, derajat, rumah dan bendera retrograde, semua 12 cusp rumah, dan setiap aspek yang terdeteksi (合相/六分/四分/三分/對分) diurutkan berdasarkan keketatan. |
| **人類圖 Human Design** | Sintesis modern astrologi, I-Ching, dan sistem chakra. Mendeskripsikan bagaimana energi Anda "terwiring" melalui gerbang, saluran, dan pusat. | Tipe, Otoritas, Profil, Definisi, Incarnation Cross, tanggal Desain 88° lebih awal, pusat terdefinisi/terbuka, saluran terdefinisi, dan aktivasi garis gerbang per-planet untuk bagan Personality dan Design. |
| **紫微斗數 Zi Wei Dou Shu** | Sistem astrologi tradisional Cina yang memetakan takdir ke papan 12-istana, dipenuhi bintang-bintang bernama. | 五行局 (Five Elements Class), 命主 (jiwa) / 身主 (tubuh), indeks 時辰 (jam), dan data per-istana — ganzhi, flag 命/身, kisaran usia dekade, dan bintang-bintang utama/minor/adjektif (dengan terang dan 四化). Opsional horoscope 大限/流年 best-effort. |

Tipe, Otoritas, dan Definisi dalam Human Design **bukan hardcoded** — mereka diturunkan dari grafik konektivitas pusat-pusat terdefinisi.

---

## Mengapa komputasi asli

Mesin ini melakukan matematika nyata daripada mendekati atau memanggil layanan. Pilihan itu menghadirkan tiga properti yang penting untuk alat bagan serius apa pun:

- **Deterministik.** Input kelahiran yang sama selalu menghasilkan keluaran yang sama, byte demi byte. Tidak ada keacakan, tidak ada model, tidak ada hanyutan pembulatan antar lintasan.
- **Dapat direproduksi.** Siapa pun dengan repo dan input yang sama dapat meregenerasi bagan Anda yang tepat. Perhitungan menggunakan Swiss Ephemeris (model Moshier) untuk langit dan py-iztro untuk 紫微斗數 — keduanya deterministik.
- **Dapat diverifikasi lintas-silang.** Karena tiga sistem independen dihitung dari satu momen kelahiran, Anda dapat triangulasi. **Ketika ketiga sistem menunjuk pada sinyal yang sama, perlakukan sebagai kepercayaan tinggi. Ketika hanya satu sistem menunjukkan detail, perlakukan sebagai titik referensi, bukan kesimpulan.** Ini adalah prinsip desain inti mesin — ia menghasilkan fakta untuk dibaca silang, bukan satu vonis.

---

## Mulai cepat

### Instalasi satu baris (direkomendasikan)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Memasang ke `~/.life-chart-engine` (ganti dengan `LIFE_CHART_DIR`). Tidak ada `sudo`, tidak ada perubahan seluruh sistem — hanya mengkloning repo dan membangun venv CPython 3.12 terisolasi. Memerlukan `git` dan [`uv`](https://docs.astral.sh/uv/). Jalankan kembali kapan saja untuk memperbarui ke versi terbaru.

### Dari sumber

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### Apa yang dilakukan `setup.sh`

Berjalan di bawah `set -euo pipefail` dan melakukan lima langkah:

1. **Menyelesaikan lokasi venv** — `${LIFE_VENV:-<repo>/.venv}`. Atur variabel lingkungan `LIFE_VENV` untuk mengganti; default `.venv/` diabaikan git.
2. **Preflight: memerlukan [`uv`](https://docs.astral.sh/uv/)** — jika `uv` tidak ada di `PATH` keluar `1` dan cetak petunjuk instalasi:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Membuat venv CPython 3.12** — `uv venv --python 3.12 "$VENV"` (lihat [Mengapa CPython 3.12](#why-cpython-312-specifically)).
4. **Memasang dependensi terpasak** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Menjalankan uji asap** — mengeksekusi mesin sekali dengan input sampel tetap (membuang stdout) dan mencetak `OK — engine runs.` pada kesuksesan. Ini juga mencetak petunjuk penggunaan untuk kedua mode.

### Langkah `uv` manual (tanpa `setup.sh`)

```bash
# 1. Buat venv CPython 3.12 (default <repo>/.venv; ganti dengan LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Pasang deps terpasak
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (Opsional) uji asap
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Dua dependensi langsung saja yang terpasak di `requirements.txt`:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## Mengapa CPython 3.12 spesifik

Anda harus menjalankan mesin di **CPython 3.12** — bukan 3.13, bukan 3.14. Alasannya dinyatakan identik di `requirements.txt` dan `setup.sh`:

> Dep asli py-iztro (**pythonmonkey / pydantic-core**) **tidak memiliki wheel untuk 3.13+/3.14 dan gagal membangun dari sumber**. Pasak ke 3.12.

Singkatnya: `py-iztro` bergantung pada ekstensi asli (`pythonmonkey`, `pydantic-core`) yang prebuilt wheel berhenti di 3.12. Di 3.13/3.14 tidak ada wheel dan pembangunan sumber gagal. Itulah mengapa `setup.sh` memanggil `uv venv --python 3.12`, dan mengapa Anda harus selalu menjalankan mesin dengan Python venv proyek (`<repo>/.venv/bin/python`), tidak pernah sistem `python3`.

---

## Penggunaan

Mesin memiliki dua mode, dipilih oleh kehadiran flag `--json`.

### Mode manusia (Markdown)

Hilangkan `--json` untuk mendapatkan laporan konsol yang dapat dibaca. Gunakan Python venv Anda:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Sampel nyata terpangkas (aspek terbatas pada top-10 dalam mode Markdown):

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

### Mode agen (JSON)

Tambahkan `--json` untuk mendapatkan satu objek JSON di stdout dan tidak ada lagi — ideal untuk program dan agen AI:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Sampel nyata terpangkas (array terpotong menjadi 1–2 entri; nilai verbatim):

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

## Referensi flag CLI

Tidak ada **flag `required=True`** — argparse tidak pernah error pada yang hilang. Menghilangkan `--date`/`--time`/`--tz`/`--lat`/`--lon` diam-diam kembali ke orang contoh built-in (`範例`, lahir `2000-01-01 12:00`, UTC+8, Taipei 101). Jadi untuk bagan yang benar, sediakan semuanya.

| Flag | Tipe | Diperlukan untuk penggunaan yang benar? | Default | Format / aturan |
|------|------|---------------------------|---------|---------------|
| `--name` | string | Tidak (kosmetik) | `"範例"` | Teks bebas; bergema ke output saja. |
| `--gender` | string | Hanya untuk 紫微 | `"女"` | Harus tepat `男` atau `女` (argparse `choices`; yang lain → keluar `2`). |
| `--date` | string | **Ya** | kembali ke `2000-01-01` | `YYYY-MM-DD`, pisahkan pada `-`. Tidak ada persyaratan zero-pad. |
| `--time` | string | **Ya** | kembali ke `12:00` | `HH:MM`, jam 24 jam waktu lokal jam, pisahkan pada `:`. |
| `--tz` | float | **Ya** | kembali ke `8.0` | Offset UTC termasuk DST (Taiwan = `8`). Ditulis ke kunci input `tz_offset`. |
| `--lat` | float | **Ya** | kembali ke `25.0330` | Lintang dalam derajat desimal (rumah/Asc/MC Barat). |
| `--lon` | float | **Ya** | kembali ke `121.5654` | Bujur dalam derajat desimal. |
| `--target` | string | Tidak | `"2025-01-01"` | `YYYY-MM-DD`; tanggal referensi periode keberuntungan 紫微 (運限參考日). |
| `--json` | flag | Tidak | `False` (Markdown) | Kehadiran → mode JSON; ketiadaan → Markdown. Tidak ada nilai. |

> Mesin **tidak** melakukan geocode tempat atau mencari zona waktu. Pemanggil harus mengonversi tempat → `lat`/`lon`/`tz` sendiri — dan zona waktu/DST adalah sumber kesalahan paling umum, jadi verifikasi offset UTC yang berlaku di tempat lahir dan tanggal lahir.

---

## Referensi keluaran

Selubung `--json` memiliki tujuh kunci tingkat atas, dalam urutan ini:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Blok | Ringkasan |
|-------|---------|
| `ok` | `true` pada kesuksesan (`false` dalam selubung kesalahan). |
| `schema_version` | `"1.0"`. |
| `input` | Gema input ternormalisasi: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (catatan `tz_offset`, bukan `tz`). |
| `western` | String `system`, objek posisi `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (objek atau `null`). |
| `meta` | `{ engine, version, ephemeris }` — semua literal (`ephemeris: "Moshier"`). |

Untuk kontrak bidang lengkap — setiap kunci, tipe, dan protokol invokasi agen — lihat **[AGENTS.md](./AGENTS.md)**.

### Kekhususan bidang yang perlu diketahui

- **`aspects` TIDAK terbatas dalam JSON.** Jalur JSON mengembalikan *setiap* aspek terdeteksi, diurutkan naik berdasarkan orb (terketat terlebih dahulu). Batas 10-item hanya ada dalam laporan Markdown.
- **`ziwei.horoscope` best-effort dan dapat `null`.** Ini dibungkus di `try/except`; pada pengecualian apa pun serialisasi sebagai `null`. Ketika ada itu `{ decadal, yearly }`. (Sub-objek tersebut mengekspos struktur internal ekstra — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, dll. — melampaui placeholder terdokumentasi.)
- **String bintang mengenkode terang + 四化.** Format adalah `name(brightness)[mutagen]`, dengan setiap bagian opsional — misalnya `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, atau plain `天機`. `adjective_stars` hanya nama polos (tidak ada terang/mutagen).

---

## Tingkat akurasi

Tidak setiap keluaran membawa kepercayaan yang sama. Baca setiap tingkat sesuai:

| Tingkat | Apa yang dicakupnya | Kepercayaan |
|--------|----------------|------------|
| **Tertinggi** | Bujur planet, tanda, retrograde, ditambah penempatan bintang 紫微 / 命宮·身宮 / 五行局 — matematika ephemeris dan kalender murni. | Astronomis/kalender tepat. |
| **Tinggi, tergantung waktu** | Ascendant, Midheaven, semua 12 cusp rumah, rumah yang jatuh di setiap planet, garis Human Design, dan indeks 時辰 紫微. | Tepat *diberikan* waktu kelahiran yang akurat; sensitif terhadap menit. |
| **Diverifikasi** | Terang bintang 紫微斗數 — selaras dengan keluaran pustaka py-iztro. | Diverifikasi terhadap pustaka. |
| **Flag batas ±0,3°** | Planet apa pun / gerbang / garis duduk dalam ±0,3° batas. | Perlakukan sebagai sementara dan catat dampaknya — ±0,3° dapat membaliknya lintas garis. |

---

## Batasan yang diketahui

- **Tidak ada Chiron / badan minor.** Pembangunan menggunakan ephemeris Moshier (`swe.FLG_MOSEPH`, tidak ada file data), yang tidak menyediakan Chiron atau badan minor lainnya. Hanya 10 planet klasik ditambah node lunar yang dihitung.
- **紫微斗數 menggunakan satu sekolah default.** py-iztro dipanggil dengan opsi tetap (`by_solar(..., True, 'zh-TW')`); sekolah penempatan bintang dan 四化 adalah default py-iztro apa pun. Jika Anda biasanya menggunakan 飛星 atau sekolah lain, struktur utama tidak berubah tetapi beberapa detail mungkin berbeda.
- **Waktu lahir perkiraan merendahkan tingkat tergantung waktu.** Jika waktu kelahiran tidak pasti, penugasan Ascendant/MC/rumah, garis Human Design, dan 時辰 — dan apa pun yang diturunkan darinya — menjadi tidak dapat diandalkan. Dalam hal itu, **perlakukan bidang tergantung waktu sebagai sementara** dan pertimbangkan **rektifikasi berbasis peristiwa** (mencocokkan peristiwa kehidupan yang diketahui dengan waktu bagan) sebelum mengandalkannya.

---

## Menggunakannya dari agen AI / Hermes

Model integrasi yang dimaksud adalah **instalasi-sendiri**, bukan SaaS.

Pengguna menyalin URL repo ini, dan **mereka sendiri** agen atau CLI (Claude Code, Hermes, skrip, dll.) mengkloningnya dan menjalankannya **secara lokal di mesin pengguna**. Komputasi terjadi di sisi pengguna. Tidak ada titik akhir yang dihosting untuk dipanggil, tidak ada akun, dan **tidak ada integrasi SaaS yang diperlukan** — mesin adalah subprocess stateless, deterministik, offline.

Karena penerbit tidak mengoperasikannya sebagai layanan jaringan, tidak ada kewajiban §13 yang jatuh pada penerbit untuk instalasi-sendiri seseorang. (Terpisah, §13 hanya mengikat operator yang menjalankan versi *termodifikasi* yang dapat dijangkau jaringan — bukan penggunaan lokal yang tidak dimodifikasi.)

Untuk agen, kontraknya sederhana: dispatch subprocess `--json` dengan Python venv di workdir repo, parse stdout sebagai JSON, cabang di `ok` (dan kode keluar), lalu serahkan objek terstruktur. Tidak perlu pembersihan — stateless. Kontrak CLI + JSON lengkap ada di **[AGENTS.md](./AGENTS.md)**.

### Setup salin-tempel untuk agen AI Anda

Tempel blok ini langsung ke Claude Code, ChatGPT, atau agen coding apa pun — ia memberitahu agen cara memasang dan memanggil alat:

```text
Siapkan dan gunakan "life-chart-engine" — CLI yang menghitung bagan natal Barat +
Human Design + Zi Wei Dou Shu (紫微斗數) dari data kelahiran.

1. Pasang (butuh `git` dan `uv`; jika uv hilang: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Hitung bagan dan baca stdout sebagai JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Aturan:
   - ANDA menyelesaikan kota kelahiran ke --lat/--lon dan offset UTC historis yang benar
     (sadar DST). Alat tidak geocode.
   - Konfirmasi apakah waktu kelahiran tepat sebelum mempercayai ascendant,
     rumah, garis Human Design, atau pilar jam Zi Wei.
   - Jangan pernah fabrikasi nilai bagan — selalu panggil alat.
   - Skema keluaran lengkap, kode keluar, dan kontrak agen: ~/.life-chart-engine/AGENTS.md
```

---

## Lisensi

Repositori ini dilisensikan di bawah **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 dalam bahasa Inggris sederhana.** Ini adalah GNU GPL-3.0 (lisensi copyleft kuat: jika Anda mendistribusikan perangkat lunak, Anda harus merilis sumber lengkap yang sesuai di bawah lisensi yang sama) **ditambah satu klausul ekstra, Bagian 13**. §13 menutup "celah SaaS": melampaui pemicu GPL *distribusi*, ini menambahkan bahwa jika Anda *memodifikasi* program dan membiarkan pengguna berinteraksi dengan versi termodifikasi Anda melalui jaringan, Anda harus menawarkan pengguna jarak jauh sumber yang sesuai dengan versi Anda. (Menjalankan yang tidak dimodifikasi di hulu sebagai layanan jaringan tidak memicu §13 dengan sendirinya.) AGPL bersifat timbal balik tetapi bukan tanpa batas viral — ia hanya menjangkau kode yang merupakan turunan dari, atau ditautkan dengan, kode AGPL.

**Mengapa repo ini AGPL.** Mesin menghubungkan **Swiss Ephemeris** (via `pyswisseph`) untuk posisi planet dan cusp rumah. Astrodienst **dual-lisensi** Swiss Ephemeris sebagai **AGPL-3.0 ATAU lisensi komersial**, dan kodenya tidak dapat dilisensikan ulang sebagai apa pun yang lebih permisif. Karena AGPL adalah copyleft dan proyek ini menghubungkannya, seluruh karya gabungan harus AGPL. (`py-iztro` adalah MIT dan tidak memberlakukan copyleft; Swiss Ephemeris adalah satu-satunya komponen yang memaksa AGPL di sini.)

**Apa artinya dalam praktik.**

| Apa yang Anda lakukan | Kewajiban AGPL |
|--------|-----------------|
| **Instalasi-sendiri** (menjalankannya secara lokal untuk diri sendiri) | §13 *tidak* dipicu — tidak ada pengguna jarak jauh untuk dilayani, dan Anda sudah memiliki sumbernya. Bersih. |
| **Menjalankan versi *termodifikasi* sebagai layanan jaringan** | §13 *dipicu* — Anda harus menawarkan pengguna jarak jauh sumber yang sesuai lengkap dari versi yang dikerahkan, di bawah AGPL, termasuk modifikasi Anda. Catatan: kewajiban penawar-sumber §13 disyaratkan pada modifikasi — menjalankan yang tidak dimodifikasi di hulu sebagai layanan jaringan tidak memicu §13 dengan sendirinya, meskipun sumbernya sudah publik. |

**Tiga pilihan Anda** jika kewajiban sumber jaringan tidak sesuai dengan kasus penggunaan Anda:

1. **Tetap AGPL** — publikasikan sumber lengkap yang sesuai (termasuk modifikasi) kepada siapa pun yang menggunakannya, termasuk melalui jaringan per §13. Gratis, tidak ada negosiasi.
2. **Beli lisensi komersial Swiss Ephemeris dari [Astrodienst](https://www.astro.com/swisseph/)** — ini mengangkat kewajiban AGPL untuk bagian Swiss Ephemeris, memungkinkan Anda melisensikan ulang kode Anda sendiri dan mengirim/host build tertutup. (Ini adalah model dual-licensing Astrodienst.)
3. **Tukar ephemeris** — ganti `pyswisseph` dengan sumber astronomi berlisensi permisif (misalnya **Skyfield (MIT)** ditambah **JPL DE440** ephemeris domain publik — alternatif ilustratif, bukan satu-satunya opsi). Dengan Swiss Ephemeris hilang, sisa stack (py-iztro MIT, ditambah MPL-2.0/MIT/Apache deps) tidak lagi memaksa AGPL dan seluruh repo dapat MIT. Ini adalah usaha teknik nyata: Anda harus menerapkan ulang semuanya yang saat ini bersumber dari Swiss Ephemeris — bujur planet, bendera retrograde, Asc/MC, cusp rumah Placidus, dan input ke pemecah desain 88° Human Design.

Lihat **[CREDITS.md](./CREDITS.md)** untuk atribusi lengkap dan lisensi per-dependensi.

---

## FAQ

**Bisakah saya memasukkan tanggal lunar?**
Tidak. Input adalah tanggal matahari Gregorian (`--date YYYY-MM-DD`) dan waktu jam (`--time HH:MM`). Jika Anda hanya memiliki tanggal lunar, konversi terlebih dahulu. 紫微斗數 dihitung melalui titik masuk matahari py-iztro (`by_solar`).

**Waktu kelahiran saya hanya perkiraan — apakah itu masalah?**
Posisi planet-planet baik-baik saja, tetapi Ascendant, Midheaven, cusp rumah, rumah tempat setiap planet duduk, garis Human Design, dan 時辰 semuanya sensitif waktu. Perlakukan ini sebagai sementara dan pertimbangkan rektifikasi berbasis peristiwa sebelum mengandalkannya.

**Di mana Chiron / asteroid / badan minor?**
Tidak termasuk. Ephemeris Moshier yang digunakan di sini tidak menyediakannya; hanya 10 planet klasik dan node lunar yang dihitung.

**Sekolah 紫微斗數 mana yang digunakan?**
Sekolah default seperti yang diimplementasikan oleh py-iztro (`by_solar(..., True, 'zh-TW')`). Sekolah tidak dapat dipilih pengguna.

**Apakah itu pulang telepon / gunakan jaringan?**
Tidak. Mesin sepenuhnya offline — tidak ada telemetri, tidak ada panggilan jaringan, tidak ada efek samping. Ini adalah subprocess stateless, deterministik, satu kali.

**Bisakah saya menggunakannya di dalam produk closed-source?**
Di bawah AGPL-3.0, ya untuk penggunaan pribadi/lokal. Mendistribusikan build memicu kewajiban GPL yang menyampaikan/sumber, dan melayani jaringan build *termodifikasi* memicu §13 AGPL — bagaimanapun juga Anda harus menawarkan sumber yang sesuai. Untuk sepenuhnya closed-source, baik beli lisensi komersial Swiss Ephemeris dari Astrodienst atau tukar ephemeris ke Skyfield + JPL DE440 (lihat [Lisensi](#licensing)).

---

## Disclaimer

`life-chart-engine` adalah **kerangka kerja kesadaran diri interpretatif, bukan prediksi atau fatalisme**. Keluarannya adalah titik referensi terstruktur untuk refleksi — mereka tidak meramalkan peristiwa dan tidak menentukan hasil. Gunakan mereka sebagai kalibrasi, dengan pengalaman hidup Anda sendiri sebagai otoritas final. Tidak ada di sini adalah nasihat medis, hukum, psikologis, atau keuangan. Untuk keputusan di domain tersebut, konsultasikan profesional yang berkualitas.

---

## Kredit & Lisensi

- **Swiss Ephemeris** via `pyswisseph` — © Astrodienst AG, dual-licensed AGPL-3.0 / komersial (<https://www.astro.com/swisseph/>).
- **py-iztro** (dan upstream `iztro`) — MIT, untuk 紫微斗數.
- Atribusi lengkap: **[CREDITS.md](./CREDITS.md)**.
- **Lisensi:** [AGPL-3.0](./LICENSE).
- **Kontrak agen / JSON:** [AGENTS.md](./AGENTS.md).
