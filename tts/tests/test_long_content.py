#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_generator import AudioGenerator

def test_with_book_content():
    """Test with realistic book content that might be long."""
    
    # Create AudioGenerator instance for testing
    try:
        generator = AudioGenerator(api_key="test")
    except:
        generator = object.__new__(AudioGenerator)
    
    # Simulate a very long narrative passage (like what might be found in Middlemarch)
    long_narrative = """
    In the heart of Middlemarch, where the morning light filtered through the tall windows of Lowick Manor, Dorothea Brooke found herself contemplating the vast responsibilities that lay before her as the new Mrs. Casaubon. The weight of her husband's scholarly pursuits seemed to press upon her shoulders like a mantle too heavy for her young frame, yet she bore it with the quiet dignity that had always characterized her demeanor. She had imagined that marriage would bring her closer to the great works of learning and philanthropy that she so desperately wished to pursue, but instead, she found herself increasingly isolated in the labyrinthine corridors of her husband's mind, where each thought led to another, more obscure reference, and every conversation seemed to spiral into academic abstractions that left her feeling more distant from the practical good she had hoped to accomplish in the world.

    The library, with its towering shelves and musty scent of ancient volumes, had become both her sanctuary and her prison. Here, surrounded by the accumulated wisdom of centuries, she would sit for hours, attempting to decipher her husband's notes and manuscripts, hoping to find some way to be of genuine assistance in his monumental work on the Key to All Mythologies. Yet the more she read, the more she began to understand the futility of the enterprise, the way in which Mr. Casaubon's grand vision was built upon foundations that were already crumbling in the face of newer, more rigorous scholarship. It was a realization that came to her gradually, like the slow dawning of an unwelcome truth, and with it came a profound sense of disappointment, not just in her husband's work, but in her own naive expectations of what their union would bring.

    The social obligations of her new position weighed heavily upon her as well. The endless rounds of visits to neighboring families, the careful navigation of local politics and gossip, the need to maintain appearances while harboring growing doubts about the very foundations of her new life – all of these demanded a kind of performance that went against her naturally forthright nature. She found herself longing for the simple clarity of her earlier ideals, when she had believed that doing good in the world was simply a matter of having the right intentions and the means to act upon them. Now, she was beginning to understand that the world was far more complex than she had imagined, that even the most well-intentioned actions could have unintended consequences, and that the path to true philanthropy was fraught with obstacles that she had never anticipated.

    In her quieter moments, when the demands of household management and social duty temporarily receded, Dorothea would find herself at the window, gazing out over the gardens and fields that stretched toward the horizon, wondering what her life might have been if she had chosen differently. The sight of the laborers working in the fields, their movements purposeful and direct, stood in stark contrast to the abstract nature of her daily occupations, and she envied them their clear sense of purpose and immediate connection to meaningful work. She began to understand that her desire to do good in the world had been, perhaps, too abstract, too removed from the actual needs and circumstances of real people living real lives with immediate and pressing concerns.

    These reflections led her to consider new possibilities, new ways of thinking about her role and responsibilities that might allow her to bridge the gap between her idealistic aspirations and the practical realities of her situation. She began to see that true philanthropy might require not grand gestures or sweeping reforms, but rather a patient, careful attention to the small ways in which she might improve the lives of those around her, beginning with her own household and extending outward into the community in gradually widening circles of influence and care.
    """ * 3  # Repeat to make it very long
    
    print("Testing with long book-like content...")
    print("=" * 50)
    print(f"Original text length: {len(long_narrative)} characters")
    
    # Test the splitting
    chunks = generator.split_text_at_sentences(long_narrative)
    
    print(f"Number of chunks created: {len(chunks)}")
    print(f"All chunks under 4096 chars: {all(len(chunk) <= 4096 for chunk in chunks)}")
    
    print("\nChunk details:")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: {len(chunk)} characters")
        # Check if chunk ends with proper punctuation (good sentence boundary)
        last_char = chunk.strip()[-1] if chunk.strip() else ''
        ends_with_punctuation = last_char in '.!?'
        print(f"  Ends with punctuation: {ends_with_punctuation} ('{last_char}')")
        
        # Show first and last 50 characters
        if len(chunk) > 100:
            preview_start = chunk.strip()[:50]
            preview_end = chunk.strip()[-50:]
            print(f"  Start: {preview_start}...")
            print(f"  End: ...{preview_end}")
        else:
            print(f"  Content: {chunk.strip()}")
        print()

if __name__ == "__main__":
    test_with_book_content()