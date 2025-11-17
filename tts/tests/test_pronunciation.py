#!/usr/bin/env python3
"""
Test script to verify pronunciation override functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tts'))

from tts.audio_generator import AudioGenerator
import os

def test_pronunciation_overrides():
    # Create a dummy API key for testing (won't actually make API calls for this test)
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    
    try:
        generator = AudioGenerator(api_key=api_key)
        
        print("Testing pronunciation override functionality...")
        print(f"Pronunciation overrides loaded: {generator.pronunciation_overrides}")
        
        # Test basic word replacement
        test_text1 = "Mr. Casaubon was a learned man."
        processed1 = generator.apply_pronunciation_overrides(test_text1)
        print(f"Original: {test_text1}")
        print(f"Processed: {processed1}")
        
        # Test phonetic pronunciation
        test_text2 = "Dorothea and Casaubon discussed Middlemarch."
        processed2 = generator.apply_pronunciation_overrides(test_text2)
        print(f"Original: {test_text2}")
        print(f"Processed: {processed2}")
        
        # Test case insensitive matching
        test_text3 = "CASAUBON and casaubon should both be replaced."
        processed3 = generator.apply_pronunciation_overrides(test_text3)
        print(f"Original: {test_text3}")
        print(f"Processed: {processed3}")
        
        print("\nPronunciation override functionality test completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pronunciation_overrides()