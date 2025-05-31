"""Worker module for processing Four Belt data files."""

import pandas as pd
from pathlib import Path
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException

try:
    from .db import execute_query, execute_many
    from .city_lookup import get_or_create_city
except ImportError:
    from db import execute_query, execute_many
    from city_lookup import get_or_create_city

class FourBeltWorker:
    """Worker class for processing Four Belt Excel files."""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
    
    def run(self, file_path: str, sheet: str, file_id: int) -> dict:
        """
        Process a Four Belt Excel file sheet.
        
        Args:
            file_path: Path to the Excel file
            sheet: Name of the sheet to process
            file_id: ID of the source file record
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Read the Excel sheet
            df = pd.read_excel(file_path, sheet_name=sheet)
            
            # Process each row
            people_data = []
            people_sources_data = []
            
            for index, row in df.iterrows():
                try:
                    person_data = self._process_row(row, file_id)
                    if person_data:
                        people_data.append(person_data['person'])
                        people_sources_data.append(person_data['source'])
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    self.error_count += 1
                    continue
            
            # Bulk insert people
            if people_data:
                self._bulk_insert_people(people_data, people_sources_data)
            
            return {
                'processed_count': len(people_data),
                'error_count': self.error_count,
                'sheet': sheet,
                'file_path': file_path
            }
            
        except Exception as e:
            print(f"Error processing file {file_path}, sheet {sheet}: {e}")
            return {
                'processed_count': 0,
                'error_count': 1,
                'error': str(e),
                'sheet': sheet,
                'file_path': file_path
            }
    
    def _process_row(self, row: pd.Series, file_id: int) -> Optional[dict]:
        """Process a single row from the Excel sheet."""
        # Extract basic info (adjust column names as needed)
        first_name = self._clean_string(row.get('first_name', ''))
        last_name = self._clean_string(row.get('last_name', ''))
        email = self._clean_string(row.get('email', ''))
        phone = self._clean_phone(row.get('phone', ''))
        city_raw = self._clean_string(row.get('city', ''))
        
        # Skip rows without minimum required data
        if not (first_name or last_name or email):
            return None
        
        # Get or create city
        city_id = None
        if city_raw:
            city_id = get_or_create_city(city_raw)
        
        # Prepare person data
        person_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'city_id': city_id
        }
        
        # Prepare source relationship data
        source_data = {
            'file_id': file_id,
            'row_number': row.name + 1,  # Excel row number (1-based)
            'raw_data': row.to_dict()
        }
        
        return {
            'person': person_data,
            'source': source_data
        }
    
    def _bulk_insert_people(self, people_data: list, sources_data: list):
        """Bulk insert people and their source relationships."""
        # Insert people and get their IDs
        people_query = """
        INSERT INTO people (first_name, last_name, email, phone, city_id)
        VALUES (%(first_name)s, %(last_name)s, %(email)s, %(phone)s, %(city_id)s)
        RETURNING id
        """
        
        person_ids = []
        for person_data in people_data:
            result = execute_query(people_query, person_data)
            person_ids.append(result[0][0])
        
        # Insert source relationships
        sources_query = """
        INSERT INTO people_sources (person_id, source_file_id, row_number, raw_data)
        VALUES (%s, %s, %s, %s)
        """
        
        source_params = []
        for person_id, source_data in zip(person_ids, sources_data):
            source_params.append((
                person_id,
                source_data['file_id'],
                source_data['row_number'],
                str(source_data['raw_data'])  # Convert dict to string
            ))
        
        execute_many(sources_query, source_params)
        self.processed_count += len(person_ids)
    
    def _clean_string(self, value) -> str:
        """Clean and normalize string values."""
        if pd.isna(value):
            return ''
        return str(value).strip()
    
    def _clean_phone(self, value) -> str:
        """Clean and validate phone numbers."""
        if pd.isna(value):
            return ''
        
        phone_str = str(value).strip()
        if not phone_str:
            return ''
        
        try:
            # Parse phone number (assuming US numbers)
            parsed = phonenumbers.parse(phone_str, "US")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            pass
        
        # Return original if parsing failed
        return phone_str 