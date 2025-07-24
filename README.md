# Real-Time Video Translator

Real-Time Video Translator view
<img width="857" height="647" alt="image" src="https://github.com/user-attachments/assets/5b19081e-a237-4ebe-b5c3-0d3b703ffaa8" />

A desktop application that provides real-time English translations for videos in other languages. Select a local video file, and the application will automatically generate and display synchronized subtitles as you watch.

This project leverages OpenAI's Whisper for state-of-the-art speech-to-text translation, FFmpeg for efficient audio processing, and VLC for video playback, all wrapped in a user-friendly Tkinter GUI.

---

## Features

-   **Instant Playback**: Video playback starts almost immediately, without waiting for the entire translation to complete.
-   **Chunked Translation**: Audio is processed in 10-second chunks in the background, ensuring a smooth user experience.
-   **Synchronized Subtitles**: Translated text is displayed in real-time, perfectly synced with the video's audio.
-   **Simple Interface**: An intuitive GUI with controls to open files and pause/play the video.
-   **Modular Codebase**: The source code is cleanly separated into modules for the GUI, translator, video player, and utilities, making it easy to understand and maintain.

---

## How It Works

The application follows a streamlined process to deliver real-time subtitles:

1.  **File Selection**: The user selects a local video file through the GUI.
2.  **Initial Translation**: The application first loads the Whisper model and translates the initial 10-second audio chunk. This ensures subtitles are available the moment the video starts.
3.  **Playback & Background Processing**: Once the first chunk is ready, the video begins playing. Simultaneously, a background thread continuously extracts subsequent 10-second audio chunks using **FFmpeg**.
4.  **Real-Time Transcription**: Each audio chunk is passed to the **Whisper** model for translation.
5.  **Subtitle Synchronization**: The resulting translated text segments, which include precise timestamps, are added to a shared list. The GUI constantly checks the video's current time and displays the corresponding subtitle.

---

## Installation & Setup

Follow these steps to get the application running on your local machine.

### 1. Prerequisites

-   **Python 3.7+**
-   **FFmpeg**: You must have FFmpeg installed and available in your system's PATH.
    -   **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder to your PATH.
    -   **macOS**: `brew install ffmpeg`
    -   **Linux**: `sudo apt update && sudo apt install ffmpeg`

### 2. Clone the Repository

```bash
git clone https://github.com/Ayush-Oza-ACL/NextBitMinds.git
cd NextBitMinds
```
### 2. Clone the Repository

```bash
# Install the required Python packages
pip install -r requirements.txt
```
Note: tkinter is part of the standard Python library.

---

## Usage
To run the application, execute the main.py script:

```bash
python main.py #or python3 main.py
```

Click the "Open Video & Translate" button, select a video file, and the translation process will begin automatically.

---

## Project Structure

The codebase is organized into several modules to ensure a clean separation of concerns:

**main.py**: The main entry point of the application. Initializes all components and handles the application lifecycle.

**gui.py**: Defines the VideoTranslatorApp class, which manages all Tkinter GUI elements and user interactions.

**video_player.py**: Contains the VLCPlayer class, a wrapper that abstracts all video playback functionality.

**translator.py**: Responsible for the core translation logic, using ffmpeg for audio extraction and whisper for transcription.

**utils.py**: Manages shared state and threading events that need to be accessed across different modules.

---

## Acknowledgements
OpenAI for the powerful Whisper model.

The VideoLAN team for the robust VLC media player.

The FFmpeg team for their essential multimedia framework.

