from scripts.std_codes import STD_CODES
import re
from typing import List, NamedTuple

# Module-level constants for regex patterns
_FLEXIBLE_SEP = r"[\s\-\.,/]*"  # flexible separators (0 or more)

# Compiled regex patterns - specific patterns first for priority
# Pattern 1: landline/landline sequences (highest priority)
_PATTERN_1 = re.compile(r'0([0-9]{2,4})[\s\-]+([0-9]+)/0([0-9]{2,4})[\s\-]+([0-9]+)')
# Pattern 2: Standard format with optional 91 prefix
_PATTERN_2 = re.compile(r'(?:\+91[\s\-]?|91[\s\-]+)?\(?\s*0\s*([0-9]{2,4})\s*\)?' + _FLEXIBLE_SEP + r'([0-9][\s\-\.,/0-9]*)')
# Pattern 3: International format
_PATTERN_3 = re.compile(r'(?:\+91|91)[\s\-]+([0-9]{2,4})[\s\-]+([0-9][\s\-\.,/0-9]*)')
_PATTERNS = [_PATTERN_1, _PATTERN_2, _PATTERN_3]

class LandlineMatch(NamedTuple):
    """Represents a validated landline match with precise boundaries."""
    start_pos: int
    end_pos: int
    std_code: str
    local_digits: str

def _find_valid_landline_matches(text: str) -> List[LandlineMatch]:
    """
    Find all valid landline matches in text using the Indian 10-digit rule.
    
    Returns:
        List of LandlineMatch objects with precise boundaries for removal.
    """
    valid_matches = []
    matched_regions = set()  # Track already matched character positions
    
    for pattern_idx, pattern in enumerate(_PATTERNS):
        for match in pattern.finditer(text):
            # Skip if this region overlaps with already matched regions
            match_range = set(range(match.start(), match.end()))
            if match_range & matched_regions:
                continue
                
            if pattern_idx == 0:  # landline/landline pattern
                # Extract both landlines from the sequence
                std1, local1, std2, local2 = match.groups()
                
                # Process first landline
                if std1 in STD_CODES:
                    expected_len1 = 10 - len(std1)
                    local1_digits = re.sub(r'[^\d]', '', local1)
                    if len(local1_digits) >= expected_len1:
                        actual_local1 = local1_digits[:expected_len1]
                        if len(actual_local1) == expected_len1:
                            # Find precise end of first landline
                            first_start = match.start()
                            slash_pos = text.find('/', first_start)
                            
                            valid_matches.append(LandlineMatch(
                                start_pos=first_start,
                                end_pos=slash_pos,
                                std_code=std1,
                                local_digits=actual_local1
                            ))
                
                # Process second landline  
                if std2 in STD_CODES:
                    expected_len2 = 10 - len(std2)
                    local2_digits = re.sub(r'[^\d]', '', local2)
                    if len(local2_digits) >= expected_len2:
                        actual_local2 = local2_digits[:expected_len2]
                        if len(actual_local2) == expected_len2:
                            # Find start of second landline (the "0" after the "/")
                            slash_pos = text.find('/', match.start())
                            second_zero_pos = text.find('0', slash_pos + 1)
                            
                            if second_zero_pos != -1:
                                second_start = second_zero_pos
                                
                                # Simple approach: remove characters until we've removed exactly 10 digits
                                digits_removed = 0
                                precise_end = second_start
                                
                                for i in range(second_start, len(text)):
                                    if text[i].isdigit():
                                        digits_removed += 1
                                        if digits_removed == 10:  # Total digits for complete landline
                                            precise_end = i + 1
                                            break
                                    # Continue through separators but stop at non-landline characters
                                    elif text[i] not in ' \t\n\r\f\v-.,/':
                                        break
                                    precise_end = i + 1
                                
                                valid_matches.append(LandlineMatch(
                                    start_pos=second_start,
                                    end_pos=precise_end,
                                    std_code=std2,
                                    local_digits=actual_local2
                                ))
                
                # Mark entire match region as used
                matched_regions.update(range(match.start(), match.end()))
                
            else:
                # Standard processing for patterns 2 and 3
                std_part = match.group(1)
                local_raw = match.group(2)
                
                # Check if STD code is valid first
                if std_part in STD_CODES:
                    # Calculate expected local length using 10-digit rule
                    expected_local_length = 10 - len(std_part)
                    
                    # Extract exactly the required number of digits from local_raw
                    digits_only = re.sub(r'[^\d]', '', local_raw)
                    
                    # Check if we have at least the required digits
                    if len(digits_only) >= expected_local_length:
                        # Take exactly the required number of digits
                        actual_local = digits_only[:expected_local_length]
                        
                        # Verify we have exactly the right length
                        if len(actual_local) == expected_local_length:
                            # Find the precise end position of the valid landline
                            local_start = match.start(2)
                            digit_count = 0
                            precise_end = local_start
                            
                            for i, char in enumerate(text[local_start:], local_start):
                                if char.isdigit():
                                    digit_count += 1
                                    if digit_count == expected_local_length:
                                        precise_end = i + 1
                                        break
                                elif i >= match.end():  # Safety: don't go beyond original match
                                    break
                            
                            # Store the validated match and mark region as used
                            valid_matches.append(LandlineMatch(
                                start_pos=match.start(),
                                end_pos=precise_end,
                                std_code=std_part,
                                local_digits=actual_local
                            ))
                            matched_regions.update(range(match.start(), precise_end))
    
    return valid_matches

def is_landline_chunk(chunk: str) -> bool:
    """Detect landline patterns with comprehensive format support including international formats."""
    if not chunk:
        return False
    
    # Use the shared helper function
    matches = _find_valid_landline_matches(chunk)
    return len(matches) > 0

def remove_landline_patterns(text: str) -> str:
    """Remove landline number patterns from text, preserving mobile numbers."""
    if not text:
        return text
    
    # Use the shared helper function
    valid_matches = _find_valid_landline_matches(text)
    
    if not valid_matches:
        return text
    
    # Process matches in reverse order to avoid position shifts
    cleaned_text = text
    for match in reversed(valid_matches):
        start, end = match.start_pos, match.end_pos
        cleaned_text = cleaned_text[:start] + " " * (end - start) + cleaned_text[end:]
    
    return cleaned_text