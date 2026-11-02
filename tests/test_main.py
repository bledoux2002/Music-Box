import json
import os
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

from MusicBox import MusicBox
from utils.tracks import Playlist, Track


class Value:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def __setitem__(self, key, value):
        setattr(self, key, value)


class Slider(Value):
    pass


class Widget:
    def __init__(self, value=None):
        self.value = value
        self.calls = []

    def config(self, **kwargs):
        self.calls.append(kwargs)

    def delete(self, *args):
        self.calls.append(('delete', args))

    def insert(self, *args):
        self.calls.append(('insert', args))

    def set(self, value):
        self.value = value

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def get(self, *args):
        return self.value

    def winfo_children(self):
        return []

    def columnconfigure(self, *args, **kwargs):
        self.calls.append(('columnconfigure', args, kwargs))

    def selection_set(self, value):
        self.calls.append(('selection_set', value))

    def selection_clear(self, *args):
        self.calls.append(('selection_clear', args))


class TestMusicBox:
    def make_box(self):
        box = object.__new__(MusicBox)
        box.root = SimpleNamespace(
            focus_get=lambda: box.root,
            focus_set=lambda: None,
        )
        box.cb_playlists = object()
        box.ent_url = object()
        box.sld_progress = Slider(0)
        box.var_progress = Value('')
        box.track_length = 60
        box.track_pos = 0
        box.is_playing = False
        box.last_play_time = None
        box.progress_bar_in_use = False
        return box

    def make_playback_box(self):
        box = self.make_box()
        box.volume = Value(0.5)
        box.var_volume = Value()
        box.fade = Value(1000)
        box.var_title = Value()
        box.var_length = Value()
        box.lb_tracks = Widget()
        box.var_status = Value()
        box.bar_progress = Widget()
        box.cancel_flag = threading.Event()
        box.cur_download = 0
        box.filepath = ''
        return box

    def test_url_and_formatting_helpers_delegate_to_expected_behavior(self):
        box = self.make_box()

        assert box._extract_youtube_id('https://youtu.be/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'
        assert box._get_track_len(3661.9) == (1, 1, 1)
        assert box.clean_filename('My_Favorite_Song_[abc123].mp3') == 'My Favorite Song'

    def test_forward_and_back_clamp_track_position_and_update_display(self, monkeypatch):
        box = self.make_box()
        fake_music = Mock()

        monkeypatch.setattr('MusicBox.mixer.music', fake_music)
        box.track_pos = 58
        box.forward(None)
        assert box.track_pos == 60
        assert box.sld_progress.get() == 100
        assert box.var_progress.get() == '0:01:00'

        box.back(None)
        assert box.track_pos == 55
        assert box.sld_progress.get() == 100 * 55 / 60
        assert box.var_progress.get() == '0:00:55'

        fake_music.set_pos.assert_any_call(60)
        fake_music.set_pos.assert_any_call(55)

    def test_load_settings_reads_saved_values_and_existing_track(self, tmp_path):
        box = self.make_box()
        filename = 'Saved_Track_[abc123].mp3'
        box.settings_path = str(tmp_path / 'settings.json')
        box.filepath = str(tmp_path / 'files')
        os.mkdir(box.filepath)
        (tmp_path / 'files' / filename).touch()
        box.var_playlist = Value()
        box.shuffle = Value()
        box.volume = Value()
        box.fade = Value()
        box.settings = {
            'current playlist': 'Favorites',
            'current track': filename,
            'track position': 12.5,
            'shuffle': True,
            'volume': 0.75,
            'fade': 500,
        }
        with open(box.settings_path, 'w', encoding='utf-8') as settings_file:
            json.dump(box.settings, settings_file)

        box._MusicBox__load_settings()

        assert box.var_playlist.get() == 'Favorites'
        assert box.filename == filename
        assert box.track_name == 'Saved Track'
        assert box.track_pos == 12.5
        assert box.shuffle.get()
        assert box.volume.get() == 0.75
        assert box.fade.get() == 500

    def test_setup_playlists_rebuilds_saved_playlists_from_available_files(self, tmp_path):
        box = object.__new__(MusicBox)
        first = 'First_Song_[11111111111].mp3'
        second = 'Second_Song_[22222222222].mp3'
        (tmp_path / first).touch()
        (tmp_path / second).touch()
        box.filepath = str(tmp_path)
        box.playlist_all = Playlist('All')
        box.tracks = {}
        box.playlists = {}
        box.settings = {
            'current playlist': 'Favorites',
            'shuffle': False,
            'queue position': 1,
            'playlists': {
                'Favorites': [first, 'missing.mp3'],
            },
        }

        box._MusicBox__setup_playlists()

        assert box.playlist_all.get_track_names() == ['First Song', 'Second Song']
        assert box.playlists['Favorites'].get_track_names() == ['First Song']
        assert box.tracks[first].get_playlists() == {'Favorites'}
        assert box.playlists['Favorites'].get_queue_position() == 1

    def test_save_settings_persists_player_and_playlist_state(self, tmp_path):
        box = self.make_box()
        box.settings_path = str(tmp_path / 'settings.json')
        box.track_name = 'Song'
        box.filename = 'Song_[id].mp3'
        box.track_length = 100
        box.sld_progress = Slider(25)
        box.settings = {}
        box.current_playlist = Playlist('Favorites')
        box.current_playlist.add_track('Song', box.filename)
        box.current_playlist.set_queue_pos(0)
        box.playlists = {'Favorites': box.current_playlist}
        box.shuffle = Value(False)
        box.volume = Value(0.75)
        box.fade = Value(500)

        box._MusicBox__save_settings()

        saved = json.loads((tmp_path / 'settings.json').read_text())
        assert saved['current playlist'] == 'Favorites'
        assert saved['current track'] == box.filename
        assert saved['track position'] == 25
        assert saved['playlists'] == {'Favorites': [box.filename]}

    def test_soundboard_refresh_builds_buttons_for_audio_files(self, tmp_path, monkeypatch):
        box = object.__new__(MusicBox)
        box.filepath = str(tmp_path)
        (tmp_path / 'zeta.mp3').touch()
        (tmp_path / 'alpha.wav').touch()
        (tmp_path / 'ignore.txt').touch()
        box.frm_soundboard_buttons = Widget()
        created = []

        class FakeButton:
            def __init__(self, parent, **kwargs):
                created.append(kwargs)

            def grid(self, **kwargs):
                created[-1]['grid'] = kwargs

        monkeypatch.setattr('MusicBox.Button', FakeButton)
        monkeypatch.setattr('MusicBox.Label', FakeButton)
        box._refresh_soundboard()

        assert [button['text'] for button in created] == ['alpha', 'zeta']
        assert sum(
            call[0] == 'columnconfigure' for call in box.frm_soundboard_buttons.calls
        ) == 4

    def test_empty_soundboard_shows_download_hint(self, tmp_path, monkeypatch):
        box = object.__new__(MusicBox)
        box.filepath = str(tmp_path)
        box.frm_soundboard_buttons = Widget()
        created = []

        class FakeLabel:
            def __init__(self, parent, **kwargs):
                created.append(kwargs)

            def grid(self, **kwargs):
                created[-1]['grid'] = kwargs

        monkeypatch.setattr('MusicBox.Label', FakeLabel)
        box._refresh_soundboard()

        assert created[0]['text'].startswith('Download audio files')

    def test_soundboard_playback_reports_errors(self, monkeypatch):
        box = self.make_playback_box()
        music = Mock()
        monkeypatch.setattr('MusicBox.mixer.music', music)
        box.filepath = 'files'

        box.play_soundboard_track('sound.wav')
        music.load.assert_called_once_with(os.path.join('files', 'sound.wav'))
        assert box.is_playing is False

        music.load.side_effect = RuntimeError('audio unavailable')
        with patch('MusicBox.messagebox.showerror') as show_error:
            box.play_soundboard_track('sound.wav')
        show_error.assert_called_once()

    def test_download_progress_hook_updates_status_and_honors_cancel(self):
        box = self.make_playback_box()
        box.root = SimpleNamespace(after=lambda delay, callback: callback())
        box.filename = 'current_[id].mp3'
        box.clean_filename = lambda name: name.split('[')[0].rstrip('_')
        box._yt_progress_hook({
            'status': 'downloading',
            'filename': 'new_song_[abc].mp3',
            'total_bytes': 200,
            'downloaded_bytes': 100,
        })
        assert box.bar_progress.calls[-1] == {'value': 50.0}
        assert 'Downloading new_song' in box.var_status.get()

        box._yt_progress_hook({
            'status': 'finished',
            'filename': 'new_song_[abc].mp3',
        })
        assert box.bar_progress.calls[-1] == {'value': 100}
        assert 'finished' in box.var_status.get()

        box.cancel_flag.set()
        try:
            box._yt_progress_hook({'status': 'finished', 'filename': 'x'})
        except Exception as error:
            assert str(error) == 'Download cancelled by user'
        else:
            raise AssertionError('Cancelled hook did not raise')

    def test_cancel_download_removes_partial_files(self, tmp_path):
        box = self.make_playback_box()
        box.filepath = str(tmp_path)
        box.var_status = Value()
        box.bar_progress = Widget()
        (tmp_path / 'partial.mp3.part').touch()
        (tmp_path / 'complete.mp3').touch()

        box.cancel_download()

        assert not (tmp_path / 'partial.mp3.part').exists()
        assert box.var_status.get() == 'Download cancelled'
        assert box.bar_progress.calls[-1] == {'value': 0}

    def test_seek_volume_and_progress_update(self, monkeypatch):
        box = self.make_playback_box()
        box.sld_progress = Slider(50)
        box.track_length = 100
        music = Mock()
        music.get_busy.return_value = True
        monkeypatch.setattr('MusicBox.mixer.music', music)
        monkeypatch.setattr('MusicBox.time.time', lambda: 10)
        box.is_playing = False

        box.seek_track(None)
        assert box.track_pos == 50
        assert box.var_progress.get() == '0:00:50'
        box.volume_up(None)
        box.volume_down(None)
        box.update_volume('0.25')
        assert box.var_volume.get() == 25
        music.set_pos.assert_called_with(50)

    def test_progress_updater_transitions_when_track_finishes(self, monkeypatch):
        box = self.make_playback_box()
        box.track_length = 90
        box.is_playing = True
        box.last_play_time = None
        box.root = SimpleNamespace(after=Mock())
        music = Mock()
        music.get_busy.return_value = False
        monkeypatch.setattr('MusicBox.mixer.music', music)
        box._transition = Mock()

        box._start_progress_updater()

        assert box.is_playing is False
        assert box.track_pos == 90
        assert box.sld_progress.get() == 100
        box._transition.assert_called_once_with(1)

    def test_playlist_editing_and_navigation_update_widgets(self):
        box = self.make_playback_box()
        favorite = Playlist('Favorites')
        box.playlists = {'Favorites': favorite}
        box.playlist_all = Playlist('All')
        box.current_playlist = favorite
        box.track_name = 'Song'
        box.filename = 'song.mp3'
        box.tracks = {'song.mp3': Track()}
        box.lb_tracks = Widget()
        box.var_playlists = [Value(0)]
        box.cb_playlists = Widget('All')
        box.ent_url = object()
        box.change_playlist = Mock()

        box.edit_playlists(0)
        assert favorite.get_track_names() == ['Song']
        assert box.tracks['song.mp3'].get_playlists() == {'Favorites'}

        box.playlists = {'Favorites': favorite, 'Other': Playlist('Other')}
        box.cb_playlists.set('Other')
        box.change_playlist = MusicBox.change_playlist.__get__(box)
        box.change_playlist(None)
        assert box.current_playlist.get_name() == 'Other'

    def test_on_close_saves_settings_removes_parts_and_destroys_root(self, tmp_path):
        box = self.make_playback_box()
        box.settings_path = str(tmp_path / 'settings.json')
        box.settings = {}
        box.track_name = ''
        box.filename = ''
        box.current_playlist = Playlist('All')
        box.playlists = {}
        box.shuffle = Value(False)
        box.volume = Value(0.5)
        box.fade = Value(1000)
        box.filepath = str(tmp_path)
        (tmp_path / 'download.part').touch()
        box.root = Mock()

        box.on_close()

        assert not (tmp_path / 'download.part').exists()
        box.root.destroy.assert_called_once_with()

    def test_download_starts_background_worker_with_entered_urls(self):
        box = self.make_playback_box()
        box.ent_url = Value(' first,second ')
        started = {}

        class FakeThread:
            def __init__(self, **kwargs):
                started.update(kwargs)

            def start(self):
                started['started'] = True

        with patch('MusicBox.threading.Thread', FakeThread):
            box.download()

        assert box.var_status.get() == 'Preparing...'
        assert box.bar_progress.calls[-1] == {'value': 0}
        assert started['args'] == ([' first', 'second '],)
        assert started['started'] is True

    def test_download_thread_reports_single_and_playlist_success(self, monkeypatch):
        box = self.make_playback_box()
        box.root = SimpleNamespace(after=lambda delay, callback: callback())
        box.ydl_opts = {}
        box.filename = ''
        music = Mock()
        music.get_busy.return_value = False
        monkeypatch.setattr('MusicBox.mixer.music', music)

        class FakeYDL:
            def __init__(self, options):
                self.options = options

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def add_post_processor(self, processor):
                self.processor = processor

            def extract_info(self, url, download):
                if url == 'playlist':
                    return {'entries': [1, 2]}
                return {'title': 'single'}

        monkeypatch.setattr('MusicBox.YoutubeDL', FakeYDL)
        box._download_thread([' single ', 'playlist'])

        assert box.var_status.get() == 'Playlist download complete! Downloaded 0 out of 2 tracks.'

    def test_download_thread_reports_errors(self, monkeypatch):
        box = self.make_playback_box()
        box.root = SimpleNamespace(after=lambda delay, callback: callback())
        box.ydl_opts = {}

        class FailingYDL:
            def __init__(self, options):
                pass

            def __enter__(self):
                raise RuntimeError('network unavailable')

            def __exit__(self, *args):
                return False

        monkeypatch.setattr('MusicBox.YoutubeDL', FailingYDL)
        with patch('MusicBox.messagebox.showerror') as show_error:
            box._download_thread(['url'])

        assert box.var_status.get() == 'Error'
        show_error.assert_called_once()

    def test_play_track_loads_audio_and_updates_player(self, monkeypatch):
        box = self.make_playback_box()
        box.current_playlist = Playlist('All')
        box.current_playlist.add_track('Song', 'song.mp3')
        box.current_playlist.set_queue_pos(0)
        box.tracks = {'song.mp3': Track()}
        box.playlist_var_names = [Value('Favorites')]
        box.var_playlists = [Value()]
        box.lb_tracks = Widget()
        box.filepath = 'files'
        box.start = Mock()
        box.play = Mock()
        box.audio_info = SimpleNamespace(length=125)
        box.fade = Value(400)
        music = Mock()
        monkeypatch.setattr('MusicBox.mixer.music', music)
        monkeypatch.setattr(
            'MusicBox.MP3',
            Mock(return_value=SimpleNamespace(info=box.audio_info)),
        )

        box.play_track('Song', set_queue_pos=True)

        assert box.filename == 'song.mp3'
        assert box.track_length == 125
        assert box.var_title.get() == 'Song'
        assert box.var_length.get() == '0:02:05'
        box.start.assert_called_once_with(None)
        box.play.assert_called_once_with(None)
        music.load.assert_called_once_with(os.path.join('files', 'song.mp3'))

    def test_delete_track_removes_file_and_state(self, tmp_path, monkeypatch):
        box = self.make_playback_box()
        filename = 'Song_[id].mp3'
        (tmp_path / filename).touch()
        box.filepath = str(tmp_path)
        box.playlist_all = Playlist('All')
        box.playlist_all.add_track('Song', filename)
        box.tracks = {filename: Track()}
        box.track_name = 'Song'
        box.filename = filename
        box.var_title = Value()
        box.var_length = Value()
        box.change_playlist = Mock()
        box.top_delete = Mock()
        music = Mock()
        monkeypatch.setattr('MusicBox.mixer.music', music)

        box.on_delete('Song')

        assert not (tmp_path / filename).exists()
        assert box.filename == ''
        assert box.track_name == ''
        assert filename not in box.tracks
        box.top_delete.destroy.assert_called_once_with()

    def test_play_pause_navigation_and_volume_controls(self, monkeypatch):
        box = self.make_playback_box()
        box.track_name = 'Song'
        box.track_length = 60
        box._start_progress_updater = Mock()
        transition = Mock()
        box._transition = transition
        box.last_play_time = 1
        music = Mock()
        music.get_busy.side_effect = [True, False]
        monkeypatch.setattr('MusicBox.mixer.music', music)
        monkeypatch.setattr('MusicBox.time.time', Mock(side_effect=[11, 20]))

        box.play(None)
        assert box.is_playing is False
        assert box.track_pos == 10
        box.play(None)
        assert box.is_playing is True
        box.start(None)
        assert box.track_pos == 0
        box.prev(None)
        box.end(None)
        transition.assert_any_call(-1)
        transition.assert_any_call(1)

        box.volume_up(None)
        assert box.volume.get() == 0.6
        box.volume_down(None)
        assert box.volume.get() == 0.5
        music.set_volume.assert_called()

    def test_slider_callbacks_and_frame_configuration(self):
        box = self.make_playback_box()
        box.sld_progress = Slider(50)
        box.track_length = 100
        box.cnv_playlists = Mock()
        box.cnv_playlists.bbox.return_value = (0, 0, 20, 20)
        box.seek_track = Mock()

        box._on_slider_press(None)
        assert box.progress_bar_in_use is True
        box._on_slider_release('event')
        assert box.progress_bar_in_use is False
        box.seek_track.assert_called_once_with('event')
        box._on_frame_configure(None)
        box.cnv_playlists.configure.assert_called_once_with(
            scrollregion=(0, 0, 20, 20)
        )

    def test_shuffle_transition_and_playlist_rename(self, monkeypatch):
        box = self.make_playback_box()
        playlist = Playlist('Favorites')
        playlist.add_track('Song', 'song.mp3')
        box.current_playlist = playlist
        box.playlists = {'Favorites': playlist}
        box.shuffle = Value(True)
        box.change_playlist = Mock()
        box.shuffle_toggle()
        assert playlist.get_queue_pos() == 0
        box.shuffle.set(False)
        box.shuffle_toggle()
        box.change_playlist.assert_called()

        box.fade = Value(400)
        box.lb_tracks = Widget()
        box.play_track = Mock()
        music = Mock()
        monkeypatch.setattr('MusicBox.mixer.music', music)
        box._transition(1)
        music.fadeout.assert_called_once_with(400)
        box.play_track.assert_called_once_with('Song')

        box.current_playlist = playlist
        box.playlist_all = Playlist('All')
        box.cb_playlists = Widget('Renamed')
        box.var_playlists = []
        box.playlist_var_names = []
        box.tracks = {'song.mp3': Track()}
        box.remove_focus = Mock()
        box.rename_playlist(None)
        assert 'Renamed' in box.playlists
        assert box.tracks['song.mp3'].get_playlists() == {'Renamed'}

    def test_rename_playlist_rejects_reserved_and_duplicate_names(self):
        box = self.make_playback_box()
        box.playlist_all = Playlist('All')
        box.current_playlist = box.playlist_all
        box.playlists = {}
        box.cb_playlists = Widget('New Name')
        with patch('MusicBox.messagebox.showerror') as show_error:
            box.rename_playlist(None)
        show_error.assert_called_once()
        assert box.cb_playlists.get() == 'All'

        playlist = Playlist('Favorites')
        box.current_playlist = playlist
        box.playlists = {'Favorites': playlist, 'Other': Playlist('Other')}
        box.cb_playlists = Widget('Other')
        with patch('MusicBox.messagebox.showerror') as show_error:
            box.rename_playlist(None)
        show_error.assert_called_once()
        assert box.cb_playlists.get() == 'Favorites'

    def test_load_settings_creates_defaults_when_file_is_missing(self, tmp_path):
        box = self.make_box()
        box.settings_path = str(tmp_path / 'missing.json')
        box.filepath = str(tmp_path)
        box.var_playlist = Value()
        box.shuffle = Value()
        box.volume = Value()
        box.fade = Value()

        box._MusicBox__load_settings()

        assert box.settings['current playlist'] == 'All'
        assert len(box.settings['playlists']) == 10
        assert box.volume.get() == 0.5

    def test_playlist_navigation_and_canvas_callbacks(self):
        box = self.make_playback_box()
        box.playlist_all = Playlist('All')
        box.playlist_all.add_track('All Song', 'all.mp3')
        other = Playlist('Other')
        other.add_track('Other Song', 'other.mp3')
        box.playlists = {'Other': other}
        box.current_playlist = box.playlist_all
        box.cb_playlists = Widget('All')
        box.ent_url = object()
        box.lb_tracks = Widget()
        box.change_playlist_kb(-1)
        assert box.current_playlist is box.playlist_all
        box.change_playlist_kb(0)
        assert box.current_playlist is other
        box.cnv_playlists = Mock()
        box._on_mousewheel(SimpleNamespace(delta=240))
        box._bind_mousewheel(None)
        box._unbind_mousewheel(None)
        box.remove_focus(None)
        assert box.root.focus_get() is box.root
