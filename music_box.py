import re
import os
import sys
import json
import time
import threading
import traceback
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import Scale as Scl
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs
from mutagen.mp3 import MP3
from pygame import mixer
from tracks import Playlist, Track
from ui_updater import UIUpdatePostProcessor

class MusicBox:

    def __init__(self, root):

        # Directory Information
        self.base_path = None
        self.filepath = None
        self.settings_path = None
        self.__setup_directory()

        # Initialize Attributes
        self.root = root
        self.settings = {}

        self.filename = ''
        self.track_name = ''
        self.track_pos = 0.0
        self.tracks = {}
        self.playlists = {}
        self.playlist_all = Playlist('All')
        self.current_playlist = self.playlist_all
        self.var_playlist = StringVar()
        self.prev_tracks = []
        self.queue = [] # replace self.prev_tracks elsewhere in code
        self.queue_pos = 0
        self.shuffle = BooleanVar()
        self.volume = DoubleVar()
        self.fade = IntVar()
        self.is_playing = False
        self.last_play_time = None

        self.cur_download = 0
        self.progress_bar_in_use = False
        self.cancel_flag = threading.Event()
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title).82s_[%(id)s].%(ext)s'.replace(' ', '_'),
            'restrictfilenames': True,
            'windowsFilenames': True,
            'paths': {
                'home': 'files',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                }],
            'progress_hooks': [self._yt_progress_hook],
        }

        # Setup Methods
        self.__setup_UI()
        self.__load_settings()
        self.__setup_playlists()
        self.__setup_download_frame()
        self.__setup_current_playlist_frame()
        self.__setup_player_frame()

        # PyGame Mixer
        mixer.init()
        mixer.music.set_volume(self.volume.get())
        if self.track_name:
            self.play_track(self.track_name)
            self.sld_progress.set(100 * self.track_pos / self.track_length)
            self.seek_track(None)
            self.play(None)


