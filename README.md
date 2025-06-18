# Adaptive Music Box

Adaptive Music Box is a desktop music player application built with Python and Tkinter. It allows you to manage playlists, play local and downloaded tracks, and control playback with a user-friendly interface.

## Features

- **Playlist Management:** Name and edit up to 10 playlists. Add or remove tracks from playlists.
- **Track Playback:** Play, pause, skip forward/backward, and seek within tracks.
- **Volume & Fade Controls:** Adjust volume and set fade-in/out durations.
- **Shuffle:** Shuffle tracks within playlists.
- **YouTube Download:** Download audio from YouTube URLs directly into your library.
- **Persistent Settings:** Remembers your last played track, position, volume, and playlists.
- **Keyboard Shortcuts:** Control playback and volume with keyboard keys.

## Getting Started

### __Prerequisites__

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (required for YouTube downloads)
- The following Python packages (install with `pip install -r requirements.txt`):
  - `pygame`
  - `mutagen`
  - `yt-dlp`
  - `tkinter` (usually included with Python)

### __Installation__

#### Executable
1. Download music_player.exe in `/dist`

#### Loose Files
1. Clone or download this repository.
2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
3. Ensure `ffmpeg` is installed and available in your system PATH.

### __Running the Application__

#### Python Program
```sh
python [music_player.py](http://_vscodecontentref_/0)
```

#### Executable
Run executable within a folder (files and settings will be stored here)
