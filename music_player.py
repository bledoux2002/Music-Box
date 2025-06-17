import os
from tkinter import *
from tkinter.ttk import *
import threading
from yt_dlp import YoutubeDL

class MusicBox:
    
    def __init__(self, root):
        self.root = root
        self.status = None  # Will be set in __setup_download
        self.bar_progress = None  # Will be set in __setup_download

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'windowsFilenames': True,
            'paths': {
                'home': './sound/files',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'progress_hooks': [self.yt_progress_hook]
        }
        
        # self.path = os.path.dirname(os.path.abspath(__file__))

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
        self.frm_player = Frame(self.root, style=self.style_name)
        self.frm_player.grid(row=1, column=0, padx=50, pady=25, sticky='nsew')
        self.frm_player.columnconfigure(0, weight=0, minsize=100)
        self.frm_player.columnconfigure(1, weight=1, minsize=200)
        self.frm_player.columnconfigure(2, weight=0, minsize=100)
        self.frm_player.rowconfigure(0, weight=1, minsize=50)
        self.frm_player.rowconfigure(1, weight=1, minsize=50)
        self.frm_player.rowconfigure(2, weight=1, minsize=100)
        
        
        self.title = StringVar(self.frm_player, value="Foo Bar")
        self.lbl_title = Label(self.frm_player, textvariable=self.title)
        
        self.progress = StringVar(self.frm_player, value="0:00")
        self.lbl_progress = Label(self.frm_player, textvariable=self.progress)
        self.sld_progress = Scale(self.frm_player, orient=HORIZONTAL, from_=0.0, to=100.0)
        self.length = StringVar(self.frm_player, value="99:99")
        self.lbl_length = Label(self.frm_player, textvariable=self.length)
        
        self.frm_buttons = Frame(self.frm_player)
        self.frm_buttons.grid(row=2, column=1, padx=25, pady=15, sticky='nesw')
        self.frm_buttons.columnconfigure(0, weight=1)
        self.frm_buttons.columnconfigure(1, weight=1)
        self.frm_buttons.columnconfigure(2, weight=1)
        self.btn_prev = Button(self.frm_buttons, text="|<<")
        self.btn_play = Button(self.frm_buttons, text=">/||")
        self.btn_next = Button(self.frm_buttons, text=">>|")
        # self.btn_shuffle = Button(self.frm_player, text="=x=")
        
        self.lbl_title.grid(row=0, column=1, padx=5, pady=10, sticky='n')
        self.lbl_progress.grid(row=1, column=0, padx=5, pady=10, sticky='e')
        self.sld_progress.grid(row=1, column=1, padx=5, pady=10, sticky='ew')
        self.lbl_length.grid(row=1, column=2, padx=5, pady=10, sticky='w')
        
        self.btn_prev.grid(row=0, column=0, padx=5, pady=10, sticky='e')
        self.btn_play.grid(row=0, column=1, padx=5, pady=10)
        self.btn_next.grid(row=0, column=2, padx=5, pady=10, sticky='w')
        
        self.btn_prev.bind('<Button-1>', self.prev)
        self.btn_play.bind('<Button-1>', self.play)
        self.btn_next.bind('<Button-1>', self.next)

    def yt_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                # Update progress bar in the main thread
                self.root.after(0, lambda: self.bar_progress.config(value=percent))
                self.root.after(0, lambda: self.status.set(f"Downloading... {percent:.1f}%"))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.bar_progress.config(value=100))
            self.root.after(0, lambda: self.status.set("Download finished, processing..."))

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
                    self.root.after(0, self.status.set, f"Error code: {error_code}")
        except Exception as e:
            self.root.after(0, self.status.set, f'Error: {e}')

    def prev(self, event):
        self.sld_progress.set(0)
    
    def play(self, event):
        video = None
    
    def next(self, event):
        self.sld_progress.set(100)

def main():
    
    root = Tk()
    MusicBox(root)
    root.mainloop()

if __name__ == '__main__':
    main()