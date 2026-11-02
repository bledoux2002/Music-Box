from tkinter import *
from tkinter.ttk import *
from tkinter import Scale as Scl


class MusicBoxPage:
    """Build the controls for the Music Box notebook tab."""

    def __init__(self, app, frame):
        self.app = app
        self.frame = frame

    def setup(self):
        app = self.app
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=1, minsize=100)
        self._setup_download_frame()
        self._setup_current_playlist_frame()
        self._setup_player_frame()

    def _setup_download_frame(self):
        app = self.app
        app.frm_download = Frame(self.frame, style=app.style_name)
        app.frm_download.grid(row=0, column=0, padx=50, pady=25, sticky='new')
        app.frm_download.columnconfigure(0, weight=0, minsize=10)
        app.frm_download.columnconfigure(1, weight=1)
        app.frm_download.columnconfigure(2, weight=0, minsize=50)
        for row in range(3):
            app.frm_download.rowconfigure(row, weight=1, minsize=25)

        app.var_status = StringVar(value='Please enter a URL')
        app.lbl_url = Label(app.frm_download, text='URL(s):')
        app.ent_url = Entry(app.frm_download)
        app.ent_url.insert(0, 'https://youtu.be/vz_AChHftws')
        app.btn_download = Button(
            app.frm_download, text='Download', command=app.download
        )
        app.bar_progress = Progressbar(
            master=app.frm_download, orient='horizontal'
        )
        app.btn_cancel = Button(
            app.frm_download, text='Cancel', command=app.cancel_download
        )
        app.lbl_status = Label(
            app.frm_download, textvariable=app.var_status
        )

        app.lbl_url.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        app.ent_url.grid(row=0, column=1, sticky='ew')
        app.btn_download.grid(row=0, column=2, padx=5, sticky='e')
        app.bar_progress.grid(row=1, column=1, pady=5, sticky='ew')
        app.btn_cancel.grid(row=1, column=2, padx=5, sticky='e')
        app.lbl_status.grid(row=2, column=1, sticky='ew')

    def _setup_current_playlist_frame(self):
        app = self.app
        app.frm_current_playlist = Frame(self.frame, style=app.style_name)
        app.frm_current_playlist.grid(
            row=1, column=1, padx=25, pady=25, sticky='nsew'
        )
        app.frm_current_playlist.columnconfigure(0, weight=1, minsize=100)
        app.frm_current_playlist.rowconfigure(0, weight=0, minsize=10)
        app.frm_current_playlist.rowconfigure(1, weight=1, minsize=200)

        app.cb_playlists = Combobox(
            app.frm_current_playlist, textvariable=app.var_playlist
        )
        app.cb_playlists['values'] = (
            (app.playlist_all.get_name(),)
            + tuple(name for name, _ in app.playlists.items())
        )
        app.lb_tracks = Listbox(app.frm_current_playlist)
        for track in app.current_playlist.get_queue():
            app.lb_tracks.insert(END, track)

        app.cb_playlists.grid(row=0, column=0, padx=10, pady=5, sticky='nw')
        app.lb_tracks.grid(row=1, column=0, padx=10, pady=5, sticky='nsew')
        app.cb_playlists.bind('<<ComboboxSelected>>', app.change_playlist)
        app.cb_playlists.bind('<Return>', app.rename_playlist)
        app.lb_tracks.bind(
            '<Double-1>',
            lambda e: app.play_track(
                app.lb_tracks.get(app.lb_tracks.curselection()), True
            ),
        )
        app.lb_tracks.bind(
            '<Delete>',
            lambda e: app.del_track(
                app.lb_tracks.get(app.lb_tracks.curselection())
            ),
        )
        app.change_playlist(None)

    def _setup_player_frame(self):
        app = self.app
        app.frm_player = Frame(self.frame, style=app.style_name)
        app.frm_player.grid(row=1, column=0, padx=25, pady=25, sticky='nsew')
        app.frm_player.columnconfigure(0, weight=0, minsize=100)
        app.frm_player.columnconfigure(1, weight=1, minsize=200)
        app.frm_player.columnconfigure(2, weight=0, minsize=100)
        app.frm_player.rowconfigure(0, weight=1, minsize=50)
        app.frm_player.rowconfigure(1, weight=1, minsize=50)
        app.frm_player.rowconfigure(2, weight=1, minsize=100)

        app.var_title = StringVar(value=app.track_name)
        app.var_progress = StringVar(value='0:00:00')
        app.var_length = StringVar(value='0:00:00')
        app.lbl_title = Label(app.frm_player, textvariable=app.var_title)
        app.lbl_progress = Label(
            app.frm_player, textvariable=app.var_progress
        )
        app.sld_progress = Scale(
            app.frm_player, orient=HORIZONTAL, from_=0.0, to=100.0
        )
        app.lbl_length = Label(app.frm_player, textvariable=app.var_length)

        app.lbl_title.grid(
            row=0, column=0, columnspan=3, padx=5, pady=10, sticky='n'
        )
        app.lbl_progress.grid(
            row=1, column=0, padx=5, pady=10, sticky='e'
        )
        app.sld_progress.grid(
            row=1, column=1, padx=5, pady=10, sticky='ew'
        )
        app.lbl_length.grid(
            row=1, column=2, padx=5, pady=10, sticky='w'
        )
        app.sld_progress.bind('<ButtonPress-1>', app._on_slider_press)
        app.sld_progress.bind('<ButtonRelease-1>', app._on_slider_release)
        self._setup_controls_frame()
        self._setup_volume_frame()
        self._setup_playlists_frame()

    def _setup_controls_frame(self):
        app = self.app
        app.frm_controls = Frame(app.frm_player)
        app.frm_controls.grid(
            row=2, column=1, padx=25, pady=15, sticky='nesw'
        )
        for column in range(3):
            app.frm_controls.columnconfigure(column, weight=1)
        app.var_fade = StringVar(value='Fade (ms)')
        app.btn_start = Button(app.frm_controls, text='|<<')
        app.btn_play = Button(app.frm_controls, text='>/||')
        app.btn_end = Button(app.frm_controls, text='>>|')
        app.sld_fade = Scl(
            app.frm_controls, orient=HORIZONTAL, from_=0, to=5000,
            resolution=100, variable=app.fade,
        )
        app.lbl_fade = Label(
            app.frm_controls, textvariable=app.var_fade
        )
        app.cbtn_shuffle = Checkbutton(
            app.frm_controls, text='Shuffle', variable=app.shuffle,
            command=app.shuffle_toggle,
        )
        app.btn_start.grid(row=0, column=0, padx=5, pady=10, sticky='e')
        app.btn_play.grid(row=0, column=1, padx=5, pady=10)
        app.btn_end.grid(row=0, column=2, padx=5, pady=10, sticky='w')
        app.sld_fade.grid(row=1, column=0, padx=5, sticky='nw')
        app.lbl_fade.grid(row=2, column=0, padx=5, sticky='nw')
        app.cbtn_shuffle.grid(row=1, column=1, padx=5, pady=10, sticky='n')
        app.btn_start.bind('<Button-1>', app.start)
        app.btn_start.bind('<Double-1>', app.prev)
        app.btn_play.bind('<Button-1>', app.play)
        app.btn_end.bind('<Button-1>', app.end)

    def _setup_volume_frame(self):
        app = self.app
        app.frm_volume = Frame(app.frm_player)
        app.frm_volume.grid(row=2, column=2, padx=10, pady=15, sticky='nse')
        app.frm_volume.columnconfigure(0, weight=1, minsize=20)
        app.frm_volume.rowconfigure(0, weight=1, minsize=100)
        app.frm_volume.rowconfigure(1, weight=0, minsize=10)
        app.var_volume = StringVar(value=int(100 * app.volume.get()))
        app.sld_volume = Scale(
            app.frm_volume, orient=VERTICAL, from_=1, to=0,
            variable=app.volume, command=app.update_volume,
        )
        app.lbl_volume = Label(
            app.frm_volume, textvariable=app.var_volume
        )
        app.sld_volume.grid(row=0, column=0, padx=10, pady=5, sticky='nsw')
        app.lbl_volume.grid(row=1, column=0, padx=5, pady=5, sticky='n')

    def _setup_playlists_frame(self):
        app = self.app
        app.frm_playlists = Frame(app.frm_player, style=app.style_name)
        app.frm_playlists.grid(
            row=2, column=0, padx=10, pady=15, sticky='nsw'
        )
        app.frm_playlists.columnconfigure(0, weight=1)
        app.frm_playlists.rowconfigure(0, weight=1)
        app.cnv_playlists = Canvas(
            app.frm_playlists, borderwidth=0, highlightthickness=0,
            width=100, height=180,
        )
        app.scrollbar_playlists = Scrollbar(
            app.frm_playlists, orient=VERTICAL,
            command=app.cnv_playlists.yview,
        )
        app.cnv_playlists.configure(
            yscrollcommand=app.scrollbar_playlists.set
        )
        app.cnv_playlists.grid(row=0, column=0, sticky='nsew')
        app.scrollbar_playlists.grid(row=0, column=1, sticky='ns')
        app.frm_playlists_inner = Frame(app.cnv_playlists)
        app.cnv_playlists.create_window(
            (0, 0), window=app.frm_playlists_inner, anchor='nw'
        )

        app.playlist_var_names = []
        app.var_playlists = []
        app.cbtn_playlists = []
        for index, (playlist_name, _) in enumerate(app.playlists.items()):
            app.playlist_var_names.append(StringVar(value=playlist_name))
            playlists = (
                app.tracks[app.filename].get_playlists()
                if app.filename else []
            )
            value = index if playlist_name in playlists else -index - 1
            app.var_playlists.append(Variable(value=value))
            app.cbtn_playlists.append(Checkbutton(
                app.frm_playlists_inner,
                textvariable=app.playlist_var_names[index],
                variable=app.var_playlists[index],
                offvalue=-index - 1,
                onvalue=index,
                command=lambda idx=index: app.edit_playlists(idx),
            ))
            app.cbtn_playlists[index].grid(
                row=index, column=0, padx=10, sticky='nw'
            )
        app.frm_playlists_inner.bind(
            '<Configure>', app._on_frame_configure
        )
        app.cnv_playlists.bind('<Enter>', app._bind_mousewheel)
        app.cnv_playlists.bind('<Leave>', app._unbind_mousewheel)
