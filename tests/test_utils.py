import os
from unittest.mock import patch

from utils import (
    clean_filename,
    extract_youtube_id,
    format_track_length,
    get_resource_path,
    get_user_data_dir,
    setup_app_directories,
)


def test_setup_app_directories_creates_files_directory(tmp_path):
    base_path = str(tmp_path)
    result = setup_app_directories(base_path)

    assert result == (
        base_path,
        os.path.join(base_path, 'files'),
        os.path.join(base_path, 'settings.json'),
    )
    assert os.path.isdir(os.path.join(base_path, 'files'))

def test_get_user_data_dir_uses_platform_conventions():
        with patch('utils.helpers.platform.system', return_value='Windows'), \
                patch.dict(os.environ, {'APPDATA': r'C:\AppData'}, clear=False):
            assert get_user_data_dir('TestApp') == os.path.join(r'C:\AppData', 'TestApp')

        with patch('utils.helpers.platform.system', return_value='Darwin'), \
                patch('utils.helpers.os.path.expanduser', return_value=r'C:\Users\test'):
            assert get_user_data_dir('TestApp') == os.path.join(
                r'C:\Users\test', 'Library', 'Application Support', 'TestApp'
            )

def test_clean_filename_and_format_track_length():
    assert clean_filename('My_Favorite_Song_[abc123].mp3') == 'My Favorite Song'
    assert format_track_length(3661.9) == (1, 1, 1)

def test_extract_youtube_id_supports_common_urls_and_rejects_invalid_values():
    video_id = 'dQw4w9WgXcQ'
    urls = (
        f'https://youtu.be/{video_id}',
        f'https://www.youtube.com/watch?v={video_id}&list=abc',
        f'https://www.youtube.com/embed/{video_id}',
    )

    for url in urls:
        assert extract_youtube_id(url) == video_id

    assert extract_youtube_id(None) is None
    assert extract_youtube_id('https://example.com/watch?v=' + video_id) is None
    assert extract_youtube_id('https://youtu.be/too-short') is None

def test_get_resource_path_uses_packaged_base_path_when_present():
    with patch.object(__import__('utils.helpers', fromlist=['sys']).sys,
                      '_MEIPASS', r'C:\bundle', create=True):
        assert get_resource_path('icon.ico') == os.path.join(r'C:\bundle', 'icon.ico')
