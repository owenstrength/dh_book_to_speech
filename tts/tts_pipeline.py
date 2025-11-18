import os
import hashlib
from pathlib import Path
import re

from content_extractor import ContentExtractor
from audio_generator import AudioGenerator
from progress_manager import ProgressManager


class TTSPipeline:
    def __init__(self, data_dir=None, output_dir="audio_output", api_key=None, book_name=None):
        # Load config to get the default data directory and book info
        config = self.load_config()
        
        # Determine the book name to use (passed in parameter takes precedence, then config, then default)
        if book_name is None:
            book_name = config.get("active_book", "Middlemarch")
        self.book_name = book_name
        
        # Determine the data directory based on the book
        if data_dir is None:
            # First try to get the path from the specific book config
            book_config = config.get("books", {}).get(book_name, {})
            if "path" in book_config:
                data_dir = book_config["path"]
            else:
                # Fall back to default books path
                data_dir = config.get("default_books_path", "./Middlemarch-8_books_byCJ")
        
        print(f"Initializing TTSPipeline for book: {book_name}")
        print(f"Using data directory: {data_dir}")
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        self.content_extractor = ContentExtractor()
        self.audio_generator = AudioGenerator(api_key=api_key, output_dir=output_dir)
        self.progress_manager = ProgressManager(output_dir=output_dir)
        
        # Keep track of all characters across all books
        self.all_characters = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def load_config(self):
        """Load the config file to get settings like books path"""
        import json  # Ensure json is imported locally
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        if not os.path.exists(config_file):
            print(f"Config file {config_file} not found. Using default values.")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded config from {config_file}")
            return data
        except Exception as e:
            print(f"Error loading config file: {e}. Using default values.")
            return {}
    
    @property
    def character_voices(self):
        return self.audio_generator.character_voices
    
    @property
    def character_descriptions(self):
        return self.audio_generator.character_descriptions
    
    @property
    def character_genders(self):
        return self.audio_generator.character_genders
    
    def process_book(self, book_identifier, mode="multi_voice", resume=True):
        """
        Process a book, supporting both:
        - Multi-file books (like Middlemarch with book1.xml, book2.xml, etc.)
        - Single-file books (like Romola as a single XML file)
        """
        print(f"\nStarting processing for book: {book_identifier} in {mode} mode...")
        
        book_format = self.detect_book_format()
        
        if book_format == "single_file":
            # Process a single XML file as one book
            return self.process_single_file_book(book_identifier, mode, resume)
        else:
            # Process multi-file book (original behavior)
            return self.process_multi_file_book(book_identifier, mode, resume)
    
    def detect_book_format(self):
        """Detect if the book path points to a single file or a directory of files"""
        # Handle relative paths properly by checking from the project root
        import os
        
        # Check if data_dir is an absolute path
        if os.path.isabs(self.data_dir):
            full_path = self.data_dir
        else:
            # If relative path, try to resolve from the project root 
            # (where config.json is located, which is at the same level as Books/)
            script_dir = os.path.dirname(os.path.abspath(__file__))  # tts directory
            project_root = os.path.dirname(script_dir)  # project root
            full_path = os.path.join(project_root, self.data_dir)
        
        if full_path and os.path.isfile(full_path):
            return "single_file"
        else:
            return "multi_file"
    
    def process_single_file_book(self, book_identifier, mode="multi_voice", resume=True):
        """Process a single XML file book like Romola"""
        # Resolve the file path properly
        import os
        if os.path.isabs(self.data_dir):
            book_file_path = self.data_dir
        else:
            # If relative path, resolve from project root
            script_dir = os.path.dirname(os.path.abspath(__file__))  # tts directory
            project_root = os.path.dirname(script_dir)  # project root
            book_file_path = os.path.join(project_root, self.data_dir)
        
        print(f"Processing single-file book: {book_file_path}")
        
        # Check if file exists
        if not os.path.exists(book_file_path):
            print(f"Book file not found: {book_file_path}")
            return None
        
        existing_data = None
        completed_files = set()
        if resume:
            # Use book_identifier as a unique identifier for the single file
            existing_data = self.progress_manager.load_existing_progress(book_identifier, mode)
            if existing_data:
                completed_files = {result['filename'] for result in existing_data.get('audio_files', [])}
                if existing_data.get('character_voices'):
                    self.audio_generator.character_voices.update(existing_data['character_voices'])
                if existing_data.get('character_descriptions'):
                    self.audio_generator.character_descriptions.update(existing_data['character_descriptions'])
                if existing_data.get('character_genders'):
                    self.audio_generator.character_genders.update(existing_data['character_genders'])
        
        # Extract characters from the single file
        print("Loading character definitions from the book...")
        book_characters = self.content_extractor.extract_characters_from_xml(book_file_path)
        print(f"Found {len(book_characters)} characters in the book")
        
        # Add characters to our global collection
        for char_id, char_name in book_characters.items():
            if char_id not in self.all_characters:
                self.all_characters[char_id] = char_name
        
        # Only assign voices to characters that don't already have them
        unassigned_characters = {}
        for char_id, char_name in self.all_characters.items():
            if char_id not in self.audio_generator.character_voices:
                unassigned_characters[char_id] = char_name
        
        if unassigned_characters:
            print(f"Assigning voices to {len(unassigned_characters)} new characters")
            for char_id, char_name in unassigned_characters.items():
                gender = self.audio_generator.determine_character_gender(char_name, char_id)
                self.audio_generator.character_genders[char_id] = gender
                
                description = self.audio_generator.generate_character_description(char_name, char_id)
                self.audio_generator.character_descriptions[char_id] = description
                
                # Use the same voice assignment logic as original
                if gender == "male":
                    available_voices = self.audio_generator.male_voices
                    voice_index = sum(1 for v in self.audio_generator.character_voices.values() if v in self.audio_generator.male_voices)
                    voice = available_voices[voice_index % len(available_voices)]
                elif gender == "female":
                    available_voices = self.audio_generator.female_voices
                    voice_index = sum(1 for v in self.audio_generator.character_voices.values() if v in self.audio_generator.female_voices)
                    voice = available_voices[voice_index % len(available_voices)]
                else:
                    # Default to female voice
                    available_voices = self.audio_generator.female_voices
                    voice_index = sum(1 for v in self.audio_generator.character_voices.values() if v in self.audio_generator.female_voices)
                    voice = available_voices[voice_index % len(available_voices)]
                
                self.audio_generator.character_voices[char_id] = voice
                print(f"Assigned {voice} voice to {char_name} ({gender})")
        else:
            print("All characters already have assigned voices")
        
        print(f"\nLoading book from: {book_file_path}")
        print("Extracting all content blocks (narrative + dialogue)...")
        
        # Use book_identifier as a book number for the single file
        content_blocks = self.content_extractor.extract_all_content_blocks(
            book_file_path, 
            self.all_characters, 
            book_identifier
        )
        print(f"Found {len(content_blocks)} total content blocks")
        
        if len(content_blocks) == 0:
            print("No content found! Check XML format.")
            return None
        
        self.progress_manager.display_content_statistics(content_blocks)
        
        results = existing_data.get('audio_files', []) if existing_data else []
        skipped_count = len(results)
        
        if skipped_count > 0:
            print(f"Resuming from block {skipped_count + 1}. Skipping {skipped_count} already processed blocks.")
        
        print(f"\nGenerating audio for {len(content_blocks) - skipped_count} remaining content blocks...")
        
        for i, block in enumerate(content_blocks):
            text_hash = hashlib.md5(block['text'].encode()).hexdigest()[:8]
            content_suffix = "narrative" if block['character_id'] == 'NARRATOR' else "dialogue"
            chapter_number = block.get('chapter_number', 1)
            
            if block.get('content_type') == 'narrative_combined':
                content_suffix = "narrative_combined"
            elif block.get('content_type') == 'title_combined':
                content_suffix = "title_combined"
            
            expected_filename = f"{block['global_index']:04d}_B{book_identifier:02d}C{chapter_number:02d}_{block['character_id']}_{content_suffix}_{text_hash}.mp3"
            
            if expected_filename in completed_files:
                chapter_dir = Path(self.output_dir) / f"book_{book_identifier:02d}" / f"chapter_{chapter_number:02d}"
                expected_path = chapter_dir / expected_filename
                if expected_path.exists():
                    continue
            
            current_progress = i + 1
            if current_progress % 5 == 0 or current_progress <= 10:
                progress_msg = self.progress_manager.format_progress_update(current_progress, len(content_blocks), block)
                print(progress_msg)
            
            result = self.audio_generator.generate_speech_for_block(block, mode)
            if result:
                # Handle both single result and list of results (for split text)
                if isinstance(result, list):
                    results.extend(result)
                    print(f"  Generated {len(result)} audio chunks for this block")
                else:
                    results.append(result)
                
                if len(results) % 10 == 0 or block.get('content_type') == 'chapter_title':
                    print(f"Saving progress... ({len(results)} blocks completed)")
                    self.progress_manager.save_progress(
                        book_identifier, mode, 
                        self.audio_generator.character_voices,
                        self.audio_generator.character_descriptions,
                        self.audio_generator.character_genders,
                        results
                    )
        
        metadata = {
            'book': book_identifier,
            'mode': mode,
            'character_voices': self.audio_generator.character_voices,
            'character_descriptions': self.audio_generator.character_descriptions,
            'character_genders': self.audio_generator.character_genders,
            'total_blocks_processed': len(results),
            'audio_files': results
        }
        
        metadata_file = Path(self.output_dir) / f"book_{book_identifier:02d}_{mode}_metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Generated {len(results)} total audio files for book {book_identifier}")
        print(f"Final metadata saved to: {metadata_file}")
        return metadata
    
    def process_multi_file_book(self, book_number, mode="multi_voice", resume=True):
        """Process multi-file book (original behavior)"""
        print(f"\nStarting processing for book {book_number} in {mode} mode...")
        
        existing_data = None
        completed_files = set()
        if resume:
            existing_data = self.progress_manager.load_existing_progress(book_number, mode)
            if existing_data:
                completed_files = {result['filename'] for result in existing_data.get('audio_files', [])}
                if existing_data.get('character_voices'):
                    self.audio_generator.character_voices.update(existing_data['character_voices'])
                if existing_data.get('character_descriptions'):
                    self.audio_generator.character_descriptions.update(existing_data['character_descriptions'])
                if existing_data.get('character_genders'):
                    self.audio_generator.character_genders.update(existing_data['character_genders'])
        
        # Load character definitions from ALL books to ensure we have all characters
        # This is important when resuming from a book that is not the first book
        print("Loading character definitions from ALL books...")
        for book_num in self.get_available_books():
            book_file = os.path.join(self.data_dir, f'book{book_num}.xml')
            if os.path.exists(book_file):
                book_characters = self.content_extractor.extract_characters_from_xml(book_file)
                print(f"Found {len(book_characters)} characters in book{book_num}.xml")
                
                # Add characters from this book to our global collection
                for char_id, char_name in book_characters.items():
                    if char_id not in self.all_characters:
                        self.all_characters[char_id] = char_name
        
        print(f"Total characters across all books: {len(self.all_characters)}")
        
        # Extract character definitions specifically for the current book
        print(f"Loading current book {book_number} character definitions...")
        book_file = os.path.join(self.data_dir, f'book{book_number}.xml')
        current_book_characters = self.content_extractor.extract_characters_from_xml(book_file)
        print(f"Found {len(current_book_characters)} characters in current book definition list")
        
        # Only assign voices to characters that don't already have them
        unassigned_characters = {}
        for char_id, char_name in self.all_characters.items():
            if char_id not in self.audio_generator.character_voices:
                unassigned_characters[char_id] = char_name
        
        if unassigned_characters:
            print(f"Assigning voices to {len(unassigned_characters)} new characters")
            # Create a temporary AudioGenerator instance to assign voices without affecting existing ones
            for char_id, char_name in unassigned_characters.items():
                gender = self.audio_generator.determine_character_gender(char_name, char_id)
                self.audio_generator.character_genders[char_id] = gender
                
                description = self.audio_generator.generate_character_description(char_name, char_id)
                self.audio_generator.character_descriptions[char_id] = description
                
                # Use the same voice assignment logic as original
                if gender == "male":
                    available_voices = self.audio_generator.male_voices
                    voice_index = sum(1 for v in self.audio_generator.character_voices.values() if v in self.audio_generator.male_voices)
                    voice = available_voices[voice_index % len(available_voices)]
                elif gender == "female":
                    available_voices = self.audio_generator.female_voices
                    voice_index = sum(1 for v in self.audio_generator.character_voices.values() if v in self.audio_generator.female_voices)
                    voice = available_voices[voice_index % len(available_voices)]
                else:
                    # Default to female voice
                    available_voices = self.audio_generator.female_voices
                    voice_index = sum(1 for v in self.audio_generator.character_voices.values() if v in self.audio_generator.female_voices)
                    voice = available_voices[voice_index % len(available_voices)]
                
                self.audio_generator.character_voices[char_id] = voice
                print(f"Assigned {voice} voice to {char_name} ({gender})")
        else:
            print("All characters already have assigned voices")
        
        print(f"\nLoading book {book_number}...")
        book_file = os.path.join(self.data_dir, f'book{book_number}.xml')
        if not os.path.exists(book_file):
            print(f"Book {book_number} not found at {book_file}")
            return None
        
        print("Extracting all content blocks (narrative + dialogue)...")
        content_blocks = self.content_extractor.extract_all_content_blocks(book_file, self.all_characters, book_number)
        print(f"Found {len(content_blocks)} total content blocks")
        
        if len(content_blocks) == 0:
            print("No content found! Check XML format.")
            return None
        
        self.progress_manager.display_content_statistics(content_blocks)
        
        results = existing_data.get('audio_files', []) if existing_data else []
        skipped_count = len(results)
        
        if skipped_count > 0:
            print(f"Resuming from block {skipped_count + 1}. Skipping {skipped_count} already processed blocks.")
        
        print(f"\nGenerating audio for {len(content_blocks) - skipped_count} remaining content blocks...")
        
        for i, block in enumerate(content_blocks):
            text_hash = hashlib.md5(block['text'].encode()).hexdigest()[:8]
            content_suffix = "narrative" if block['character_id'] == 'NARRATOR' else "dialogue"
            chapter_number = block.get('chapter_number', 1)
            
            if block.get('content_type') == 'narrative_combined':
                content_suffix = "narrative_combined"
            elif block.get('content_type') == 'title_combined':
                content_suffix = "title_combined"
            
            expected_filename = f"{block['global_index']:04d}_B{book_number:02d}C{chapter_number:02d}_{block['character_id']}_{content_suffix}_{text_hash}.mp3"
            
            if expected_filename in completed_files:
                chapter_dir = Path(self.output_dir) / f"book_{book_number:02d}" / f"chapter_{chapter_number:02d}"
                expected_path = chapter_dir / expected_filename
                if expected_path.exists():
                    continue
            
            current_progress = i + 1
            if current_progress % 5 == 0 or current_progress <= 10:
                progress_msg = self.progress_manager.format_progress_update(current_progress, len(content_blocks), block)
                print(progress_msg)
            
            result = self.audio_generator.generate_speech_for_block(block, mode)
            if result:
                # Handle both single result and list of results (for split text)
                if isinstance(result, list):
                    results.extend(result)
                    print(f"  Generated {len(result)} audio chunks for this block")
                else:
                    results.append(result)
                
                if len(results) % 10 == 0 or block.get('content_type') == 'chapter_title':
                    print(f"Saving progress... ({len(results)} blocks completed)")
                    self.progress_manager.save_progress(
                        book_number, mode, 
                        self.audio_generator.character_voices,
                        self.audio_generator.character_descriptions,
                        self.audio_generator.character_genders,
                        results
                    )
        
        metadata = {
            'book': book_number,
            'mode': mode,
            'character_voices': self.audio_generator.character_voices,
            'character_descriptions': self.audio_generator.character_descriptions,
            'character_genders': self.audio_generator.character_genders,
            'total_blocks_processed': len(results),
            'audio_files': results
        }
        
        metadata_file = Path(self.output_dir) / f"book_{book_number}_{mode}_metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Generated {len(results)} total audio files for book {book_number}")
        print(f"Final metadata saved to: {metadata_file}")
        return metadata
    
    def show_progress(self, book_number, mode="multi_voice"):
        return self.progress_manager.show_progress(book_number, mode)
    
    def get_available_books(self):
        """Get all available book numbers from the data directory"""
        book_files = []
        
        # Check if the data_dir is a single file or a directory
        if os.path.isfile(self.data_dir):
            # This is a single file, don't return anything for multi-file logic
            return []
        
        if os.path.isdir(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.startswith('book') and filename.endswith('.xml'):
                    match = re.match(r'book(\d+)\.xml', filename)
                    if match:
                        book_files.append(int(match.group(1)))
        
        return sorted(book_files)
    
    def is_book_fully_processed(self, book_identifier, mode="multi_voice"):
        """
        Check if a book has been fully processed by comparing the number of 
        completed blocks with the total possible blocks in the book.
        """
        # Load existing progress
        existing_data = self.progress_manager.load_existing_progress(book_identifier, mode)
        
        if existing_data is None:
            # No progress file exists, so book is not processed at all
            return False
        
        completed_blocks = existing_data.get('audio_files', [])
        completed_count = len(completed_blocks)
        
        # Load the book to get total possible blocks
        book_format = self.detect_book_format()
        
        if book_format == "single_file":
            # Resolve the file path properly
            import os
            if os.path.isabs(self.data_dir):
                book_file_path = self.data_dir
            else:
                # If relative path, resolve from project root
                script_dir = os.path.dirname(os.path.abspath(__file__))  # tts directory
                project_root = os.path.dirname(script_dir)  # project root
                book_file_path = os.path.join(project_root, self.data_dir)
                
            # For single file book
            if not os.path.exists(book_file_path):
                print(f"Book file not found: {book_file_path}")
                return False
                
            # Extract characters from the single file
            current_book_characters = self.content_extractor.extract_characters_from_xml(book_file_path)
            
            # Add these characters to our global collection temporarily (for content extraction)
            temp_all_characters = self.all_characters.copy()
            for char_id, char_name in current_book_characters.items():
                if char_id not in temp_all_characters:
                    temp_all_characters[char_id] = char_name
            
            # Get all content blocks for the book
            total_content_blocks = self.content_extractor.extract_all_content_blocks(book_file_path, temp_all_characters, book_identifier)
            total_count = len(total_content_blocks)
            
        else:
            # For multi-file book
            book_file = os.path.join(self.data_dir, f'book{book_identifier}.xml')
            if not os.path.exists(book_file):
                print(f"Book {book_identifier} not found at {book_file}")
                return False
                
            # Extract characters from the current book
            current_book_characters = self.content_extractor.extract_characters_from_xml(book_file)
            
            # Add these characters to our global collection temporarily (for content extraction)
            temp_all_characters = self.all_characters.copy()
            for char_id, char_name in current_book_characters.items():
                if char_id not in temp_all_characters:
                    temp_all_characters[char_id] = char_name
            
            # Get all content blocks for the book
            total_content_blocks = self.content_extractor.extract_all_content_blocks(book_file, temp_all_characters, book_identifier)
            total_count = len(total_content_blocks)
        
        print(f"Book {book_identifier}: {completed_count} blocks completed out of {total_count} total")
        
        # Return True if all blocks have been processed
        return completed_count >= total_count


if __name__ == "__main__":
    print("Starting TTS Pipeline...")
    print("Checking for API key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key not found!")
        print("Please set your API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr run with API key as parameter:")
        print("pipeline = TTSPipeline(api_key='your-key')")
        exit(1)
    
    print("API key found")
    print("Initializing pipeline...")
    
    pipeline = TTSPipeline(api_key=api_key)
    print("Pipeline initialized")
    
    # Get the book format to determine processing approach
    book_format = pipeline.detect_book_format()
    print(f"DEBUG: Detected book format is {book_format}, data_dir: {pipeline.data_dir}, abs path exists: {os.path.exists(os.path.abspath(pipeline.data_dir))}")
    
    if book_format == "single_file":
        # Process single file book (like Romola)
        print(f"Detected single-file book format: {pipeline.data_dir}")
        
        # Try to get book identifier from config or default to 1
        config = pipeline.load_config()
        active_book = config.get("active_book", "Romola")
        
        # Use the path hash or a simple identifier for the single file
        import hashlib
        book_identifier = int(hashlib.md5(pipeline.data_dir.encode()).hexdigest(), 16) % 10000
        
        print(f"\n{'='*50}")
        print(f"Processing single book: {active_book} (identifier: {book_identifier})")
        print(f"{'='*50}")
        
        # Check if the book is fully processed
        if pipeline.is_book_fully_processed(book_identifier, mode="multi_voice"):
            print(f"Book {active_book} is already fully processed. Skipping...")
        else:
            print(f"Book {active_book} needs processing...")
            print(f"\nChecking existing progress...")
            pipeline.show_progress(book_identifier, mode="multi_voice")
            
            result = pipeline.process_book(book_identifier, mode="multi_voice", resume=True)
            
            if result:
                print(f"\nCompleted processing for book {active_book}")
                print(f"Final progress summary:")
                pipeline.show_progress(book_identifier, mode="multi_voice")
            else:
                print(f"\nFailed to process book {active_book}")
    
    else:
        # Process multi-file book (original behavior, like Middlemarch)
        # Get all available books
        available_books = pipeline.get_available_books()
        print(f"\nFound available books: {available_books}")
        
        # Process only unprocessed or partially processed books
        for book_num in available_books:
            print(f"\n{'='*50}")
            print(f"Checking status for Book {book_num}")
            print(f"{'='*50}")
            
            # Check if the book is fully processed
            if pipeline.is_book_fully_processed(book_num, mode="multi_voice"):
                print(f"Book {book_num} is already fully processed. Skipping...")
                continue
            
            print(f"Book {book_num} needs processing...")
            print(f"\nChecking existing progress for book {book_num}...")
            pipeline.show_progress(book_num, mode="multi_voice")
            
            result = pipeline.process_book(book_num, mode="multi_voice", resume=True)
            
            if result:
                print(f"\nCompleted processing for book {book_num}")
                print(f"Final progress summary for book {book_num}:")
                pipeline.show_progress(book_num, mode="multi_voice")
            else:
                print(f"\nFailed to process book {book_num}")
    
    print(f"\n{'='*50}")
    print("All books processed!")
    print(f"{'='*50}")