#!/usr/bin/env python3
"""
Name Columns Merger Script

Searches for FIRST NAME, MIDDLE NAME, LAST NAME headers in Excel files.
Only processes files that contain ALL THREE headers.
Merges the name columns from all qualifying files into a single CSV.

Usage:
    python scripts/name_columns_merger.py input_folder output_file.csv
    python scripts/name_columns_merger.py test/ names_merged.csv
"""

import argparse
import pandas as pd
import time
from pathlib import Path
from typing import List, Tuple, Optional

# Required headers (case-insensitive matching)
REQUIRED_HEADERS = ['FIRST NAME', 'MIDDLE NAME', 'LAST NAME']

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

def find_name_columns(df: pd.DataFrame) -> Optional[Tuple[int, int, int]]:
    """
    Search for FIRST NAME, MIDDLE NAME, LAST NAME columns in the DataFrame.
    Returns tuple of column indices if all three are found, None otherwise.
    """
    # Convert all headers to uppercase for case-insensitive comparison
    headers = [str(col).upper().strip() for col in df.columns]
    
    # Find indices for each required header
    first_name_idx = None
    middle_name_idx = None
    last_name_idx = None
    
    for i, header in enumerate(headers):
        if 'FIRST NAME' in header or header == 'FIRSTNAME':
            first_name_idx = i
        elif 'MIDDLE NAME' in header or header == 'MIDDLENAME':
            middle_name_idx = i
        elif 'LAST NAME' in header or header == 'LASTNAME':
            last_name_idx = i
    
    # Return indices only if all three are found
    if all(idx is not None for idx in [first_name_idx, middle_name_idx, last_name_idx]):
        return (first_name_idx, middle_name_idx, last_name_idx)
    
    return None

def extract_name_data(excel_path: Path) -> pd.DataFrame:
    """
    Extract name columns from an Excel file if all required headers are found.
    Returns empty DataFrame if headers not found or file can't be read.
    """
    try:
        excel_file = pd.ExcelFile(excel_path)
        all_name_data = []
        
        for sheet_name in excel_file.sheet_names:
            try:
                # Read sheet with headers
                df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)
                
                # Skip empty sheets
                if df.empty:
                    continue
                
                # Look for name columns
                name_columns = find_name_columns(df)
                
                if name_columns is None:
                    print(f"   ⚠️  Sheet '{sheet_name}': Required name columns not found")
                    continue
                
                first_idx, middle_idx, last_idx = name_columns
                
                # Extract only the name columns
                name_df = df.iloc[:, [first_idx, middle_idx, last_idx]].copy()
                name_df.columns = ['first_name', 'middle_name', 'last_name']
                
                # Add metadata columns
                name_df.insert(0, 'source_file', excel_path.name)
                name_df.insert(1, 'source_sheet', sheet_name)
                
                # Filter out rows where all name fields are empty
                name_df = name_df.dropna(subset=['first_name', 'middle_name', 'last_name'], how='all')
                
                if not name_df.empty:
                    all_name_data.append(name_df)
                    print(f"   ✅ Sheet '{sheet_name}': Found {len(name_df)} name records")
                else:
                    print(f"   ⚠️  Sheet '{sheet_name}': No valid name data found")
                
            except Exception as e:
                print(f"   ❌ Error reading sheet '{sheet_name}': {e}")
                continue
        
        if all_name_data:
            # Combine all sheets from this Excel file
            combined_df = pd.concat(all_name_data, ignore_index=True)
            return combined_df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"   ❌ Error reading {excel_path.name}: {e}")
        return pd.DataFrame()

def merge_name_files(input_folder: Path, output_file: Path):
    """
    Process Excel files and merge name columns from files that have all required headers.
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
    print(f"🔍 Looking for files with headers: {', '.join(REQUIRED_HEADERS)}")
    print("=" * 70)
    
    all_name_data = []
    processed_files = 0
    skipped_files = 0
    total_records = 0
    
    start_time = time.time()
    
    for i, excel_file in enumerate(excel_files, 1):
        print(f"[{i}/{len(excel_files)}] Processing: {excel_file.name}")
        
        name_df = extract_name_data(excel_file)
        
        if not name_df.empty:
            all_name_data.append(name_df)
            processed_files += 1
            file_records = len(name_df)
            total_records += file_records
            print(f"   ✅ Added {file_records:,} name records")
        else:
            skipped_files += 1
            print(f"   ❌ Skipped - no qualifying name columns found")
    
    if not all_name_data:
        print("❌ No files with the required name columns were found")
        return False
    
    print(f"\n📊 Merging name data from {processed_files} qualifying file(s)...")
    
    try:
        # Merge all name DataFrames
        merged_df = pd.concat(all_name_data, ignore_index=True)
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save merged CSV
        merged_df.to_csv(output_file, index=False)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n✅ Successfully merged {total_records:,} name records from {processed_files} Excel files")
        print(f"📄 Output saved to: {output_file}")
        print(f"📊 Final dataset: {len(merged_df):,} rows × {len(merged_df.columns)} columns")
        print(f"⚠️  Skipped {skipped_files} files (missing required headers)")
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error merging data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Extract and merge name columns (FIRST NAME, MIDDLE NAME, LAST NAME) from Excel files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/name_columns_merger.py test/ names_output.csv
  python scripts/name_columns_merger.py /path/to/excel/files exports/all_names.csv
  python scripts/name_columns_merger.py data/ results/merged_names.csv

Note: Only processes files that contain ALL THREE required headers:
- FIRST NAME (or FIRSTNAME)
- MIDDLE NAME (or MIDDLENAME)  
- LAST NAME (or LASTNAME)
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
    
    success = merge_name_files(input_folder, output_file)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main() 