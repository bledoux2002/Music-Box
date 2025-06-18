import os
import sys
import json
import time
import threading
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import Scale as Scl
from yt_dlp import YoutubeDL
# import mutagen
from mutagen.mp3 import MP3
from pygame import mixer
from tracks import Playlist, Track

class MusicBox:

# Core

    def __init__(self, root):
        # Directory Information
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.filepath = self._resource_path('files')
        self.files = os.listdir(self.filepath)
        
        self.settings = {}

        # Mixer
        # add 2 channels for fade in/out
        mixer.init()
        self.volume = DoubleVar()
        self.fade = IntVar()
        self.cur_track = None
        self.prev_tracks = []
        self.shuffle = BooleanVar()

        # TKinter Setup
        self.root = root
        root.configure(bg='medium purple')
        root.minsize(750, 450)
        self.root.title('Adaptive Music Box')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        self.style_default = Style()
        self.style_name = 'Outlined.TFrame' # helps show where frames are, mostly temporary
        self.style_default.configure(self.style_name, borderwidth=2, relief='solid')

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1, minsize=100)
        
        self.root.bind('<Escape>', self.remove_focus)
        
        self.progress_bar_in_use = False

        self.playlist_all = Playlist('All')
        self.tracks = {}
        for track in self.files:
            self.playlist_all.add_track(self._clean_filename(track), track)
            self.tracks[track] = Track()

        # TKinter Vars
        self.var_playlist = StringVar()

        # Setup
        self.__load_settings()
        self.__setup_playlists()
        
        # Current Track and Playlist
        # self.filename = self.playlist.queue_pop(self.shuffle.get())
        self.filename = self.cur_track
        if self.filename:
            self.track_name = self._clean_filename(self.filename)
        else:
            self.track_name = ''
        mixer.music.set_volume(self.volume.get())

        # Setup Frames
        self.__setup_download_frame()
        self.__setup_playlists_frame()
        self.__setup_player_frame()
        
        # YT_DLP Options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'windowsFilenames': True,
            'paths': {
                'home': './files',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'progress_hooks': [self._yt_progress_hook],
            'nooverwrites': True,
        }

        if (self.filename):
            self.play_track(self.track_name)
            self.track_pos = float(self.settings['current position'])
            self.sld_progress.set(100 * self.track_pos / self.track_length)
            self.seek_track(None)
            self.play(None)

    def __setup_download_frame(self):
        '''
        Sets up the Download Frame
        '''
        self.frm_download = Frame(self.root, style=self.style_name)
        self.frm_download.grid(row=0, column=0, padx=50, pady=25, sticky='new')
        self.frm_download.columnconfigure(0, weight=0, minsize=10)
        self.frm_download.columnconfigure(1, weight=1)
        self.frm_download.columnconfigure(2, weight=0, minsize=50)
        self.frm_download.rowconfigure(0, weight=1, minsize=25)
        self.frm_download.rowconfigure(1, weight=1, minsize=25)
        self.frm_download.rowconfigure(2, weight=1, minsize=25)

        self.lbl_url = Label(self.frm_download, text='URL:')
        self.ent_url = Entry(self.frm_download)
        self.ent_url.insert(0, 'https://youtu.be/FcaHJDj6KEE')
        self.btn_url = Button(self.frm_download, text='Download')
        self.bar_progress = Progressbar(master=self.frm_download, orient='horizontal')
        self.var_status = StringVar(value='Please enter a URL')
        self.lbl_status = Label(self.frm_download, textvariable=self.var_status)

        self.lbl_url.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.ent_url.grid(row=0, column=1, sticky='ew')
        self.btn_url.grid(row=0, column=2, padx=5, sticky='e')
        self.bar_progress.grid(row=1, column=1, pady=5, sticky='ew')
        self.lbl_status.grid(row=2, column=1, sticky='ew')

        self.btn_url.bind('<Button-1>', self.download)

    def __setup_player_frame(self):
        '''
        Sets up track Player Frame
        '''
        self.frm_player = Frame(self.root, style=self.style_name)
        self.frm_player.grid(row=1, column=0, padx=25, pady=25, sticky='nsew')
        self.frm_player.columnconfigure(0, weight=0, minsize=100)
        self.frm_player.columnconfigure(1, weight=1, minsize=200)
        self.frm_player.columnconfigure(2, weight=0, minsize=100)
        self.frm_player.rowconfigure(0, weight=1, minsize=50)
        self.frm_player.rowconfigure(1, weight=1, minsize=50)
        self.frm_player.rowconfigure(2, weight=1, minsize=100)

        self.var_title = StringVar(value=self.track_name)
        self.lbl_title = Label(self.frm_player, textvariable=self.var_title)

        self.var_progress = StringVar(value='0:00:00')
        self.lbl_progress = Label(self.frm_player, textvariable=self.var_progress)
        self.sld_progress = Scale(self.frm_player, orient=HORIZONTAL, from_=0.0, to=100.0)
        self.var_length = StringVar(value='0:00:00')
        self.lbl_length = Label(self.frm_player, textvariable=self.var_length)

        # Navigation
        self.frm_buttons = Frame(self.frm_player)
        self.frm_buttons.grid(row=2, column=1, padx=25, pady=15, sticky='nesw')
        self.frm_buttons.columnconfigure(0, weight=1)
        self.frm_buttons.columnconfigure(1, weight=1)
        self.frm_buttons.columnconfigure(2, weight=1)
        self.frm_buttons.rowconfigure(0, weight=0)
        self.frm_buttons.rowconfigure(1, weight=0)

        self.btn_start = Button(self.frm_buttons, text='|<<')
        self.btn_play = Button(self.frm_buttons, text='>/||')
        self.btn_end = Button(self.frm_buttons, text='>>|')
        self.sld_fade = Scl(self.frm_buttons, orient=HORIZONTAL, from_=0, to=5000, resolution=100, variable=self.fade)
        self.var_fade = StringVar(value=f'Fade (ms)')
        self.lbl_fade = Label(self.frm_buttons, textvariable=self.var_fade)
        self.cbtn_shuffle = Checkbutton(self.frm_buttons, text='Shuffle', variable=self.shuffle, command=self.shuffle_songs)

        self.lbl_title.grid(row=0, column=0, columnspan=3, padx=5, pady=10, sticky='n')
        self.lbl_progress.grid(row=1, column=0, padx=5, pady=10, sticky='e')
        self.sld_progress.grid(row=1, column=1, padx=5, pady=10, sticky='ew')
        self.lbl_length.grid(row=1, column=2, padx=5, pady=10, sticky='w')

        self.btn_start.grid(row=0, column=0, padx=5, pady=10, sticky='e')
        self.btn_play.grid(row=0, column=1, padx=5, pady=10)
        self.btn_end.grid(row=0, column=2, padx=5, pady=10, sticky='w')
        self.sld_fade.grid(row=1, column=0, padx=5, sticky='nw')
        self.lbl_fade.grid(row=2, column=0, padx=5, sticky='nw')
        self.cbtn_shuffle.grid(row=1, column=1, padx=5, pady=10, sticky='n')

        # Volume
        self.frm_volume = Frame(self.frm_player)
        self.frm_volume.grid(row=2, column=2, padx=10, pady=15, sticky='nse')
        self.frm_volume.columnconfigure(0, weight=1, minsize=20)
        self.frm_volume.rowconfigure(0, weight=1, minsize=100)
        self.frm_volume.rowconfigure(1, weight=0, minsize=10)

        self.sld_volume = Scale(self.frm_volume, orient=VERTICAL, from_=1, to=0, variable=self.volume, command=self.update_volume)
        self.var_volume = StringVar(value=(int(100 * self.volume.get())))
        self.lbl_volume = Label(self.frm_volume, textvariable=self.var_volume)

        self.sld_volume.grid(row=0, column=0, padx=10, pady=5, sticky='nsw')
        self.lbl_volume.grid(row=1, column=0, padx=5, pady=5, sticky='n')

        # Playlist with Scrollbar
        self.frm_playlists = Frame(self.frm_player, style=self.style_name)
        self.frm_playlists.grid(row=2, column=0, padx=10, pady=15, sticky='nsw')
        self.frm_playlists.columnconfigure(0, weight=1)
        self.frm_playlists.rowconfigure(0, weight=1)

        # Canvas and Scrollbar for scrolling checkbuttons
        self.cnv_playlists = Canvas(self.frm_playlists, borderwidth=0, highlightthickness=0, width= 100, height=180)
        self.scrollbar_playlists = Scrollbar(self.frm_playlists, orient=VERTICAL, command=self.cnv_playlists.yview)
        self.cnv_playlists.configure(yscrollcommand=self.scrollbar_playlists.set)

        self.cnv_playlists.grid(row=0, column=0, sticky='nsew')
        self.scrollbar_playlists.grid(row=0, column=1, sticky='ns')

        # Frame inside canvas to hold checkbuttons
        self.frm_playlists_inner = Frame(self.cnv_playlists)
        self.cnv_playlists.create_window((0, 0), window=self.frm_playlists_inner, anchor='nw')

        self.playlist_var_names = []
        self.cbtn_playlists = []
        self.var_playlists = []
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

        self.btn_start.bind('<Button-1>', self.start)
        self.btn_start.bind('<Double-1>', self.prev)
        self.btn_play.bind('<Button-1>', self.play)
        self.btn_end.bind('<Button-1>', self.end)
        self.sld_progress.bind('<ButtonPress-1>', self._on_slider_press)
        self.sld_progress.bind('<ButtonRelease-1>', self._on_slider_release)
        self.root.bind('<Key-space>', self.play)
        self.root.bind('<Right>', self.forward)
        self.root.bind('<Left>', self.back)
        self.root.bind('<Up>', self.volume_up)
        self.root.bind('<Down>', self.volume_down)
        self.root.bind('<KP_Home>', self.start)
        self.root.bind('<KP_End>', self.end)
        self.frm_playlists_inner.bind('<Configure>', self._on_frame_configure)
        self.cnv_playlists.bind('<Enter>', self._bind_mousewheel)
        self.cnv_playlists.bind('<Leave>', self._unbind_mousewheel)

    def __setup_playlists_frame(self):
        '''
        Sets up Playlists Frame
        '''
        self.frm_playlist = Frame(self.root, style=self.style_name)
        self.frm_playlist.grid(row=1, column=1, padx=25, pady=25, sticky='nsew')

        self.frm_playlist.columnconfigure(0, weight=1, minsize=100)
        self.frm_playlist.rowconfigure(0, weight=0, minsize=10)
        self.frm_playlist.rowconfigure(1, weight=1, minsize=200)

        self.cb_playlists = Combobox(self.frm_playlist, textvariable=self.var_playlist)
        self.cb_playlists['values'] = tuple([self.playlist_all.name]) + tuple(name for name, _ in self.playlists.items())
        self.lb_tracks = Listbox(self.frm_playlist)
        for track in self.playlist.get_track_names():
            self.lb_tracks.insert(END, track)

        self.cb_playlists.grid(row=0, column=0, padx=10, pady=5, sticky='nw')
        self.lb_tracks.grid(row=1, column=0, padx=10, pady=5, sticky='nsew')

        self.cb_playlists.bind('<<ComboboxSelected>>', self.change_playlist)
        self.lb_tracks.bind('<Double-1>', lambda e: self.play_track(self.lb_tracks.get(self.lb_tracks.curselection())))
        self.lb_tracks.bind('<Delete>', lambda e: self.del_track(self.lb_tracks.get(self.lb_tracks.curselection())))

        self.change_playlist(None)

    def __load_settings(self):
        '''
        Loads settings from json file
        '''
        settings_path = self._resource_path('settings.json')
        with open(settings_path, 'r', encoding='utf-8') as settings_file:
            self.settings = json.load(settings_file)
        self.volume.set(float(self.settings['volume']))
        self.fade.set(int(self.settings['fade']))
        self.cur_track = self.settings['current track']
        self.shuffle.set(self.settings['shuffle'])
        self.var_playlist.set(self.settings['playlist'])

    def __save_settings(self):
        '''
        Saves settings to json file
        '''
        if self.track_name != '':
            val = self.sld_progress.get()
            self.track_pos = float(val) * (self.track_length / 100)
        else:
            self.track_pos = 0.0
        settings_path = self._resource_path('settings.json')
        self.settings['volume'] = self.volume.get()
        self.settings['fade'] = self.fade.get()
        self.settings['current track'] = self.filename
        self.settings['current position'] = self.track_pos
        self.settings['shuffle'] = self.shuffle.get()
        self.settings['playlist'] = self.playlist.name
        del self.settings['playlists']
        self.settings['playlists'] = {}
        for playlist, obj in self.playlists.items():
            self.settings['playlists'][playlist] = obj.get_tracks()
        with open(settings_path, 'w', encoding='utf-8') as settings_file:
            json.dump(self.settings, settings_file, indent=4)

    def __setup_playlists(self):
        self.playlists = {}
        saved_lists = self.settings['playlists']
        for playlist, tracks in saved_lists.items():
            self.playlists[playlist] = Playlist(playlist)
            for track in tracks:
                self.playlists[playlist].add_track(self._clean_filename(track), track)
                self.tracks[track].add_to_playlist(playlist)
        if self.settings['playlist'] != 'All':
            self.playlist = self.playlists[self.settings['playlist']]
        else:
            self.playlist = self.playlist_all


