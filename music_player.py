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
        self.root = root
        
        # Download Frame
        self.status = None  # Will be set in __setup_download
        self.bar_progress = None  # Will be set in __setup_download
        
        # Player Frame
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path += '/files'
        self.files = os.listdir(self.path)
        self.file = self.files[0]
        self.audio_info = MP3(f'{self.path}/{self.file}').info
        self.track_length = int(self.audio_info.length)
        self.track_pos = 0  # Track position in ms
        self.is_playing = False
        self.last_play_time = None
        self.volume = 0.5

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
        }

        self.root = root
        root.configure(bg='medium purple')
        root.minsize(500, 500)
        self.root.title('Adaptive Music Box')
        
        self.style_default = Style()
        self.style_name = 'Outlined.TFrame'
        self.style_default.configure(self.style_name, borderwidth=2, relief='solid')
        # self.style_default.configure(self.style_name)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        
        self.__setup_download()
        self.__setup_player()
        
    def __setup_download(self):
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
        self.status = StringVar(self.frm_download, value='Please enter a URL')
        self.lbl_status = Label(self.frm_download, textvariable=self.status)
        
        self.lbl_url.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.ent_url.grid(row=0, column=1, sticky='ew')
        self.btn_url.grid(row=0, column=2, padx=5, sticky='e')
        self.bar_progress.grid(row=1, column=1, pady=5, sticky='ew')
        self.lbl_status.grid(row=2, column=1, sticky='ew')
        
        self.btn_url.bind('<Button-1>', self.download)

    def __setup_player(self):
        
        mixer.init()
        mixer.music.set_volume(self.volume)
        
        self.frm_player = Frame(self.root, style=self.style_name)
        self.frm_player.grid(row=1, column=0, padx=50, pady=25, sticky='nsew')
        self.frm_player.columnconfigure(0, weight=0, minsize=100)
        self.frm_player.columnconfigure(1, weight=1, minsize=200)
        self.frm_player.columnconfigure(2, weight=0, minsize=100)
        self.frm_player.rowconfigure(0, weight=1, minsize=50)
        self.frm_player.rowconfigure(1, weight=1, minsize=50)
        self.frm_player.rowconfigure(2, weight=1, minsize=100)
        
        
        self.title = StringVar(self.frm_player, value='Foo Bar')
        self.lbl_title = Label(self.frm_player, textvariable=self.title)
        
        self.progress = StringVar(self.frm_player, value='0:00:00')
        self.lbl_progress = Label(self.frm_player, textvariable=self.progress)
        self.sld_progress = Scale(self.frm_player, orient=HORIZONTAL, from_=0.0, to=100.0)
        self.length = StringVar(self.frm_player, value='99:99:99')
        self.lbl_length = Label(self.frm_player, textvariable=self.length)
        
        self.frm_buttons = Frame(self.frm_player)
        self.frm_buttons.grid(row=2, column=1, padx=25, pady=15, sticky='nesw')
        self.frm_buttons.columnconfigure(0, weight=1)
        self.frm_buttons.columnconfigure(1, weight=1)
        self.frm_buttons.columnconfigure(2, weight=1)
        self.btn_start = Button(self.frm_buttons, text='|<<')
        self.btn_play = Button(self.frm_buttons, text='>/||')
        self.btn_end = Button(self.frm_buttons, text='>>|')
        # self.btn_shuffle = Button(self.frm_player, text='=x=')
        
        self.lbl_title.grid(row=0, column=1, padx=5, pady=10, sticky='n')
        self.lbl_progress.grid(row=1, column=0, padx=5, pady=10, sticky='e')
        self.sld_progress.grid(row=1, column=1, padx=5, pady=10, sticky='ew')
        self.lbl_length.grid(row=1, column=2, padx=5, pady=10, sticky='w')
        
        self.btn_start.grid(row=0, column=0, padx=5, pady=10, sticky='e')
        self.btn_play.grid(row=0, column=1, padx=5, pady=10)
        self.btn_end.grid(row=0, column=2, padx=5, pady=10, sticky='w')
        
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
        
        mixer.music.stop()
        mixer.music.unload()
        self.title.set(self.file)
        mixer.music.load(f'{self.path}/{self.file}')
        hours, mins, secs = self._get_track_len(self.track_length)
        self.length.set(f'{hours}:{mins:02}:{secs:02}')
        mixer.music.play()
        mixer.music.pause()

    def _yt_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                # Update progress bar in the main thread
                self.root.after(0, lambda: self.bar_progress.config(value=percent))
                self.root.after(0, lambda: self.status.set(f'Downloading... {percent:.1f}%'))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.bar_progress.config(value=100))
            self.root.after(0, lambda: self.status.set('Download finished, processing...'))

    def download(self, event):
        self.status.set('Preparing...')
        self.bar_progress.config(value=0)
        url = self.ent_url.get()
        URLs = [url]
        # Run download in a separate thread to avoid blocking the GUI
        threading.Thread(target=self._download_thread, args=(URLs,), daemon=True).start()

    def _download_thread(self, URLs):
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                error_code = ydl.download(URLs)
                if error_code == 0:
                    self.root.after(0, self.status.set, 'Success!')
                else:
                    self.root.after(0, self.status.set, f'Error code: {error_code}')
        except Exception as e:
            self.root.after(0, self.status.set, f'Error: {e}')

    def start(self, event):
        self.sld_progress.set(0)
        self.progress.set('0:00:00')
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
        self.progress.set(f'{hours}:{mins:02}:{secs:02}')
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
        self.progress.set(f'{hours}:{mins:02}:{secs:02}')
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
        self.progress.set(f'{hours}:{mins:02}:{secs:02}')
        if self.is_playing:
            self.last_play_time = time.time()
        else:
            self.last_play_time = None

    def volume_up(self, event):
        self.volume = min(self.volume + 0.1, 1)
        mixer.music.set_volume(self.volume)

    def volume_down(self, event):
        self.volume = max(self.volume - 0.1, 1)
        mixer.music.set_volume(self.volume)
        
    def _start_progress_updater(self):
        if self.is_playing:
            if not mixer.music.get_busy():
                # Playback finished
                self.is_playing = False
                self.track_pos = self.track_length
                hours, mins, secs = self._get_track_len(self.track_length)
                self.progress.set(f'{hours}:{mins:02}:{secs:02}')
                self.sld_progress.set(100)
                return
            # Calculate current position
            if self.last_play_time:
                elapsed = time.time() - self.last_play_time
                current_pos = self.track_pos + elapsed
            else:
                current_pos = self.track_pos
            hours, mins, secs = self._get_track_len(current_pos)
            self.progress.set(f'{hours}:{mins:02}:{secs:02}')
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

def main():
    
    root = Tk()
    MusicBox(root)
    root.mainloop()

if __name__ == '__main__':
    main()