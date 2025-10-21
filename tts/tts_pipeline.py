import os
import hashlib
from pathlib import Path

from content_extractor import ContentExtractor
from audio_generator import AudioGenerator
from progress_manager import ProgressManager


class TTSPipeline:
    def __init__(self, data_dir="./Middlemarch-8_books_byCJ", output_dir="audio_output", api_key=None):
        print(f"Initializing TTSPipeline with data_dir: {data_dir}")
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        self.content_extractor = ContentExtractor()
        self.audio_generator = AudioGenerator(api_key=api_key, output_dir=output_dir)
        self.progress_manager = ProgressManager(output_dir=output_dir)
        
        # Keep track of all characters across all books
        self.all_characters = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    @property
    def character_voices(self):
        return self.audio_generator.character_voices
    
    @property
    def character_descriptions(self):
        return self.audio_generator.character_descriptions
    
    @property
    def character_genders(self):
        return self.audio_generator.character_genders
    
    def process_book(self, book_number, mode="multi_voice", resume=True):
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
        import re
        book_files = []
        for filename in os.listdir(self.data_dir):
            if filename.startswith('book') and filename.endswith('.xml'):
                match = re.match(r'book(\d+)\.xml', filename)
                if match:
                    book_files.append(int(match.group(1)))
        
        return sorted(book_files)
    
    def is_book_fully_processed(self, book_number, mode="multi_voice"):
        """
        Check if a book has been fully processed by comparing the number of 
        completed blocks with the total possible blocks in the book.
        """
        # Load existing progress
        existing_data = self.progress_manager.load_existing_progress(book_number, mode)
        
        if existing_data is None:
            # No progress file exists, so book is not processed at all
            return False
        
        completed_blocks = existing_data.get('audio_files', [])
        completed_count = len(completed_blocks)
        
        # Load the book to get total possible blocks
        book_file = os.path.join(self.data_dir, f'book{book_number}.xml')
        if not os.path.exists(book_file):
            print(f"Book {book_number} not found at {book_file}")
            return False
            
        # Extract characters from the current book
        current_book_characters = self.content_extractor.extract_characters_from_xml(book_file)
        
        # Add these characters to our global collection temporarily (for content extraction)
        temp_all_characters = self.all_characters.copy()
        for char_id, char_name in current_book_characters.items():
            if char_id not in temp_all_characters:
                temp_all_characters[char_id] = char_name
        
        # Get all content blocks for the book
        total_content_blocks = self.content_extractor.extract_all_content_blocks(book_file, temp_all_characters, book_number)
        total_count = len(total_content_blocks)
        
        print(f"Book {book_number}: {completed_count} blocks completed out of {total_count} total")
        
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
    
    pipeline = TTSPipeline()
    print("Pipeline initialized")
    
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