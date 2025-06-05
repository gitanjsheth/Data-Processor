"""
make_training_data.py
Creates labeled_cells.csv with 1 000 NAME rows and 1 000 OTHER rows.
Edit the base lists to fine-tune variety; append real mistakes as you find
them and re-run candidate_harvester.py --train.
"""

import csv
import random
from pathlib import Path

first_names  = ["Rajesh", "Vishal", "Magan", "Ganesh", "Shalini", "Kiran",
                "Meena", "Rakesh", "Sumit", "Neha", "Pooja", "Farhan"]
middle_names = ["Kumar", "Mohanbhai", "Lal", "Bhai", "Prasad", "Chandra"]
surnames     = ["Sharma", "Patel", "Thacker", "Singh", "Desai", "Mehta",
                "Gupta", "Rao", "Iyer", "Nair", "Banerjee"]

address_parts = [
    "PLOT NO 42 WARD 4-B", "SADHU VASWANI NAGAR", "NR HAPPY HOME",
    "C/O GUJARAT NRE COKE LTD", "PHASE 2 INDUSTRIAL ESTATE", "TALUKA ANAND",
    "OPP BUS STAND", "SHOP 12, MARKET YARD", "WARD NO 7",
    "PVT LTD", "LLP", "ROAD NO 1"
]

other_misc = ["Chief Executive", "GSTIN 24ABCD1234E1Z5", "PIN 370205",
              "sales@company.com", "26°54'12\" N", "01-22-2024"]

def random_name():
    style = random.choice([1,2,3,4])
    if style == 1:   # first last
        return f"{random.choice(first_names)} {random.choice(surnames)}"
    if style == 2:   # last first
        return f"{random.choice(surnames)} {random.choice(first_names)}"
    if style == 3:   # first middle last
        return f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(surnames)}"
    # single surname or single first name
    return random.choice(first_names + surnames)

out = Path("labeled_cells.csv").open("w", newline="", encoding="utf-8")
writer = csv.writer(out)

# 1 000 NAME rows
for _ in range(1000):
    writer.writerow([random_name(), 1])

# 1 000 OTHER rows (addresses, org lines, misc)
for _ in range(800):
    part1 = random.choice(address_parts)
    part2 = random.choice(address_parts)
    writer.writerow([f"{part1} {part2}", 0])

for _ in range(200):
    writer.writerow([random.choice(other_misc), 0])

out.close()
print("labeled_cells.csv created with 2 000 rows")