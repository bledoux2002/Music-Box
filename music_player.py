import os
from tkinter import *
from tkinter.ttk import *
from pygame import mixer
import mutagen
from mutagen.mp3 import MP3
import threading
from yt_dlp import YoutubeDL
import time

class MusicBox:

    def __init__(self, root):
        # Directory Information
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.filepath = self.path + '/files'
        print(self.filepath)
        self.files = os.listdir(self.filepath)

        # Current Track and Playlist
        self.track_name = self.files[0] # change to only name
        self.filename = self.files[0]
        self.audio_info = MP3(f'{self.filepath}/{self.filename}').info
        self.track_length = int(self.audio_info.length)
        self.track_pos = 0  # Track position in ms
        self.is_playing = False
        self.last_play_time = None
        self.volume = DoubleVar()
        self.volume.set(0.5)

        self.all_tracks = Playlist('All')
        for track in self.files:
            self.all_tracks.add_track(self._clean_filename(track), track)
        self.playlists = []
        for i in range(10): #change to have their own names saved in json file (each listed under playlistN has a name att and the dict of tracks)
            self.playlists.append(Playlist(f'Playlist {i}'))

        self.playlist = self.all_tracks

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

        # TKinter Setup
        self.root = root
        root.configure(bg='medium purple')
        root.minsize(750, 500)
        self.root.title('Adaptive Music Box')

        self.style_default = Style()
        self.style_name = 'Outlined.TFrame' # helps show where frames are, mostly temporary
        self.style_default.configure(self.style_name, borderwidth=2, relief='solid')

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1, minsize=100)
        
        self.root.bind('<Escape>', self.remove_focus)

        # Frame Setups
        self.__setup_download()
        self.__setup_player()
        self.__setup_playlists()

    def __setup_download(self):
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
        self.var_status = StringVar(self.frm_download, value='Please enter a URL')
        self.lbl_status = Label(self.frm_download, textvariable=self.var_status)

        self.lbl_url.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.ent_url.grid(row=0, column=1, sticky='ew')
        self.btn_url.grid(row=0, column=2, padx=5, sticky='e')
        self.bar_progress.grid(row=1, column=1, pady=5, sticky='ew')
        self.lbl_status.grid(row=2, column=1, sticky='ew')

        self.btn_url.bind('<Button-1>', self.download)

    def __setup_player(self):
        '''
        Sets up track Player Frame
        '''

        # pygame Mixer
        # Eventually add 2 channels to fade music in and out with each other
        mixer.init()
        mixer.music.set_volume(self.volume.get())

        self.frm_player = Frame(self.root, style=self.style_name)
        self.frm_player.grid(row=1, column=0, padx=25, pady=25, sticky='nsew')
        self.frm_player.columnconfigure(0, weight=0, minsize=100)
        self.frm_player.columnconfigure(1, weight=1, minsize=200)
        self.frm_player.columnconfigure(2, weight=0, minsize=100)
        self.frm_player.rowconfigure(0, weight=1, minsize=50)
        self.frm_player.rowconfigure(1, weight=1, minsize=50)
        self.frm_player.rowconfigure(2, weight=1, minsize=100)

        self.var_title = StringVar(self.frm_player, value='Foo Bar')
        self.lbl_title = Label(self.frm_player, textvariable=self.var_title)

        self.var_progress = StringVar(self.frm_player, value='0:00:00')
        self.lbl_progress = Label(self.frm_player, textvariable=self.var_progress)
        self.sld_progress = Scale(self.frm_player, orient=HORIZONTAL, from_=0.0, to=100.0)
        self.var_length = StringVar(self.frm_player, value='99:99:99')
        self.lbl_length = Label(self.frm_player, textvariable=self.var_length)

        # Navigation
        self.frm_buttons = Frame(self.frm_player)
        self.frm_buttons.grid(row=2, column=1, padx=25, pady=15, sticky='nesw')
        self.frm_buttons.columnconfigure(0, weight=1)
        self.frm_buttons.columnconfigure(1, weight=1)
        self.frm_buttons.columnconfigure(2, weight=1)

        self.btn_start = Button(self.frm_buttons, text='|<<')
        self.btn_play = Button(self.frm_buttons, text='>/||')
        self.btn_end = Button(self.frm_buttons, text='>>|')
        # self.btn_shuffle = Button(self.frm_player, text='=x=')

        self.lbl_title.grid(row=0, column=0, columnspan=3, padx=5, pady=10, sticky='n')
        self.lbl_progress.grid(row=1, column=0, padx=5, pady=10, sticky='e')
        self.sld_progress.grid(row=1, column=1, padx=5, pady=10, sticky='ew')
        self.lbl_length.grid(row=1, column=2, padx=5, pady=10, sticky='w')

        self.btn_start.grid(row=0, column=0, padx=5, pady=10, sticky='e')
        self.btn_play.grid(row=0, column=1, padx=5, pady=10)
        self.btn_end.grid(row=0, column=2, padx=5, pady=10, sticky='w')

        # Volume
        self.frm_volume = Frame(self.frm_player)
        self.frm_volume.grid(row=2, column=2, padx=10, pady=15, sticky='nse')
        self.frm_volume.columnconfigure(0, weight=1, minsize=20)
        self.frm_volume.rowconfigure(0, weight=1, minsize=100)
        self.frm_volume.rowconfigure(1, weight=0, minsize=10)

        self.sld_volume = Scale(self.frm_volume, orient=VERTICAL, from_=1, to=0, variable=self.volume, command=self.update_volume)
        self.var_volume = StringVar(self.frm_volume, value=(int(100 * self.volume.get())))
        self.lbl_volume = Label(self.frm_volume, textvariable=self.var_volume)

        self.sld_volume.grid(row=0, column=0, padx=10, pady=5, sticky='nsw')
        self.lbl_volume.grid(row=1, column=0, padx=5, pady=5, sticky='n')

        # Playlist with Scrollbar
        self.frm_playlists = Frame(self.frm_player, style=self.style_name)
        self.frm_playlists.grid(row=2, column=0, padx=10, pady=15, sticky='nw')
        self.frm_playlists.columnconfigure(0, weight=1)
        self.frm_playlists.rowconfigure(0, weight=1)

        # Canvas and Scrollbar for scrolling checkbuttons
        self.cnv_playlists = Canvas(self.frm_playlists, borderwidth=0, highlightthickness=0, width= 100, height=180)
        self.scrollbar_playlists = Scrollbar(self.frm_playlists, orient=VERTICAL, command=self.cnv_playlists.yview)
        self.cnv_playlists.configure(yscrollcommand=self.scrollbar_playlists.set)

        self.cnv_playlists.grid(row=0, column=0, sticky='nsew')
        self.scrollbar_playlists.grid(row=0, column=1, sticky='ns')

        # Frame inside canvas to hold checkbuttons
        self.inner_playlists = Frame(self.cnv_playlists)
        self.cnv_playlists.create_window((0, 0), window=self.inner_playlists, anchor='nw')

        self.playlist_var_names = []
        self.cbtn_playlists = []
        self.var_playlists = []
        for i in range(10):
            self.playlist_var_names.append(StringVar(self.inner_playlists, value=self.playlists[i].name))
            self.var_playlists.append(Variable(self.inner_playlists, value=-i-1))
            self.cbtn_playlists.append(Checkbutton(self.inner_playlists, textvariable=self.playlist_var_names[i], variable=self.var_playlists[i], offvalue=-i-1, onvalue=i, command=self.toggle_playlist))
            self.cbtn_playlists[i].grid(row=i, column=0, padx=10, sticky='nw')

        self.btn_start.bind('<Button-1>', self.start)
        self.btn_play.bind('<Button-1>', self.play)
        self.btn_end.bind('<Button-1>', self.end)
        self.root.bind('<Key-space>', self.play)
        self.root.bind('<Right>', self.forward)
        self.root.bind('<Left>', self.back)
        self.root.bind('<Up>', self.volume_up)
        self.root.bind('<Down>', self.volume_down)
        self.root.bind('<KP_Home>', self.start)
        self.root.bind('<KP_End>', self.end)
        self.inner_playlists.bind("<Configure>", self._on_frame_configure)
        self.cnv_playlists.bind("<Enter>", self._bind_mousewheel)
        self.cnv_playlists.bind("<Leave>", self._unbind_mousewheel)

        mixer.music.stop()
        mixer.music.unload()
        self.var_title.set(self.filename)
        mixer.music.load(f'{self.filepath}/{self.filename}')
        hours, mins, secs = self._get_track_len(self.track_length)
        self.var_length.set(f'{hours}:{mins:02}:{secs:02}')
        mixer.music.play()
        mixer.music.pause()

    def __setup_playlists(self):
        '''
        Sets up Playlists Frame
        '''
        self.frm_playlist = Frame(self.root, style=self.style_name)
        self.frm_playlist.grid(row=1, column=1, padx=25, pady=25, sticky='nsew')

        self.frm_playlist.columnconfigure(0, weight=1, minsize=100)
        self.frm_playlist.rowconfigure(0, weight=0, minsize=10)
        self.frm_playlist.rowconfigure(1, weight=1, minsize=200)

        self.var_playlist = StringVar(self.frm_playlist, value=self.all_tracks.name)
        self.cb_playlists = Combobox(self.frm_playlist, textvariable=self.var_playlist)
        self.cb_playlists['values'] = tuple([self.all_tracks.name]) + tuple(playlist.name for playlist in self.playlists)
        self.lb_tracks = Listbox(self.frm_playlist)
        i = 1
        for track in self.playlist.get_track_names():
            self.lb_tracks.insert(i, track)
            i += 1

        self.cb_playlists.grid(row=0, column=0, padx=10, pady=5, sticky='nw')
        self.lb_tracks.grid(row=1, column=0, padx=10, pady=5, sticky='nsew')

        self.cb_playlists.bind('<<ComboboxSelected>>', self.change_playlist)

    def remove_focus(self, event):
        self.root.focus_set()

    def _yt_progress_hook(self, d):
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
        except Exception as e:
            print(f'Error unloading music: {e}')
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
                    print(f'Will save as: {filename}')
                    self.all_music.add_track(self._clean_filename(filename), filename)
                    self.root.after(0, self.var_status.set, 'Success!')
        except Exception as e:
            self.root.after(0, self.var_status.set, f'Error: {e}')

    def start(self, event):
        self.sld_progress.set(0)
        self.var_progress.set('0:00:00')
        mixer.music.rewind()
        self.last_play_time = None
        self.track_pos = 0

    def play(self, event):
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
        self.sld_progress.set(100)
        hours, mins, secs = self._get_track_len(self.track_length)
        self.var_progress.set(f'{hours}:{mins:02}:{secs:02}')
        mixer.music.fadeout(1000) # may have ot swap for manual fade in/out as it blocks during fadeout
        # mixer.music.stop()

    def forward(self, event):
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

    def volume_up(self, event):
        if self.root.focus_get() == self.root:
            self.volume.set(round(min(self.volume.get() + 0.1, 1), 2))
            mixer.music.set_volume(self.volume.get())
            self.var_volume.set(int(100 * self.volume.get()))

    def volume_down(self, event):
        if self.root.focus_get() == self.root:
            self.volume.set(round(max(self.volume.get() - 0.1, 0), 2))
            mixer.music.set_volume(self.volume.get())
            self.var_volume.set(int(100 * self.volume.get()))

    def update_volume(self, val):
        mixer.music.set_volume(self.volume.get())
        self.var_volume.set(int(float(val) * 100))

    def _start_progress_updater(self):
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
            self.sld_progress.set(100 * current_pos / self.track_length)
            # Schedule next update
            self.root.after(100, self._start_progress_updater)

    def _get_track_len(self, length):
        hours = int(length // 3600)
        length %= 3600
        mins = int(length // 60)
        length %= 60
        secs = int(length)

        return hours, mins, secs

    def _on_frame_configure(self, event):
        self.cnv_playlists.configure(scrollregion=self.cnv_playlists.bbox("all"))

    def _on_mousewheel(self, event):
        self.cnv_playlists.yview_scroll(int(-1*(event.delta/120)), "units")

    def _bind_mousewheel(self, event):
        self.cnv_playlists.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.cnv_playlists.unbind_all("<MouseWheel>")

    def change_playlist(self, event):
        print(self.var_playlist.get())

    def toggle_playlist(self, val):
        if val >=0:
            self.playlists[val].add_track(self.track_name, self.file)
        else:
            self.playlists[-val-1].remove_track(self.track_name)
        self._update_playlist(val)

    def _update_playlist(self, num): #update playlist frame
        if num >=0:
            pass
        else:
            pass

    def _clean_filename(self, file):
        index = file.index('[')
        return file[:index-1]

class Playlist:
    def __init__(self, name):
        self.name = name
        self.tracks = {}

    def set_name(self, name):
        self.name = name

    def add_track(self, name, file):
        self.tracks[name] = file

    def remove_track(self, name):
        del self.tracks[name]

    def get_track_names(self):
        names = []
        for name, _ in self.tracks.items():
            names.append(name)
        return names

    def get_tracks(self):
        tracks = []
        for _, track in self.tracks.items():
            tracks.append(track)
        return tracks

    def get_track(self, name):
        return self.tracks[name]

def main():
    root = Tk()
    MusicBox(root)
    root.mainloop()

if __name__ == '__main__':
    main()