# Downloading

    def _yt_progress_hook(self, d):
        '''
        Update progress bar and status
        '''
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                # Update progress bar in the main thread
                self.root.after(0, lambda: self.bar_progress.config(value=percent))
                self.root.after(0, lambda: self.var_status.set(f'Downloading... {percent:.1f}%'))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.bar_progress.config(value=100))
            self.root.after(0, lambda: self.var_status.set('Download finished, processing...'))

    def download(self, event):
        self.var_status.set('Preparing...')
        if mixer.music.get_busy():
            mixer.music.stop()
        try:
            mixer.music.unload()
        except:
            pass
        self.bar_progress.config(value=0)
        url = self.ent_url.get()
        URLs = [url]
        # Run download in a separate thread to avoid blocking the GUI
        threading.Thread(target=self._download_thread, args=(URLs,), daemon=True).start()

    def _download_thread(self, URLs):
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                for url in URLs:
                    info = ydl.extract_info(url, download=True)  # Don't download yet
                    filename = ydl.prepare_filename(info)
                    mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                    basename = os.path.basename(mp3_filename)
                    self.playlist_all.add_track(self._clean_filename(basename), basename)
                    self.tracks[basename] = Track()
                    self.change_playlist(None)
                    self.root.after(0, self.var_status.set, 'Success!')
        except Exception as e:
            self.root.after(0, self.var_status.set, f'Error: {e}')


