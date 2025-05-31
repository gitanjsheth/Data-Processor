"""City export module for generating Excel reports."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from .config import EXPORT_DIR
    from .db import execute_query
except ImportError:
    from config import EXPORT_DIR
    from db import execute_query

def export_city(city_name: str) -> Path:
    """
    Export all people from a specific city to an Excel file.
    
    Args:
        city_name: Name of the city to export
        
    Returns:
        Path to the generated Excel file
    """
    # Query for city and people data
    query = """
    SELECT 
        p.first_name,
        p.last_name,
        p.email,
        p.phone,
        c.name as city_name,
        sf.filename as source_file,
        ps.row_number,
        sf.created_at as file_date
    FROM people p
    JOIN cities c ON p.city_id = c.id
    LEFT JOIN people_sources ps ON p.id = ps.person_id
    LEFT JOIN source_files sf ON ps.source_file_id = sf.id
    WHERE c.name ILIKE %s
    ORDER BY p.last_name, p.first_name
    """
    
    results = execute_query(query, (f"%{city_name}%",))
    
    if not results:
        # Create empty file if no results
        df = pd.DataFrame(columns=[
            'first_name', 'last_name', 'email', 'phone', 
            'city_name', 'source_file', 'row_number', 'file_date'
        ])
    else:
        # Convert results to DataFrame
        df = pd.DataFrame(results, columns=[
            'first_name', 'last_name', 'email', 'phone',
            'city_name', 'source_file', 'row_number', 'file_date'
        ])
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_city_name = "".join(c for c in city_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_city_name = safe_city_name.replace(' ', '_')
    filename = f"export_{safe_city_name}_{timestamp}.xlsx"
    
    # Ensure export directory exists
    export_path = Path(EXPORT_DIR)
    export_path.mkdir(parents=True, exist_ok=True)
    
    # Full file path
    file_path = export_path / filename
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, sheet_name='People', index=False)
        
        # Summary sheet
        summary_data = _generate_summary(df, city_name)
        summary_df = pd.DataFrame(summary_data.items(), columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Source files sheet
        if not df.empty:
            source_summary = df.groupby(['source_file', 'file_date']).size().reset_index(name='record_count')
            source_summary.to_excel(writer, sheet_name='Source_Files', index=False)
    
    print(f"Exported {len(df)} records to {file_path}")
    return file_path

def export_all_cities() -> Path:
    """
    Export people from all cities to a single Excel file with separate sheets per city.
    
    Returns:
        Path to the generated Excel file
    """
    # Get all cities
    cities_query = "SELECT id, name FROM cities ORDER BY name"
    cities = execute_query(cities_query)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_all_cities_{timestamp}.xlsx"
    file_path = Path(EXPORT_DIR) / filename
    
    # Ensure export directory exists
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        total_records = 0
        
        # Create a sheet for each city
        for city_id, city_name in cities:
            city_data = _get_city_data(city_name)
            if not city_data.empty:
                safe_sheet_name = "".join(c for c in city_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_sheet_name = safe_sheet_name.replace(' ', '_')[:31]  # Excel sheet name limit
                
                city_data.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                total_records += len(city_data)
        
        # Create summary sheet
        summary_data = {
            'Total Cities': len(cities),
            'Total Records': total_records,
            'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'File Name': filename
        }
        summary_df = pd.DataFrame(summary_data.items(), columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"Exported {total_records} records from {len(cities)} cities to {file_path}")
    return file_path

def export_source_file_summary() -> Path:
    """
    Export a summary of all source files and their processing status.
    
    Returns:
        Path to the generated Excel file
    """
    query = """
    SELECT 
        filename,
        file_path,
        file_size,
        status,
        processed_count,
        error_count,
        created_at,
        processed_at,
        error_message
    FROM source_files
    ORDER BY created_at DESC
    """
    
    results = execute_query(query)
    
    if results:
        df = pd.DataFrame(results, columns=[
            'filename', 'file_path', 'file_size', 'status',
            'processed_count', 'error_count', 'created_at',
            'processed_at', 'error_message'
        ])
    else:
        df = pd.DataFrame()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"source_files_summary_{timestamp}.xlsx"
    file_path = Path(EXPORT_DIR) / filename
    
    # Ensure export directory exists
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Source_Files', index=False)
        
        # Add summary statistics
        if not df.empty:
            summary_stats = {
                'Total Files': len(df),
                'Completed Files': len(df[df['status'] == 'completed']),
                'Failed Files': len(df[df['status'] == 'failed']),
                'Files with Errors': len(df[df['status'] == 'completed_with_errors']),
                'Total Records Processed': df['processed_count'].sum(),
                'Total Errors': df['error_count'].sum(),
                'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            summary_df = pd.DataFrame(summary_stats.items(), columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"Exported source files summary to {file_path}")
    return file_path

def _get_city_data(city_name: str) -> pd.DataFrame:
    """Get all people data for a specific city."""
    query = """
    SELECT 
        p.first_name,
        p.last_name,
        p.email,
        p.phone,
        c.name as city_name,
        sf.filename as source_file,
        ps.row_number
    FROM people p
    JOIN cities c ON p.city_id = c.id
    LEFT JOIN people_sources ps ON p.id = ps.person_id
    LEFT JOIN source_files sf ON ps.source_file_id = sf.id
    WHERE c.name = %s
    ORDER BY p.last_name, p.first_name
    """
    
    results = execute_query(query, (city_name,))
    
    if results:
        return pd.DataFrame(results, columns=[
            'first_name', 'last_name', 'email', 'phone',
            'city_name', 'source_file', 'row_number'
        ])
    else:
        return pd.DataFrame()

def _generate_summary(df: pd.DataFrame, city_name: str) -> dict:
    """Generate summary statistics for a city export."""
    if df.empty:
        return {
            'City Name': city_name,
            'Total Records': 0,
            'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Records with Email': 0,
            'Records with Phone': 0,
            'Unique Source Files': 0
        }
    
    return {
        'City Name': city_name,
        'Total Records': len(df),
        'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Records with Email': len(df[df['email'].notna() & (df['email'] != '')]),
        'Records with Phone': len(df[df['phone'].notna() & (df['phone'] != '')]),
        'Unique Source Files': df['source_file'].nunique() if 'source_file' in df.columns else 0,
        'Date Range': f"{df['file_date'].min()} to {df['file_date'].max()}" if 'file_date' in df.columns and not df['file_date'].isna().all() else 'N/A'
    } 