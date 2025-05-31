"""City lookup and canonicalization module."""

from typing import Tuple, Optional
from rapidfuzz import fuzz, process

try:
    from .db import execute_query
except ImportError:
    from db import execute_query

def canonical_city(raw_city: str) -> Tuple[Optional[int], float]:
    """
    Find the canonical city for a raw city string.
    
    Args:
        raw_city: Raw city string from input data
        
    Returns:
        Tuple of (city_id, confidence_score)
        city_id is None if no good match found
        confidence_score is 0.0-1.0
    """
    if not raw_city or not raw_city.strip():
        return None, 0.0
    
    raw_city = raw_city.strip()
    
    # Get all cities from database
    cities = execute_query("SELECT id, name FROM cities")
    
    if not cities:
        # No cities in database yet - could auto-create or return None
        return None, 0.0
    
    # Create list of city names for fuzzy matching
    city_names = [city[1] for city in cities]
    city_dict = {city[1]: city[0] for city in cities}
    
    # Use rapidfuzz to find best match
    best_match = process.extractOne(
        raw_city, 
        city_names, 
        scorer=fuzz.ratio,
        score_cutoff=60  # Minimum 60% similarity
    )
    
    if best_match:
        matched_name, confidence, _ = best_match
        city_id = city_dict[matched_name]
        return city_id, confidence / 100.0  # Convert to 0.0-1.0 scale
    
    return None, 0.0

def add_city(city_name: str) -> int:
    """
    Add a new city to the database.
    
    Args:
        city_name: Name of the city to add
        
    Returns:
        city_id of the newly created city
    """
    result = execute_query(
        "INSERT INTO cities (name) VALUES (%s) RETURNING id",
        (city_name.strip(),)
    )
    return result[0][0]

def get_or_create_city(raw_city: str, min_confidence: float = 0.8) -> int:
    """
    Get existing city or create new one if confidence is too low.
    
    Args:
        raw_city: Raw city string
        min_confidence: Minimum confidence to use existing city
        
    Returns:
        city_id
    """
    city_id, confidence = canonical_city(raw_city)
    
    if city_id and confidence >= min_confidence:
        return city_id
    
    # Create new city
    return add_city(raw_city) 