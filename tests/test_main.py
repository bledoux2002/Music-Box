import json
import os
from types import SimpleNamespace
from unittest.mock import Mock

from MusicBox import MusicBox
from utils.tracks import Playlist


class Value:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Slider(Value):
    pass


class TestMusicBox:
    def make_box(self):
        box = object.__new__(MusicBox)
        box.root = SimpleNamespace(focus_get=lambda: box.root)
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

    def test_url_and_formatting_helpers_delegate_to_expected_behavior(self):
        box = self.make_box()

        assert box._extract_youtube_id('https://youtu.be/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'
        assert box._get_track_len(3661.9) == (1, 1, 1)
        assert box.clean_filename('My_Favorite_Song_[abc123].mp3') == 'My Favorite Song'

    def test_forward_and_back_clamp_track_position_and_update_display(self, monkeypatch):
        box = self.make_box()
        fake_music = Mock()

        monkeypatch.setattr('main.mixer.music', fake_music)
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