# Setup Functions

    def __setup_directory(self):
        '''
        Assign directory paths based on whether program running as python file or executable
        '''
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller EXE
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(self.base_path, 'files')
        self.settings_path = os.path.join(self.base_path, 'settings.json')
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

    def __setup_UI(self):
        '''
        Set up main window UI
        '''
        # Configure
        self.root.configure(bg='medium purple')
        self.root.minsize(750, 450)
        self.root.title('Music Box')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        # Style
        self.style_default = Style()
        self.style_name = 'Outlined.TFrame' # helps show where frames are, mostly temporary
        self.style_default.configure(self.style_name, borderwidth=2, relief='solid')

        # Grid
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1, minsize=100)

        # Bindings
        self.root.bind('<Escape>', self.remove_focus)
        self.root.bind('<Key-space>', self.play)
        self.root.bind('<Up>', self.volume_up)
        self.root.bind('<Down>', self.volume_down)
        self.root.bind('<Right>', self.forward)
        self.root.bind('<Left>', self.back)
        self.root.bind('<KP_Home>', self.start)
        self.root.bind('<KP_End>', self.end)
        self.root.bind('`', lambda e: self.change_playlist_kb(-1))
        self.root.bind('.', lambda e: self.change_playlist_kb(-1))
        for i in range(10):
            self.root.bind(f'{i}', lambda e: self.change_playlist_kb(i))

    def __load_settings(self):
        '''
        Loads settings from json file
        '''
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r', encoding='utf-8') as settings_file:
                self.settings = json.load(settings_file)
        else:
            self.settings = {
                'current playlist': 'All',
                'current track': None,
                'track position': 0.0,
                'queue position': 0,
                'shuffle': False,
                'volume': 0.5,
                'fade': 1000,
                'playlists': {
                    'Playlist 0': [],
                    'Playlist 1': [],
                    'Playlist 2': [],
                    'Playlist 3': [],
                    'Playlist 4': [],
                    'Playlist 5': [],
                    'Playlist 6': [],
                    'Playlist 7': [],
                    'Playlist 8': [],
                    'Playlist 9': []
                }
            }

        self.var_playlist.set(self.settings['current playlist'])
        self.filename = self.settings['current track']
        self.track_pos = float(self.settings['track position'])
        self.queue_pos = int(self.settings['queue position'])
        self.shuffle.set(self.settings['shuffle'])
        self.volume.set(float(self.settings['volume']))
        self.fade.set(int(self.settings['fade']))
        files = os.listdir(self.filepath)
        if self.filename and self.filename in files:
            self.track_name = self.clean_filename(self.filename)

    def __save_settings(self):
        '''
        Saves settings to json file
        '''
        # Get current position of track for next boot
        if self.track_name:
            val = self.sld_progress.get()
            self.track_pos = float(val) * (self.track_length / 100)
        else:
            self.track_pos = 0.0

        self.settings['current playlist'] = self.current_playlist.name
        self.settings['current track'] = self.filename
        self.settings['track position'] = self.track_pos
        self.settings['queue position'] = self.queue_pos
        self.settings['shuffle'] = self.shuffle.get()
        self.settings['volume'] = round(self.volume.get(), 2)
        self.settings['fade'] = self.fade.get()
        self.settings['playlists'] = {}
        for name, obj in self.playlists.items():
            self.settings['playlists'][name] = obj.get_tracks()

        with open(self.settings_path, 'w', encoding='utf-8') as settings_file:
            json.dump(self.settings, settings_file, indent=4)

    def __setup_playlists(self):
        '''
        Create "All" playlist and load saved playlists from settings
        '''
        # Create Track objects, and add all tracks to "All" playlist
        files = os.listdir(self.filepath)
        for track in files:
            self.playlist_all.add_track(self.clean_filename(track), track)
            self.tracks[track] = Track()

        # Create Playlist objects and add their tracks, and add playlists to Track objects
        saved_lists = self.settings['playlists']
        for playlist, tracks in saved_lists.items():
            self.playlists[playlist] = Playlist(playlist)
            for track in tracks:
                if track in files:
                    self.playlists[playlist].add_track(self.clean_filename(track), track)
                    self.tracks[track].add_to_playlist(playlist)

        # Assign current playlist
        cur_playlist = self.settings['current playlist']
        if cur_playlist != 'All':
            self.current_playlist = self.playlists[cur_playlist]
        if self.shuffle.get():
            self.shuffle_songs()

    def __setup_download_frame(self):
        '''
        Sets up the Download Frame
        '''
        # Base Frame
        self.frm_download = Frame(self.root, style=self.style_name)
        self.frm_download.grid(row=0, column=0, padx=50, pady=25, sticky='new')
        self.frm_download.columnconfigure(0, weight=0, minsize=10)
        self.frm_download.columnconfigure(1, weight=1)
        self.frm_download.columnconfigure(2, weight=0, minsize=50)
        self.frm_download.rowconfigure(0, weight=1, minsize=25)
        self.frm_download.rowconfigure(1, weight=1, minsize=25)
        self.frm_download.rowconfigure(2, weight=1, minsize=25)

        # Variables
        self.var_status = StringVar(value='Please enter a URL') # Shows the progress of current download

        # Widgets
        self.lbl_url = Label(self.frm_download, text='URL(s):')
        self.ent_url = Entry(self.frm_download)
        self.ent_url.insert(0, 'https://youtu.be/vz_AChHftws') # A DMCA-free default URL to download. Primarily for testing purposes
        self.btn_download = Button(self.frm_download, text='Download', command=self.download)
        self.bar_progress = Progressbar(master=self.frm_download, orient='horizontal')
        self.btn_cancel = Button(self.frm_download, text='Cancel', command=self.cancel_download)
        self.lbl_status = Label(self.frm_download, textvariable=self.var_status)

        # Grid
        self.lbl_url.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.ent_url.grid(row=0, column=1, sticky='ew')
        self.btn_download.grid(row=0, column=2, padx=5, sticky='e')
        self.bar_progress.grid(row=1, column=1, pady=5, sticky='ew')
        self.btn_cancel.grid(row=1, column=2, padx=5, sticky='e')
        self.lbl_status.grid(row=2, column=1, sticky='ew')

    def __setup_current_playlist_frame(self):
        '''
        Sets up Current Playlist Frame
        '''
        # Base Frame
        self.frm_current_playlist = Frame(self.root, style=self.style_name)
        self.frm_current_playlist.grid(row=1, column=1, padx=25, pady=25, sticky='nsew')
        self.frm_current_playlist.columnconfigure(0, weight=1, minsize=100)
        self.frm_current_playlist.rowconfigure(0, weight=0, minsize=10)
        self.frm_current_playlist.rowconfigure(1, weight=1, minsize=200)

        # Widgets
        self.cb_playlists = Combobox(self.frm_current_playlist, textvariable=self.var_playlist)
        self.cb_playlists['values'] = tuple([self.playlist_all.name]) + tuple(name for name, _ in self.playlists.items())
        self.lb_tracks = Listbox(self.frm_current_playlist)
        for track in self.current_playlist.get_track_names():
            self.lb_tracks.insert(END, track)

        # Grid
        self.cb_playlists.grid(row=0, column=0, padx=10, pady=5, sticky='nw')
        self.lb_tracks.grid(row=1, column=0, padx=10, pady=5, sticky='nsew')

        # Bindings
        self.cb_playlists.bind('<<ComboboxSelected>>', self.change_playlist)
        self.cb_playlists.bind('<Return>', self.rename_playlist)
        self.lb_tracks.bind('<Double-1>', lambda e: self.play_track(self.lb_tracks.get(self.lb_tracks.curselection())))
        self.lb_tracks.bind('<Delete>', lambda e: self.del_track(self.lb_tracks.get(self.lb_tracks.curselection())))

        self.change_playlist(None)

    def __setup_player_frame(self):
        '''
        Sets up track Player Frame
        '''
        # Base Frame
        self.frm_player = Frame(self.root, style=self.style_name)
        self.frm_player.grid(row=1, column=0, padx=25, pady=25, sticky='nsew')
        self.frm_player.columnconfigure(0, weight=0, minsize=100)
        self.frm_player.columnconfigure(1, weight=1, minsize=200)
        self.frm_player.columnconfigure(2, weight=0, minsize=100)
        self.frm_player.rowconfigure(0, weight=1, minsize=50)
        self.frm_player.rowconfigure(1, weight=1, minsize=50)
        self.frm_player.rowconfigure(2, weight=1, minsize=100)

        # Variables
        self.var_title = StringVar(value=self.track_name)
        self.var_progress = StringVar(value='0:00:00')
        self.var_length = StringVar(value='0:00:00')

        # Widgets
        self.lbl_title = Label(self.frm_player, textvariable=self.var_title)
        self.lbl_progress = Label(self.frm_player, textvariable=self.var_progress)
        self.sld_progress = Scale(self.frm_player, orient=HORIZONTAL, from_=0.0, to=100.0)
        self.lbl_length = Label(self.frm_player, textvariable=self.var_length)

        # Grid
        self.lbl_title.grid(row=0, column=0, columnspan=3, padx=5, pady=10, sticky='n')
        self.lbl_progress.grid(row=1, column=0, padx=5, pady=10, sticky='e')
        self.sld_progress.grid(row=1, column=1, padx=5, pady=10, sticky='ew')
        self.lbl_length.grid(row=1, column=2, padx=5, pady=10, sticky='w')

        # Bindings
        self.sld_progress.bind('<ButtonPress-1>', self._on_slider_press)
        self.sld_progress.bind('<ButtonRelease-1>', self._on_slider_release)

        # Inner Frames
        self.__setup_controls_frame()
        self.__setup_volume_frame()
        self.__setup_playlists_frame()

    def __setup_controls_frame(self):
        '''
        Setup the Controls frame inside of the Player frame
        '''
        # Base Frame
        self.frm_controls = Frame(self.frm_player)
        self.frm_controls.grid(row=2, column=1, padx=25, pady=15, sticky='nesw')
        self.frm_controls.columnconfigure(0, weight=1)
        self.frm_controls.columnconfigure(1, weight=1)
        self.frm_controls.columnconfigure(2, weight=1)
        self.frm_controls.rowconfigure(0, weight=0)
        self.frm_controls.rowconfigure(1, weight=0)

        # Variables
        self.var_fade = StringVar(value=f'Fade (ms)')

        # Widgets
        self.btn_start = Button(self.frm_controls, text='|<<')
        self.btn_play = Button(self.frm_controls, text='>/||')
        self.btn_end = Button(self.frm_controls, text='>>|')
        self.sld_fade = Scl(self.frm_controls, orient=HORIZONTAL, from_=0, to=5000, resolution=100, variable=self.fade) #ttk Scale doesn't have resolution option, so fade will use classic Scale
        self.lbl_fade = Label(self.frm_controls, textvariable=self.var_fade)
        self.cbtn_shuffle = Checkbutton(self.frm_controls, text='Shuffle', variable=self.shuffle, command=self.shuffle_songs)

        # Grid
        self.btn_start.grid(row=0, column=0, padx=5, pady=10, sticky='e')
        self.btn_play.grid(row=0, column=1, padx=5, pady=10)
        self.btn_end.grid(row=0, column=2, padx=5, pady=10, sticky='w')
        self.sld_fade.grid(row=1, column=0, padx=5, sticky='nw')
        self.lbl_fade.grid(row=2, column=0, padx=5, sticky='nw')
        self.cbtn_shuffle.grid(row=1, column=1, padx=5, pady=10, sticky='n')

        # Bindings
        self.btn_start.bind('<Button-1>', self.start)
        self.btn_start.bind('<Double-1>', self.prev)
        self.btn_play.bind('<Button-1>', self.play)
        self.btn_end.bind('<Button-1>', self.end)

    def __setup_volume_frame(self):
        '''
        Setup Volume frame inside of the Player frame
        '''
        # Base Frame
        self.frm_volume = Frame(self.frm_player)
        self.frm_volume.grid(row=2, column=2, padx=10, pady=15, sticky='nse')
        self.frm_volume.columnconfigure(0, weight=1, minsize=20)
        self.frm_volume.rowconfigure(0, weight=1, minsize=100)
        self.frm_volume.rowconfigure(1, weight=0, minsize=10)

        # Variables
        self.var_volume = StringVar(value=(int(100 * self.volume.get())))

        # Widgets
        self.sld_volume = Scale(self.frm_volume, orient=VERTICAL, from_=1, to=0, variable=self.volume, command=self.update_volume)
        self.lbl_volume = Label(self.frm_volume, textvariable=self.var_volume)

        # Grid
        self.sld_volume.grid(row=0, column=0, padx=10, pady=5, sticky='nsw')
        self.lbl_volume.grid(row=1, column=0, padx=5, pady=5, sticky='n')

    def __setup_playlists_frame(self):
        '''
        Setup Playlists frame inside of the Player frame
        '''
        # Base Frame
        self.frm_playlists = Frame(self.frm_player, style=self.style_name)
        self.frm_playlists.grid(row=2, column=0, padx=10, pady=15, sticky='nsw')
        self.frm_playlists.columnconfigure(0, weight=1)
        self.frm_playlists.rowconfigure(0, weight=1)

        # Widgets
        self.cnv_playlists = Canvas(self.frm_playlists, borderwidth=0, highlightthickness=0, width= 100, height=180)
        self.scrollbar_playlists = Scrollbar(self.frm_playlists, orient=VERTICAL, command=self.cnv_playlists.yview)
        self.cnv_playlists.configure(yscrollcommand=self.scrollbar_playlists.set)

        # Grid
        self.cnv_playlists.grid(row=0, column=0, sticky='nsew')
        self.scrollbar_playlists.grid(row=0, column=1, sticky='ns')

        # Inner Playlist Frame
        self.frm_playlists_inner = Frame(self.cnv_playlists)
        self.cnv_playlists.create_window((0, 0), window=self.frm_playlists_inner, anchor='nw')

        # Variables, Widgets
        self.playlist_var_names = []
        self.var_playlists = []
        self.cbtn_playlists = []
        for i, (playlist_name, obj) in enumerate(self.playlists.items()):
            self.playlist_var_names.append(StringVar(value=playlist_name))
            if self.filename:
                playlists = self.tracks[self.filename].get_playlists()
            else:
                playlists = []
            if playlist_name in playlists:
                self.var_playlists.append(Variable(value=i))
            else:
                self.var_playlists.append(Variable(value=-i-1))
            self.cbtn_playlists.append(Checkbutton(self.frm_playlists_inner, textvariable=self.playlist_var_names[i], variable=self.var_playlists[i], offvalue=-i-1, onvalue=i, command=self.edit_playlists))
            self.cbtn_playlists[i].grid(row=i, column=0, padx=10, sticky='nw')

        # Bindings
        self.frm_playlists_inner.bind('<Configure>', self._on_frame_configure)
        self.cnv_playlists.bind('<Enter>', self._bind_mousewheel)
        self.cnv_playlists.bind('<Leave>', self._unbind_mousewheel)


