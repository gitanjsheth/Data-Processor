from scripts.std_codes import STD_CODES

import re

_SEP = r"[\s\-\.,/]"  # allowed separator between STD and local number

def is_landline_chunk(chunk: str) -> bool:
    """Detect 0 + STD + separator land-line pattern with 10-digit rule."""
    # Pattern that captures STD and local number properly
    pattern = re.compile(r'\(?\s*0\s*([0-9]+)\s*\)?' + _SEP + r'+([0-9]+)')
    
    for match in pattern.finditer(chunk):
        std_part = match.group(1)
        local_part = match.group(2)
        
        # Check if STD code is valid
        if std_part in STD_CODES:
            # Apply Indian landline rule: STD + local = exactly 10 digits
            expected_local_length = 10 - len(std_part)
            
            if len(local_part) == expected_local_length:
                return True
    
    return False

def remove_landline_patterns(text: str) -> str:
    """Remove landline number patterns from text, preserving mobile numbers."""
    if not text:
        return text
    
    cleaned_text = text
    
    # Use the SAME pattern as detection for consistency
    pattern = re.compile(r'\(?\s*0\s*([0-9]+)\s*\)?' + _SEP + r'+([0-9]+)')
    
    # Find all matches and process them
    matches = list(pattern.finditer(text))
    
    # Process matches in reverse order to avoid position shifts
    for match in reversed(matches):
        std_part = match.group(1)
        local_part = match.group(2)
        
        # Check if STD code is valid
        if std_part in STD_CODES:
            # Apply Indian landline rule: STD + local = exactly 10 digits
            expected_local_length = 10 - len(std_part)
            
            if len(local_part) == expected_local_length:
                # This is a valid landline - remove it
                start, end = match.span()
                cleaned_text = cleaned_text[:start] + " " * (end - start) + cleaned_text[end:]
    
    return cleaned_text