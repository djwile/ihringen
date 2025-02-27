import pandas as pd


def koelner_phonetik(name):
    """
    Implements the Kölner Phonetik (Cologne Phonetics) algorithm for German phonetic matching.
    Adapted for historical German-Jewish names from the 19th century.
    
    Rules based on: https://de.wikipedia.org/wiki/Kölner_Phonetik
    """
    if not name:
        return "0000"
        
    # Convert to uppercase and split compound names
    name_parts = name.upper().split()
    result_codes = []
    
    for part in name_parts:
        # Initial preprocessing
        word = part.replace('Ä', 'AE').replace('Ö', 'OE').replace('Ü', 'UE')
        word = word.replace('ß', 'SS').replace('É', 'E').replace('È', 'E')
        
        if not word:
            continue
            
        code = []
        last_code = -1  # Initialize with invalid code
        length = len(word)
        
        # Process each character
        for i in range(length):
            c = word[i]
            
            # Rules for specific positions and combinations
            if c in 'AEIJOUYHW':
                current_code = 0
            elif c in 'B':
                current_code = 1
            elif c in 'P':
                if i + 1 < length and word[i + 1] == 'H':
                    current_code = 3
                else:
                    current_code = 1
            elif c in 'DT':
                if i + 1 < length and word[i + 1] in 'CSZ':
                    current_code = 8
                else:
                    current_code = 2
            elif c in 'F':
                current_code = 3
            elif c in 'GKQ':
                current_code = 4
            elif c == 'C':
                if i == 0:
                    if i + 1 < length and word[i + 1] in 'AHKLOQRUX':
                        current_code = 4
                    else:
                        current_code = 8
                else:
                    if i > 0 and word[i - 1] in 'SZ':
                        current_code = 8
                    elif i + 1 < length and word[i + 1] in 'AHKOQUX':
                        current_code = 4
                    else:
                        current_code = 8
            elif c in 'X':
                if i == 0:
                    current_code = 48
                else:
                    current_code = 8
            elif c in 'L':
                current_code = 5
            elif c in 'MN':
                current_code = 6
            elif c in 'R':
                current_code = 7
            elif c in 'SZ':
                current_code = 8
            else:
                current_code = -1
                
            # Only append if code is different from last code
            if current_code != -1 and current_code != last_code:
                code.append(str(current_code))
                last_code = current_code
        
        # Remove zeros except at start
        if code:
            result = code[0] + ''.join(c for c in code[1:] if c != '0')
            # Pad with zeros to make it 4 characters
            result = (result + '0' * 4)[:4]
            result_codes.append(result)
    
    return ' '.join(result_codes) if result_codes else '0000'

def apply_phonetic_filter(df, column, term):
    """
    Applies Kölner Phonetik filtering to a DataFrame column.
    Handles compound names by matching each part independently.
    """
    name_parts_phonetic = koelner_phonetik(term).split()
    
    # Create a mask for each part of the name
    mask = pd.Series([True] * len(df), index=df.index)
    for i, part_phonetic in enumerate(name_parts_phonetic):
        part_mask = df[column].apply(lambda x: 
            len(koelner_phonetik(x).split()) > i and 
            koelner_phonetik(x).split()[i] == part_phonetic)
        mask = mask & part_mask
    
    return df[mask]