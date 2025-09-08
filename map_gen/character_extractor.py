import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
import os
import json

class CharacterExtractor:
    def __init__(self, data_dir="../Middlemarch-8_books_byCJ"):
        self.data_dir = data_dir
        self.characters = {}
        self.interactions = defaultdict(list)
        self.character_contexts = defaultdict(list)
        self.dialogue_counts = defaultdict(int)
        self.co_occurrence_matrix = defaultdict(lambda: defaultdict(int))
        
    def extract_characters_from_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        characters = {}
        character_pattern = r'<item xml:id="([^"]+)"/>\s*<name>([^<]+)</name>'
        matches = re.findall(character_pattern, content)
        
        for char_id, char_name in matches:
            characters[char_id.strip()] = char_name.strip()
        
        return characters
    
    def extract_interactions_from_file(self, file_path, characters, proximity_window=500):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        interactions = defaultdict(list)
        dialogue_counts = defaultdict(int)
        contexts = defaultdict(list)
        
        mentions = []
        for char_id in characters:
            pattern = rf'who="#{char_id}"'
            for match in re.finditer(pattern, content):
                mentions.append((match.start(), char_id, 'interaction'))
        
        dialogue_pattern = r'<said who="#([^"]+)"[^>]*>(.*?)</said>'
        for match in re.finditer(dialogue_pattern, content, re.DOTALL):
            char_id = match.group(1)
            if char_id in characters:
                dialogue_counts[char_id] += 1
                dialogue_text = match.group(2).strip()
                contexts[char_id].append({
                    'type': 'dialogue',
                    'text': dialogue_text[:200],
                    'position': match.start()
                })
                mentions.append((match.start(), char_id, 'dialogue'))
        
        mentions.sort()
        
        co_occurrences = defaultdict(lambda: defaultdict(int))
        for i, (pos1, char1, type1) in enumerate(mentions):
            for j in range(i + 1, len(mentions)):
                pos2, char2, type2 = mentions[j]
                if pos2 - pos1 > proximity_window:
                    break
                if char1 != char2:
                    co_occurrences[char1][char2] += 1
                    co_occurrences[char2][char1] += 1
                    interactions[char1].append(char2)
                    interactions[char2].append(char1)
        
        return dict(interactions), dict(dialogue_counts), dict(contexts), dict(co_occurrences)
    
    def extract_character_descriptions(self, file_path, characters):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        descriptions = {}
        
        for char_id, char_name in characters.items():
            pattern = rf'who="#{char_id}"'
            match = re.search(pattern, content)
            
            if match:
                start = max(0, match.start() - 1000)
                end = min(len(content), match.end() + 1000)
                context = content[start:end]
                
                context = re.sub(r'<[^>]+>', '', context)
                context = re.sub(r'\s+', ' ', context).strip()
                
                descriptions[char_id] = context[:500]
        
        return descriptions
    
    def get_master_character_list(self):
        book1_file = os.path.join(self.data_dir, 'book1.xml')
        if os.path.exists(book1_file):
            return self.extract_characters_from_file(book1_file)
        return {}
    
    def process_book(self, book_number):
        book_file = os.path.join(self.data_dir, f'book{book_number}.xml')
        if not os.path.exists(book_file):
            return None
        
        characters = self.get_master_character_list()
        interactions, dialogue_counts, contexts, co_occurrences = self.extract_interactions_from_file(book_file, characters)
        descriptions = self.extract_character_descriptions(book_file, characters)
        
        return {
            'book': book_number,
            'characters': characters,
            'interactions': interactions,
            'dialogue_counts': dialogue_counts,
            'contexts': contexts,
            'co_occurrences': co_occurrences,
            'descriptions': descriptions
        }
    
    def process_all_books(self):
        all_data = []
        combined_characters = {}
        combined_interactions = defaultdict(list)
        combined_dialogue = defaultdict(int)
        combined_contexts = defaultdict(list)
        combined_co_occurrences = defaultdict(lambda: defaultdict(int))
        combined_descriptions = {}
        
        for book_num in range(1, 9):
            book_data = self.process_book(book_num)
            if book_data:
                all_data.append(book_data)
                
                combined_characters.update(book_data['characters'])
                
                for char, interactions in book_data['interactions'].items():
                    combined_interactions[char].extend(interactions)
                
                for char, count in book_data['dialogue_counts'].items():
                    combined_dialogue[char] += count
                
                for char, context_list in book_data['contexts'].items():
                    combined_contexts[char].extend(context_list)
                
                for char1, char_dict in book_data['co_occurrences'].items():
                    for char2, count in char_dict.items():
                        combined_co_occurrences[char1][char2] += count
                
                combined_descriptions.update(book_data['descriptions'])
        
        return {
            'individual_books': all_data,
            'combined': {
                'characters': combined_characters,
                'interactions': dict(combined_interactions),
                'dialogue_counts': dict(combined_dialogue),
                'contexts': dict(combined_contexts),
                'co_occurrences': {k: dict(v) for k, v in combined_co_occurrences.items()},
                'descriptions': combined_descriptions
            }
        }
    
    def save_enhanced_data(self, output_dir="outputs"):
        os.makedirs(output_dir, exist_ok=True)
        
        all_data = self.process_all_books()
        
        with open(os.path.join(output_dir, "character_data_raw.json"), 'w') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        for book_data in all_data['individual_books']:
            filename = f"book_{book_data['book']}_data.json"
            with open(os.path.join(output_dir, filename), 'w') as f:
                json.dump(book_data, f, indent=2, ensure_ascii=False)
        
        return all_data

if __name__ == "__main__":
    extractor = CharacterExtractor()
    data = extractor.save_enhanced_data()
    
    print(f"Processed {len(data['individual_books'])} books")
    print(f"Found {len(data['combined']['characters'])} unique characters")
    print(f"Total interactions: {sum(len(interactions) for interactions in data['combined']['interactions'].values())}")
    
    dialogue_sorted = sorted(data['combined']['dialogue_counts'].items(), 
                           key=lambda x: x[1], reverse=True)[:10]
    print("\nTop characters by dialogue count:")
    for char_id, count in dialogue_sorted:
        char_name = data['combined']['characters'].get(char_id, char_id)
        print(f"  {char_name}: {count}")