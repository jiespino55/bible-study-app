import json
import re

def load_strongs():
    # Load Greek dictionary
    with open('strongs-master/greek/strongs-greek-dictionary.js', 'r') as f:
        content = f.read()
    
    # Extract the JSON object from the JS file
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    greek = json.loads(match.group(1))
    
    # Load Hebrew dictionary
    with open('strongs-master/hebrew/strongs-hebrew-dictionary.js', 'r') as f:
        content = f.read()
    
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    hebrew = json.loads(match.group(1))
    
    print(f"Loaded {len(greek)} Greek words")
    print(f"Loaded {len(hebrew)} Hebrew words")
    
    return greek, hebrew

greek, hebrew = load_strongs()

# Test a few lookups
print("\nG26 (agape - love):")
print(greek['G26'])

print("\nH157 (ahab - love):")
print(hebrew['H157'])