import xml.etree.ElementTree as ET
import re
import json
import os
from pathlib import Path
from openai import OpenAI
from collections import defaultdict
import hashlib

class TTSPipeline:
    def __init__(self, data_dir="/Users/owenstrength/Documents/school/senior_design/character_maps/Middlemarch-8_books_byCJ", output_dir="audio_output", api_key=None):
        print(f"Initializing TTSPipeline with data_dir: {data_dir}")
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Please either:\n"
                    "1. Set OPENAI_API_KEY environment variable, or\n"
                    "2. Pass api_key parameter to TTSPipeline(api_key='your-key')"
                )
            self.client = OpenAI()
        
        # Available OpenAI voices
        self.male_voices = ["echo", "fable", "onyx"]
        self.female_voices = ["alloy", "nova", "shimmer", "coral"]
        
        self.character_voices = {}
        self.character_genders = {}
        self.character_descriptions = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_characters_from_xml(self, file_path):
        """Extract character definitions from XML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        characters = {}
        character_pattern = r'<item xml:id="([^"]+)"/>\s*<name>([^<]+)</name>'
        matches = re.findall(character_pattern, content)
        
        for char_id, char_name in matches:
            characters[char_id.strip()] = char_name.strip()
        
        return characters
    
    def determine_character_gender(self, char_name, char_id):
        """Use LLM to determine character gender"""
        print(f"Determining gender for {char_name}...")
        
        prompt = f"""
        Based on the character name "{char_name}" from the novel Middlemarch by George Eliot, 
        determine if this character is male or female. Respond with only "male" or "female".
        
        Character name: {char_name}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            gender = response.choices[0].message.content.strip().lower()
            print(f"  -> {char_name}: {gender}")
            return gender if gender in ["male", "female"] else "unknown"
        except Exception as e:
            print(f"Error determining gender for {char_name}: {e}")
            return "unknown"
    
    def generate_character_description(self, char_name, char_id):
        """Generate character description for TTS instructions"""
        print(f"Generating description for {char_name}...")
        
        prompt = f"""
        Create a brief character description for "{char_name}" from Middlemarch by George Eliot.
        Focus on their personality, social status, and speaking style. Keep it under 100 words.
        This will be used for text-to-speech voice instructions.
        
        Character: {char_name}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            description = response.choices[0].message.content.strip()
            print(f"  -> Description generated for {char_name}")
            return description
        except Exception as e:
            print(f"Error generating description for {char_name}: {e}")
            return f"A character from Middlemarch named {char_name}"
    
    def assign_voices_to_characters(self, characters):
        """Assign consistent voices to characters based on gender"""
        print(f"\n=== Assigning voices to {len(characters)} characters ===")
        male_count = 0
        female_count = 0
        
        for i, (char_id, char_name) in enumerate(characters.items(), 1):
            print(f"\n[{i}/{len(characters)}] Processing {char_name} ({char_id})")
            
            # Determine gender
            gender = self.determine_character_gender(char_name, char_id)
            self.character_genders[char_id] = gender
            
            # Generate description
            description = self.generate_character_description(char_name, char_id)
            self.character_descriptions[char_id] = description
            
            # Assign voice
            if gender == "male":
                voice = self.male_voices[male_count % len(self.male_voices)]
                male_count += 1
            elif gender == "female":
                voice = self.female_voices[female_count % len(self.female_voices)]
                female_count += 1
            else:
                # Default to female voice for unknown
                voice = self.female_voices[female_count % len(self.female_voices)]
                female_count += 1
            
            self.character_voices[char_id] = voice
            print(f"✓ Assigned {voice} voice to {char_name} ({gender})")
        
        print(f"\n=== Voice assignment complete! ===")
    
    def analyze_dialogue_sentiment(self, dialogue_text):
        """Analyze sentiment and tone of dialogue for TTS instructions"""
        prompt = f"""
        Analyze the tone and emotion of this dialogue from Middlemarch. 
        Provide 2-3 descriptive words for how it should be spoken (e.g., "thoughtful and melancholic", "excited and passionate").
        
        Dialogue: "{dialogue_text[:200]}..."
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "conversational"
    
    def extract_all_content_blocks(self, file_path, characters, book_number):
        """Extract all content blocks (narrative + dialogue) from XML with global indexing"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_blocks = []
        global_index = 1
        
        # Find all content elements in document order
        all_elements = []
        
        # Find dialogue blocks
        dialogue_pattern = r'<said who="#([^"]+)"[^>]*>(.*?)</said>'
        for match in re.finditer(dialogue_pattern, content, re.DOTALL):
            char_id = match.group(1)
            dialogue_text = match.group(2).strip()
            
            if char_id in characters:
                clean_text = re.sub(r'<[^>]+>', '', dialogue_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if clean_text and len(clean_text.strip()) > 3:  # Ensure meaningful content
                    all_elements.append({
                        'position': match.start(),
                        'end_position': match.end(),
                        'type': 'dialogue',
                        'character_id': char_id,
                        'character_name': characters[char_id],
                        'text': clean_text
                    })
        
        # Find chapter headings and other structural elements
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
                
                if heading_text and len(heading_text.strip()) > 2:  # Ensure meaningful content
                    all_elements.append({
                        'position': match.start(),
                        'end_position': match.end(),
                        'type': element_type,
                        'character_id': 'NARRATOR',
                        'character_name': 'Narrator',
                        'text': heading_text.strip()
                    })
        
        # Find paragraph content (narrative text)
        # Remove dialogue and headings first, then extract paragraphs
        temp_content = content
        
        # Remove dialogue
        temp_content = re.sub(dialogue_pattern, '', temp_content, flags=re.DOTALL)
        
        # Remove headings
        for pattern, _ in heading_patterns:
            temp_content = re.sub(pattern, '', temp_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Find paragraphs
        paragraph_pattern = r'<P[^>]*>(.*?)</P>'
        for match in re.finditer(paragraph_pattern, temp_content, re.DOTALL | re.IGNORECASE):
            para_text = re.sub(r'<[^>]+>', '', match.group(1))
            para_text = re.sub(r'\s+', ' ', para_text).strip()
            
            if para_text and len(para_text) > 20:  # Skip very short paragraphs
                # Find original position in the full content
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
        
        # Sort all elements by position in the document
        all_elements.sort(key=lambda x: x['position'])
        
        # Convert to content blocks with global indexing
        for element in all_elements:
            content_blocks.append({
                'global_index': global_index,
                'book_number': book_number,
                'content_type': element['type'],
                'character_id': element['character_id'],
                'character_name': element['character_name'],
                'text': element['text'],
                'position': element['position']
            })
            global_index += 1
        
        return content_blocks
    
    def generate_speech_for_block(self, content_block, mode="multi_voice"):
        """Generate speech for a single content block (dialogue or narrative)"""
        global_index = content_block['global_index']
        book_number = content_block['book_number']
        char_id = content_block['character_id']
        char_name = content_block['character_name']
        text = content_block['text']
        content_type = content_block.get('content_type', 'dialogue')
        
        
        # Choose voice based on content type and mode
        if char_id == 'NARRATOR' or mode == "single_narrator":
            # Use narrator voice - bold, distinctive voice for all narrative content
            voice = "onyx"  # Deep, authoritative voice for narrator
            tts_input = text
            
            if content_type == 'chapter_title':
                instructions = f"Narrator reading chapter title with dramatic emphasis"
            elif content_type == 'main_title':
                instructions = f"Narrator reading main title with authority"
            elif content_type == 'epigraph':
                instructions = f"Narrator reading epigraph with reverent, thoughtful tone"
            elif content_type in ['subtitle', 'section_title']:
                instructions = f"Narrator reading section heading"
            elif content_type == 'narrative':
                instructions = f"Narrator reading narrative text"
            else:
                instructions = f"Narrator reading for {char_name}" if char_name != 'Narrator' else "Narrator"
                
        else:
            # Multi-voice mode for character dialogue
            voice = self.character_voices.get(char_id, "alloy")
            char_description = self.character_descriptions.get(char_id, f"A character named {char_name}")
            sentiment = self.analyze_dialogue_sentiment(text)
            
            tts_input = text
            instructions = f"{char_name} ({sentiment}): {char_description}"
        
        # Generate filename with content type
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        content_suffix = "narrative" if char_id == 'NARRATOR' else "dialogue"
        filename = f"{global_index:04d}_BOOK_{book_number:02d}_{char_id}_{content_suffix}_{text_hash}.mp3"
        speech_file_path = Path(self.output_dir) / filename
        
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=tts_input,
            )
            
            with open(speech_file_path, "wb") as f:
                f.write(response.content)
            
            return {
                'global_index': global_index,
                'book_number': book_number,
                'character_id': char_id,
                'character_name': char_name,
                'content_type': content_type,
                'voice': voice,
                'file_path': str(speech_file_path),
                'filename': filename,
                'text': text,
                'instructions': instructions
            }
        
        except Exception as e:
            print(f"Error generating speech for {char_name}: {e}")
            return None
    
    def process_book(self, book_number, mode="multi_voice"):
        """Process a single book and generate audio"""
        print(f"\n🎯 Starting processing for book {book_number} in {mode} mode...")
        
        print("📖 Loading character definitions from book1.xml...")
        book1_file = os.path.join(self.data_dir, 'book1.xml')
        characters = self.extract_characters_from_xml(book1_file)
        print(f"Found {len(characters)} characters in definition list")
        
        if not self.character_voices:
            self.assign_voices_to_characters(characters)
        else:
            print("Using previously assigned character voices")
        
        print(f"\n📚 Loading book {book_number}...")
        book_file = os.path.join(self.data_dir, f'book{book_number}.xml')
        if not os.path.exists(book_file):
            print(f"❌ Book {book_number} not found at {book_file}")
            return None
        
        print("📖 Extracting all content blocks (narrative + dialogue)...")
        content_blocks = self.extract_all_content_blocks(book_file, characters, book_number)
        print(f"Found {len(content_blocks)} total content blocks")
        
        if len(content_blocks) == 0:
            print("⚠️ No content found! Check XML format.")
            return None
        
        # Show content type distribution
        type_counts = {}
        char_counts = {}
        for block in content_blocks:
            content_type = block.get('content_type', 'unknown')
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            char_counts[block['character_name']] = char_counts.get(block['character_name'], 0) + 1
        
        print(f"\nContent type distribution:")
        for content_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {content_type}: {count} blocks")
            
        print(f"\nCharacter/Speaker distribution:")
        for char, count in sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:7]:
            print(f"  {char}: {count} blocks")
        
        print(f"\n🎙️ Generating audio for {len(content_blocks)} content blocks...")
        results = []
        for i, block in enumerate(content_blocks):
            if i % 10 == 0:  # Progress every 10 blocks
                print(f"Progress: {i+1}/{len(content_blocks)} ({(i+1)/len(content_blocks)*100:.1f}%)")
            result = self.generate_speech_for_block(block, mode)
            if result:
                results.append(result)
        
        metadata = {
            'book': book_number,
            'mode': mode,
            'character_voices': self.character_voices,
            'character_descriptions': self.character_descriptions,
            'character_genders': self.character_genders,
            'dialogue_count': len(results),
            'audio_files': results
        }
        
        metadata_file = Path(self.output_dir) / f"book_{book_number}_{mode}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Generated {len(results)} audio files for book {book_number}")
        print(f"📁 Metadata saved to: {metadata_file}")
        return metadata

if __name__ == "__main__":
    print("🚀 Starting TTS Pipeline...")
    print("Checking for API key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key not found!")
        print("Please set your API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr run with API key as parameter:")
        print("pipeline = TTSPipeline(api_key='your-key')")
        exit(1)
    
    print("✓ API key found")
    print("Initializing pipeline...")
    
    pipeline = TTSPipeline()
    print("✓ Pipeline initialized")
    
    result = pipeline.process_book(1, mode="multi_voice")
    
    # Optionally process in single narrator mode
    # result = pipeline.process_book(1, mode="single_narrator")