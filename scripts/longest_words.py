#!/usr/bin/env python3
"""
Scan a CSV, ignore the first column if it is the phone list,
and print the N longest unique alphabetic words found.

Usage:
    python longest_words.py input.csv 30
"""

import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

ALPHA_RE = re.compile(r"[A-Za-z][A-Za-z'\-]{1,}")

def longest_words(csv_path: Path, top_n: int = 30, skip_first_col: bool = True):
    seen = defaultdict(int)      # word -> length (len is key anyway)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            cells = row[1:] if skip_first_col else row
            for cell in cells:
                for token in ALPHA_RE.findall(cell):
                    token_clean = token.strip("'- ")
                    if token_clean:
                        seen[token_clean] = len(token_clean)

    # sort by length desc, then alphabetical for ties
    longest = sorted(seen.items(), key=lambda x: (-x[1], x[0]))[:top_n]
    return longest

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python longest_words.py input.csv [N_top_words]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    N = int(sys.argv[2]) if len(sys.argv) == 3 else 30

    for word, length in longest_words(input_file, N):
        print(f"{length:>2}  {word}")