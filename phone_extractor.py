import re
import pandas as pd
import time
import argparse
from pathlib import Path
from scripts.landline_detector import remove_landline_patterns

def extract_valid_phones(text: str) -> list[str]:
    """Extract and normalize phone numbers using specified rules"""
    if not text:
        return []
    
    valid_numbers = set()
    
    # First, handle separator-based splitting for "/" and ","
    # Split on both "/" and "," and process each part separately
    parts = re.split(r'[/,]', text)
    
    # Process each split part individually
    for part in parts:
        part = part.strip()  # Remove leading/trailing whitespace
        if part:
            valid_numbers.update(extract_phones_from_chunk(part))
    
    # Also process the original text with separators removed (joined version)
    # Remove "," but keep other separators (removed "/" from joining)
    joined_text = re.sub(r'[,]', ' ', text)
    valid_numbers.update(extract_phones_from_chunk(joined_text))
    
    return sorted(list(valid_numbers))

def extract_phones_from_chunk(text: str) -> list[str]:
    """Extract phones from a single chunk of text"""
    if not text:
        return []
    
    # Remove landline patterns first, preserving mobile numbers
    cleaned_text = remove_landline_patterns(text)
    
    # Find all potential phone number chunks (digits with common separators)
    chunks = re.findall(r'[\+\(\)]?[\d\s\-\(\)]{10,}', cleaned_text)
    
    valid_numbers = set()
    
    for chunk in chunks:
        # Step 1: Remove all non-digit characters (spaces, dashes, brackets, plus signs)
        digits = re.sub(r'\D', '', chunk)
        
        # Step 2: Length check - only process 10-12 digit numbers
        if len(digits) < 10 or len(digits) > 12:
            continue
            
        # Step 3: Handle prefix removal with the 91 exception
        if digits.startswith('91'):
            if len(digits) == 12:
                # Remove 91 only if exactly 12 digits (91 + 10 more digits)
                digits = digits[2:]
        elif digits.startswith('0'):
            # Remove leading 0
            digits = digits[1:]
            
        # Step 4: Validate final result
        if len(digits) == 10 and digits[0] in '6789':
            valid_numbers.add(digits)
    
    return list(valid_numbers)

def process_excel(input_path: Path, output_path: Path):
    """Process a single Excel file and extract phone numbers"""
    start_time = time.time()
    
    try:
        writer = pd.ExcelFile(input_path)
        output_rows = []
        dropped_rows = 0

        for sheet in writer.sheet_names:
            df = writer.parse(sheet, header=None, dtype=str)
            for _, row in df.iterrows():
                row_values = [str(cell) if pd.notna(cell) else "" for cell in row.tolist()]
                
                # Process each cell individually and collect all phone numbers
                all_phones = set()
                for cell_value in row_values:
                    if cell_value.strip():  # Skip empty cells
                        phones = extract_valid_phones(cell_value)
                        all_phones.update(phones)
                
                # Quality control: Only add rows that have phone numbers AND not too many
                if all_phones:
                    if len(all_phones) <= 3:  # Maximum 3 phone numbers per row
                        phone_result = ", ".join(sorted(all_phones))
                        # Put phone_result first, then the original row data
                        output_rows.append([phone_result] + row_values)
                    else:
                        # Drop rows with more than 3 phone numbers (likely malformed data)
                        dropped_rows += 1

        end_time = time.time()
        processing_time = end_time - start_time

        if output_rows:  # Only create output if we have rows with phone numbers
            max_cols = max(len(row) for row in output_rows)
            # phone_result is now first column, followed by original columns
            headers = ["phone_result"] + [f"col_{i}" for i in range(max_cols - 1)]
            out_df = pd.DataFrame(output_rows, columns=headers)
            out_df.to_csv(output_path, index=False)
            print(f"✅ {input_path.name} -> {output_path.name} ({len(output_rows)} rows with phones)")
            if dropped_rows > 0:
                print(f"   ⚠️  Dropped {dropped_rows} rows with >3 phone numbers")
        else:
            print(f"❌ {input_path.name} -> No phone numbers found")
            if dropped_rows > 0:
                print(f"   ⚠️  {dropped_rows} rows were dropped due to having >3 phone numbers")
        
        print(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
        return len(output_rows) > 0
        
    except Exception as e:
        print(f"❌ Error processing {input_path.name}: {e}")
        return False

def process_folder(input_folder: Path, output_folder: Path = None):
    """Process all Excel files in a folder"""
    if not input_folder.exists():
        print(f"❌ Input folder does not exist: {input_folder}")
        return
    
    if not input_folder.is_dir():
        print(f"❌ Input path is not a folder: {input_folder}")
        return
    
    # If no output folder specified, use the same as input folder
    if output_folder is None:
        output_folder = input_folder
    else:
        output_folder.mkdir(parents=True, exist_ok=True)
    
    # Find all Excel files
    excel_extensions = ['.xlsx', '.xls']
    excel_files = []
    for ext in excel_extensions:
        excel_files.extend(input_folder.glob(f'*{ext}'))
        excel_files.extend(input_folder.glob(f'*{ext.upper()}'))  # Also check uppercase
    
    if not excel_files:
        print(f"❌ No Excel files found in {input_folder}")
        return
    
    print(f"📁 Found {len(excel_files)} Excel file(s) in {input_folder}")
    print("=" * 60)
    
    processed_count = 0
    successful_count = 0
    
    for excel_file in sorted(excel_files):
        # Skip temporary Excel files (start with ~$)
        if excel_file.name.startswith('~$'):
            continue
            
        processed_count += 1
        
        # Generate output filename: {input_filename}_conv.csv
        output_filename = f"{excel_file.stem}_conv.csv"
        output_path = output_folder / output_filename
        
        print(f"\n[{processed_count}/{len(excel_files)}] Processing: {excel_file.name}")
        success = process_excel(excel_file, output_path)
        if success:
            successful_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Summary: {successful_count}/{processed_count} files processed successfully")

def main():
    parser = argparse.ArgumentParser(
        description="Extract phone numbers from Excel files in a folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python phone_extractor.py test/
  python phone_extractor.py test/ --output exports/
  python phone_extractor.py /path/to/excel/files --output /path/to/output
        """
    )
    
    parser.add_argument(
        "input_folder",
        help="Path to folder containing Excel files"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output folder for CSV files (default: same as input folder)"
    )
    
    args = parser.parse_args()
    
    input_folder = Path(args.input_folder)
    output_folder = Path(args.output) if args.output else None
    
    process_folder(input_folder, output_folder)

if __name__ == "__main__":
    main()