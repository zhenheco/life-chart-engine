> 🌐 [English](./README.md) · [繁體中文](./README.zh-TW.md) · [简体中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Português](./README.pt.md) · [Русский](./README.ru.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md) · [Bahasa Indonesia](./README.id.md) · **Tiếng Việt** · [ไทย](./README.th.md) · [Italiano](./README.it.md) · [Türkçe](./README.tr.md) · [Nederlands](./README.nl.md) · [Polski](./README.pl.md)

# life-chart-engine

**Tính toán xác định cục bộ của ba hệ thống biểu đồ sự sống — chiêm tinh phương Tây, 人類圖 (Human Design), và 紫微斗數 (Zi Wei Dou Shu) — từ một bản ghi thông tin sinh.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](#why-cpython-312-specifically)
[![No telemetry · offline](https://img.shields.io/badge/no%20telemetry-offline-green.svg)](#faq)

`life-chart-engine` là một công cụ dòng lệnh nhỏ, hoạt động ngoại tuyến. Bạn cung cấp cho nó dữ liệu sinh của một người — ngày, giờ, múi giờ và tọa độ địa điểm — và nó tính toán ba hệ thống biểu đồ độc lập trong một lần thực hiện, sau đó xuất ra một báo cáo Markdown dễ đọc hoặc một đối tượng JSON được cấu trúc cho các chương trình và agent AI sử dụng.

Nó được xây dựng cho những người muốn **tính toán biểu đồ có thể lặp lại, có thể xác minh** thay vì một ứng dụng web hộp đen: từ những người hành nghề, các nhà phát triển xây dựng công cụ tự nhận thức, và các agent AI cần một bước tính toán thuần túy. Mỗi con số đều từ tính toán thiên văn thực (Swiss Ephemeris) và một thư viện 紫微斗數 thực (py-iztro) — không từ một dịch vụ từ xa, không từ các tìm kiếm được lưu trong bộ nhớ đệm, và không bao giờ qua mạng.

---

## Nó tính toán cái gì

Động cơ chạy ba hệ thống dựa trên **cùng một thời điểm sinh**, vì vậy đầu ra của chúng có thể xác nhận lẫn nhau. Mỗi hệ thống trả lời một loại câu hỏi khác nhau:

| Hệ thống | Nó là gì (bằng tiếng Anh bình thường) | Công cụ mang lại gì |
|--------|----------------------------|------------------------|
| **Chiêm tinh phương Tây** (Tropical / Placidus) | Chiêm tinh phương Tây cổ điển — các hành tinh nằm ở đâu so với hoàng đạo vào thời sinh của bạn, chia thành 12 cung. | Ascendant + Midheaven, 12 hành tinh/điểm (太陽 → 南交點) với ký hiệu, độ, cung và cờ tuần hành ngược, tất cả 12 cạnh cung, và mọi khía cạnh được phát hiện (合相/六分/四分/三分/對分) được sắp xếp theo độ chặt chẽ. |
| **人類圖 Human Design** | Một sự tổng hợp hiện đại của chiêm tinh, Dịch Kinh, và hệ thống chakra. Mô tả cách năng lượng của bạn "được dây dợi" thông qua các cổng, kênh và trung tâm. | Loại, Authority, Profile, Definition, Incarnation Cross, ngày Design sớm hơn 88°, các trung tâm xác định/mở, các kênh xác định, và các kích hoạt cổng.dòng trên bản đồ cho cả hai biểu đồ Personality và Design. |
| **紫微斗數 Zi Wei Dou Shu** | Một hệ thống chiêm tinh truyền thống của Trung Quốc ánh xạ vận mệnh vào bảng 12 cung, được điền bằng các ngôi sao có tên. | 五行局 (Five Elements Class), 命主 (linh hồn) / 身主 (thân thể), chỉ số 時辰 giờ, và dữ liệu cho mỗi cung — ganzhi, cờ 命/身, phạm vi tuổi thập kỷ, và các ngôi sao chính/phụ/tính từ (có độ sáng và 四化). Tùy chọn là một biểu đồ 大限/流年 nỗ lực tốt nhất. |

Type, Authority, và Definition trong Human Design **không được hardcode** — chúng được bắt nguồn từ biểu đồ kết nối của các trung tâm xác định.

---

## Tại sao tính toán cục bộ

Động cơ này làm toán học thực tế thay vì xấp xỉ hoặc gọi ra một dịch vụ. Lựa chọn đó mang lại ba thuộc tính quan trọng đối với bất kỳ công cụ biểu đồ nghiêm túc nào:

- **Xác định.** Cùng một đầu vào sinh luôn tạo ra cùng một đầu ra, byte-for-byte. Không có tính ngẫu nhiên, không có mô hình, không có sai lệch làm tròn giữa các lần chạy.
- **Có thể lặp lại.** Bất kỳ ai có repo và cùng đầu vào có thể tạo lại biểu đồ chính xác của bạn. Các phép tính sử dụng Swiss Ephemeris (mô hình Moshier) cho bầu trời và py-iztro cho 紫微斗數 — cả hai đều xác định.
- **Có thể xác minh chéo.** Vì ba hệ thống độc lập được tính toán từ một thời điểm sinh, bạn có thể tam giác. **Khi cả ba hệ thống chỉ đến cùng một tín hiệu, hãy coi nó là độ tin cậy cao. Khi chỉ một hệ thống hiển thị một chi tiết, hãy coi nó là một điểm tham chiếu, không phải kết luận.** Đây là nguyên tắc thiết kế cốt lõi của động cơ — nó tạo ra những sự kiện để đọc chéo, không phải một phán quyết duy nhất.

---

## Khởi động nhanh

### Cài đặt một dòng (được khuyến nghị)

```bash
curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
```

Cài đặt vào `~/.life-chart-engine` (ghi đè bằng `LIFE_CHART_DIR`). Không cần `sudo`, không có thay đổi toàn hệ thống — nó chỉ sao chép repo và xây dựng một venv CPython 3.12 cô lập. Yêu cầu `git` và [`uv`](https://docs.astral.sh/uv/). Chạy lại bất cứ lúc nào để cập nhật lên phiên bản mới nhất.

### Từ nguồn

```bash
git clone https://github.com/zhenheco/life-chart-engine.git
cd life-chart-engine
bash setup.sh
```

### `setup.sh` làm gì

Nó chạy dưới `set -euo pipefail` và thực hiện năm bước:

1. **Giải quyết vị trí venv** — `${LIFE_VENV:-<repo>/.venv}`. Đặt biến env `LIFE_VENV` để ghi đè; mặc định `.venv/` bị git-ignored.
2. **Kiểm tra trước: yêu cầu [`uv`](https://docs.astral.sh/uv/)** — nếu `uv` không có trên `PATH` nó thoát `1` và in gợi ý cài đặt:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Tạo venv CPython 3.12** — `uv venv --python 3.12 "$VENV"` (xem [Tại sao CPython 3.12](#why-cpython-312-specifically)).
4. **Cài đặt các phụ thuộc được ghim** — `uv pip install --python "$VENV/bin/python" -r requirements.txt`.
5. **Chạy kiểm tra khói** — thực hiện động cơ một lần với đầu vào mẫu cố định (loại bỏ stdout) và in `OK — engine runs.` khi thành công. Nó cũng in các gợi ý sử dụng cho cả hai chế độ.

### Các bước `uv` thủ công (không có `setup.sh`)

```bash
# 1. Tạo venv CPython 3.12 (mặc định <repo>/.venv; ghi đè bằng LIFE_VENV)
uv venv --python 3.12 .venv

# 2. Cài đặt các phụ thuộc được ghim
uv pip install --python .venv/bin/python -r requirements.txt

# 3. (Tùy chọn) kiểm tra khói
.venv/bin/python scripts/chart_engine.py --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null
```

Hai phụ thuộc trực tiếp duy nhất được ghim trong `requirements.txt`:

```
pyswisseph==2.10.3.2
py-iztro==0.1.5
```

---

## Tại sao CPython 3.12 cụ thể

Bạn phải chạy động cơ trên **CPython 3.12** — không phải 3.13, không phải 3.14. Lý do được nêu giống hệt nhau trong `requirements.txt` và `setup.sh`:

> các phụ thuộc gốc của py-iztro (**pythonmonkey / pydantic-core**) **không có wheels cho 3.13+/3.14 và không thể xây dựng từ nguồn**. Ghim vào 3.12.

Nói ngắn gọn: `py-iztro` phụ thuộc vào các tiện ích mở rộng gốc (`pythonmonkey`, `pydantic-core`) có bánh xe được xây dựng sẵn dừng lại ở 3.12. Trên 3.13/3.14 không có bánh xe và xây dựng nguồn không thành công. Đó chính xác là lý do tại sao `setup.sh` gọi `uv venv --python 3.12`, và tại sao bạn luôn nên gọi động cơ với Python của venv dự án (`<repo>/.venv/bin/python`), không bao giờ `python3` của hệ thống.

---

## Cách dùng

Động cơ có hai chế độ, được chọn bằng sự hiện diện của cờ `--json`.

### Chế độ người dùng (Markdown)

Bỏ qua `--json` để nhận báo cáo bàn điều khiển dễ đọc. Sử dụng Python của venv của bạn:

```bash
.venv/bin/python scripts/chart_engine.py \
  --name "Sample" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Mẫu thực được cắt ngắn (các khía cạnh được capped ở top-10 ở chế độ Markdown):

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

### Chế độ Agent (JSON)

Thêm `--json` để nhận một đối tượng JSON trên stdout và không có gì khác — lý tưởng cho các chương trình và agent AI:

```bash
.venv/bin/python scripts/chart_engine.py --json \
  --name "小明" --gender 女 \
  --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.033 --lon 121.5654 \
  --target 2025-01-01
```

Mẫu thực được cắt ngắn (mảng bị cắt ngắn thành 1–2 mục; các giá trị theo ngôn từ):

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

## Tham khảo cờ CLI

Không có cờ `required=True` — argparse không bao giờ lỗi trên một cờ bị thiếu. Bỏ qua `--date`/`--time`/`--tz`/`--lat`/`--lon` sẽ yên tĩnh quay lại một người ví dụ được tích hợp (`範例`, sinh `2000-01-01 12:00`, UTC+8, Taipei 101). Vì vậy, để có biểu đồ chính xác, hãy cung cấp tất cả.

| Cờ | Kiểu | Yêu cầu để sử dụng chính xác? | Mặc định | Định dạng / quy tắc |
|------|------|---------------------------|---------|---------------|
| `--name` | string | Không (trang trí) | `"範例"` | Văn bản miễn phí; được lặp lại vào đầu ra chỉ. |
| `--gender` | string | Chỉ cho 紫微 | `"女"` | Phải chính xác là `男` hoặc `女` (argparse `choices`; bất cứ điều gì khác → thoát `2`). |
| `--date` | string | **Có** | quay lại `2000-01-01` | `YYYY-MM-DD`, chia tách trên `-`. Không yêu cầu zero-pad. |
| `--time` | string | **Có** | quay lại `12:00` | `HH:MM`, đồng hồ địa phương 24 giờ, chia tách trên `:`. |
| `--tz` | float | **Có** | quay lại `8.0` | Offset UTC bao gồm DST (Taiwan = `8`). Được viết vào khóa đầu vào `tz_offset`. |
| `--lat` | float | **Có** | quay lại `25.0330` | Vĩ độ theo độ thập phân (các cung/Asc/MC phương Tây). |
| `--lon` | float | **Có** | quay lại `121.5654` | Kinh độ theo độ thập phân. |
| `--target` | string | Không | `"2025-01-01"` | `YYYY-MM-DD`; ngày tham chiếu kỳ may mắn 紫微 (運限參考日). |
| `--json` | flag | Không | `False` (Markdown) | Có mặt → chế độ JSON; vắng mặt → Markdown. Không có giá trị. |

> Động cơ **không** geocode các địa điểm hoặc tìm kiếm múi giờ. Người gọi phải tự chuyển đổi địa điểm → `lat`/`lon`/`tz` — và múi giờ/DST là nguồn lỗi phổ biến nhất, vì vậy hãy xác minh offset UTC áp dụng tại nơi sinh và ngày sinh.

---

## Tham khảo đầu ra

Phong bì `--json` có bảy khóa cấp cao nhất, theo thứ tự này:

`ok` · `schema_version` · `input` · `western` · `human_design` · `ziwei` · `meta`

| Khối | Tóm tắt |
|-------|---------|
| `ok` | `true` khi thành công (`false` ở phong bì lỗi). |
| `schema_version` | `"1.0"`. |
| `input` | Echo của đầu vào được chuẩn hóa: `name`, `gender`, `date`, `time`, `tz_offset`, `lat`, `lon`, `target` (lưu ý `tz_offset`, không phải `tz`). |
| `western` | Chuỗi `system`, các đối tượng vị trí `ascendant`/`midheaven`, `planets[]`, `houses[]` (×12), `aspects[]`. |
| `human_design` | `type`, `authority`, `profile`, `definition`, `incarnation_cross`, `design_date`, `defined_centers[]`, `open_centers[]`, `channels[]`, `gates[]`. |
| `ziwei` | `five_elements_class`, `soul`, `body`, `hour_index`, `palaces[]`, `horoscope` (object hoặc `null`). |
| `meta` | `{ engine, version, ephemeris }` — tất cả các chữ (ephemeris: "Moshier"`). |

Đối với hợp đồng trường đầy đủ — mọi khóa, kiểu, và giao thức gọi agent — xem **[AGENTS.md](./AGENTS.md)**.

### Các tính năng trường đáng biết

- **`aspects` KHÔNG được capped ở JSON.** Đường dẫn JSON trả về *mọi* khía cạnh được phát hiện, được sắp xếp tăng dần theo orb (chặt chẽ nhất trước tiên). Giới hạn 10 mục chỉ tồn tại trong báo cáo Markdown.
- **`ziwei.horoscope` là best-effort và có thể là `null`.** Nó được bao bọc trong `try/except`; trên bất kỳ ngoại lệ nào nó tuần tự hóa như `null`. Khi có mặt nó là `{ decadal, yearly }`. (Các đối tượng phụ đó tiếp xúc cấu trúc nội bộ bổ sung — `index`, `mutagen[]`, `stars[][]`, `yearly_dec_star`, v.v. — vượt quá trình giữ chỗ được ghi chép.)
- **Chuỗi sao mã hóa độ sáng + 四化.** Định dạng là `name(brightness)[mutagen]`, với mỗi phần tùy chọn — ví dụ `紫微(廟)[祿]`, `紫微(廟)`, `天機[祿]`, hoặc trơn `天機`. `adjective_stars` chỉ là tên đơn giản (không có độ sáng/mutagen).

---

## Các tiers độ chính xác

Không phải mỗi đầu ra đều mang lại sự tự tin giống nhau. Đọc mỗi tier phù hợp:

| Tier | Nó bao gồm gì | Độ tin cậy |
|------|----------------|------------|
| **Cao nhất** | Các kinh độ hành tinh, ký hiệu, tuần hành ngược, cộng với vị trí sao 紫微 / 命宮·身宮 / 五行局 — toán học ephemeris và lịch thuần túy. | Chính xác thiên văn/lịch. |
| **Cao, phụ thuộc vào thời gian** | Ascendant, Midheaven, tất cả 12 cạnh cung, cung mà mỗi hành tinh rơi vào, các dòng Human Design, và chỉ số 紫微 時辰. | Chính xác *với* thời gian sinh chính xác; nhạy cảm với từng phút. |
| **Được xác minh** | Độ sáng sao 紫微斗數 — được căn chỉnh với đầu ra của thư viện py-iztro. | Được xác minh so với thư viện. |
| **Cờ ranh giới ±0.3°** | Bất kỳ hành tinh / cổng / dòng nào ngồi trong ±0.3° của một ranh giới. | Coi là sơ bộ và lưu ý tác động — ±0.3° có thể lật nó qua ranh giới. |

---

## Các hạn chế đã biết

- **Không có Chiron / các cơ thể nhỏ.** Bản dựng sử dụng ephemeris Moshier (`swe.FLG_MOSEPH`, không có tệp dữ liệu), không cung cấp Chiron hoặc các cơ thể nhỏ khác. Chỉ 10 hành tinh cổ điển cộng với các nút Mặt Trăng được tính toán.
- **紫微斗數 sử dụng một trường phái mặc định.** py-iztro được gọi với các tùy chọn cố định (`by_solar(..., True, 'zh-TW')`); trường phái đặt sao và 四化 là bất cứ gì py-iztro mặc định. Nếu bạn thường sử dụng 飛星 hoặc một trường phái khác, cấu trúc chính không thay đổi nhưng một số chi tiết có thể khác.
- **Thời gian sinh gần đúng làm giảm tier phụ thuộc vào thời gian.** Nếu thời gian sinh không chắc chắn, các bài tập Ascendant/MC/house, các dòng Human Design, và 時辰 — và bất cứ điều gì bắt nguồn từ chúng — trở nên không đáng tin cậy. Trong trường hợp đó, **coi các trường phụ thuộc vào thời gian là sơ bộ** và xem xét **sửa lỗi dựa trên sự kiện** (khớp các sự kiện cuộc sống đã biết với thời gian biểu đồ) trước khi dựa vào chúng.

---

## Sử dụng từ một agent AI / Hermes

Mô hình tích hợp dự định là **self-install**, không phải SaaS.

Một người dùng sao chép URL của repo này, và **agent của họ** hoặc **CLI** (Claude Code, Hermes, một script, v.v.) sao chép nó và chạy nó **cục bộ trên máy của người dùng**. Tính toán xảy ra ở phía người dùng. Không có điểm cuối được lưu trữ để gọi, không có tài khoản, và **không cần tích hợp SaaS** — động cơ là một quá trình thừa số, xác định, ngoại tuyến.

Vì nhà xuất bản không vận hành nó như một dịch vụ mạng, không có §13 nghĩa vụ rơi vào nhà xuất bản đối với self-install của người khác. (Riêng biệt, §13 chỉ bắt buộc một nhà khai thác chạy phiên bản *modified* có thể truy cập mạng — không sử dụng cục bộ chưa sửa đổi.)

Đối với các agent, hợp đồng đơn giản: gửi quá trình con `--json` với venv Python trong workdir repo, phân tích cú pháp stdout dưới dạng JSON, nhánh trên `ok` (và mã thoát), sau đó chuyển đối tượng được cấu trúc. Không cần dọn dẹp — nó không có trạng thái. Hợp đồng CLI + JSON đầy đủ sống trong **[AGENTS.md](./AGENTS.md)**.

### Thiết lập sao chép-dán cho agent AI của bạn

Dán khối này trực tiếp vào Claude Code, ChatGPT, hoặc bất kỳ agent mã hóa — nó cho agent biết cách cài đặt và gọi công cụ:

```text
Thiết lập và sử dụng "life-chart-engine" — một CLI tính toán biểu đồ sinh phương Tây +
Human Design + Zi Wei Dou Shu (紫微斗數) từ dữ liệu sinh.

1. Cài đặt (cần `git` và `uv`; nếu uv bị thiếu: curl -LsSf https://astral.sh/uv/install.sh | sh):
   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash

2. Tính toán biểu đồ và đọc stdout dưới dạng JSON:
   ~/.life-chart-engine/.venv/bin/python ~/.life-chart-engine/scripts/chart_engine.py --json \
     --name "<label>" --gender <男|女> \
     --date <YYYY-MM-DD> --time <HH:MM> \
     --tz <utc_offset_including_DST> --lat <latitude> --lon <longitude> \
     --target <YYYY-MM-DD>

3. Quy tắc:
   - BẠN giải quyết thành phố sinh vào --lat/--lon và offset UTC lịch sử chính xác
     (nhận thức DST). Công cụ không geocode.
   - Xác nhận xem thời gian sinh có chính xác trước khi tin tưởng ascendant,
     các cung, các dòng Human Design, hoặc trụ giờ Zi Wei.
   - Không bao giờ bịa chuyện các giá trị biểu đồ — luôn gọi công cụ.
   - Hợp đồng đầu ra đầy đủ, mã thoát, và giao thức agent: ~/.life-chart-engine/AGENTS.md
```

---

## Cấp phép

Repository này được cấp phép dưới **[AGPL-3.0](./LICENSE)**.

**AGPL-3.0 bằng tiếng Anh bình thường.** Nó là GNU GPL-3.0 (một giấy phép copyleft mạnh: nếu bạn phân phối phần mềm, bạn phải phát hành toàn bộ mã nguồn tương ứng dưới cùng một giấy phép) **cộng với một điều khoản bổ sung, Phần 13**. §13 đóng "lỗ hổng SaaS": vượt quá kích hoạt *phân phối* của GPL, nó thêm rằng nếu bạn *sửa đổi* chương trình và cho phép người dùng tương tác với phiên bản đã sửa đổi của bạn qua mạng, bạn phải cung cấp cho những người dùng từ xa đó mã nguồn tương ứng của bạn. (Chạy một phiên bản không sửa đổi phía trước như một dịch vụ mạng không bằng chính nó kích hoạt §13.) AGPL là có tính đưới nhưng không vô tận bị phong bì — nó chỉ tiếp cận mã là dẫn xuất từ, hoặc được liên kết với, mã AGPL.

**Tại sao repo này là AGPL.** Động cơ liên kết **Swiss Ephemeris** (qua `pyswisseph`) cho các vị trí hành tinh và cạnh cung. Astrodienst **dual-licenses** Swiss Ephemeris như **AGPL-3.0 HOẶC một giấy phép thương mại**, và mã của nó không thể được cấp phép lại thành bất cứ cái gì cho phép hơn. Vì AGPL là copyleft và dự án này liên kết nó, toàn bộ công việc kết hợp phải là AGPL. (`py-iztro` là MIT và không áp đặt copyleft; Swiss Ephemeris là thành phần duy nhất buộc AGPL ở đây.)

**Nó có nghĩa gì trong thực tế.**

| Bạn làm | Nghĩa vụ AGPL |
|--------|-----------------|
| **Self-install** (chạy cục bộ cho chính bạn) | §13 *không* được kích hoạt — không có người dùng từ xa để phục vụ, và bạn đã có mã nguồn. Sạch. |
| **Chạy một phiên bản *modified* như một dịch vụ mạng** | §13 *được* kích hoạt — bạn phải cung cấp cho những người dùng từ xa đó toàn bộ mã nguồn tương ứng của phiên bản được triển khai của bạn, dưới AGPL, bao gồm các sửa đổi của bạn. Lưu ý: §13 của trách nhiệm cung cấp nguồn bị điều kiện trên sửa đổi — chạy upstream không sửa đổi như một dịch vụ mạng không bằng chính nó kích hoạt §13, mặc dù mã nguồn đã công khai. |

**Ba tùy chọn của bạn** nếu nghĩa vụ nguồn mạng không phù hợp với trường hợp sử dụng của bạn:

1. **Giữ AGPL** — xuất bản toàn bộ mã nguồn tương ứng (bao gồm sửa đổi) cho bất kỳ ai sử dụng nó, bao gồm qua mạng theo §13. Miễn phí, không cần đàm phán.
2. **Mua một giấy phép thương mại Swiss Ephemeris từ [Astrodienst](https://www.astro.com/swisseph/)** — điều này nâng lên nghĩa vụ AGPL cho phần Swiss Ephemeris, cho phép bạn cấp phép lại mã của riêng bạn và gửi/lưu trữ một bản dựng đóng. (Đây là mô hình dual-licensing của Astrodienst.)
3. **Trao đổi ephemeris** — thay thế `pyswisseph` bằng một nguồn thiên văn được cấp phép cho phép (ví dụ **Skyfield (MIT)** cộng với ephemeris miền công cộng **JPL DE440** — các lựa chọn thay thế minh họa, không phải tùy chọn duy nhất). Với Swiss Ephemeris biến mất, ngăn xếp còn lại (py-iztro MIT, cộng với phụ thuộc MPL-2.0/MIT/Apache) không còn buộc AGPL và toàn bộ repo có thể là MIT. Đây là nỗ lực kỹ thuật thực: bạn phải triển khai lại mọi thứ hiện tại được lấy từ Swiss Ephemeris — kinh độ hành tinh, cờ tuần hành ngược, Asc/MC, cạnh cung Placidus, và đầu vào cho trình giải quyết thiết kế 88° Human Design.

Xem **[CREDITS.md](./CREDITS.md)** để có đầy đủ quy cho và giấy phép cho mỗi phụ thuộc.

---

## Câu hỏi thường gặp

**Tôi có thể nhập một ngày âm lịch không?**
Không. Đầu vào là một ngày mặt trời Gregorian (`--date YYYY-MM-DD`) và thời gian đồng hồ (`--time HH:MM`). Nếu bạn chỉ có một ngày âm lịch, hãy chuyển đổi nó trước. 紫微斗數 được tính toán qua điểm nhập cảnh mặt trời của py-iztro (`by_solar`).

**Thời gian sinh của tôi chỉ xấp xỉ — đó có phải là vấn đề không?**
Các vị trí hành tinh ổn thốn, nhưng Ascendant, Midheaven, cạnh cung, cung mà mỗi hành tinh ngồi, các dòng Human Design, và 時辰 tất cả đều nhạy cảm với thời gian. Coi đó là sơ bộ và xem xét sửa lỗi dựa trên sự kiện trước khi dựa vào chúng.

**Chiron ở đâu / tiểu hành tinh / các cơ thể nhỏ?**
Không bao gồm. Ephemeris Moshier sử dụng ở đây không cung cấp chúng; chỉ 10 hành tinh cổ điển và các nút Mặt Trăng được tính toán.

**Trường phái 紫微斗數 nào mà nó sử dụng?**
Trường phái mặc định như được triển khai bởi py-iztro (`by_solar(..., True, 'zh-TW')`). Trường phái không thể chọn bởi người dùng.

**Nó gọi nhà / sử dụng mạng?**
Không. Động cơ hoàn toàn ngoại tuyến — không có telemetry, không có cuộc gọi mạng, không có tác dụng phụ. Nó là một quá trình thừa số, xác định, một lần.

**Tôi có thể sử dụng nó bên trong một sản phẩm nguồn đóng không?**
Dưới AGPL-3.0, có cho sử dụng cá nhân/cục bộ. Phân phối một bản dựng kích hoạt các nghĩa vụ GPL vận chuyển/nguồn, và phục vụ mạng một bản dựng *modified* kích hoạt AGPL §13 — bằng cách nào nó bạn phải cung cấp mã nguồn tương ứng. Để đi hoàn toàn nguồn đóng, hãy mua một giấy phép thương mại Swiss Ephemeris từ Astrodienst hoặc trao đổi ephemeris thành Skyfield + JPL DE440 (xem [Cấp phép](#licensing)).

---

## Tuyên bố từ chối trách nhiệm

`life-chart-engine` là một **khuôn khung tự nhận thức giải thích, không phải dự đoán hoặc định mệnh**. Đầu ra là các điểm tham chiếu được cấu trúc để phản ánh — chúng không dự đoán sự kiện và không xác định kết quả. Sử dụng chúng làm hiệu chỉnh, với kinh nghiệm cuộc sống của riêng bạn làm thẩm quyền cuối cùng. Không có gì ở đây là lời khuyên y tế, pháp lý, tâm lý hoặc tài chính. Đối với các quyết định trong các lĩnh vực đó, hãy tham khảo một chuyên gia có trình độ.

---

## Tín dụng & Giấy phép

- **Swiss Ephemeris** qua `pyswisseph` — © Astrodienst AG, dual-licensed AGPL-3.0 / commercial (<https://www.astro.com/swisseph/>).
- **py-iztro** (và upstream `iztro`) — MIT, cho 紫微斗數.
- Quy cho đầy đủ: **[CREDITS.md](./CREDITS.md)**.
- **Giấy phép:** [AGPL-3.0](./LICENSE).
- **Giao thức Agent / JSON:** [AGENTS.md](./AGENTS.md).
