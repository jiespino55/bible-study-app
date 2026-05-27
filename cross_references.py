import csv

def parse_reference(ref):
    # Converts "Gen.1.1" to "Genesis 1:1"
    book_map = {
        'Gen': 'Genesis', 'Exod': 'Exodus', 'Lev': 'Leviticus',
        'Num': 'Numbers', 'Deut': 'Deuteronomy', 'Josh': 'Joshua',
        'Judg': 'Judges', 'Ruth': 'Ruth', '1Sam': '1 Samuel',
        '2Sam': '2 Samuel', '1Kgs': '1 Kings', '2Kgs': '2 Kings',
        '1Chr': '1 Chronicles', '2Chr': '2 Chronicles', 'Ezra': 'Ezra',
        'Neh': 'Nehemiah', 'Esth': 'Esther', 'Job': 'Job',
        'Ps': 'Psalms', 'Prov': 'Proverbs', 'Eccl': 'Ecclesiastes',
        'Song': 'Song of Solomon', 'Isa': 'Isaiah', 'Jer': 'Jeremiah',
        'Lam': 'Lamentations', 'Ezek': 'Ezekiel', 'Dan': 'Daniel',
        'Hos': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obadiah',
        'Jonah': 'Jonah', 'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk',
        'Zeph': 'Zephaniah', 'Hag': 'Haggai', 'Zech': 'Zechariah',
        'Mal': 'Malachi', 'Matt': 'Matthew', 'Mark': 'Mark', 'Luke': 'Luke',
        'John': 'John', 'Acts': 'Acts', 'Rom': 'Romans', '1Cor': '1 Corinthians',
        '2Cor': '2 Corinthians', 'Gal': 'Galatians', 'Eph': 'Ephesians',
        'Phil': 'Philippians', 'Col': 'Colossians', '1Thess': '1 Thessalonians',
        '2Thess': '2 Thessalonians', '1Tim': '1 Timothy', '2Tim': '2 Timothy',
        'Titus': 'Titus', 'Phlm': 'Philemon', 'Heb': 'Hebrews', 'Jas': 'James',
        '1Pet': '1 Peter', '2Pet': '2 Peter', '1John': '1 John', '2John': '2 John',
        '3John': '3 John', 'Jude': 'Jude', 'Rev': 'Revelation'
    }
    
    # Handle ranges like "Prov.8.22-Prov.8.30" - just take the first verse
    ref = ref.split('-')[0]
    
    parts = ref.split('.')
    if len(parts) < 3:
        return None
    
    book_abbrev = parts[0]
    chapter = parts[1]
    verse = parts[2]
    
    book_name = book_map.get(book_abbrev)
    if not book_name:
        return None
    
    return f"{book_name} {chapter}:{verse}"

def load_cross_references():
    cross_refs = {}
    
    with open('cross_references.txt', 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) < 3:
                continue
            
            from_verse = parse_reference(row[0])
            to_verse = parse_reference(row[1])
            votes = int(row[2]) if row[2].isdigit() else 0
            
            if not from_verse or not to_verse:
                continue
            
            if from_verse not in cross_refs:
                cross_refs[from_verse] = []
            
            cross_refs[from_verse].append({
                "reference": to_verse,
                "votes": votes
            })
    
    # Sort each verse's cross refs by votes
    for verse in cross_refs:
        cross_refs[verse].sort(key=lambda x: x['votes'], reverse=True)
    
    return cross_refs

# Test it
cross_refs = load_cross_references()
print(f"Total verses with cross references: {len(cross_refs)}")
print(f"\nCross references for John 3:16:")
for ref in cross_refs.get('John 3:16', [])[:5]:
    print(f"  {ref['reference']} (votes: {ref['votes']})")