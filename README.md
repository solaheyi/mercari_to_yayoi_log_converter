# Mercari to Yayoi CSV Converter

このツールは、メルカリおよびメルカリShopsの取引データCSVを弥生会計システムで読み込み可能な形式に変換するPythonプログラムです。

## 必要な環境

- Python 3.6以上
- 標準ライブラリのみ使用（追加インストール不要）

## 使い方

### 基本的な使い方

#### 通常のメルカリ取引を変換する場合：

```bash
python mercari_to_yayoi_converter.py mercari_sold_2025_20250723_092715.csv
```

#### メルカリShopsの取引を変換する場合：

```bash
python mercari_to_yayoi_converter.py 202507-202507_report.csv --shop
```

### 出力ファイル名を指定

```bash
python mercari_to_yayoi_converter.py mercari_sold_2025_20250723_092715.csv -o yayoi_output.csv
```

### 日付範囲を指定して変換

特定の期間の取引のみを変換できます。

#### 2025年の全取引を変換：
```bash
python mercari_to_yayoi_converter.py mercari_sold_2025_20250723_092715.csv --from 2025-01-01 --to 2025-12-31
```

#### 2025年7月の取引のみ変換：
```bash
python mercari_to_yayoi_converter.py mercari_sold_2025_20250723_092715.csv --from 2025-07-01 --to 2025-07-31
```

#### 特定の日付以降の取引を変換：
```bash
python mercari_to_yayoi_converter.py mercari_sold_2025_20250723_092715.csv --from 2025-07-15
```

#### 特定の日付までの取引を変換：
```bash
python mercari_to_yayoi_converter.py mercari_sold_2025_20250723_092715.csv --to 2025-07-20
```

## 変換の仕組み

このプログラムは、メルカリの1つの取引を弥生会計の複数の仕訳に変換し、取引手段ごとに3つの別々のCSVファイルに出力します：

1. **売上仕訳** - 商品代金の全額を売上として記録
2. **支払手数料仕訳** - 販売手数料を経費として記録
3. **荷造運賃仕訳** - 配送料を経費として記録

### 出力ファイル

#### 通常のメルカリ取引の場合：
入力ファイル名が `mercari_sold_all.csv` の場合、以下の3つのファイルが生成されます：

1. `mercari_sold_all_yayoi_urikake_mercari.csv` - 売掛金（売上）
2. `mercari_sold_all_yayoi_sonota_yokin_tesuryo.csv` - 支払手数料
3. `mercari_sold_all_yayoi_sonota_yokin_soryo.csv` - 荷造運賃

#### メルカリShops取引の場合：
入力ファイル名が `shop_report.csv` の場合、以下の3つのファイルが生成されます：

1. `shop_report_yayoi_urikake_mercari_shop.csv` - 売掛金（売上）
2. `shop_report_yayoi_sonota_yokin_tesuryo.csv` - 支払手数料  
3. `shop_report_yayoi_sonota_yokin_soryo.csv` - 荷造運賃

### 変換例

メルカリCSVの1行：
```
購入完了日: 2025-07-23 00:30:00
商品ID: m30000000000
商品名: 商品サンプル
商品代金: 3280
販売手数料: 328
配送料: 160
販売利益: 2792
```

弥生CSVに変換後（3つのファイルに分かれて出力）：

**売上ファイル (urikake_mercari.csv):**
```
"2025/07/23","売上","売上","m30000000000 商品サンプル","メルカリ","3280"
```

**支払手数料ファイル (sonota_yokin_tesuryo.csv):**
```
"2025/07/23","経費","支払手数料","m30000000000 商品サンプル","メルカリ","328"
```

**荷造運賃ファイル (sonota_yokin_soryo.csv):**
```
"2025/07/23","経費","荷造運賃","m30000000000 商品サンプル","メルカリ","160"
```

## ヘルプの表示

```bash
python mercari_to_yayoi_converter.py -h
```

## 注意事項

- 日付のフォーマットは必ず `YYYY-MM-DD` 形式で指定してください（例：2025-07-23）
- 出力ファイルは自動的に3つのファイルに分割されます
- 通常のメルカリCSVファイルはUTF-8エンコーディング、ShopsのCSVファイルはShift-JISエンコーディングです
- 出力ファイルはShift-JIS形式で保存されます（弥生会計対応）
- ヘッダー行は出力されません（弥生会計の仕様に準拠）
- メルカリShopsのCSVでは、キャンセルされた取引（マイナス金額）は自動的にスキップされます

## やよいの白色申告オンラインスマート取引取込での使用方法

### 1. CSVファイルの準備

まず、メルカリからダウンロードしたファイルをPythonで変換します：

```bash
python mercari_to_yayoi_converter.py [ダウンロードしたファイル名]
```

**日付の基準：**
- メルカリ通常取引：「購入完了日」を基準にCSVに登録されます
- メルカリShops：「売上移転日」を基準にCSVに登録されます

### 2. やよいでのCSV読み込み手順

変換されたCSVファイルをやよいの白色申告オンラインで読み込む際の設定：

#### 売上ファイル（urikake_mercari.csv / urikake_mercari_shop.csv）の取り込み：
- **取引手段勘定科目**：「その他の預金」を選択
- **勘定科目**：「売上」を選択

#### 荷造運賃ファイル（sonota_yokin_soryo.csv）の取り込み：
- **取引手段勘定科目**：「荷造運賃」を選択  
- **勘定科目**：「その他の預金」を選択

#### 支払手数料ファイル（sonota_yokin_tesuryo.csv）の取り込み：
- **取引手段勘定科目**：「支払手数料」を選択
- **勘定科目**：「その他の預金」を選択