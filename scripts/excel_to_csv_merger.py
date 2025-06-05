#!/usr/bin/env python3
"""
Excel to CSV Merger Script

Converts all Excel files in a specified folder to CSV format and merges them into a single CSV file.
Does not save individual CSV files - only the final merged result.

Usage:
    python scripts/excel_to_csv_merger.py input_folder output_file.csv
    python scripts/excel_to_csv_merger.py test/ merged_data.csv
"""

import argparse
import pandas as pd
import time
from pathlib import Path
from typing import List

def find_excel_files(folder_path: Path) -> List[Path]:
    """Find all Excel files in the given folder"""
    excel_extensions = ['.xlsx', '.xls']
    excel_files = []
    
    for ext in excel_extensions:
        excel_files.extend(folder_path.glob(f'*{ext}'))
        excel_files.extend(folder_path.glob(f'*{ext.upper()}'))  # Also check uppercase
    
    # Filter out temporary Excel files (start with ~$)
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    return sorted(excel_files)

def read_excel_to_dataframe(excel_path: Path) -> pd.DataFrame:
    """
    Read an Excel file and return a combined DataFrame from all sheets.
    Adds source information columns.
    """
    try:
        excel_file = pd.ExcelFile(excel_path)
        all_sheets_data = []
        
        for sheet_name in excel_file.sheet_names:
            try:
                # Read sheet without headers to preserve all data
                df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, dtype=str)
                
                # Skip empty sheets
                if df.empty:
                    continue
                
                # Add metadata columns
                df.insert(0, 'source_file', excel_path.name)
                df.insert(1, 'source_sheet', sheet_name)
                
                all_sheets_data.append(df)
                
            except Exception as e:
                print(f"   ⚠️  Error reading sheet '{sheet_name}': {e}")
                continue
        
        if all_sheets_data:
            # Combine all sheets from this Excel file
            combined_df = pd.concat(all_sheets_data, ignore_index=True)
            return combined_df
        else:
            print(f"   ⚠️  No readable sheets found in {excel_path.name}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"   ❌ Error reading {excel_path.name}: {e}")
        return pd.DataFrame()

def merge_excel_files(input_folder: Path, output_file: Path):
    """
    Convert all Excel files in folder to CSV format and merge into single file.
    """
    if not input_folder.exists():
        print(f"❌ Input folder does not exist: {input_folder}")
        return False
    
    if not input_folder.is_dir():
        print(f"❌ Input path is not a folder: {input_folder}")
        return False
    
    # Find all Excel files
    excel_files = find_excel_files(input_folder)
    
    if not excel_files:
        print(f"❌ No Excel files found in {input_folder}")
        return False
    
    print(f"📁 Found {len(excel_files)} Excel file(s) in {input_folder}")
    print("=" * 60)
    
    all_dataframes = []
    successful_files = 0
    total_rows = 0
    
    start_time = time.time()
    
    for i, excel_file in enumerate(excel_files, 1):
        print(f"[{i}/{len(excel_files)}] Processing: {excel_file.name}")
        
        df = read_excel_to_dataframe(excel_file)
        
        if not df.empty:
            all_dataframes.append(df)
            successful_files += 1
            file_rows = len(df)
            total_rows += file_rows
            print(f"   ✅ Added {file_rows:,} rows")
        else:
            print(f"   ❌ No data extracted")
    
    if not all_dataframes:
        print("❌ No data was extracted from any Excel files")
        return False
    
    print(f"\n📊 Merging data from {successful_files} file(s)...")
    
    try:
        # Merge all DataFrames - pandas will automatically handle different column counts
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Create proper column names based on the final merged structure
        num_cols = len(merged_df.columns)
        column_names = ['source_file', 'source_sheet'] + [f'col_{i}' for i in range(num_cols - 2)]
        merged_df.columns = column_names
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save merged CSV
        merged_df.to_csv(output_file, index=False)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n✅ Successfully merged {total_rows:,} rows from {successful_files} Excel files")
        print(f"📄 Output saved to: {output_file}")
        print(f"📊 Final dataset: {len(merged_df):,} rows × {len(merged_df.columns)} columns")
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error merging data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Convert all Excel files in a folder to CSV and merge into single file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/excel_to_csv_merger.py test/ merged_output.csv
  python scripts/excel_to_csv_merger.py /path/to/excel/files exports/combined_data.csv
  python scripts/excel_to_csv_merger.py data/ results/all_data.csv
        """
    )
    
    parser.add_argument(
        "input_folder",
        help="Path to folder containing Excel files"
    )
    
    parser.add_argument(
        "output_file",
        help="Path for the output merged CSV file"
    )
    
    args = parser.parse_args()
    
    input_folder = Path(args.input_folder)
    output_file = Path(args.output_file)
    
    success = merge_excel_files(input_folder, output_file)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main() 