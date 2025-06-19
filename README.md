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

- Windows machine
- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (required for YouTube downloads)
- The following Python packages (install with `pip install -r requirements.txt`):
  - `pygame`
  - `mutagen`
  - `yt-dlp`
  - `tkinter` (usually included with Python)

### __Installation__

#### Executable (Windows)
1. Download music_player.exe in `/dist`
Note: I believe the provided executable only works on Windows machines. For other systems see **Running the Application: Python Program**.

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
Alternatively, you can compile into an executable yourself. I am not sure but I believe this will create an executable compatible with the system it is run on:
```sh
PyInstaller --onefile --windowed music_box.py --name "Music Box"
```

#### Executable
Run executable within a folder (files and settings will be stored here)

## Usage

### Downloading Files
- YouTube files will be downloaded as MP3's. Click "Share" and "Copy Link" on the video. It works with playlists as well, although currently cannot be canceled.
- Paste the URL into the box labeled URL, and click Download. Files will be downloaded to a `/files` folder in the same directory as the executable file.
- Status messages will display directly below, and will display "Success!" once the download has completed.

### Playback
- The playback frame shows the current position in the current track, the length of the current track, the volume, and the fade in/out time, as well as which playlists the current track is in and if the current playlsit is being shuffled or not.
- The horizontal slider can be dragged to seek through the track, or the Left and Right arrow keys can be used to skip back or forward 5 seconds. 
- The three buttons from left to right are Start (|<<), Play/Pause (>/||), and Next (>>|). Double-clicking the Start button will go to the previous track.
- The fade slider is in milliseconds, and determines how long the current track will fade out and the next track will fade in. So, if the fade is set to 500ms, it will take 1000ms (1 second) for the volume to reach its set level again.
- The vertical slider sets the volume of playback, as well as the Up and Down arrow keys.

### Playlists
- The playlists frame shows the current playlist, which can be changed by clicking on it to open a dropdown menu, and the tracks in the current playlist.
- Number keys can also be used to change playlists. All 10 are accessible from either the numrow or numpad keys, with tilde (`) and period (.) being assigned to the "All" playlist.
- Playlist names (except for "All") can be edited by clicking on them when they are currently selected, typing the new name, and hitting Enter/Return on your keyboard.

### Settings
- Many settings are saved to a json file to be loaded up on next boot. The current playlist, track, position in track, volume, and fade, as well as whether the playlist is shuffled.
- The same json file is also used to store which songs are in which playlists, as well as the names of those playlists.

## Future Plans
- Changing track names in the Listbox similarly to chaning playlist names
- Filtering track listbox using Entry to matching names
- Support for non-Windows machines, as I am unsure if file structure operations will function correctly on non-Windows systems.
