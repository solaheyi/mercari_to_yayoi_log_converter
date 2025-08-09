#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mercari CSV to Yayoi CSV Converter
Converts Mercari transaction data to Yayoi accounting system format
"""

import csv
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse


class MercariToYayoiConverter:
    def __init__(self, start_date: Optional[str] = None, end_date: Optional[str] = None, is_shop: bool = False):
        # Headers without 取引手段 since it will be in filename
        self.yayoi_headers = [
            "取引日", "取引分類", "科目", "摘要", "取引先", "金額"
        ]
        self.start_date = self.parse_filter_date(start_date) if start_date else None
        self.end_date = self.parse_filter_date(end_date) if end_date else None
        self.is_shop = is_shop
    
    def parse_filter_date(self, date_str: str) -> datetime:
        """Parse date string in YYYY-MM-DD format for filtering"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{date_str}'. Please use YYYY-MM-DD format.")
            sys.exit(1)
        
    def parse_mercari_csv(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Parse Mercari CSV file and return list of transactions within date range"""
        transactions = []
        filtered_count = 0
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Filter by date range if specified
                    if self.start_date or self.end_date:
                        transaction_date_str = row.get("購入完了日", "")
                        try:
                            # Parse the transaction date
                            transaction_date = datetime.strptime(transaction_date_str, "%Y-%m-%d %H:%M:%S")
                            
                            # Check if within date range
                            if self.start_date and transaction_date < self.start_date:
                                filtered_count += 1
                                continue
                            if self.end_date and transaction_date > self.end_date.replace(hour=23, minute=59, second=59):
                                filtered_count += 1
                                continue
                        except ValueError:
                            print(f"Warning: Could not parse date '{transaction_date_str}'. Including transaction.")
                    
                    transactions.append(row)
                    
            if filtered_count > 0:
                print(f"Filtered out {filtered_count} transactions outside the date range.")
                
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file_path}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            sys.exit(1)
            
        return transactions
    
    def parse_shop_csv(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Parse Mercari Shop CSV file and return list of transactions within date range"""
        transactions = []
        filtered_count = 0
        
        # Try different encodings for shop CSV files
        encodings_to_try = ['shift-jis', 'cp932', 'utf-8-sig', 'utf-8']
        file_content = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                with open(csv_file_path, 'r', encoding=encoding) as file:
                    file_content = file.read()
                    used_encoding = encoding
                    print(f"Successfully read shop CSV with {encoding} encoding")
                    break
            except UnicodeDecodeError:
                continue
        
        if file_content is None:
            print(f"Error: Could not read CSV file with any supported encoding")
            sys.exit(1)
        
        try:
            import io
            file = io.StringIO(file_content)
            reader = csv.reader(file)
            headers = next(reader)  # Skip header row
            
            for row in reader:
                if len(row) < 16:  # Need at least 16 columns
                    continue
                    
                # Skip cancelled orders (negative sales amount)
                try:
                    sales_amount = int(row[11])
                    if sales_amount < 0:
                        print(f"Skipping cancelled order: {row[0]}")
                        continue
                except (ValueError, IndexError):
                    continue
                
                # Filter by date range if specified
                if self.start_date or self.end_date:
                    sales_transfer_date_str = row[6]  # Sales transfer date (売上移転日) column
                    try:
                        # Parse the shop date format (2025/7/1 12:53:41)
                        transaction_date = datetime.strptime(sales_transfer_date_str.strip(), "%Y/%m/%d %H:%M:%S")
                        
                        # Check if within date range
                        if self.start_date and transaction_date < self.start_date:
                            filtered_count += 1
                            continue
                        if self.end_date and transaction_date > self.end_date.replace(hour=23, minute=59, second=59):
                            filtered_count += 1
                            continue
                    except ValueError:
                        print(f"Warning: Could not parse date '{sales_transfer_date_str}'. Including transaction.")
                
                # Convert to standard format for processing
                transaction = {
                    "購入完了日": row[6],  # Sales transfer date (売上移転日) - column 6
                    "商品ID": row[0],     # Order ID
                    "商品名": row[8],     # Product name
                    "商品代金": row[12],  # Product price
                    "販売手数料": row[15], # Sales fee
                    "配送料": row[13],    # Shipping fee
                    "販売利益": row[11],  # Sales profit (net amount)
                    "購入者": row[19]     # Shop name (use as counterparty)
                }
                transactions.append(transaction)
                    
            if filtered_count > 0:
                print(f"Filtered out {filtered_count} transactions outside the date range.")
                
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file_path}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            sys.exit(1)
            
        return transactions
    
    def format_date(self, date_str: str) -> str:
        """Convert date from Mercari format to Yayoi format (YYYY/MM/DD)"""
        try:
            # Try shop format first (e.g., "2025/7/1 12:53:41")
            dt = datetime.strptime(date_str.strip(), "%Y/%m/%d %H:%M:%S")
            return dt.strftime("%Y/%m/%d")
        except ValueError:
            try:
                # Try regular format (e.g., "2025-07-23 06:33:08")
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%Y/%m/%d")
            except ValueError:
                # Try date-only format
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    return dt.strftime("%Y/%m/%d")
                except ValueError:
                    print(f"Warning: Could not parse date '{date_str}'. Using as-is.")
                    return date_str
    
    def create_yayoi_transactions(self, mercari_transaction: Dict[str, Any]) -> List[Dict[str, str]]:
        """Convert a single Mercari transaction to multiple Yayoi transactions"""
        yayoi_transactions = []
        
        # Extract data from Mercari transaction
        date = self.format_date(mercari_transaction.get("購入完了日", ""))
        product_id = mercari_transaction.get("商品ID", "")
        product_name = mercari_transaction.get("商品名", "")
        
        # Clean up product name to remove problematic Unicode characters
        # Replace narrow no-break space (U+202F) and other problematic characters
        product_name = product_name.replace('\u202f', ' ')  # narrow no-break space
        product_name = product_name.replace('\u00a0', ' ')  # non-breaking space
        product_name = product_name.replace('\u2009', ' ')  # thin space
        product_name = product_name.replace('\u200a', ' ')  # hair space
        
        # Convert price fields to integers, handling non-numeric values
        try:
            product_price = int(mercari_transaction.get("商品代金", 0))
        except (ValueError, TypeError):
            print(f"Warning: Invalid price for product {product_id}. Skipping.")
            return []
            
        try:
            sales_fee = int(mercari_transaction.get("販売手数料", 0))
        except (ValueError, TypeError):
            sales_fee = 0
            
        try:
            shipping_fee = int(mercari_transaction.get("配送料", 0))
        except (ValueError, TypeError):
            shipping_fee = 0
            
        try:
            sales_profit = int(mercari_transaction.get("販売利益", 0))
        except (ValueError, TypeError):
            sales_profit = 0
        
        description = f"{product_id} {product_name}"
        
        # Determine the counterparty based on whether it's shop or regular
        if self.is_shop:
            counterparty = "メルカリSHOP"
            accounts_receivable = "売掛金（メルカリSHOP）"
            transfer_method = "売掛金（メルカリSHOP）⇒その他の預金"
        else:
            counterparty = "メルカリ"
            accounts_receivable = "売掛金（メルカリ）"
            transfer_method = "売掛金（メルカリ）⇒その他の預金"
        
        # 1. Sales entry (売上)
        sales_entry = {
            "取引日": date,
            "取引分類": "売上",
            "科目": "売上",
            "摘要": description,
            "取引先": counterparty,
            "取引手段": accounts_receivable,
            "金額": str(product_price)
        }
        yayoi_transactions.append(sales_entry)
        
        # 2. Sales fee expense entry (支払手数料)
        if sales_fee > 0:
            fee_entry = {
                "取引日": date,
                "取引分類": "経費",
                "科目": "支払手数料",
                "摘要": description,
                "取引先": counterparty,
                "取引手段": "その他の預金",
                "金額": str(sales_fee)
            }
            yayoi_transactions.append(fee_entry)
        
        # 3. Shipping fee expense entry (荷造運賃)
        if shipping_fee > 0:
            shipping_entry = {
                "取引日": date,
                "取引分類": "経費",
                "科目": "荷造運賃",
                "摘要": description,
                "取引先": counterparty,
                "取引手段": "その他の預金",
                "金額": str(shipping_fee)
            }
            yayoi_transactions.append(shipping_entry)
        
        return yayoi_transactions
    
    def convert_to_yayoi(self, input_csv_path: str, output_csv_path: str = None) -> List[str]:
        """Convert Mercari CSV to Yayoi CSV format, split by transaction method"""
        base_output_path = output_csv_path or input_csv_path.replace('.csv', '_yayoi')
        
        # Parse CSV based on type (shop or regular)
        if self.is_shop:
            mercari_transactions = self.parse_shop_csv(input_csv_path)
        else:
            mercari_transactions = self.parse_mercari_csv(input_csv_path)
        
        # Convert to Yayoi format and group by transaction method and expense type
        transactions_by_method = {}
        for mercari_transaction in mercari_transactions:
            yayoi_transactions = self.create_yayoi_transactions(mercari_transaction)
            for transaction in yayoi_transactions:
                method = transaction.get('取引手段', '')
                account = transaction.get('科目', '')
                
                # Create separate keys for different expense types
                if method == "その他の預金" and account in ["支払手数料", "荷造運賃"]:
                    key = f"{method}_{account}"
                else:
                    key = method
                
                if key not in transactions_by_method:
                    transactions_by_method[key] = []
                # Remove 取引手段 from the transaction data
                transaction_copy = transaction.copy()
                del transaction_copy['取引手段']
                transactions_by_method[key].append(transaction_copy)
        
        # Write separate CSV files for each transaction method
        output_files = []
        try:
            for method, transactions in transactions_by_method.items():
                # Create filename based on transaction method
                method_filename = self._get_filename_for_method(method)
                output_path = f"{base_output_path}_{method_filename}.csv"
                
                with open(output_path, 'w', newline='', encoding='shift_jis', errors='replace') as file:
                    writer = csv.DictWriter(file, fieldnames=self.yayoi_headers, quoting=csv.QUOTE_ALL)
                    # Don't write header - Yayoi doesn't need it
                    
                    # Write rows one by one to handle encoding issues
                    for transaction in transactions:
                        try:
                            # Clean up all fields to ensure Shift-JIS compatibility
                            cleaned_transaction = {}
                            for key, value in transaction.items():
                                if value and isinstance(value, str):
                                    # Replace problematic Unicode characters
                                    value = value.replace('\u202f', ' ')  # narrow no-break space
                                    value = value.replace('\u00a0', ' ')  # non-breaking space
                                    value = value.replace('\u2009', ' ')  # thin space
                                    value = value.replace('\u200a', ' ')  # hair space
                                    # Try to encode to shift_jis to check for other issues
                                    try:
                                        value.encode('shift_jis')
                                    except UnicodeEncodeError:
                                        # Replace any remaining problematic characters with spaces
                                        value = ''.join(char if ord(char) < 0x10000 else ' ' for char in value)
                                cleaned_transaction[key] = value
                            writer.writerow(cleaned_transaction)
                        except Exception as e:
                            print(f"Warning: Could not write transaction: {e}")
                            continue
                
                output_files.append(output_path)
                print(f"Created: {output_path} ({len(transactions)} entries)")
            
            print(f"\nConversion completed successfully!")
            print(f"Input: {input_csv_path}")
            print(f"Converted {len(mercari_transactions)} Mercari transactions")
            print(f"Created {len(output_files)} output files")
            
            return output_files
            
        except Exception as e:
            print(f"Error writing output CSV: {e}")
            sys.exit(1)
    
    def _get_filename_for_method(self, method: str) -> str:
        """Convert transaction method to safe filename"""
        # Map transaction methods to filename-safe strings
        method_map = {
            "売掛金（メルカリ）": "urikake_mercari",
            "売掛金（メルカリ）⇒その他の預金": "furikae_mercari_to_yokin",
            "その他の預金": "sonota_yokin",
            "その他の預金_支払手数料": "sonota_yokin_tesuryo",
            "その他の預金_荷造運賃": "sonota_yokin_soryo",
            "売掛金（メルカリSHOP）": "urikake_mercari_shop",
            "売掛金（メルカリSHOP）⇒その他の預金": "furikae_mercari_shop_to_yokin",
            "売掛金（ヤフオク）": "urikake_yahoo",
            "売掛金（ヤフオク）⇒その他の預金": "furikae_yahoo_to_yokin",
        }
        return method_map.get(method, "other")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Mercari CSV to Yayoi CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert regular Mercari transactions
  python mercari_to_yayoi_converter.py mercari.csv
  
  # Convert Mercari Shop transactions
  python mercari_to_yayoi_converter.py shop_report.csv --shop
  
  # Convert with custom output filename
  python mercari_to_yayoi_converter.py mercari.csv -o yayoi_output.csv
  
  # Convert only transactions from 2025
  python mercari_to_yayoi_converter.py mercari.csv --from 2025-01-01 --to 2025-12-31
  
  # Convert shop transactions from specific month
  python mercari_to_yayoi_converter.py shop_report.csv --shop --from 2025-07-01 --to 2025-07-31
        """
    )
    parser.add_argument('input_csv', help='Path to Mercari CSV file')
    parser.add_argument('-o', '--output', help='Output CSV file path (optional)')
    parser.add_argument('--from', dest='start_date', help='Start date (YYYY-MM-DD) for filtering transactions')
    parser.add_argument('--to', dest='end_date', help='End date (YYYY-MM-DD) for filtering transactions')
    parser.add_argument('--shop', action='store_true', help='Process Mercari Shop CSV format instead of regular format')
    
    args = parser.parse_args()
    
    # Display date range if specified
    if args.start_date or args.end_date:
        print("Date range filter:")
        if args.start_date:
            print(f"  From: {args.start_date}")
        if args.end_date:
            print(f"  To: {args.end_date}")
        print()
    
    converter = MercariToYayoiConverter(args.start_date, args.end_date, args.shop)
    converter.convert_to_yayoi(args.input_csv, args.output)


if __name__ == "__main__":
    main()