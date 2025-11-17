#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_generator import AudioGenerator

def test_text_splitting():
    """Test the text splitting functionality with sample texts."""
    
    # Create AudioGenerator instance (no API key needed for text splitting test)
    try:
        generator = AudioGenerator(api_key="test")
    except:
        # Create a mock generator just for testing the split function
        generator = object.__new__(AudioGenerator)
    
    # Test cases
    test_cases = [
        {
            "name": "Short text (under 4096)",
            "text": "This is a short text. It should not be split.",
            "expected_chunks": 1
        },
        {
            "name": "Medium text with sentences",
            "text": "This is the first sentence. " * 200 + "This is the last sentence.",
            "expected_chunks": 1  # Should still fit in one chunk
        },
        {
            "name": "Long text requiring split",
            "text": "This is a very long sentence that contains many words and phrases. " * 100,
            "expected_chunks": 2  # Should be split into multiple chunks
        },
        {
            "name": "Text with various punctuation",
            "text": "Hello world! How are you today? I hope you're doing well. " * 100,
            "expected_chunks": 2  # Should split at sentence boundaries
        }
    ]
    
    print("Testing text splitting functionality...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Text length: {len(test_case['text'])} characters")
        
        # Test the splitting function
        chunks = generator.split_text_at_sentences(test_case['text'])
        
        print(f"Number of chunks: {len(chunks)}")
        
        # Verify all chunks are under 4096 characters
        all_under_limit = all(len(chunk) <= 4096 for chunk in chunks)
        print(f"All chunks under 4096 chars: {all_under_limit}")
        
        # Show chunk sizes
        for j, chunk in enumerate(chunks):
            print(f"  Chunk {j+1}: {len(chunk)} characters")
            # Show first 100 characters of each chunk
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"    Preview: {preview}")
        
        # Verify that when rejoined, we get the original text
        rejoined = " ".join(chunks)
        original_words = test_case['text'].split()
        rejoined_words = rejoined.split()
        
        print(f"Text preservation: {len(original_words) == len(rejoined_words)}")
        
        print("-" * 30)
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_text_splitting()