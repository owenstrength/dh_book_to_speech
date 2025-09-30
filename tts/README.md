# TTS Pipeline

A modular text-to-speech pipeline for generating audiobooks from XML-formatted literary texts, specifically designed for Middlemarch by George Eliot.

## 🏗️ Architecture

The pipeline uses a modular design with focused components:

- **`content_extractor.py`** - XML parsing and content organization
- **`audio_generator.py`** - Voice assignment and TTS generation  
- **`progress_manager.py`** - Progress tracking and resume functionality
- **`tts_pipeline.py`** - Main orchestrator

## 📁 File Organization

```
audio_output/
├── book_01/
│   ├── chapter_01/
│   │   ├── 0001_B01C01_NARRATOR_chapter_title_abc123.mp3
│   │   ├── 0002_B01C01_NARRATOR_narrative_combined_def456.mp3
│   │   └── 0003_B01C01_D_dialogue_ghi789.mp3
│   ├── chapter_02/
│   └── ...
└── book_1_multi_voice_metadata.json
```

## 🚀 Setup

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

2. Install requirements:
```bash
pip install openai
```

## 🎯 Usage

### Basic Usage
```bash
python tts_pipeline.py
```

### Programmatic Usage
```python
from tts_pipeline import TTSPipeline

# Initialize with API key
pipeline = TTSPipeline(api_key='your-openai-api-key')

# Process a book with resume functionality
result = pipeline.process_book(1, mode="multi_voice", resume=True)

# Check progress
pipeline.show_progress(1, mode="multi_voice")
```

## ✨ Features

- ✅ **Modular Design**: Clean separation of concerns
- ✅ **Chapter Organization**: Files organized by book/chapter  
- ✅ **Resume Functionality**: Continue from interruption
- ✅ **Progress Tracking**: Incremental saves every 10 blocks
- ✅ **Narrator Optimization**: Group continuous text to reduce API calls
- ✅ **Chapter Numbering**: Chapters start at 1 (Prelude = Chapter 1)
- ✅ **Enhanced Filenames**: Include chapter information
- ✅ **Multi-voice Support**: Different voices for different characters
- ✅ **Character Analysis**: AI-powered gender determination and voice assignment

## 📊 Output

The pipeline generates:
- **Audio files**: Organized by book/chapter structure
- **Metadata**: Complete tracking of characters, voices, and files
- **Progress files**: Enable resume functionality
- **Statistics**: Content analysis and processing reports

## 🔧 Processing Pipeline

1. **Extract** character definitions from XML
2. **Analyze** character genders using AI
3. **Assign** consistent voices to characters
4. **Parse** content blocks with chapter mapping
5. **Group** continuous narrator text
6. **Generate** speech files with organized naming
7. **Save** progress incrementally for resume capability

## 🎙️ Voice Assignment

**Male voices**: echo, fable, onyx  
**Female voices**: alloy, nova, shimmer, coral  
**Narrator**: onyx (deep, authoritative voice)

Characters maintain consistent voices across all processing runs.

## 📝 File Naming Convention

- Format: `XXXX_B##C##_CHAR_TYPE_HASH.mp3`
- Example: `0042_B01C01_D_dialogue_eeb4a9a3.mp3`
- Components:
  - `XXXX`: Global index (4 digits)
  - `B##`: Book number (2 digits)  
  - `C##`: Chapter number (2 digits)
  - `CHAR`: Character ID
  - `TYPE`: Content type (dialogue/narrative/narrative_combined)
  - `HASH`: Text content hash (8 chars)