#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
from collections import defaultdict
from datetime import datetime

def analyze_transactions(filename):
    # Read the CSV file
    sales_entries = []
    transfer_entries = []
    all_entries = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        line_count = 0
        for row in reader:
            line_count += 1
            if len(row) >= 8:
                # Skip header rows and check if first column is a number
                if row[0] and row[0].strip().isdigit():
                    try:
                        entry = {
                            'no': int(row[0].strip()),
                            'date': row[1].strip() if row[1] else '',
                            'type': row[2].strip() if row[2] else '',
                            'category': row[3].strip() if row[3] else '',
                            'description': row[4].strip() if row[4] else '',
                            'counterparty': row[5].strip() if row[5] else '',
                            'method': row[6].strip() if row[6] else '',
                            'amount': row[7].strip().replace(',', '') if row[7] else '0'
                        }
                        
                        all_entries.append(entry)
                        
                        # Check for sales entries
                        if '売上' in row[1] and row[3].strip() == '売上':
                            sales_entries.append(entry)
                        # Check for transfer entries  
                        elif '振替' in row[1] and '振替' in row[3]:
                            transfer_entries.append(entry)
                    except Exception as e:
                        print(f"Error processing line {line_count}: {e}")
                        continue
    
    print(f"Successfully read {line_count} lines from file")
    print(f"\nTotal transaction entries: {len(all_entries)}")
    print(f"売上 (Sales) entries: {len(sales_entries)}")
    print(f"振替 (Transfer) entries: {len(transfer_entries)}")
    print(f"Difference (売上 - 振替): {len(sales_entries) - len(transfer_entries)}")
    
    # Analyze sales without transfers
    # Group by date (without time) and amount
    sales_by_date_amount = defaultdict(list)
    transfer_by_date_amount = defaultdict(list)
    
    for sale in sales_entries:
        try:
            amount = int(sale['amount'])
            # Extract just the date part (YYYY/MM/DD)
            date_match = re.match(r'(\d{4}/\d{2}/\d{2})', sale['date'])
            if date_match:
                date = date_match.group(1)
                key = f"{date}_{amount}"
                sales_by_date_amount[key].append(sale)
        except Exception as e:
            print(f"Error processing sale: {e}")
    
    for transfer in transfer_entries:
        try:
            amount = int(transfer['amount'])
            # Extract just the date part
            date_match = re.match(r'(\d{4}/\d{2}/\d{2})', transfer['date'])
            if date_match:
                date = date_match.group(1)
                key = f"{date}_{amount}"
                transfer_by_date_amount[key].append(transfer)
        except Exception as e:
            print(f"Error processing transfer: {e}")
    
    # Find unmatched sales
    unmatched_sales = []
    matched_count = 0
    
    for key, sales in sales_by_date_amount.items():
        transfers = transfer_by_date_amount.get(key, [])
        if len(sales) > len(transfers):
            # Add unmatched sales
            for i in range(len(transfers), len(sales)):
                unmatched_sales.append(sales[i])
        matched_count += min(len(sales), len(transfers))
    
    print(f"\nMatched sales (with transfers): {matched_count}")
    print(f"Unmatched sales (without transfers): {len(unmatched_sales)}")
    
    print(f"\n=== UNMATCHED SALES (売上 without corresponding 振替) ===")
    print(f"Found {len(unmatched_sales)} unmatched sales:")
    
    # Sort by date and transaction number
    unmatched_sales.sort(key=lambda x: (x['date'], x['no']))
    
    # Group by date for better readability
    unmatched_by_date = defaultdict(list)
    for sale in unmatched_sales:
        date_match = re.match(r'(\d{4}/\d{2}/\d{2})', sale['date'])
        if date_match:
            date = date_match.group(1)
            unmatched_by_date[date].append(sale)
    
    # Show first 30 unmatched sales by date
    shown = 0
    for date in sorted(unmatched_by_date.keys()):
        if shown >= 30:
            remaining = len(unmatched_sales) - shown
            print(f"\n... and {remaining} more unmatched sales")
            break
            
        sales = unmatched_by_date[date]
        print(f"\n{date}:")
        for sale in sales:
            if shown >= 30:
                break
            print(f"  No: {sale['no']}, Amount: {int(sale['amount']):,} yen, "
                  f"Counterparty: {sale['counterparty']}")
            if sale['description']:
                print(f"    Description: {sale['description'][:60]}")
            shown += 1
    
    # Analyze patterns
    print("\n\n=== PATTERN ANALYSIS ===")
    
    # Unmatched sales by counterparty
    unmatched_by_counterparty = defaultdict(list)
    for sale in unmatched_sales:
        unmatched_by_counterparty[sale['counterparty']].append(sale)
    
    print("\nUnmatched sales by counterparty:")
    for cp in sorted(unmatched_by_counterparty.keys(), 
                     key=lambda x: len(unmatched_by_counterparty[x]), reverse=True):
        sales = unmatched_by_counterparty[cp]
        total = sum(int(s['amount']) for s in sales)
        print(f"  {cp}: {len(sales)} unmatched sales, Total: {total:,} yen")
    
    # Amount analysis for unmatched sales
    unmatched_amounts = []
    for sale in unmatched_sales:
        try:
            unmatched_amounts.append(int(sale['amount']))
        except:
            pass
    
    if unmatched_amounts:
        print(f"\nUnmatched sales amount statistics:")
        print(f"  Min: {min(unmatched_amounts):,} yen")
        print(f"  Max: {max(unmatched_amounts):,} yen")
        print(f"  Average: {sum(unmatched_amounts) / len(unmatched_amounts):,.2f} yen")
        print(f"  Total: {sum(unmatched_amounts):,} yen")
    
    # Check for patterns in dates
    print("\n\n=== DATE PATTERN ANALYSIS ===")
    
    # Count unmatched by month
    unmatched_by_month = defaultdict(int)
    for sale in unmatched_sales:
        date_match = re.match(r'(\d{4}/\d{2})', sale['date'])
        if date_match:
            month = date_match.group(1)
            unmatched_by_month[month] += 1
    
    print("\nUnmatched sales by month:")
    for month in sorted(unmatched_by_month.keys()):
        count = unmatched_by_month[month]
        print(f"  {month}: {count} unmatched sales")
    
    # Check for mathematical discrepancies
    print("\n\n=== MATHEMATICAL CHECKS ===")
    
    # Group all entries by transaction ID
    transactions_by_id = defaultdict(list)
    
    for entry in all_entries:
        desc = entry['description']
        # Look for transaction IDs
        id_patterns = [
            r'm\d{8,}',           # Mercari IDs
            r'order_[A-Za-z0-9]+',  # Order IDs  
            r'z\d{8,}',           # Other platform IDs
            r'd\d{8,}',           # Other IDs
            r'\b\d{9,}\b'         # Long numeric IDs
        ]
        
        found_ids = []
        for pattern in id_patterns:
            matches = re.findall(pattern, desc)
            found_ids.extend(matches)
        
        # Use the first found ID
        if found_ids:
            trans_id = found_ids[0]
            transactions_by_id[trans_id].append(entry)
    
    # Check for inconsistencies
    inconsistencies = []
    
    for trans_id, entries in transactions_by_id.items():
        if len(entries) >= 3:  # Need multiple entries to check
            sales_total = 0
            expense_total = 0
            transfer_total = 0
            
            for entry in entries:
                try:
                    amount = int(entry['amount'])
                    if '売上' in entry['date'] and entry['category'] == '売上':
                        sales_total += amount
                    elif '経費' in entry['date']:
                        expense_total += amount
                    elif '振替' in entry['date'] and '振替' in entry['category']:
                        transfer_total += amount
                except:
                    pass
            
            # Check mathematical consistency
            if transfer_total > 0 and sales_total > 0:
                expected_transfer = sales_total - expense_total
                diff = abs(transfer_total - expected_transfer)
                
                if diff > 1:  # Allow 1 yen rounding difference
                    inconsistencies.append({
                        'id': trans_id,
                        'sales': sales_total,
                        'expenses': expense_total,
                        'transfer': transfer_total,
                        'expected': expected_transfer,
                        'difference': transfer_total - expected_transfer,
                        'entries': len(entries)
                    })
    
    if inconsistencies:
        # Sort by difference amount
        inconsistencies.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        print(f"\nFound {len(inconsistencies)} potential mathematical inconsistencies:")
        for i, inc in enumerate(inconsistencies[:10]):
            print(f"\n{i+1}. Transaction ID: {inc['id']} ({inc['entries']} entries)")
            print(f"   Sales total: {inc['sales']:,} yen")
            print(f"   Expenses total: {inc['expenses']:,} yen")
            print(f"   Transfer amount: {inc['transfer']:,} yen")
            print(f"   Expected transfer: {inc['expected']:,} yen")
            print(f"   Discrepancy: {inc['difference']:+,} yen")
        
        if len(inconsistencies) > 10:
            print(f"\n... and {len(inconsistencies) - 10} more inconsistencies")
    else:
        print("\nNo mathematical inconsistencies found in transaction groups.")
    
    # Final summary
    print("\n\n=== SUMMARY ===")
    print(f"1. Total 売上 (sales) entries: {len(sales_entries)}")
    print(f"2. Total 振替 (transfer) entries: {len(transfer_entries)}")
    print(f"3. Matched sales-transfer pairs: {matched_count}")
    print(f"4. Unmatched sales (売上 without 振替): {len(unmatched_sales)}")
    
    if unmatched_sales:
        unmatched_total = sum(int(s['amount']) for s in unmatched_sales)
        print(f"5. Total amount of unmatched sales: {unmatched_total:,} yen")
        print(f"6. Percentage of unmatched sales: {len(unmatched_sales)/len(sales_entries)*100:.1f}%")
    
    if inconsistencies:
        total_discrepancy = sum(abs(inc['difference']) for inc in inconsistencies)
        print(f"7. Mathematical inconsistencies found: {len(inconsistencies)}")
        print(f"8. Total discrepancy amount: {total_discrepancy:,} yen")

if __name__ == "__main__":
    analyze_transactions("取引帳.csv")