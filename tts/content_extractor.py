import xml.etree.ElementTree as ET
import re
from pathlib import Path


class ContentExtractor:
    def __init__(self):
        pass
    
    def detect_book_format(self, file_path):
        """
        Detect if the book format is the Middlemarch format (with character definitions and <said> tags)
        or a generic format (with <q> tags for dialogue but no character IDs)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if there are character definitions in <item xml:id="..."><name>...</name> format
        has_character_definitions = bool(re.search(r'<item xml:id="[^"]+"/>.*?<name>[^<]+</name>', content, re.DOTALL))
        
        # Check if there are <said who="#..."> tags
        has_said_tags = bool(re.search(r'<said who="#[^"]+">', content))
        
        # Check if there are <q> tags (for dialogue) but no said tags
        has_q_tags = bool(re.search(r'<q>', content))
        
        if has_character_definitions and has_said_tags:
            return "middlemarch"
        elif has_q_tags and not has_said_tags:
            return "generic"  # This covers Romola and similar books
        else:
            return "middlemarch"  # Default to middlemarch for safety
    
    def extract_characters_from_xml(self, file_path):
        """
        Extract characters from XML file, supporting both Middlemarch and generic formats
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        book_format = self.detect_book_format(file_path)
        
        if book_format == "middlemarch":
            # Extract characters in the Middlemarch format
            characters = {}
            character_pattern = r'<item xml:id="([^"]+)"[^>]*>\s*<name>([^<]+)</name>'
            matches = re.findall(character_pattern, content, re.DOTALL)
            
            for char_id, char_name in matches:
                characters[char_id.strip()] = char_name.strip()
            
            return characters
        else:
            # For generic format, we need to extract character names from dialogue tags
            # In generic format like Romola, character names are in <name> tags within <q> tags
            # or in general text, so we'll extract all names and later identify speakers from context
            names = set()
            name_pattern = r'<name>([^<]+)</name>'
            name_matches = re.findall(name_pattern, content, re.DOTALL)
            
            for name in name_matches:
                clean_name = name.strip()
                if clean_name:  # Skip empty names
                    names.add(clean_name)
            
            # Create character dictionary with unique IDs
            characters = {}
            for i, name in enumerate(sorted(names)):
                char_id = f"CHAR_{i+1:03d}"
                characters[char_id] = name
            
            return characters
    
    def extract_dialogue_blocks_generic(self, content, characters, book_number, chapter_map):
        """
        Extract dialogue blocks from generic format (like Romola) where dialogue is in <q> tags
        and character names are in <name> tags.
        """
        all_elements = []
        global_index = 1  # This will be updated by the main function later
        
        # Extract dialogue that is associated with a speaker context
        # Pattern: [Speaker] [verb]: <q>dialogue</q> or [Speaker] [verb] <q>dialogue</q>
        context_pattern = r'(<name>([^<]+)</name>\s*(?:said|replied|asked|answered|spoke|cried|called|whispered|exclaimed|remarked|observed|stated|declared|added|continued|began|returned|responded|rejoined|inquired|called out|observed|remarked|stated|declared|added|continued|began|returned|responded|cried out|shouted|called|whispered|said|replied|asked|answered|spoke)\s*:\s*|<name>([^<]+)</name>\s+(?:said|replied|asked|answered|spoke|cried|called|whispered|exclaimed|remarked|observed|stated|declared|added|continued|began|returned|responded|rejoined|inquired|called out|observed|remarked|stated|declared|added|continued|began|returned|responded|cried out|shouted|called|whispered))\s*<q[^>]*>(.*?)</q>'
        
        for match in re.finditer(context_pattern, content, re.DOTALL | re.IGNORECASE):
            # Get the character name from either group 2 or 3 (depending on which pattern matched)
            potential_speaker = (match.group(2) or match.group(3)).strip()
            dialogue_text = match.group(4).strip()
            
            if potential_speaker:  # If we have a potential speaker
                clean_text = re.sub(r'<[^>]+>', '', dialogue_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if clean_text and len(clean_text) > 3:
                    character_id = None
                    character_name = None
                    
                    # Find character ID that matches this name
                    for char_id, char_name in characters.items():
                        if potential_speaker.lower() in char_name.lower() or char_name.lower() in potential_speaker.lower():
                            character_id = char_id
                            character_name = char_name
                            break
                    
                    # If we couldn't find a matching name, assign to narrator
                    if character_id is None:
                        character_id = "NARRATOR"
                        character_name = "Narrator"
                    
                    all_elements.append({
                        'position': match.start(),
                        'end_position': match.end(),
                        'type': 'dialogue',
                        'character_id': character_id,
                        'character_name': character_name,
                        'text': clean_text
                    })
        
        # Extract remaining <q> tags that don't have clear speaker context
        # These might be dialogue without an explicit speaker tag
        dialogue_pattern = r'<q[^>]*>(.*?)</q>'
        for match in re.finditer(dialogue_pattern, content, re.DOTALL):
            dialogue_text = match.group(1).strip()
            
            # Check if this match is already covered by the context pattern above
            already_processed = any(match.start() >= elem['position'] and match.end() <= elem['end_position'] 
                                  for elem in all_elements)
            
            if not already_processed:
                # Clean the dialogue text
                clean_text = re.sub(r'<[^>]+>', '', dialogue_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if clean_text and len(clean_text) > 3:
                    # Look for names in the dialogue content to identify possible speaker
                    name_matches = re.findall(r'<name>([^<]+)</name>', dialogue_text, re.IGNORECASE)
                    if name_matches:
                        # Find the first name in the dialogue which is likely the speaker
                        potential_speaker = name_matches[0].strip()
                        
                        # Find the character ID that matches this name
                        character_id = None
                        character_name = None
                        for char_id, char_name in characters.items():
                            if potential_speaker.lower() in char_name.lower() or char_name.lower() in potential_speaker.lower():
                                character_id = char_id
                                character_name = char_name
                                break
                        
                        if character_id is None:
                            character_id = "NARRATOR"
                            character_name = "Narrator"
                    else:
                        # Default to narrator if we can't identify speaker
                        character_id = "NARRATOR"
                        character_name = "Narrator"
                    
                    all_elements.append({
                        'position': match.start(),
                        'end_position': match.end(),
                        'type': 'dialogue',
                        'character_id': character_id,
                        'character_name': character_name,
                        'text': clean_text
                    })
        
        return all_elements
    
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
        """
        Extract all content blocks (narrative and dialogue) from the XML file,
        supporting both Middlemarch and generic formats.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_blocks = []
        global_index = 1
        
        chapter_map = self.build_chapter_position_map(content)
        all_elements = []
        
        book_format = self.detect_book_format(file_path)
        
        if book_format == "middlemarch":
            # Use the original Middlemarch-specific extraction
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
        else:
            # Use the generic extraction for books like Romola
            all_elements = self.extract_dialogue_blocks_generic(content, characters, book_number, chapter_map)
        
        # Extract headings for all formats
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
        
        # Extract narrative text (non-dialogue)
        # For Middlemarch format, remove dialogue tags we already processed
        temp_content = content
        
        if book_format == "middlemarch":
            dialogue_pattern = r'<said who="#[^"]+"[^>]*>.*?</said>'
            temp_content = re.sub(dialogue_pattern, '', temp_content, flags=re.DOTALL)
        else:
            # For generic format, remove q tags we already processed
            dialogue_pattern = r'<q[^>]*>.*?</q>'
            temp_content = re.sub(dialogue_pattern, '', temp_content, flags=re.DOTALL)
        
        # Remove heading tags from temp content to avoid duplication
        for pattern, _ in heading_patterns:
            temp_content = re.sub(pattern, '', temp_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract paragraphs - this is format-agnostic
        # We need to handle both uppercase <P> and lowercase <p>
        paragraph_pattern = r'<[Pp][^>]*>(.*?)</[Pp]>'
        for match in re.finditer(paragraph_pattern, temp_content, re.DOTALL | re.IGNORECASE):
            para_text = re.sub(r'<[^>]+>', '', match.group(1))
            para_text = re.sub(r'\s+', ' ', para_text).strip()
            
            if para_text and len(para_text) > 20:
                original_match = re.search(re.escape(match.group(0)), content, re.DOTALL | re.IGNORECASE)
                if original_match:
                    all_elements.append({
                        'position': original_match.start(),
                        'end_position': original_match.end(),
                        'type': 'narrative',
                        'character_id': 'NARRATOR',
                        'character_name': 'Narrator',
                        'text': para_text
                    })
        
        # Sort all elements by position in the document
        all_elements.sort(key=lambda x: x['position'])
        
        # Create content blocks with chapter information
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