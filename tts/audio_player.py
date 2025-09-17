import json
import os
import glob
from pathlib import Path
import subprocess
import sys
import time

class AudioBookPlayer:
    def __init__(self, audio_dir="audio_output"):
        self.audio_dir = audio_dir
        
    def load_metadata(self, book_number, mode="multi_voice"):
        """Load metadata for a specific book"""
        metadata_file = Path(self.audio_dir) / f"book_{book_number}_{mode}_metadata.json"
        if not os.path.exists(metadata_file):
            print(f"Metadata file not found: {metadata_file}")
            return None
            
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    def get_audio_files_in_order(self, book_number, mode="multi_voice"):
        """Get all audio files for a book in the correct order"""
        metadata = self.load_metadata(book_number, mode)
        if not metadata:
            return []
        
        audio_files = sorted(metadata['audio_files'], key=lambda x: x['global_index'])
        return audio_files
    
    def print_character_info(self, metadata):
        """Print character descriptions and voice assignments"""
        print("\n" + "="*60)
        print("CHARACTER CAST")
        print("="*60)
        
        for char_id, description in metadata['character_descriptions'].items():
            char_name = metadata['character_voices'].get(char_id, 'Unknown')
            voice = metadata['character_voices'].get(char_id, 'unknown')
            gender = metadata['character_genders'].get(char_id, 'unknown')
            
            print(f"\n{char_name} ({char_id}) - {gender}")
            print(f"Voice: {voice}")
            print(f"Description: {description}")
            print("-" * 40)
    
    def play_audio_file(self, file_path):
        """Play a single audio file using system audio player"""
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.run(['afplay', file_path])
        elif sys.platform.startswith('linux'):  # Linux
            subprocess.run(['aplay', file_path])
        elif sys.platform.startswith('win'):    # Windows
            subprocess.run(['start', file_path], shell=True)
        else:
            print(f"Unsupported platform: {sys.platform}")
            print(f"Please manually play: {file_path}")
            input("Press Enter when ready to continue...")
    
    def play_book(self, book_number, mode="multi_voice", interactive=True):
        """Play all audio files for a book in order"""
        print(f"🎧 Loading audiobook for Book {book_number} ({mode} mode)...")
        
        metadata = self.load_metadata(book_number, mode)
        if not metadata:
            return
        
        audio_files = self.get_audio_files_in_order(book_number, mode)
        
        print(f"Found {len(audio_files)} audio clips")
        
        # Show character info
        self.print_character_info(metadata)
        
        if interactive:
            input("\nPress Enter to start playback...")
        
        print(f"\n🎵 Starting playback of {len(audio_files)} clips...")
        print("="*60)
        
        for i, audio_info in enumerate(audio_files, 1):
            content_type = audio_info.get('content_type', 'dialogue')
            speaker = audio_info['character_name']
            
            # Format display based on content type
            if content_type == 'narrative':
                print(f"\n[{i}/{len(audio_files)}] 📖 NARRATOR: {speaker}")
            elif content_type == 'epigraph':
                print(f"\n[{i}/{len(audio_files)}] ✨ EPIGRAPH: {speaker}")
            elif content_type in ['chapter_title', 'main_title', 'subtitle', 'section_title']:
                print(f"\n[{i}/{len(audio_files)}] 📚 {content_type.upper()}: {speaker}")
            else:
                print(f"\n[{i}/{len(audio_files)}] 💬 {speaker}:")
                
            print(f"Type: {content_type}")
            print(f"File: {audio_info['filename']}")
            print(f"Text: {audio_info['text'][:150]}{'...' if len(audio_info['text']) > 150 else ''}")
            
            if interactive:
                user_input = input("Press Enter to play, 's' to skip, 'q' to quit: ").strip().lower()
                if user_input == 'q':
                    break
                elif user_input == 's':
                    continue
            
            # Check if file exists
            if not os.path.exists(audio_info['file_path']):
                print(f"⚠️ Audio file not found: {audio_info['file_path']}")
                continue
            
            print("▶️ Playing...")
            try:
                self.play_audio_file(audio_info['file_path'])
                print("✅ Finished")
            except Exception as e:
                print(f"❌ Error playing audio: {e}")
            
            if interactive:
                print("-" * 40)
        
        print(f"\n🎉 Finished playing Book {book_number}!")
    
    def list_available_books(self):
        """List all available books and modes"""
        metadata_files = glob.glob(os.path.join(self.audio_dir, "book_*_metadata.json"))
        
        books = {}
        for file in metadata_files:
            filename = os.path.basename(file)
            # Parse filename: book_X_MODE_metadata.json
            parts = filename.replace('_metadata.json', '').split('_')
            if len(parts) >= 3:
                book_num = int(parts[1])
                mode = '_'.join(parts[2:])
                if book_num not in books:
                    books[book_num] = []
                books[book_num].append(mode)
        
        if not books:
            print("No audiobooks found in the output directory")
            return
        
        print("Available audiobooks:")
        for book_num in sorted(books.keys()):
            modes = ', '.join(books[book_num])
            print(f"  Book {book_num}: {modes}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python audio_player.py <book_number> [mode] [--non-interactive]")
        print("       python audio_player.py list")
        print("\nModes: multi_voice (default), single_narrator")
        return
    
    player = AudioBookPlayer()
    
    if sys.argv[1] == "list":
        player.list_available_books()
        return
    
    try:
        book_number = int(sys.argv[1])
    except ValueError:
        print("Error: Book number must be an integer")
        return
    
    mode = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "--non-interactive" else "multi_voice"
    interactive = "--non-interactive" not in sys.argv
    
    player.play_book(book_number, mode, interactive)

if __name__ == "__main__":
    main()