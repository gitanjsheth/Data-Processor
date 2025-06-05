#!/usr/bin/env python3
"""
Script to parse Excel or CSV files cell by cell and count word frequencies.
Outputs a CSV with unique words and their frequencies.

Usage:
    python scripts/word_frequency_parser.py input.xlsx output.csv
    python scripts/word_frequency_parser.py input.csv output.csv
    python scripts/word_frequency_parser.py test/Book1.xlsx word_frequency_output.csv
"""

import argparse
import pandas as pd
import re
import csv
from collections import Counter
from pathlib import Path

def clean_and_extract_words(text):
    """
    Extract words from text, cleaning and normalizing them.
    
    Args:
        text: Input text string
        
    Returns:
        List of cleaned words
    """
    if pd.isna(text) or text is None:
        return []
    
    # Convert to string if not already
    text = str(text)
    
    # Convert to lowercase and extract words (alphanumeric characters)
    # This regex keeps words with letters and numbers, removing punctuation
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    
    # Filter out single characters and very short words if desired
    # You can adjust the minimum length as needed
    words = [word for word in words if len(word) >= 2]
    
    return words

def parse_csv_to_word_frequency(csv_path, output_csv_path):
    """
    Parse CSV file cell by cell and count word frequencies.
    
    Args:
        csv_path: Path to the CSV file
        output_csv_path: Path for the output CSV file
    """
    print(f"Reading CSV file: {csv_path}")
    
    # Counter to store word frequencies
    word_counter = Counter()
    total_cells_processed = 0
    
    try:
        # Read the CSV file without headers to process all data
        df = pd.read_csv(csv_path, header=None, dtype=str)
        
        print(f"Found CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Process each cell in the dataframe
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                cell_value = df.iloc[row_idx, col_idx]
                
                # Extract words from the cell
                words = clean_and_extract_words(cell_value)
                
                # Add words to counter
                word_counter.update(words)
                
                total_cells_processed += 1
                
                # Progress indicator for large files
                if total_cells_processed % 10000 == 0:
                    print(f"Processed {total_cells_processed} cells...")
                    
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return
    
    print(f"Total cells processed: {total_cells_processed}")
    print(f"Total unique words found: {len(word_counter)}")
    
    # Sort words by frequency (descending order)
    sorted_words = word_counter.most_common()
    
    # Write to output CSV
    write_frequency_results(sorted_words, output_csv_path)

def parse_excel_to_word_frequency(excel_path, output_csv_path):
    """
    Parse Excel file cell by cell and count word frequencies.
    
    Args:
        excel_path: Path to the Excel file
        output_csv_path: Path for the output CSV file
    """
    print(f"Reading Excel file: {excel_path}")
    
    # Read all sheets from the Excel file
    try:
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names
        print(f"Found {len(sheet_names)} sheet(s): {sheet_names}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Counter to store word frequencies
    word_counter = Counter()
    total_cells_processed = 0
    
    # Process each sheet
    for sheet_name in sheet_names:
        print(f"Processing sheet: {sheet_name}")
        
        try:
            # Read the sheet
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
            
            # Process each cell in the dataframe
            for row_idx in range(len(df)):
                for col_idx in range(len(df.columns)):
                    cell_value = df.iloc[row_idx, col_idx]
                    
                    # Extract words from the cell
                    words = clean_and_extract_words(cell_value)
                    
                    # Add words to counter
                    word_counter.update(words)
                    
                    total_cells_processed += 1
                    
                    # Progress indicator for large files
                    if total_cells_processed % 10000 == 0:
                        print(f"Processed {total_cells_processed} cells...")
                        
        except Exception as e:
            print(f"Error processing sheet '{sheet_name}': {e}")
            continue
    
    print(f"Total cells processed: {total_cells_processed}")
    print(f"Total unique words found: {len(word_counter)}")
    
    # Sort words by frequency (descending order)
    sorted_words = word_counter.most_common()
    
    # Write to output CSV
    write_frequency_results(sorted_words, output_csv_path)

def write_frequency_results(sorted_words, output_csv_path):
    """
    Write word frequency results to CSV file.
    
    Args:
        sorted_words: List of (word, frequency) tuples sorted by frequency
        output_csv_path: Path for the output CSV file
    """
    print(f"Writing results to: {output_csv_path}")
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['word', 'frequency'])
            
            # Write word frequencies
            for word, frequency in sorted_words:
                writer.writerow([word, frequency])
                
        print(f"Successfully wrote {len(sorted_words)} unique words to {output_csv_path}")
        
        # Display top 10 most frequent words
        print("\nTop 10 most frequent words:")
        for i, (word, freq) in enumerate(sorted_words[:10], 1):
            print(f"{i:2d}. {word}: {freq}")
            
    except Exception as e:
        print(f"Error writing CSV file: {e}")

def parse_file_to_word_frequency(input_path, output_path):
    """
    Parse input file (Excel or CSV) and count word frequencies.
    
    Args:
        input_path: Path to the input file
        output_path: Path for the output CSV file
    """
    file_extension = input_path.suffix.lower()
    
    if file_extension in ['.xlsx', '.xls']:
        parse_excel_to_word_frequency(input_path, output_path)
    elif file_extension == '.csv':
        parse_csv_to_word_frequency(input_path, output_path)
    else:
        print(f"Error: Unsupported file format '{file_extension}'. Supported formats: .xlsx, .xls, .csv")
        return False
    
    return True

def main():
    """Main function to run the word frequency analysis."""
    parser = argparse.ArgumentParser(
        description="Parse Excel or CSV files cell by cell and count word frequencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/word_frequency_parser.py input.xlsx output.csv
  python scripts/word_frequency_parser.py input.csv output.csv
  python scripts/word_frequency_parser.py test/Book1.xlsx word_frequency_output.csv
  python scripts/word_frequency_parser.py data.csv word_frequencies.csv
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Path to input file (.xlsx, .xls, or .csv)"
    )
    
    parser.add_argument(
        "output_file", 
        help="Path to output CSV file"
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    
    # Check if input file exists
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return 1
    
    # Check if input file has supported extension
    supported_extensions = ['.xlsx', '.xls', '.csv']
    if input_path.suffix.lower() not in supported_extensions:
        print(f"Error: Input file must be one of: {', '.join(supported_extensions)}")
        return 1
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the analysis
    success = parse_file_to_word_frequency(input_path, output_path)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 