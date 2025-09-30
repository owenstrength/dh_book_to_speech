import json
from pathlib import Path


class ProgressManager:
    def __init__(self, output_dir="audio_output"):
        self.output_dir = output_dir
    
    def load_existing_progress(self, book_number, mode):
        metadata_file = Path(self.output_dir) / f"book_{book_number}_{mode}_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    existing_data = json.load(f)
                print(f"Found existing progress: {len(existing_data.get('audio_files', []))} files already processed")
                return existing_data
            except Exception as e:
                print(f"Error loading existing progress: {e}")
        return None
    
    def save_progress(self, book_number, mode, character_voices, character_descriptions, character_genders, completed_blocks):
        metadata_file = Path(self.output_dir) / f"book_{book_number}_{mode}_metadata.json"
        
        updated_metadata = {
            'book': book_number,
            'mode': mode,
            'character_voices': character_voices,
            'character_descriptions': character_descriptions,
            'character_genders': character_genders,
            'total_blocks_processed': len(completed_blocks),
            'audio_files': completed_blocks,
            'last_updated': str(Path().cwd())
        }
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(updated_metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def show_progress(self, book_number, mode="multi_voice"):
        existing_data = self.load_existing_progress(book_number, mode)
        if existing_data:
            total_files = len(existing_data.get('audio_files', []))
            print(f"Progress for Book {book_number} ({mode} mode):")
            print(f"   • {total_files} audio files generated")
            print(f"   • Last block processed: {existing_data.get('total_blocks_processed', 0)}")
            
            content_types = {}
            chapter_counts = {}
            for audio_file in existing_data.get('audio_files', []):
                content_type = audio_file.get('content_type', 'unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1
                
                chapter_num = audio_file.get('chapter_number', 1)
                chapter_counts[chapter_num] = chapter_counts.get(chapter_num, 0) + 1
            
            if content_types:
                print("   • Content types processed:")
                for ctype, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"     - {ctype}: {count}")
            
            if chapter_counts:
                print("   • Chapters processed:")
                for chapter, count in sorted(chapter_counts.items())[:5]:
                    print(f"     - Chapter {chapter}: {count} blocks")
                if len(chapter_counts) > 5:
                    print(f"     - ... and {len(chapter_counts) - 5} more chapters")
        else:
            print(f"No existing progress found for Book {book_number} ({mode} mode)")
    
    def display_content_statistics(self, content_blocks):
        type_counts = {}
        char_counts = {}
        chapter_counts = {}
        for block in content_blocks:
            content_type = block.get('content_type', 'unknown')
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            char_counts[block['character_name']] = char_counts.get(block['character_name'], 0) + 1
            chapter_num = block.get('chapter_number', 1)
            chapter_counts[chapter_num] = chapter_counts.get(chapter_num, 0) + 1
        
        print(f"\nContent type distribution:")
        for content_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {content_type}: {count} blocks")
            
        print(f"\nChapter distribution:")
        for chapter, count in sorted(chapter_counts.items()):
            print(f"  Chapter {chapter}: {count} blocks")
            
        print(f"\nCharacter/Speaker distribution:")
        for char, count in sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:7]:
            print(f"  {char}: {count} blocks")
    
    def format_progress_update(self, current_progress, total_blocks, block):
        chapter_name = f"Ch.{block.get('chapter_number', 1)}"
        content_info = f"{block.get('content_type', 'unknown')}"
        if block.get('content_type') == 'narrative_combined':
            content_info += f" ({block.get('original_block_count', 1)} combined)"
        elif block.get('content_type') == 'title_combined':
            original_count = block.get('original_block_count', 1)
            original_types = block.get('original_types', [])
            types_str = "+".join(original_types) if original_types else "titles"
            content_info += f" ({original_count} {types_str})"
        
        percentage = current_progress/total_blocks*100
        return f"Progress: {current_progress}/{total_blocks} ({percentage:.1f}%) - {chapter_name} | {content_info} | Block {block['global_index']}"