# Functionality

    def remove_focus(self, event):
        '''
        Removes focus on any widget to allow for volume controls thru keyboard
        '''
        self.root.focus_set()

    def start(self, event):
        '''
        Set player back to start of track
        '''
        self.sld_progress.set(0)
        self.var_progress.set('0:00:00')
        mixer.music.rewind()
        self.last_play_time = None
        self.track_pos = 0

    def prev(self, event):
        '''
        Go back to previous track
        '''
        track = self.prev_tracks[0]
        self.prev_tracks = self.prev_tracks[1:]
        self.playlist.queue.insert(0, self.track_name)
        self.play_track(track)

    def play(self, event):
        '''
        Play/Pause track
        '''
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
        self.sld_progress.set(100)
        hours, mins, secs = self._get_track_len(self.track_length)
        self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
        
        self._transition()

    def shuffle_songs(self):
        '''
        Shuffle current queue
        '''
        if self.shuffle.get():
            self.playlist.shuffle_queue()
        else:
            self.playlist.new_queue()

    def forward(self, event):
        '''
        Skip ahead 5 seconds in current track
        '''
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
        mixer.music.set_volume(self.volume.get())
        self.var_volume.set(int(float(val) * 100))

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

    def _on_frame_configure(self, event):
        '''
        Uhhhh this might be unnecessary. The code is important but it might not need to be in this separate function
        '''
        self.cnv_playlists.configure(scrollregion=self.cnv_playlists.bbox('all'))

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
    
    def _transition(self):
        '''
        Helper function for fading track out and fading next track in
        '''
        mixer.music.fadeout(self.fade.get())
        self.prev_tracks.insert(0, self.track_name)
        mixer.music.unload()
        self.play_track(self._clean_filename(self.playlist.queue_pop(self.shuffle.get())))

    def play_track(self, name):
        '''
        Finds the corresponding file and plays the track, while updating the UI
        '''
        self.track_name = name
        try:
            self.filename = self.playlist.get_track(name)
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

    def del_track(self, name):
        self.top = Toplevel(self.root)
        self.top.title('Confirmation')
        self.top.grab_set()
        warning = 'Delete file?'
        Label(self.top, text=warning).pack(padx=20, pady=10)
        
        frm_buttons = Frame(self.top)
        frm_buttons.pack(pady=10)

        Button(frm_buttons, text='DELETE', width=10, command=lambda: self.on_delete(name)).pack(side=LEFT, padx=5)
        Button(frm_buttons, text='CANCEL', width=10, command=self.top.destroy).pack(side=LEFT, padx=5)

    def on_delete(self, name):
        filename = self.playlist_all.get_track(name)
        if self.track_name == name:
            mixer.music.stop()
            mixer.music.unload()
            self.var_title.set('')
            self.var_progress.set('0:00:00')
            self.var_length.set('0:00:00')
            self.sld_progress.set(0)
        self.playlist_all.remove_track(name)
        for p_name, playlist in self.playlists.items():
            if filename in playlist.get_tracks():
                playlist.remove_track(name)
                self.tracks[filename].remove_from_playlist(p_name)
        self.change_playlist(None)
        os.remove(f'{self.filepath}/{filename}')
        self.top.destroy()

    def change_playlist(self, event):
        '''
        Updates current playlist and list of tracks in playlist frame based on currently selected playlist
        '''
        playlist = self.cb_playlists.get()
        if playlist == 'All':
            self.playlist = self.playlist_all
        else:
            self.playlist = self.playlists[playlist]
        self.lb_tracks.delete(0, END)
        for track in self.playlist.get_track_names():
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
                    if playlists[val] == self.playlist.name:
                        self.lb_tracks.insert(END, self.track_name)
                else:
                    try:
                        self.playlists[playlists[-val-1]].remove_track(self.track_name)
                        self.tracks[self.filename].remove_from_playlist(self.playlists[playlists[-val-1]].name)
                        if playlists[-val-1] == self.playlist.name:
                            tracks = self.lb_tracks.get(0, END)
                            for i, track in enumerate(tracks):
                                if track == self.track_name:
                                    self.lb_tracks.delete(i)
                    except:
                        pass

    def _clean_filename(self, file):
        '''
        Helper function for taking raw filename with ID and extension, and trimming to only name (based on yt_dlp default filename)
        '''
        index = file.index('[')
        return file[:index-1]

    def on_close(self):
        '''
        Closing function to save settings
        '''
        self.__save_settings()
        # Now destroy the window
        self.root.destroy()

    def _resource_path(self, relative_path):
        '''
        Get absolute path to resource, works for dev and for PyInstaller
        '''
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath('.')
        return os.path.join(base_path, relative_path)

def main():
    root = Tk()
    MusicBox(root)
    root.mainloop()

if __name__ == '__main__':
    main()