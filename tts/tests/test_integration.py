#!/usr/bin/env python3
"""
Integration test to verify pronunciation override functionality works with the full pipeline
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tts'))

from tts.audio_generator import AudioGenerator
import hashlib

def test_integration():
    # Create a dummy API key for testing 
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    
    try:
        generator = AudioGenerator(api_key=api_key, output_dir="test_output")
        
        print("Testing full integration with pronunciation override...")
        print(f"Available pronunciations: {list(generator.pronunciation_overrides['pronunciations'].keys())}")
        print(f"Available replacements: {list(generator.pronunciation_overrides['replacements'].keys())}")
        
        # Test how the text would be processed in generate_speech_for_block
        test_text = "Mr. Casaubon and Dorothea discussed Middlemarch at length."
        processed_text = generator.apply_pronunciation_overrides(test_text)
        print(f"\nOriginal text: {test_text}")
        print(f"Processed text: {processed_text}")
        
        # Verify that all expected replacements occurred
        expected_changes = [
            ("Mr. Casaubon", "Mr. kɑˈsɔbən"),
            ("Dorothea", "dəˈroʊθiə"), 
            ("Middlemarch", "MID-əl-märch")
        ]
        
        success = True
        for original, expected in expected_changes:
            if expected not in processed_text:
                print(f"ERROR: Expected '{expected}' not found in processed text")
                success = False
            else:
                print(f"✓ '{original}' correctly replaced with '{expected}'")
        
        if success:
            print("\n✓ All pronunciation overrides working correctly in integration test!")
        else:
            print("\n✗ Some pronunciation overrides failed")
        
    except Exception as e:
        print(f"Error during integration test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()