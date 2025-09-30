import os
import hashlib
from pathlib import Path

from content_extractor import ContentExtractor
from audio_generator import AudioGenerator
from progress_manager import ProgressManager


class TTSPipeline:
    def __init__(self, data_dir="/Users/owenstrength/Documents/school/senior_design/character_maps/Middlemarch-8_books_byCJ", output_dir="audio_output", api_key=None):
        print(f"Initializing TTSPipeline with data_dir: {data_dir}")
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        self.content_extractor = ContentExtractor()
        self.audio_generator = AudioGenerator(api_key=api_key, output_dir=output_dir)
        self.progress_manager = ProgressManager(output_dir=output_dir)
        
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
        
        print("Loading character definitions from book1.xml...")
        book1_file = os.path.join(self.data_dir, 'book1.xml')
        characters = self.content_extractor.extract_characters_from_xml(book1_file)
        print(f"Found {len(characters)} characters in definition list")
        
        if not self.audio_generator.character_voices:
            self.audio_generator.assign_voices_to_characters(characters)
        else:
            print("Using previously assigned character voices")
        
        print(f"\nLoading book {book_number}...")
        book_file = os.path.join(self.data_dir, f'book{book_number}.xml')
        if not os.path.exists(book_file):
            print(f"Book {book_number} not found at {book_file}")
            return None
        
        print("Extracting all content blocks (narrative + dialogue)...")
        content_blocks = self.content_extractor.extract_all_content_blocks(book_file, characters, book_number)
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
    
    print("\nChecking existing progress...")
    pipeline.show_progress(1, mode="multi_voice")
    
    result = pipeline.process_book(1, mode="multi_voice", resume=True)
    
    print("\nFinal progress summary:")
    pipeline.show_progress(1, mode="multi_voice")