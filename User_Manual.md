# Digital Humanities Group #1
## User Manual: Pipeline for Natural Sounding Text-to-Speech for AudioBooks
### https://github.com/owenstrength/dh_book_to_speech

### Authors:
- Owen Strength (OS)
- Mitchell Dogan (MD)
- William Messenger (WM)

#### Comp 4710 Senior Design
Department of Computer Science and Software Engineering
Samuel Ginn College of Engineering, Auburn University

## Overview

Welcome to the Audiobook for the George Eliot Archive! This application provides an immersive listening experience for George Eliot's classic novels, featuring character-specific voices that bring the text to life. The player uses advanced text-to-speech technology to assign unique voices to different characters, creating a more engaging audiobook experience similar to a full cast production.

## How to Access the Application

The Audiobook for the George Eliot Archive is available online at: **[georgeelliotarchive.github.io](https://georgeelliotarchive.github.io)**

Simply visit the website in any modern web browser (Chrome, Firefox, Safari, Edge) to begin exploring the available audiobooks.

## Getting Started

### 1. Selecting a Story

When you first visit the website, you'll see a dropdown menu labeled "Select a story...". Currently, the following stories are available:

- **Middlemarch**: George Eliot's masterpiece following the lives of Dorothea Brooke and other residents of the fictional town of Middlemarch, set in the 1820s-1830s.
- **Romola**: Set in 15th-century Florence, following the titular character through political intrigue and personal growth.

### 2. Selecting a Book

After choosing a story, a second dropdown labeled "Select a book..." will become active. George Eliot's novels are often divided into multiple books:

- **Middlemarch** is divided into 8 books, each containing multiple chapters
- **Romola** is available as 1 complete book

Select the book you wish to listen to from the dropdown menu.

### 3. Starting Playback

Once you've selected both a story and a book, the player will automatically load the first chapter. The audio will begin playing immediately, or you can click the play button (▶) to start playback.

## Using the Player Interface

### Now Playing Section

The "Now Playing" section displays important information about the current audio:

- **Book Title**: Shows the current book and story name
- **Book/Chapter**: Displays the current book number and chapter number (e.g., "Book 1, Chapter 1")
- **Speaker Information**: Shows which character is currently speaking (e.g., "Dorothea", "Mr. Casaubon", "Narrator")

### Playback Controls

#### Basic Controls
- **Play/Pause (▶/⏸)**: Toggle between playing and pausing the audio
- **Previous Track (◀)**: Jump to the previous track (different character speaking or narrative section)
- **Next Track (▶)**: Jump to the next track
- **Previous Chapter (⏮)**: Jump to the first track of the previous chapter
- **Next Chapter (⏭)**: Jump to the first track of the next chapter

#### Progress Bar
- Click anywhere on the progress bar to jump to that point in the current track
- The progress bar shows how much of the current track has been played

#### Volume Controls
- **Volume Slider**: Drag to adjust volume from 0% to 100%
- **Volume Buttons**: Use the (-) and (+) buttons to decrease/increase volume in 10% increments

#### Speed Controls
- **Speed Display**: Shows current playback speed (default: 1.0x)
- **Speed Buttons**: Use (-) and (+) buttons to adjust speed in 0.25x increments
- **Available Speeds**: 0.5x to 2.0x playback speed

### Playback Queue

The "Playback Queue" section shows all available tracks for the current book:
- Click on any track to jump directly to that section
- The currently playing track is highlighted in the list
- Click the section header to collapse/expand the queue

## Understanding the Audio Experience

### Character Voices

Each character in the story is assigned a unique voice based on their gender and character type:
- **Male Characters**: Voices like "Echo", "Fable", and "Onyx" (deeper, more authoritative tones)
- **Female Characters**: Voices like "Alloy", "Nova", "Shimmer", and "Coral" (varied feminine tones)
- **Narrator**: Uses the "Onyx" voice for storytelling sections

### Content Types

The player handles different types of content from the original text:
- **Dialog**: Character dialogue sections
- **Narrative**: Storytelling and description sections
- **Titles**: Chapter titles and book headings
- **Epigraphs**: Quotations at the beginning of chapters

## Troubleshooting

### Audio Won't Play
- Ensure you're using a modern web browser with HTML5 audio support
- Check that your browser hasn't blocked autoplay (some browsers require user interaction to start audio)
- Verify your internet connection is stable
- Try refreshing the page if audio is stuck

### Content Not Loading
- If the book selection doesn't populate, try refreshing the page
- Check that you have a stable internet connection
- The application fetches content from cloud storage, so connectivity is required

### No Audio When Switching Books
- After selecting a new book, the player may take a few seconds to load the new content
- Wait for the tracks to appear in the playback queue before attempting to play

## Technical Requirements

### Supported Browsers
- Google Chrome (latest version)
- Mozilla Firefox (latest version)
- Safari (latest version)
- Microsoft Edge (latest version)

### Internet Connection
- A stable broadband connection is recommended
- Audio files are streamed from cloud storage
- Mobile data connections will work but may consume significant data

### Device Compatibility
- Desktop computers (Windows, macOS, Linux)
- Laptops
- Tablets (iPad, Android tablets)
- Smartphones (iPhone, Android devices) with modern browsers

## Data Usage

Please note that streaming audiobooks consumes internet data. A full book can require several hundred megabytes to several gigabytes depending on length. Consider this when using mobile data connections or limited data plans.

## Privacy Information

- The application does not collect personal information
- No tracking or analytics are implemented
- Audio files are served directly from cloud storage
- Your listening progress is not saved between sessions

## About the Project

This application was developed as part of a Senior Design project focused on creating realistic audiobook generation using large language models (LLMs) and text-to-speech (TTS) models. The goal was to generate character maps from book text, which would then be used to inform the TTS model to produce more contextually accurate and emotionally resonant audio renditions of the text.

The system uses OpenAI's TTS technology with character-specific voices to create an immersive experience that helps listeners better understand the narrative and character relationships in George Eliot's complex works.

---

*Thank you for using the Audiobook for the George Eliot Archive. Enjoy your journey through classic literature with modern technology!*