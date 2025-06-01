import re
import pandas as pd
from pathlib import Path

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
    
    # Find all potential phone number chunks (digits with common separators)
    chunks = re.findall(r'[\+\(\)]?[\d\s\-\(\)]{10,}', text)
    
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

def process_excel(input_path: str, output_csv: str):
    input_path = Path(input_path)
    writer = pd.ExcelFile(input_path)
    output_rows = []

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
            
            phone_note = ", ".join(sorted(all_phones)) if all_phones else "No phone number found"
            output_rows.append(row_values + [phone_note])

    max_cols = max(len(row) for row in output_rows)
    headers = [f"col_{i}" for i in range(max_cols - 1)] + ["phone_result"]
    out_df = pd.DataFrame(output_rows, columns=headers)
    out_df.to_csv(output_csv, index=False)
    print(f"✅ Done. Output saved to {output_csv}")

# Sample usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python phone_extractor.py input.xlsx output.csv")
    else:
        process_excel(sys.argv[1], sys.argv[2])