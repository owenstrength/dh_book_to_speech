import xml.etree.ElementTree as ET
import re
from collections import defaultdict
import os

def extract_characters_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    characters = {}
    
    character_pattern = r'<item xml:id="([^"]+)"/>\s*<name>([^<]+)</name>'
    matches = re.findall(character_pattern, content)
    
    for char_id, char_name in matches:
        characters[char_id.strip()] = char_name.strip()
    
    return characters

def extract_interactions_from_file(file_path, characters):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    interactions = defaultdict(list)
    
    interaction_pattern = r'who="#([^"]+)"'
    matches = re.findall(interaction_pattern, content)
    
    for i in range(len(matches) - 1):
        char1 = matches[i]
        char2 = matches[i + 1]
        
        if char1 in characters and char2 in characters and char1 != char2:
            interactions[char1].append(char2)
            interactions[char2].append(char1)
    
    return dict(interactions)

def process_middlemarch_data(data_dir):
    all_characters = {}
    all_interactions = defaultdict(list)
    
    for i in range(1, 9):
        book_file = os.path.join(data_dir, f'book{i}.xml')
        if os.path.exists(book_file):
            characters = extract_characters_from_file(book_file)
            all_characters.update(characters)
            
            interactions = extract_interactions_from_file(book_file, all_characters)
            for char, connected_chars in interactions.items():
                all_interactions[char].extend(connected_chars)
    
    for char in all_interactions:
        all_interactions[char] = list(set(all_interactions[char]))
    
    return all_characters, dict(all_interactions)

if __name__ == "__main__":
    data_dir = "../Middlemarch-8_books_byCJ"
    characters, interactions = process_middlemarch_data(data_dir)
    
    print(f"Found {len(characters)} characters:")
    for char_id, name in characters.items():
        print(f"  {char_id}: {name}")
    
    print(f"\nFound interactions for {len(interactions)} characters")