# Download Frame Functions

    def _extract_youtube_id(self, url):
        '''
        Helper function to extract YouTube video ID from different formats.

        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/watch?v=VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID
        - URLs with additional parameters
        - Embedded URLs
        '''
        if not url or not isinstance(url, str):
            return None

        # Remove whitespace
        url = url.strip()

        # Pattern for youtu.be short URLs
        youtu_be_pattern = r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtu_be_pattern, url)
        if match:
            return match.group(1)

        # Pattern for youtube.com URLs with v parameter
        youtube_pattern = r'(?:youtube\.com.*[?&]v=)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_pattern, url)
        if match:
            return match.group(1)

        # Pattern for embedded URLs
        embed_pattern = r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
        match = re.search(embed_pattern, url)
        if match:
            return match.group(1)

        # Fallback: try parsing as URL and extract v parameter
        try:
            parsed = urlparse(url)
            if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                if 'v' in query_params:
                    video_id = query_params['v'][0]
                    # Validate video ID format (11 characters, alphanumeric + _ -)
                    if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                        return video_id
        except:
            pass
        
        return None

    def _yt_progress_hook(self, d):
        '''
        Update progress bar and status as track is downloaded
        '''
        # Check if download should be cancelled
        if self.cancel_flag.is_set():
            raise Exception('Download cancelled by user')

        filename = d.get('filename', '')
        if d['status'] == 'downloading':
            # this MIGHT work for playlists
            if filename == self.filename:
                print(F'FILENAME: {filename}, CURRENT: {self.filename}')
                if mixer.music.get_busy():
                        mixer.music.stop()
                        mixer.music.unload()
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                self.root.after(0, lambda: self.bar_progress.config(value=percent))
                self.root.after(0, lambda: self.var_status.set(f'Downloading {self.clean_filename(os.path.basename(filename))} ({self.cur_download + 1}/?)... {percent:.1f}%'))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.bar_progress.config(value=100))
            self.root.after(0, lambda: self.var_status.set(f'{self.clean_filename(os.path.basename(filename))} finished ({self.cur_download + 1}/?), processing...'))

    def download(self):
        '''
        Begin download of URLs.

        NOTE Must be separated by a comma,
        space is optional and will be removed if necessary.
        In the case that the ID of any video being downloaded
        matches the currently playing track, the current track
        will be stopped and unloaded. The progress updater
        will detect this and move to the next track in the queue.
        '''

        self.cancel_flag.clear()
        self.var_status.set('Preparing...')
        self.bar_progress.config(value=0)
        entry = self.ent_url.get()
        urls = entry.split(',')

        # Run download in a separate thread to avoid blocking the GUI
        self.download_thread = threading.Thread(target=self._download_thread, args=(urls,), daemon=True)
        self.download_thread.start()

    def _download_thread(self, urls):
        '''
        Download each url provided, single videos or playlists
        '''
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                ydl.add_post_processor(UIUpdatePostProcessor(self))
                for url in urls:
                    if self.cancel_flag.is_set():
                        self.root.after(0, lambda: self.var_status.set(f'Download cancelled. Downloaded {self.cur_download} out of {total_entries} tracks.'))
                        return
                    url = url.strip()
                    # Stop current track if needed
                    if mixer.music.get_busy():
                        if self._extract_youtube_id(url) == self.filename[-16:-5]:
                            mixer.music.stop()
                            mixer.music.unload()

                    # Download (playlist or single)
                    info = ydl.extract_info(url, download=True)

                    if 'entries' in info:
                        entries = info['entries']
                        total_entries = len(entries)
                        self.root.after(0, lambda: self.var_status.set(f'Playlist download complete! Downloaded {self.cur_download} out of {total_entries} tracks.'))
                    else:
                        # filename = ydl.prepare_filename(info)
                        # mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                        # basename = os.path.basename(mp3_filename)
                        self.root.after(0, lambda: self.var_status.set('Success!'))

        except Exception as e:
            if self.cancel_flag.is_set():
                self.root.after(0, lambda: self.var_status.set('Download cancelled'))
            else:
                self.root.after(0, lambda: self.var_status.set('Error'))
                self.root.after(0, lambda e=e: messagebox.showerror('Error', f'Error: {e}'))

    def cancel_download(self):
        '''
        Cancel the current download and remove any .part files
        '''
        try:
            self.cancel_flag.set()
            self.var_status.set('Cancelling download...')
            # If download thread is running, wait for it to finish
            if hasattr(self, 'download_thread') and self.download_thread and self.download_thread.is_alive():
                self.download_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish

            # Remove any .part files in the download directory
            for fname in os.listdir(self.filepath):
                if fname.endswith('.part'):
                    try:
                        os.remove(os.path.join(self.filepath, fname))
                    except Exception as e:
                        print(f'Error removing {fname}: {e}')

            self.var_status.set('Download cancelled')
            self.bar_progress.config(value=0)
        except Exception as e:
            self.var_status.set(f'Error cancelling download: {e}')


