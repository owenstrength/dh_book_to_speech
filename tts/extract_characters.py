#!/usr/bin/env python3

import os
import json
from content_extractor import ContentExtractor
from audio_generator import AudioGenerator

def extract_character_data():
    print("Extracting Character Data for TTS Pipeline")
    print("=" * 50)
    
    data_dir = "/Users/owenstrength/Documents/school/senior_design/character_maps/Middlemarch-8_books_byCJ"
    
    extractor = ContentExtractor()
    
    print("Extracting characters from book1.xml...")
    book1_file = os.path.join(data_dir, 'book1.xml')
    characters = extractor.extract_characters_from_xml(book1_file)
    print(f"Found {len(characters)} characters")
    
    print("\nCreating character data template...")
    
    male_voices = ["echo", "fable", "onyx"]
    female_voices = ["alloy", "nova", "shimmer", "coral"]
    
    character_data = {}
    
    for i, (char_id, char_name) in enumerate(characters.items(), 1):
        print(f"[{i}/{len(characters)}] Creating template for {char_name} ({char_id})")
        
        character_data[char_id] = {
            "name": char_name,
            "gender": "auto-detect",
            "suggested_voice": "auto-assign",
            "ai_description": "Will be generated automatically",
            "custom_instructions": f"Read as {char_name} with appropriate character voice",
            "voice_notes": "Add specific voice directions here (e.g., 'authoritative', 'gentle', 'nervous')",
            "enabled": True
        }
    
    output_file = "character_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "source": "Middlemarch by George Eliot",
                "total_characters": len(character_data),
                "extraction_date": "auto-generated",
                "available_voices": {
                    "male": male_voices,
                    "female": female_voices,
                    "narrator": ["onyx"]
                },
                "instructions": {
                    "gender": "Set to 'male', 'female', or 'auto-detect'",
                    "suggested_voice": "Choose from available voices or 'auto-assign'",
                    "custom_instructions": "Custom TTS instructions for this character",
                    "voice_notes": "Additional voice direction notes",
                    "enabled": "Set to false to skip this character during TTS"
                }
            },
            "characters": character_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nCharacter data template saved to: {output_file}")
    print(f"Total characters: {len(character_data)}")
    
    print(f"\nCharacters found:")
    for char_id, char_data in list(character_data.items())[:10]:
        print(f"  {char_id}: {char_data['name']}")
    if len(character_data) > 10:
        print(f"  ... and {len(character_data) - 10} more")
    
    print(f"\nEdit {output_file} to customize:")
    print("  • custom_instructions: TTS voice directions")
    print("  • suggested_voice: Change voice assignment")
    print("  • voice_notes: Add specific notes")
    print("  • enabled: Enable/disable characters")
    
    return output_file

if __name__ == "__main__":
    try:
        output_file = extract_character_data()
        print(f"\nNext steps:")
        print(f"1. Edit {output_file} with your custom voice instructions")
        print(f"2. Run the TTS pipeline with: python tts_pipeline.py")
        print(f"   (Pipeline will automatically use the character data)")
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This script requires character extraction but will fail at AI generation without API key")
        print("Run with: python extract_characters.py")