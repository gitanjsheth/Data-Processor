#!/usr/bin/env python3
"""
ML Engine Database Builder - Name Matcher Script

This script processes individual name components and finds corresponding full names
from a large names database, ensuring no duplicates based on component inclusion.

Author: AI Assistant
"""

import csv
import sys
from typing import Set, List, Dict, Optional

def read_input_names(input_file: str) -> List[str]:
    """Read individual name components from input CSV."""
    names = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    names.append(row[0].strip().lower())
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(names)} name components from {input_file}")
    return names

def find_matching_name(component: str, names_output_file: str, used_components: Set[str]) -> Optional[Dict[str, str]]:
    """
    Find the first full name in names_output.csv that contains the component,
    but only if none of its components are already used.
    """
    try:
        with open(names_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                first_name = row.get('first_name', '').strip().lower()
                middle_name = row.get('middle_name', '').strip().lower()
                last_name = row.get('last_name', '').strip().lower()
                
                # Check if any part of this full name exactly matches our component
                full_name_parts = [first_name, middle_name, last_name]
                component_found = any(component == part for part in full_name_parts if part)
                
                if component_found:
                    # Check if any component of this full name is already used
                    current_components = {part for part in full_name_parts if part}
                    
                    if not current_components.intersection(used_components):
                        # This is a new combination, return it
                        return {
                            'source_file': row.get('source_file', ''),
                            'source_sheet': row.get('source_sheet', ''),
                            'first_name': row.get('first_name', ''),
                            'middle_name': row.get('middle_name', ''),
                            'last_name': row.get('last_name', '')
                        }
    
    except FileNotFoundError:
        print(f"Error: Names output file '{names_output_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading names output file: {e}")
        sys.exit(1)
    
    return None

def process_names(input_file: str, names_output_file: str, output_file: str):
    """Main processing function."""
    print("Starting name matching process...")
    
    # Read input components
    input_components = read_input_names(input_file)
    
    # Track used components to avoid duplicates
    used_components: Set[str] = set()
    
    # Results to write
    results: List[Dict[str, str]] = []
    
    # Process each component
    processed_count = 0
    skipped_count = 0
    
    for i, component in enumerate(input_components, 1):
        print(f"Processing {i}/{len(input_components)}: '{component}'", end=' ')
        
        # Skip if this component is already used
        if component in used_components:
            print("-> SKIPPED (already used)")
            skipped_count += 1
            continue
        
        # Find matching full name
        match = find_matching_name(component, names_output_file, used_components)
        
        if match:
            results.append(match)
            
            # Add all components of this full name to used set
            first_name = match['first_name'].strip().lower()
            middle_name = match['middle_name'].strip().lower()
            last_name = match['last_name'].strip().lower()
            
            if first_name:
                used_components.add(first_name)
            if middle_name:
                used_components.add(middle_name)
            if last_name:
                used_components.add(last_name)
            
            print(f"-> FOUND: {match['first_name']} {match['middle_name']} {match['last_name']}")
            processed_count += 1
        else:
            print("-> NOT FOUND")
    
    # Write results to output file
    print(f"\nWriting {len(results)} results to {output_file}...")
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['source_file', 'source_sheet', 'first_name', 'middle_name', 'last_name']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(results)
            
        print(f"✅ Successfully wrote {len(results)} unique full names to {output_file}")
        print(f"📊 Statistics:")
        print(f"   - Input components: {len(input_components)}")
        print(f"   - Processed (found matches): {processed_count}")
        print(f"   - Skipped (already used): {skipped_count}")
        print(f"   - Not found: {len(input_components) - processed_count - skipped_count}")
        print(f"   - Final unique full names: {len(results)}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    input_file = "Input.csv"
    names_output_file = "names_output.csv"
    output_file = "matched_names_output.csv"
    
    print("=" * 60)
    print("ML Engine Database Builder - Name Matcher")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Names database: {names_output_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    process_names(input_file, names_output_file, output_file)
    
    print("\n🎉 Name matching process completed successfully!")

if __name__ == "__main__":
    main() 