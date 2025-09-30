import xml.etree.ElementTree as ET
import re
from pathlib import Path


class ContentExtractor:
    def __init__(self):
        pass
    
    def extract_characters_from_xml(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        characters = {}
        character_pattern = r'<item xml:id="([^"]+)"/>\s*<name>([^<]+)</name>'
        matches = re.findall(character_pattern, content)
        
        for char_id, char_name in matches:
            characters[char_id.strip()] = char_name.strip()
        
        return characters
    
    def build_chapter_position_map(self, content):
        chapter_map = []
        chapter_pattern = r'<div type="chapter" n="([^"]+)"[^>]*>'
        
        for match in re.finditer(chapter_pattern, content):
            chapter_num = match.group(1)
            try:
                if chapter_num == "0":
                    chapter_int = 1
                else:
                    chapter_int = int(chapter_num.lstrip('0') or '0')
            except ValueError:
                chapter_int = 1
            
            chapter_map.append({
                'position': match.start(),
                'chapter': chapter_int,
                'chapter_str': chapter_num
            })
        
        chapter_map.sort(key=lambda x: x['position'])
        return chapter_map
    
    def get_chapter_for_position(self, position, chapter_map):
        if not chapter_map:
            return 1
        
        current_chapter = 1
        for chapter_info in chapter_map:
            if position >= chapter_info['position']:
                current_chapter = chapter_info['chapter']
            else:
                break
        
        return current_chapter
    
    def extract_all_content_blocks(self, file_path, characters, book_number):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_blocks = []
        global_index = 1
        
        chapter_map = self.build_chapter_position_map(content)
        all_elements = []
        
        dialogue_pattern = r'<said who="#([^"]+)"[^>]*>(.*?)</said>'
        for match in re.finditer(dialogue_pattern, content, re.DOTALL):
            char_id = match.group(1)
            dialogue_text = match.group(2).strip()
            
            if char_id in characters:
                clean_text = re.sub(r'<[^>]+>', '', dialogue_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if clean_text and len(clean_text.strip()) > 3:
                    all_elements.append({
                        'position': match.start(),
                        'end_position': match.end(),
                        'type': 'dialogue',
                        'character_id': char_id,
                        'character_name': characters[char_id],
                        'text': clean_text
                    })
        
        heading_patterns = [
            (r'<head[^>]*>(.*?)</head>', 'chapter_title'),
            (r'<H1[^>]*>(.*?)</H1>', 'main_title'),
            (r'<H2[^>]*>(.*?)</H2>', 'subtitle'),
            (r'<H3[^>]*>(.*?)</H3>', 'section_title'),
            (r'<epigraph[^>]*>(.*?)</epigraph>', 'epigraph')
        ]
        
        for pattern, element_type in heading_patterns:
            for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                heading_text = re.sub(r'<[^>]+>', '', match.group(1))
                heading_text = re.sub(r'\s+', ' ', heading_text).strip()
                
                if heading_text and len(heading_text.strip()) > 2:
                    all_elements.append({
                        'position': match.start(),
                        'end_position': match.end(),
                        'type': element_type,
                        'character_id': 'NARRATOR',
                        'character_name': 'Narrator',
                        'text': heading_text.strip()
                    })
        
        temp_content = content
        temp_content = re.sub(dialogue_pattern, '', temp_content, flags=re.DOTALL)
        
        for pattern, _ in heading_patterns:
            temp_content = re.sub(pattern, '', temp_content, flags=re.DOTALL | re.IGNORECASE)
        
        paragraph_pattern = r'<P[^>]*>(.*?)</P>'
        for match in re.finditer(paragraph_pattern, temp_content, re.DOTALL | re.IGNORECASE):
            para_text = re.sub(r'<[^>]+>', '', match.group(1))
            para_text = re.sub(r'\s+', ' ', para_text).strip()
            
            if para_text and len(para_text) > 20:
                original_match = re.search(re.escape(match.group(0)), content)
                if original_match:
                    all_elements.append({
                        'position': original_match.start(),
                        'end_position': original_match.end(),
                        'type': 'narrative',
                        'character_id': 'NARRATOR',
                        'character_name': 'Narrator',
                        'text': para_text
                    })
        
        all_elements.sort(key=lambda x: x['position'])
        
        for element in all_elements:
            chapter_number = self.get_chapter_for_position(element['position'], chapter_map)
            content_blocks.append({
                'global_index': global_index,
                'book_number': book_number,
                'chapter_number': chapter_number,
                'content_type': element['type'],
                'character_id': element['character_id'],
                'character_name': element['character_name'],
                'text': element['text'],
                'position': element['position']
            })
            global_index += 1
        
        grouped_blocks = self.group_continuous_blocks(content_blocks)
        return grouped_blocks
    
    def group_continuous_blocks(self, content_blocks):
        grouped_blocks = []
        i = 0
        
        title_types = {'main_title', 'subtitle', 'section_title', 'chapter_title'}
        narrative_types = {'narrative'}
        
        while i < len(content_blocks):
            current_block = content_blocks[i]
            
            if (current_block['character_id'] == 'NARRATOR' and 
                current_block['content_type'] in title_types):
                
                title_group = [current_block]
                j = i + 1
                
                while (j < len(content_blocks) and 
                       content_blocks[j]['character_id'] == 'NARRATOR' and
                       content_blocks[j]['content_type'] in title_types and
                       content_blocks[j]['chapter_number'] == current_block['chapter_number']):
                    title_group.append(content_blocks[j])
                    j += 1
                
                if len(title_group) > 1:
                    combined_text = '. '.join([block['text'] for block in title_group])
                    
                    combined_block = {
                        'global_index': current_block['global_index'],
                        'book_number': current_block['book_number'],
                        'chapter_number': current_block['chapter_number'],
                        'content_type': 'title_combined',
                        'character_id': 'NARRATOR',
                        'character_name': 'Narrator',
                        'text': combined_text,
                        'position': current_block['position'],
                        'original_block_count': len(title_group),
                        'original_indices': [block['global_index'] for block in title_group],
                        'original_types': [block['content_type'] for block in title_group]
                    }
                    
                    grouped_blocks.append(combined_block)
                    i = j
                else:
                    grouped_blocks.append(current_block)
                    i += 1
            
            elif (current_block['character_id'] == 'NARRATOR' and 
                  current_block['content_type'] in narrative_types):
                
                narrator_group = [current_block]
                j = i + 1
                
                while (j < len(content_blocks) and 
                       content_blocks[j]['character_id'] == 'NARRATOR' and
                       content_blocks[j]['content_type'] in narrative_types and
                       content_blocks[j]['chapter_number'] == current_block['chapter_number']):
                    narrator_group.append(content_blocks[j])
                    j += 1
                
                if len(narrator_group) > 1:
                    combined_text = ' '.join([block['text'] for block in narrator_group])
                    
                    combined_block = {
                        'global_index': current_block['global_index'],
                        'book_number': current_block['book_number'],
                        'chapter_number': current_block['chapter_number'],
                        'content_type': 'narrative_combined',
                        'character_id': 'NARRATOR',
                        'character_name': 'Narrator',
                        'text': combined_text,
                        'position': current_block['position'],
                        'original_block_count': len(narrator_group),
                        'original_indices': [block['global_index'] for block in narrator_group]
                    }
                    
                    grouped_blocks.append(combined_block)
                    i = j
                else:
                    grouped_blocks.append(current_block)
                    i += 1
            else:
                grouped_blocks.append(current_block)
                i += 1
        
        return grouped_blocks