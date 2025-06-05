#!/usr/bin/env python3
"""
PDF Text & Name Extractor

This script extracts all text from PDF files and optionally filters for name-like patterns.
Supports multiple PDF libraries for maximum compatibility.

Usage:
  python pdf_text_extractor.py input.pdf output.txt [--names-only]
  python pdf_text_extractor.py temp/2GPList.pdf extracted_names.txt --names-only
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set

def extract_with_pypdf(pdf_path: Path) -> str:
    """Extract text using PyPDF2/pypdf library."""
    try:
        import pypdf
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except ImportError:
        return None
    except Exception as e:
        print(f"Error with pypdf: {e}")
        return None

def extract_with_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber library."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        return None
    except Exception as e:
        print(f"Error with pdfplumber: {e}")
        return None

def extract_with_pymupdf(pdf_path: Path) -> str:
    """Extract text using PyMuPDF (fitz) library."""
    try:
        import fitz  # PyMuPDF
        text = ""
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except ImportError:
        return None
    except Exception as e:
        print(f"Error with PyMuPDF: {e}")
        return None

def extract_with_pdfminer(pdf_path: Path) -> str:
    """Extract text using pdfminer library."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(pdf_path))
    except ImportError:
        return None
    except Exception as e:
        print(f"Error with pdfminer: {e}")
        return None

def extract_pdf_text(pdf_path: Path) -> str:
    """Try multiple PDF libraries to extract text."""
    extractors = [
        ("PyMuPDF", extract_with_pymupdf),
        ("pdfplumber", extract_with_pdfplumber),
        ("pypdf", extract_with_pypdf),
        ("pdfminer", extract_with_pdfminer),
    ]
    
    for name, extractor in extractors:
        print(f"Trying {name}...")
        text = extractor(pdf_path)
        if text:
            print(f"✅ Successfully extracted text using {name}")
            return text
        elif text is None:
            print(f"❌ {name} not available (install: pip install {name.lower()})")
        else:
            print(f"⚠️ {name} failed to extract text")
    
    raise Exception("❌ All PDF extraction methods failed. Install one of: pypdf, pdfplumber, PyMuPDF, or pdfminer3k")

def clean_and_split_text(text: str) -> List[str]:
    """Clean text and split into individual strings/words."""
    # Remove extra whitespace and split by various delimiters
    lines = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Split by common delimiters
    words = re.split(r'[,;\n\r\t\s]+', lines)
    
    # Clean each word
    cleaned_words = []
    for word in words:
        # Remove special characters from start/end
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', word)
        if cleaned and len(cleaned) > 1:  # Skip single characters and empty
            cleaned_words.append(cleaned)
    
    return cleaned_words

def filter_name_candidates(words: List[str]) -> List[str]:
    """Filter words that look like names."""
    name_candidates = []
    
    # Pattern for name-like strings
    name_pattern = re.compile(r'^[A-Za-z][a-zA-Z\s\'-]{1,30}$')
    
    # Common non-name words to exclude
    exclude_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'page', 'pdf', 'document', 'file', 'text', 'data', 'list', 'table', 'row', 'column',
        'number', 'date', 'time', 'year', 'month', 'day', 'total', 'sum', 'count',
        'true', 'false', 'yes', 'no', 'null', 'none', 'empty', 'blank',
        'www', 'http', 'https', 'com', 'org', 'net', 'edu', 'gov'
    }
    
    for word in words:
        if (name_pattern.match(word) and 
            word.lower() not in exclude_words and
            not word.isdigit() and
            len(word) >= 2):
            name_candidates.append(word)
    
    return name_candidates

def extract_and_save(pdf_path: Path, output_path: Path, names_only: bool = False):
    """Main extraction function."""
    print(f"📄 Processing PDF: {pdf_path}")
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Extract text from PDF
    raw_text = extract_pdf_text(pdf_path)
    print(f"📝 Extracted {len(raw_text)} characters of text")
    
    # Process text
    all_words = clean_and_split_text(raw_text)
    print(f"🔤 Found {len(all_words)} words/strings")
    
    if names_only:
        # Filter for name-like patterns
        name_candidates = filter_name_candidates(all_words)
        final_output = sorted(set(name_candidates))  # Remove duplicates and sort
        print(f"👤 Identified {len(final_output)} potential names")
    else:
        # Output all unique strings
        final_output = sorted(set(all_words))  # Remove duplicates and sort
        print(f"📋 Total unique strings: {len(final_output)}")
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in final_output:
            f.write(f"{item}\n")
    
    print(f"💾 Saved results to: {output_path}")
    
    # Show sample results
    print(f"\n📋 Sample results (first 20):")
    for i, item in enumerate(final_output[:20], 1):
        print(f"  {i:2d}. {item}")
    
    if len(final_output) > 20:
        print(f"  ... and {len(final_output) - 20} more")

def install_requirements():
    """Show installation instructions for PDF libraries."""
    print("📦 To install PDF processing libraries, run one or more of:")
    print("  pip install pypdf")
    print("  pip install pdfplumber")
    print("  pip install PyMuPDF")
    print("  pip install pdfminer3k")
    print("\nRecommended: pip install pdfplumber PyMuPDF")

def main():
    parser = argparse.ArgumentParser(description="Extract text and names from PDF files")
    parser.add_argument("pdf_file", help="Input PDF file path")
    parser.add_argument("output_file", help="Output text file path")
    parser.add_argument("--names-only", action="store_true", 
                       help="Extract only name-like patterns (default: all text)")
    parser.add_argument("--install-help", action="store_true",
                       help="Show installation instructions for PDF libraries")
    
    args = parser.parse_args()
    
    if args.install_help:
        install_requirements()
        return
    
    try:
        pdf_path = Path(args.pdf_file)
        output_path = Path(args.output_file)
        
        extract_and_save(pdf_path, output_path, args.names_only)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTry: python pdf_text_extractor.py --install-help")
        sys.exit(1)

if __name__ == "__main__":
    main() 