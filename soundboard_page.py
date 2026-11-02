import os
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


class SoundboardPage:
    """Build and refresh the Soundboard notebook tab."""

    def __init__(self, app, frame):
        self.app = app
        self.frame = frame
        self.buttons_frame = None

    def setup(self):
        app = self.app
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        # Label(
        #     self.frame,
        #     text='Soundboard',
        #     font=('TkDefaultFont', 14, 'bold'),
        # ).grid(row=0, column=0, padx=20, pady=(20, 5), sticky='w')
        self.buttons_frame = Frame(self.frame)
        self.buttons_frame.grid(
            row=1, column=0, padx=20, pady=10, sticky='nsew'
        )
        self.refresh()

    def refresh(self):
        app = self.app
        if self.buttons_frame is None:
            return
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        try:
            filenames = sorted(
                filename for filename in os.listdir(app.filepath)
                if filename.lower().endswith(
                    ('.mp3', '.ogg', '.wav', '.flac')
                )
            )
        except OSError as error:
            app.logger.exception(
                'Unable to read soundboard files from %s', app.filepath
            )
            messagebox.showerror('Error', f'Unable to read audio files: {error}')
            return

        for index, filename in enumerate(filenames):
            Button(
                self.buttons_frame,
                text=os.path.splitext(filename)[0].replace('_', ' '),
                command=lambda name=filename: app.play_soundboard_track(name),
            ).grid(
                row=index // 4, column=index % 4, padx=8, pady=8,
                sticky='nsew',
            )
        for column in range(4):
            self.buttons_frame.columnconfigure(column, weight=1)
        if not filenames:
            Label(
                self.buttons_frame,
                text='Download audio files to add buttons to the soundboard.',
            ).grid(row=0, column=0, columnspan=4, padx=10, pady=20)

    def on_tab_changed(self, event):
        if self.app.notebook.select() == str(self.frame):
            self.refresh()
