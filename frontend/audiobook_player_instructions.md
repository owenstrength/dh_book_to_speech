# Audiobook Player Setup Instructions

The audiobook player requires a web server to serve the files due to browser security restrictions on loading local files. Here are several ways to run it:

## Option 1: Python Simple Server (if Python is available)
From the project root directory:
```bash
python -m http.server 8000
```
Then visit: http://localhost:8000/frontend/audiobook_player.html

## Option 2: Node.js Live Server (if Node.js is available)
First install live-server:
```bash
npm install -g live-server
```
Then from the project root directory:
```bash
live-server
```

## Option 3: PHP Built-in Server (if PHP is available)
From the project root directory:
```bash
php -S localhost:8000
```
Then visit: http://localhost:8000/frontend/audiobook_player.html

## Option 4: Python 3
From the project root directory:
```bash
python3 -m http.server 8000
```
Then visit: http://localhost:8000/frontend/audiobook_player.html

## Important Notes:
- The player now correctly looks for audio files in the audio_output_old directory as that's where they currently exist
- Make sure you're serving from the project root directory (the directory containing both frontend/ and audio_output_old/ folders)
- Audio files will not play if you just open the HTML file directly in the browser due to CORS restrictions

## Troubleshooting
- Check the browser console (F12) for specific error messages
- Make sure the audio_output_old directory and its files exist and are accessible
- If the player still doesn't load, refresh the page after starting the server