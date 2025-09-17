# TTS Pipeline for Middlemarch Audiobook Generation

This pipeline generates multi-character audiobook content from XML-encoded Middlemarch text using OpenAI's TTS models.

## Features

- **Multi-voice mode**: Each character gets a unique voice (male/female appropriate)
- **Single narrator mode**: Traditional audiobook narration
- **Character consistency**: Same voice throughout all books
- **Sentiment analysis**: Dynamic tone adjustment based on dialogue context
- **Gender detection**: LLM-based character gender assignment
- **Character descriptions**: Auto-generated personality profiles for voice instructions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage
```python
from tts_pipeline import TTSPipeline

# Initialize pipeline
pipeline = TTSPipeline()

# Process book 1 in multi-voice mode
result = pipeline.process_book(1, mode="multi_voice")

# Process book 1 in single narrator mode
result = pipeline.process_book(1, mode="single_narrator")
```

### Voice Assignment

The pipeline automatically assigns voices based on character gender:

**Male voices**: echo, fable, onyx
**Female voices**: alloy, nova, shimmer, coral

Characters are consistently assigned the same voice across all books.

## Output Structure

```
audio_output/
├── {character_id}_{hash}.mp3     # Individual dialogue audio files
├── book_1_multi_voice_metadata.json  # Processing metadata
└── book_1_single_narrator_metadata.json
```

## Pipeline Process

1. **Character Extraction**: Parses XML to identify characters from book 1
2. **Gender Detection**: Uses LLM to determine character gender
3. **Voice Assignment**: Assigns consistent voices based on gender
4. **Character Profiling**: Generates personality descriptions
5. **Dialogue Processing**: Extracts dialogue blocks from target book
6. **Sentiment Analysis**: Analyzes tone for each dialogue
7. **Speech Generation**: Creates audio with character-appropriate instructions
8. **Metadata Export**: Saves processing details and file mappings

## Instructions Template

Each TTS call includes:
- Character name and description
- Sentiment/tone analysis
- Standard audiobook pacing instruction: "Pauses: brief natural pauses for someone reading an audiobook"

## Multi-Book Support

The pipeline uses book 1 for character definitions and voice assignments, then applies these consistently across all subsequent books.