# Playback

    def play_track(self, name):
        '''
        Finds the corresponding file and plays the track, while updating the UI
        '''
        self.track_name = name
        try:
            self.filename = self.current_playlist.get_track(name)
        except:
            self.filename = self.playlist_all.get_track(name)
        self.audio_info = MP3(f'{self.filepath}/{self.filename}').info
        self.track_length = int(self.audio_info.length)
        self.track_pos = 0  # Track position in ms
        self.is_playing = False
        self.last_play_time = None

        playlists = self.tracks[self.filename].get_playlists()
        for i, var in enumerate(self.playlist_var_names):
            if var.get() in playlists:
                self.var_playlists[i].set(i)
            else:
                self.var_playlists[i].set(-i-1)

        mixer.music.stop()
        mixer.music.unload()
        self.var_title.set(self.track_name)
        mixer.music.load(f'{self.filepath}/{self.filename}')
        hours, mins, secs = self._get_track_len(self.track_length)
        self.var_length.set(f'{hours}:{mins:02}:{secs:02}')
        mixer.music.play(fade_ms=self.fade.get())
        mixer.music.pause()
        self.start(None)
        self.play(None)

    def start(self, event):
        '''
        Set player back to start of track
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url:
            self.sld_progress.set(0)
            self.var_progress.set('0:00:00')
            mixer.music.rewind()
            self.last_play_time = None
            self.track_pos = 0

    def prev(self, event):
        '''
        Go back to previous track
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url and self.prev_tracks:
            track = self.prev_tracks[0]
            self.prev_tracks = self.prev_tracks[1:]
            self.current_playlist.queue.insert(0, self.track_name)
            self.play_track(track)

    def play(self, event):
        '''
        Play/Pause track
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url and self.track_name != '':
            if mixer.music.get_busy():
                mixer.music.pause()
                self.is_playing = False
                if self.last_play_time:
                    # Add elapsed time since last unpause to track_pos
                    self.track_pos += (time.time() - self.last_play_time)
                    self.last_play_time = None
            else:
                mixer.music.unpause()
                self.is_playing = True
                self.last_play_time = time.time()
                self._start_progress_updater()  # Start updating progress

    def end(self, event):
        '''
        Go to end of track and fadeout, then transition to next track
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url and self.track_name != '':
            self.sld_progress.set(100)
            hours, mins, secs = self._get_track_len(self.track_length)
            self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')

            self._transition()

    def shuffle_songs(self):
        '''
        Shuffle current queue
        '''
        if self.shuffle.get():
            self.current_playlist.shuffle_queue()
        else:
            self.current_playlist.new_queue()

    def forward(self, event):
        '''
        Skip ahead 5 seconds in current track
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url:
            # Update track_pos with elapsed time
            if self.is_playing and self.last_play_time:
                self.track_pos += (time.time() - self.last_play_time)
            self.track_pos = min(self.track_pos + 5, self.track_length)
            mixer.music.rewind()
            mixer.music.set_pos(self.track_pos)
            hours, mins, secs = self._get_track_len(self.track_pos)
            self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
            self.sld_progress.set(100 * self.track_pos / self.track_length)
            if self.is_playing:
                self.last_play_time = time.time()
            else:
                self.last_play_time = None

    def back(self, event):
        '''
        Skip backwards 5 seconds in current track
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url:
            # Update track_pos with elapsed time
            if self.is_playing and self.last_play_time:
                self.track_pos += (time.time() - self.last_play_time)
            self.track_pos = max(self.track_pos - 5, 0)
            mixer.music.rewind()
            mixer.music.set_pos(self.track_pos)
            hours, mins, secs = self._get_track_len(self.track_pos)
            self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
            self.sld_progress.set(100 * self.track_pos / self.track_length)
            if self.is_playing:
                self.last_play_time = time.time()
            else:
                self.last_play_time = None

    def _on_slider_press(self, event):
        '''
        Helper function for preventing progress slider from moving while clicked
        '''
        self.progress_bar_in_use = True

    def _on_slider_release(self, event):
        '''
        Helper function for allowing progress slider to move once it is released
        '''
        self.progress_bar_in_use = False
        self.seek_track(event)

    def seek_track(self, event):
        '''
        When progress slider is moved, this will update the track to match the current position of the slider
        '''
        val = self.sld_progress.get()
        self.track_pos = float(val) * (self.track_length / 100)
        mixer.music.rewind()
        mixer.music.set_pos(self.track_pos)
        hours, mins, secs = self._get_track_len(self.track_pos)
        self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
        if self.is_playing:
            self.last_play_time = time.time()
        else:
            self.last_play_time = None

    def volume_up(self, event):
        '''
        Increase volume by 10%
        '''
        if self.root.focus_get() == self.root:
            self.volume.set(round(min(self.volume.get() + 0.1, 1), 2))
            mixer.music.set_volume(self.volume.get())
            self.var_volume.set(int(100 * self.volume.get()))

    def volume_down(self, event):
        '''
        Decrease volume by 10%
        '''
        if self.root.focus_get() == self.root:
            self.volume.set(round(max(self.volume.get() - 0.1, 0), 2))
            mixer.music.set_volume(self.volume.get())
            self.var_volume.set(int(100 * self.volume.get()))

    def update_volume(self, val):
        '''
        Change volume based on slider
        '''
        val = round(float(val), 2)
        mixer.music.set_volume(self.volume.get())
        self.volume.set(round(self.volume.get(), 2))
        self.var_volume.set(int(val * 100))

    def _start_progress_updater(self):
        '''
        Continuously updates progress slider to reflect current position of current track
        '''
        if self.is_playing:
            if not mixer.music.get_busy():
                # Playback finished
                self.is_playing = False
                self.track_pos = self.track_length
                hours, mins, secs = self._get_track_len(self.track_length)
                self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
                self.sld_progress.set(100)
                self._transition()
                return
            # Calculate current position
            if self.last_play_time:
                elapsed = time.time() - self.last_play_time
                current_pos = self.track_pos + elapsed
            else:
                current_pos = self.track_pos
            hours, mins, secs = self._get_track_len(current_pos)
            self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
            if not self.progress_bar_in_use:
                self.sld_progress.set(100 * current_pos / self.track_length)
            # Schedule next update
            self.root.after(100, self._start_progress_updater)

    def _get_track_len(self, length):
        '''
        Helper function for formatting track length
        '''
        hours = int(length // 3600)
        length %= 3600
        mins = int(length // 60)
        length %= 60
        secs = int(length)

        return hours, mins, secs    

    def _transition(self):
        '''
        Helper function for fading track out and fading next track in
        '''
        mixer.music.fadeout(self.fade.get())
        self.prev_tracks.insert(0, self.track_name)
        mixer.music.unload()
        self.play_track(self.clean_filename(self.current_playlist.queue_pop(self.shuffle.get())))


# Playlists

    def del_track(self, name):
        '''
        Prompts user to confirm deletion of track
        '''
        self.top = Toplevel(self.root)
        self.top.title('Confirmation')
        self.top.geometry(f'300x100+{self.root.winfo_x() + 250}+{self.root.winfo_y() + 150}')
        self.top.grab_set()
        warning = 'Delete file?'
        Label(self.top, text=warning).pack(padx=20, pady=10)
        
        frm_controls = Frame(self.top)
        frm_controls.pack(pady=10)

        Button(frm_controls, text='DELETE', width=10, command=lambda: self.on_delete(name)).pack(side=LEFT, padx=5)
        Button(frm_controls, text='CANCEL', width=10, command=self.top.destroy).pack(side=LEFT, padx=5)

    def on_delete(self, name):
        '''
        Deletes file
        '''
        filename = self.playlist_all.get_track(name)
        if self.track_name == name:
            mixer.music.stop()
            mixer.music.unload()
            self.var_title.set('')
            self.var_progress.set('0:00:00')
            self.var_length.set('0:00:00')
            self.sld_progress.set(0)
            self.track_name = ''
            self.filename = ''
        self.playlist_all.remove_track(name)
        for p_name, playlist in self.playlists.items():
            if filename in playlist.get_tracks():
                playlist.remove_track(name)
                self.tracks[filename].remove_from_playlist(p_name)
        self.change_playlist(None)
        os.remove(f'{self.filepath}/{filename}')
        self.top.destroy()

    def change_playlist_kb(self, num):
        '''
        Change playlist using keyboard
        '''
        focus = self.root.focus_get()
        if focus != self.cb_playlists and focus != self.ent_url:
            playlists = list(self.playlists.keys())
            if num == -1:
                self.cb_playlists.set('All')
            else:
                self.cb_playlists.set(playlists[num])
            self.change_playlist(None)

    def change_playlist(self, event):
        '''
        Updates current playlist and list of tracks in playlist frame based on currently selected playlist
        '''
        playlist = self.cb_playlists.get()
        if playlist == 'All':
            self.current_playlist = self.playlist_all
        else:
            self.current_playlist = self.playlists[playlist]
        self.lb_tracks.delete(0, END)
        for track in self.current_playlist.get_track_names():
            self.lb_tracks.insert(END, track)

    def edit_playlists(self):
        '''
        Updates which playlists a track is in based on the checkboxes. A bit redundant going over all of them
        '''
        if self.track_name != '':
            for i, var in enumerate(self.var_playlists):
                val = var.get()
                playlists = list(self.playlists.keys())
                if val >= 0:
                    self.playlists[playlists[val]].add_track(self.track_name, self.filename)
                    self.tracks[self.filename].add_to_playlist(self.playlists[playlists[val]].name)
                    if playlists[val] == self.current_playlist.name:
                        self.lb_tracks.insert(END, self.track_name)
                else:
                    try:
                        self.playlists[playlists[-val-1]].remove_track(self.track_name)
                        self.tracks[self.filename].remove_from_playlist(self.playlists[playlists[-val-1]].name)
                        if playlists[-val-1] == self.current_playlist.name:
                            tracks = self.lb_tracks.get(0, END)
                            for i, track in enumerate(tracks):
                                if track == self.track_name:
                                    self.lb_tracks.delete(i)
                    except:
                        pass

    def rename_playlist(self, event):
        '''
        Change playlist name based on Combobox
        '''
        oldname = self.current_playlist.name
        newname = self.cb_playlists.get()
        if oldname == 'All':
            messagebox.showerror('Can\'t change name', '"All" playlist name cannot be changed.')
            self.cb_playlists.set('All')
            return
        if newname in self.playlists.keys():
            if newname == oldname:
                return
            messagebox.showerror('Can\'t change name', 'Playlist name already in use.')
            self.cb_playlists.set(oldname)
            return
        self.playlists[oldname].set_name(newname)
        self.playlists = {name if name != oldname else newname: playlist for name, playlist in self.playlists.items()}
        self.current_playlist = self.playlists[newname]
        for track in self.current_playlist.get_tracks():
            self.tracks[track].remove_from_playlist(oldname)
            self.tracks[track].add_to_playlist(newname)
        for var in self.var_playlists:
            if var.get() == oldname:
                var.set(newname)
        for var in self.playlist_var_names:
            if var.get() == oldname:
                var.set(newname)
        self.cb_playlists['values'] = tuple([self.playlist_all.name]) + tuple({name if name != oldname else newname: name for name in self.playlists.keys()})
        self.remove_focus(None)


# Navigation

    def _on_mousewheel(self, event):
        '''
        Scrolls list of playlist checkboxes for current track
        '''
        self.cnv_playlists.yview_scroll(int(-1*(event.delta/120)), 'units')

    def _bind_mousewheel(self, event):
        '''
        Helper function for only scrolling playlist checkboxes when hovering over them
        '''
        self.cnv_playlists.bind_all('<MouseWheel>', self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        '''
        Helper function for not scrolling playlsit checkboxes when not hovering over them
        '''
        self.cnv_playlists.unbind_all('<MouseWheel>')

    def remove_focus(self, event):
        '''
        Removes focus on any widget to allow for volume controls thru keyboard
        '''
        self.root.focus_set()

    def on_close(self):
        '''
        Closing function to save settings
        '''
        self.__save_settings()
        # Now destroy the window
        self.root.destroy()

    def _on_frame_configure(self, event):
        '''
        Limits scrollable area to just the playlists
        '''
        self.cnv_playlists.configure(scrollregion=self.cnv_playlists.bbox('all'))

# Helper Functions

    def clean_filename(self, file):
        '''
        Helper function for taking raw filename with ID and extension, and trimming to only name (based on yt_dlp default filename)
        '''
        index = file.index('[')
        name = file[:index-1].replace('_', ' ')
        return name

    def _resource_path(self, relative_path):
        '''
        Get absolute path to resource, works for dev and for PyInstaller
        '''
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath('.')
        return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    try:
        root = Tk()
        MusicBox(root)
        root.mainloop()
    except Exception as e:
        try:
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(traceback.format_exc())
            root = Tk()
            root.withdraw()
            messagebox.showerror('Error', 'An unexpected error occurred. See error_log.txt for details.')
            root.destroy()
        except:
            pass