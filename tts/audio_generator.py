import hashlib
import os
import json
import re
from pathlib import Path
from openai import OpenAI


class AudioGenerator:
    def __init__(self, api_key=None, output_dir="audio_output", character_data_file="character_data.json"):
        self.output_dir = output_dir
        self.character_data_file = character_data_file
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Please either:\n"
                    "1. Set OPENAI_API_KEY environment variable, or\n"
                    "2. Pass api_key parameter to AudioGenerator(api_key='your-key')"
                )
            self.client = OpenAI()
        
        self.male_voices = ["echo", "fable", "onyx"]
        self.female_voices = ["alloy", "nova", "shimmer", "coral"]
        
        self.character_voices = {}
        self.character_genders = {}
        self.character_descriptions = {}
        self.character_custom_instructions = {}
        
        # Load pronunciation overrides
        self.pronunciation_overrides = self.load_pronunciation_overrides()
        # Load config file for additional settings
        self.config = self.load_config_file()
        
        os.makedirs(output_dir, exist_ok=True)
    
    def load_pronunciation_overrides(self):
        """Load pronunciation overrides from JSON file"""
        pronunciation_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        if not os.path.exists(pronunciation_file):
            print(f"Pronunciation overrides file {pronunciation_file} not found. Using default text.")
            return {"pronunciations": {}, "replacements": {}}
        
        try:
            with open(pronunciation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded pronunciation overrides from {pronunciation_file}")
            
            if "pronunciations" not in data:
                data["pronunciations"] = {}
            if "replacements" not in data:
                data["replacements"] = {}
                
            return data
        except Exception as e:
            print(f"Error loading pronunciation overrides: {e}. Using default text.")
            return {"pronunciations": {}, "replacements": {}}
    
    def load_config_file(self):
        """Load the full config file"""
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        if not os.path.exists(config_file):
            print(f"Config file {config_file} not found. Using default values.")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded config file from {config_file}")
            return data
        except Exception as e:
            print(f"Error loading config file: {e}. Using default values.")
            return {}
    
    def apply_pronunciation_overrides(self, text):
        """Apply pronunciation overrides to text before TTS generation"""
        # First apply replacements (for full phrases/phrases)
        for original, replacement in self.pronunciation_overrides["replacements"].items():
            text = text.replace(original, replacement)
        
        # Then apply word-by-word pronunciation overrides
        for original_word, phonetic in self.pronunciation_overrides["pronunciations"].items():
            # Use word boundaries to replace whole words only
            # This prevents partial matches within other words
            pattern = r'\b' + re.escape(original_word) + r'\b'
            text = re.sub(pattern, phonetic, text, flags=re.IGNORECASE)
        
        return text
        if not os.path.exists(self.character_data_file):
            print(f"Character data file {self.character_data_file} not found. Using auto-generation.")
            return None
        
        try:
            with open(self.character_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"Loaded character data from {self.character_data_file}")
            return data.get('characters', {})
        except Exception as e:
            print(f"Error loading character data: {e}. Using auto-generation.")
            return None
    
    def determine_character_gender(self, char_name, char_id):
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
        print(f"\nAssigning voices to {len(characters)} characters")
        
        character_data = self.load_character_data()
        
        if character_data:
            self.assign_voices_from_file(characters, character_data)
        else:
            self.assign_voices_automatically(characters)
        
        print(f"\nVoice assignment complete!")
    
    def assign_voices_from_file(self, characters, character_data):
        print("Using custom character data from file")
        male_count = 0
        female_count = 0
        
        for i, (char_id, char_name) in enumerate(characters.items(), 1):
            if char_id not in character_data:
                print(f"Character {char_name} ({char_id}) not found in data file, skipping")
                continue
            
            char_info = character_data[char_id]
            
            if not char_info.get('enabled', True):
                print(f"Character {char_name} ({char_id}) disabled in data file, skipping")
                continue
            
            print(f"\n[{i}/{len(characters)}] Processing {char_name} ({char_id})")
            
            gender = char_info.get('gender', 'auto-detect')
            if gender == 'auto-detect':
                gender = self.determine_character_gender(char_name, char_id)
            
            self.character_genders[char_id] = gender
            
            description = char_info.get('ai_description', 'Will be generated automatically')
            if description == 'Will be generated automatically':
                description = self.generate_character_description(char_name, char_id)
            
            self.character_descriptions[char_id] = description
            
            custom_instructions = char_info.get('custom_instructions', f"Read as {char_name}")
            self.character_custom_instructions[char_id] = custom_instructions
            
            suggested_voice = char_info.get('suggested_voice', 'auto-assign')
            if suggested_voice == 'auto-assign':
                if gender == "male":
                    voice = self.male_voices[male_count % len(self.male_voices)]
                    male_count += 1
                elif gender == "female":
                    voice = self.female_voices[female_count % len(self.female_voices)]
                    female_count += 1
                else:
                    voice = self.female_voices[female_count % len(self.female_voices)]
                    female_count += 1
            else:
                voice = suggested_voice
            
            self.character_voices[char_id] = voice
            print(f"Assigned {voice} voice to {char_name} ({gender})")
            
            voice_notes = char_info.get('voice_notes', '')
            if voice_notes and voice_notes != "Add specific voice directions here (e.g., 'authoritative', 'gentle', 'nervous')":
                print(f"  Voice notes: {voice_notes}")
    
    def assign_voices_automatically(self, characters):
        print("Using automatic character assignment")
        male_count = 0
        female_count = 0
        
        for i, (char_id, char_name) in enumerate(characters.items(), 1):
            print(f"\n[{i}/{len(characters)}] Processing {char_name} ({char_id})")
            
            gender = self.determine_character_gender(char_name, char_id)
            self.character_genders[char_id] = gender
            
            description = self.generate_character_description(char_name, char_id)
            self.character_descriptions[char_id] = description
            
            self.character_custom_instructions[char_id] = f"Read as {char_name}, {description}"
            
            if gender == "male":
                voice = self.male_voices[male_count % len(self.male_voices)]
                male_count += 1
            elif gender == "female":
                voice = self.female_voices[female_count % len(self.female_voices)]
                female_count += 1
            else:
                voice = self.female_voices[female_count % len(self.female_voices)]
                female_count += 1
            
            self.character_voices[char_id] = voice
            print(f"Assigned {voice} voice to {char_name} ({gender})")
    
    def split_text_at_sentences(self, text, max_length=4096):
        """
        Split text into chunks at sentence boundaries, ensuring no chunk exceeds max_length.
        Returns a list of text chunks.
        """
        if len(text) <= max_length:
            return [text]
        
        # Split text into sentences using regex that handles various punctuation
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed the limit
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split it at word boundaries
                    words = sentence.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                # Single word is too long, just add it
                                chunks.append(word)
                                current_chunk = ""
                        else:
                            current_chunk = current_chunk + " " + word if current_chunk else word
            else:
                current_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def analyze_dialogue_sentiment(self, dialogue_text):
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
    
    def generate_speech_for_block(self, content_block, mode="multi_voice"):
        global_index = content_block['global_index']
        book_number = content_block['book_number']
        chapter_number = content_block.get('chapter_number', 1)
        char_id = content_block['character_id']
        char_name = content_block['character_name']
        text = content_block['text']
        content_type = content_block.get('content_type', 'dialogue')
        
        # Split text if it's longer than 4096 characters
        text_chunks = self.split_text_at_sentences(text)
        
        if char_id == 'NARRATOR' or mode == "single_narrator":
            voice = "onyx"
            
            if content_type == 'chapter_title':
                instructions = f"Narrator reading chapter title with dramatic emphasis"
            elif content_type == 'main_title':
                instructions = f"Narrator reading main title with authority"
            elif content_type == 'title_combined':
                original_count = content_block.get('original_block_count', 1)
                original_types = content_block.get('original_types', [])
                types_str = ", ".join(original_types) if original_types else "titles"
                instructions = f"Narrator reading combined titles with authority and dramatic emphasis (combined from {original_count} title elements: {types_str})"
            elif content_type == 'epigraph':
                instructions = f"Narrator reading epigraph with reverent, thoughtful tone"
            elif content_type in ['subtitle', 'section_title']:
                instructions = f"Narrator reading section heading"
            elif content_type in ['narrative', 'narrative_combined']:
                instructions = f"Narrator reading narrative text"
                if content_type == 'narrative_combined':
                    original_count = content_block.get('original_block_count', 1)
                    instructions += f" (combined from {original_count} paragraphs)"
            else:
                instructions = f"Narrator reading for {char_name}" if char_name != 'Narrator' else "Narrator"
                
        else:
            voice = self.character_voices.get(char_id, "alloy")
            
            if char_id in self.character_custom_instructions:
                instructions = self.character_custom_instructions[char_id]
            else:
                char_description = self.character_descriptions.get(char_id, f"A character named {char_name}")
                sentiment = self.analyze_dialogue_sentiment(text)
                instructions = f"{char_name} ({sentiment}): {char_description}"
        
        chapter_dir = Path(self.output_dir) / f"book_{book_number:02d}" / f"chapter_{chapter_number:02d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        content_suffix = "narrative" if char_id == 'NARRATOR' else "dialogue"
        
        if content_type == 'narrative_combined':
            content_suffix = "narrative_combined"
        elif content_type == 'title_combined':
            content_suffix = "title_combined"
        
        # If text needs to be split, generate multiple files
        if len(text_chunks) > 1:
            print(f"Text too long ({len(text)} chars), splitting into {len(text_chunks)} chunks")
            results = []
            
            for chunk_idx, chunk_text in enumerate(text_chunks):
                chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
                filename = f"{global_index:04d}_B{book_number:02d}C{chapter_number:02d}_{char_id}_{content_suffix}_part{chunk_idx+1:02d}_{chunk_hash}.mp3"
                speech_file_path = chapter_dir / filename
                
                processed_chunk_text = self.apply_pronunciation_overrides(chunk_text)
                
                try:
                    response = self.client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=processed_chunk_text,
                    )
                    
                    with open(speech_file_path, "wb") as f:
                        f.write(response.content)
                    
                    result = {
                        'global_index': global_index,
                        'book_number': book_number,
                        'chapter_number': chapter_number,
                        'character_id': char_id,
                        'character_name': char_name,
                        'content_type': content_type,
                        'voice': voice,
                        'file_path': str(speech_file_path),
                        'filename': filename,
                        'text': chunk_text,
                        'instructions': instructions,
                        'is_split': True,
                        'chunk_index': chunk_idx + 1,
                        'total_chunks': len(text_chunks),
                        'original_text_length': len(text)
                    }
                    
                    if content_type == 'narrative_combined':
                        result['original_block_count'] = content_block.get('original_block_count', 1)
                        result['original_indices'] = content_block.get('original_indices', [global_index])
                    elif content_type == 'title_combined':
                        result['original_block_count'] = content_block.get('original_block_count', 1)
                        result['original_indices'] = content_block.get('original_indices', [global_index])
                        result['original_types'] = content_block.get('original_types', [])
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"Error generating speech for {char_name} chunk {chunk_idx+1}: {e}")
                    return None
            
            return results
        
        else:
            # Single file generation (original logic)
            filename = f"{global_index:04d}_B{book_number:02d}C{chapter_number:02d}_{char_id}_{content_suffix}_{text_hash}.mp3"
            speech_file_path = chapter_dir / filename
            
            # Apply pronunciation overrides to the text before TTS
            processed_text = self.apply_pronunciation_overrides(text)
            
            try:
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=processed_text,
                )
                
                with open(speech_file_path, "wb") as f:
                    f.write(response.content)
                
                result = {
                    'global_index': global_index,
                    'book_number': book_number,
                    'chapter_number': chapter_number,
                    'character_id': char_id,
                    'character_name': char_name,
                    'content_type': content_type,
                    'voice': voice,
                    'file_path': str(speech_file_path),
                    'filename': filename,
                    'text': text,
                    'instructions': instructions,
                    'is_split': False
                }
                
                if content_type == 'narrative_combined':
                    result['original_block_count'] = content_block.get('original_block_count', 1)
                    result['original_indices'] = content_block.get('original_indices', [global_index])
                elif content_type == 'title_combined':
                    result['original_block_count'] = content_block.get('original_block_count', 1)
                    result['original_indices'] = content_block.get('original_indices', [global_index])
                    result['original_types'] = content_block.get('original_types', [])
                
                return result
            
            except Exception as e:
                print(f"Error generating speech for {char_name}: {e}")
                return None