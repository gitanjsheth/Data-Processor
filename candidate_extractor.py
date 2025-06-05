#!/usr/bin/env python3
"""
Simple Cell-by-Cell Name Harvester
═══════════════════════════════════

Logic:
1. For each cell, check if it contains blacklisted words → reject
2. Check if it contains bad characters → reject  
3. If clean, take the entire cell as a name candidate

Input:  Phone-filtered CSVs
Output: *_names.csv files with extracted names
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import List, Set

import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BAD_CHARS_RE = re.compile(r"[0-9@/#$&*_\:;'\"\\()\[\]-]")
COMMA_PATTERN_RE = re.compile(r'[A-Za-z],')


def load_wordlist(path: Path) -> Set[str]:
    """Load a wordlist from file, returning empty set if file doesn't exist."""
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as f:
        return {w.strip().lower() for w in f if w.strip()}


BLACKLIST = load_wordlist(Path("documents/blacklist.txt"))

# ═══════════════════════════════════════════════════════════════════════════════
# NAME EXTRACTION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def extract_name_chunks(cell: str) -> List[str]:
    """
    Extract name candidates from a cell.
    
    Returns the entire cell if it passes validation, empty list otherwise.
    """
    cell = cell.strip()
    if not cell:
        return []
    
    # Reject if any word is blacklisted
    words_in_cell = set(word.lower() for word in cell.split())
    if words_in_cell & BLACKLIST:
        return []
    
    # Special comma rule: allow only if comma follows a single letter
    if ',' in cell:
        comma_count = cell.count(',')
        # Reject if more than one comma
        if comma_count > 1:
            return []
        # Reject if the single comma doesn't follow a letter
        if not COMMA_PATTERN_RE.search(cell):
            return []
    
    # Reject if contains bad characters (including digits)
    if BAD_CHARS_RE.search(cell):
        return []
        
    # Clean cell - take it as-is
    return [cell]


# ═══════════════════════════════════════════════════════════════════════════════
# FILE PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def process_file(csv_path: Path, output_dir: Path) -> None:
    """Process a single CSV file and extract names from all cells."""
    start_time = time.time()
    
    # Load data
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    output_rows = []
    n_cols = df.shape[1]
    
    # Process each row
    for idx in range(len(df)):
        row = df.iloc[idx]
        phone_pk = row.iat[0]  # Keep phone column unchanged
        name_candidates = []
        
        # Scan all cells except phone column
        for col in range(1, n_cols):
            cell = row.iat[col].strip()
            if cell:
                name_candidates.extend(extract_name_chunks(cell))
        
        # Store results with original columns for debugging
        output_row = {
            "phone_pk": phone_pk,
            "blob_list": json.dumps(sorted(set(name_candidates)), ensure_ascii=False)
        }
        
        # Add all original columns except phone column
        for col in range(1, n_cols):
            output_row[f"col_{col}"] = row.iat[col]
        
        output_rows.append(output_row)
    
    # Save output
    output_df = pd.DataFrame(output_rows)
    output_csv = output_dir / f"{csv_path.stem}_names.csv"
    output_df.to_csv(output_csv, index=False)
    
    # Report progress
    elapsed = time.time() - start_time
    print(f"✓ {csv_path.name} → {output_csv.name} ({len(output_df)} rows) [{elapsed:.1f}s]")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROGRAM
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Extract names from CSV files")
    parser.add_argument("input_dir", help="Input directory with CSV files")
    parser.add_argument("output_dir", help="Output directory for results")
    args = parser.parse_args()

    # Setup directories
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find and process files
    csv_files = list(input_dir.glob("*.csv"))
    print(f"Processing {len(csv_files)} CSV file(s)...")
    
    start_time = time.time()
    for csv_file in csv_files:
        process_file(csv_file, output_dir)
    
    total_time = time.time() - start_time
    print(f"\n🎉 Completed in {total_time:.1f} seconds")


if __name__ == "__main__":
    main() 