# Senior Design Character Maps & Audio Generation

The project focused mainly on creating a realistic audiobook generation pipeline using large language models (LLMs) and text-to-speech (TTS) models. The goal was to generate character maps from book text, which would then be used to inform the TTS model to produce more contextually accurate and emotionally resonant audio renditions of the text.

## Using Cloudflare R2 for Audio Files

Due to the large size of audio files, this project uses Cloudflare R2 to serve audio content while keeping the main HTML/JS files on GitHub Pages.

### Configuration Complete

The Cloudflare R2 configuration has been completed. All audio files and metadata will be served through Cloudflare R2 from the bucket `pub-4b3889db161a4e9c8a8e34ccec2cc57e.r2.dev`.

### Setup Instructions:

1. **Upload your audio files** to your Cloudflare R2 bucket
   - Include all audio files in `audio_output/` directory structure
   - Include all metadata files (`book_1_multi_voice_metadata.json`, etc.)

2. **Deploy your main project** using GitHub Pages
   - Push the `index.html` and other static files to your main repository
   - Enable GitHub Pages in the repository settings

### Cloudflare R2 URL Format:
- Metadata files: `https://pub-4b3889db161a4e9c8a8e34ccec2cc57e.r2.dev/audio_output/book_1_multi_voice_metadata.json`
- Audio files: `https://pub-4b3889db161a4e9c8a8e34ccec2cc57e.r2.dev/audio_output/book_01/chapter_01/FILENAME.mp3`

The player will automatically convert local audio paths to Cloudflare R2 URLs when loading and playing files. 

### Code Changes

{"Casaubon": "kɑˈsɔbən"} 